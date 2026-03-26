"""
聊天API路由
提供聊天相关的API接口
支持多轮对话上下文 + Redis 历史缓存 + RAG 文档检索增强
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest, ErrorResponse
from app.services.ai_service import ai_service, AIService
from app.services.redis_service import redis_service
from app.services.rag_service import rag_service
from app.database import get_mongodb
from app.dao.chat_dao import ChatDAO
from app.dao.session_dao import SessionDAO
from app.utils.auth import get_current_user
from models.user import User
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import json

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    流式聊天接口（支持多轮对话上下文 + Redis 历史缓存 + RAG 检索增强）

    集成能力：
      - Redis Cache-Aside：对话历史优先从 Redis 缓存读取，减少 MongoDB IO
      - RAG 检索增强：当会话有上传文件时，自动检索相关片段注入 Prompt
      - SSE 流式响应：AI 回复实时推送，无需等待完整生成

    Args:
        request: 聊天请求，包含用户消息和 session_id
        current_user: 当前登录用户（JWT 鉴权）
        mongodb: MongoDB 数据库实例

    Returns:
        StreamingResponse: SSE 流式响应
    """

    async def generate():
        """生成 SSE 事件流（集成 Redis 缓存 + RAG 检索）"""
        user_id = current_user.id
        session_id = getattr(request, 'session_id', 'default_session')
        full_reply = ""

        try:
            logger.info(f"收到流式聊天请求: {request.message[:50]}...")

            # ① 保存用户消息到 MongoDB
            await ChatDAO.save_message(
                db=mongodb,
                user_id=user_id,
                session_id=session_id,
                message_type="user",
                content=request.message
            )

            # ② Redis Cache-Aside 读取历史消息
            history_messages = await redis_service.get_cached_messages(user_id, session_id)
            if history_messages is not None:
                logger.info(f"Redis 缓存命中 (Cache Hit): {len(history_messages)} 条历史消息")
            else:
                # 缓存未命中，回源 MongoDB
                history_messages = await ChatDAO.get_session_messages(
                    db=mongodb,
                    user_id=user_id,
                    session_id=session_id
                ) or []
                # 写回 Redis 缓存（下次命中）
                await redis_service.set_cached_messages(user_id, session_id, history_messages)
                logger.info(f"MongoDB 回源 (Cache Miss): {len(history_messages)} 条历史消息")

            # 转换为 LangChain 格式（排除刚添加的当前消息，最多保留最近10轮）
            chat_history = AIService.convert_history_to_messages(
                history_messages[:-1] if history_messages else [],
                max_rounds=10
            )
            logger.info(f"加载了 {len(chat_history)} 条历史消息作为上下文")

            # ③ RAG 检索：从全局健康知识库检索相关内容注入 Prompt
            augmented_message = request.message
            if rag_service.has_knowledge_base():
                retrieved = await rag_service.retrieve(request.message)
                if retrieved:
                    context = rag_service.build_rag_context(retrieved)
                    augmented_message = f"{context}\n用户问题: {request.message}"
                    logger.info(f"RAG 增强: 检索到 {len(retrieved)} 个健康知识片段")

            # ④ 调用 AI 服务（流式，传入 RAG 增强后的消息）
            async for text_chunk in ai_service.chat_stream(augmented_message, chat_history):
                full_reply += text_chunk
                data = json.dumps({"text": text_chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            yield "data: [DONE]\n\n"
            logger.info("流式聊天请求处理成功")

        except Exception as e:
            logger.error(f"流式聊天请求处理失败: {str(e)}")
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

        finally:
            # 无论成功/失败/客户端断开，都保存已有回复并维护缓存一致性
            if full_reply:
                await ChatDAO.save_message(
                    db=mongodb,
                    user_id=user_id,
                    session_id=session_id,
                    message_type="ai",
                    content=full_reply
                )
            await redis_service.invalidate_session_cache(user_id, session_id)
            await SessionDAO.update_session(
                db=mongodb,
                user_id=user_id,
                session_id=session_id,
                increment_message_count=True
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )
