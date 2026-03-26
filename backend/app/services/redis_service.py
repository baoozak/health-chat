"""
Redis 缓存服务
提供两大核心功能：
1. 会话历史消息缓存 (Cache-Aside)：减少 MongoDB 高频读取压力
2. JWT Token 黑名单：用户主动登出后使 token 立即失效

设计原则：
- 所有操作在 Redis 不可用时均降级处理（graceful degradation），不影响主流程
- Key 命名规范：chat_history:{user_id}:{session_id} / token_blacklist:{token}
"""
import json
import logging
from typing import List, Dict, Optional

import redis.asyncio as aioredis

from config.settings import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis 异步服务类
    使用 redis-py 的异步客户端，与 FastAPI 异步框架完全兼容
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def get_client(self) -> Optional[aioredis.Redis]:
        """
        获取 Redis 客户端（懒加载 + 连接池复用）

        Returns:
            Redis 异步客户端，连接失败时返回 None（降级处理）
        """
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,  # 2秒连接超时，快速降级
                    socket_timeout=2,
                )
                # 发送 PING 验证连接是否真实可用
                await self._client.ping()
                logger.info(f"Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis 连接失败，将降级为直接读取 MongoDB: {e}")
                self._client = None
        return self._client

    async def close(self):
        """关闭 Redis 连接（应在应用关闭时调用）"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Redis 连接已关闭")

    # ─────────────────────────────────────────────────────────
    # 会话历史缓存 (Cache-Aside Pattern)
    # ─────────────────────────────────────────────────────────

    def _chat_cache_key(self, user_id: int, session_id: str) -> str:
        """生成会话历史缓存 Key"""
        return f"chat_history:{user_id}:{session_id}"

    async def get_cached_messages(
        self, user_id: int, session_id: str
    ) -> Optional[List[Dict]]:
        """
        从 Redis 获取缓存的会话历史消息

        Cache-Aside 读取流程：
          1. 先查 Redis → 命中则直接返回（快速路径）
          2. 未命中则返回 None → 调用方去 MongoDB 查询后调用 set_cached_messages 写入

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            消息列表，缓存不存在或 Redis 不可用时返回 None
        """
        client = await self.get_client()
        if client is None:
            return None
        try:
            key = self._chat_cache_key(user_id, session_id)
            raw = await client.get(key)
            if raw:
                messages = json.loads(raw)
                logger.debug(f"Redis 缓存命中: {key}，共 {len(messages)} 条消息")
                return messages
            logger.debug(f"Redis 缓存未命中: {key}")
            return None
        except Exception as e:
            logger.warning(f"Redis 读取会话历史失败（降级）: {e}")
            return None

    async def set_cached_messages(
        self,
        user_id: int,
        session_id: str,
        messages: List[Dict],
    ) -> bool:
        """
        将会话历史写入 Redis 缓存

        Args:
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表（MongoDB 原始格式）

        Returns:
            是否写入成功
        """
        client = await self.get_client()
        if client is None:
            return False
        try:
            key = self._chat_cache_key(user_id, session_id)
            # 序列化：datetime 等非 JSON 序列化对象需转为字符串
            serializable = []
            for msg in messages:
                m = dict(msg)
                if "timestamp" in m and hasattr(m["timestamp"], "isoformat"):
                    m["timestamp"] = m["timestamp"].isoformat()
                # 不缓存 base64 图片数据（太大，意义不大）
                m.pop("image_data", None)
                serializable.append(m)
            await client.setex(
                key,
                settings.REDIS_CHAT_CACHE_TTL,
                json.dumps(serializable, ensure_ascii=False),
            )
            logger.debug(f"Redis 缓存写入成功: {key}，TTL={settings.REDIS_CHAT_CACHE_TTL}s")
            return True
        except Exception as e:
            logger.warning(f"Redis 写入会话历史失败（降级）: {e}")
            return False

    async def invalidate_session_cache(self, user_id: int, session_id: str) -> bool:
        """
        使会话缓存失效（发送新消息后调用，保持缓存一致性）

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        client = await self.get_client()
        if client is None:
            return False
        try:
            key = self._chat_cache_key(user_id, session_id)
            await client.delete(key)
            logger.debug(f"Redis 缓存已失效: {key}")
            return True
        except Exception as e:
            logger.warning(f"Redis 缓存失效操作失败（降级）: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # JWT Token 黑名单
    # ─────────────────────────────────────────────────────────

    def _blacklist_key(self, token: str) -> str:
        """生成黑名单 Key（使用完整 Token 的 SHA256 哈希，避免前缀碰撞导致误判）"""
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"token_blacklist:{token_hash}"

    async def blacklist_token(self, token: str) -> bool:
        """
        将 JWT Token 加入黑名单（用户登出时调用）

        TTL 与 token 有效期保持一致，过期后自动清除无需手动维护

        Args:
            token: JWT token 字符串

        Returns:
            是否操作成功
        """
        client = await self.get_client()
        if client is None:
            logger.warning("Redis 不可用，登出时无法写入 Token 黑名单")
            return False
        try:
            key = self._blacklist_key(token)
            await client.setex(key, settings.REDIS_TOKEN_BLACKLIST_TTL, "1")
            logger.info(f"Token 已加入黑名单: {token[:20]}...")
            return True
        except Exception as e:
            logger.warning(f"Redis 写入 Token 黑名单失败（降级）: {e}")
            return False

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        检查 Token 是否在黑名单中

        Args:
            token: JWT token 字符串

        Returns:
            True 表示 Token 已被吊销，False 表示有效（含 Redis 不可用时降级为 False）
        """
        client = await self.get_client()
        if client is None:
            return False  # Redis 不可用时降级：允许通过（不影响正常使用）
        try:
            key = self._blacklist_key(token)
            result = await client.exists(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis 查询 Token 黑名单失败（降级允许）: {e}")
            return False

    async def ping(self) -> bool:
        """健康检查：测试 Redis 连接是否正常"""
        client = await self.get_client()
        if client is None:
            return False
        try:
            return await client.ping()
        except Exception:
            return False


# ─── 全局单例 ─────────────────────────────────────────────────────────────────
redis_service = RedisService()
