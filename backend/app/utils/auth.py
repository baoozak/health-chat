"""
认证工具模块
提供密码加密、JWT token生成和验证等功能
支持 Redis Token 黑名单：用户主动登出后立即失效
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from app.database import get_async_db
from app.dao.user_dao import UserDAO
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希密码
    """
    # bcrypt限制密码最多72字节
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问token

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT token

    Args:
        token: JWT token字符串

    Returns:
        解码后的数据或None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT解码失败: {str(e)}")
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取当前登录用户（已集成 Redis Token 黑名单校验）

    校验顺序：
      1. Token 黑名单检查（Redis）—— 登出的 token 即刻拒绝
      2. JWT 签名解码验证
      3. 数据库用户存在性验证

    Args:
        token: JWT token
        db: 数据库会话

    Returns:
        用户对象

    Raises:
        HTTPException: 认证失败时
    """
    logger.info(f"验证token: {token[:20]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ① Redis Token 黑名单检查（登出后即刻失效）
    from app.services.redis_service import redis_service
    if await redis_service.is_token_blacklisted(token):
        logger.warning(f"Token 已被列入黑名单（已登出）: {token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ② 解码 JWT
    payload = decode_access_token(token)
    if payload is None:
        logger.error("Token解码失败")
        raise credentials_exception

    # ③ 获取用户ID
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        logger.error("Token中没有用户ID")
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.error(f"用户ID格式错误: {user_id_str}")
        raise credentials_exception

    logger.info(f"从token中获取用户ID: {user_id}")

    # ④ 查询用户
    user = await UserDAO.get_user_by_id(db, user_id=user_id)
    if user is None:
        logger.error(f"用户不存在: {user_id}")
        raise credentials_exception

    logger.info(f"用户验证成功: {user.username}")
    return user


async def logout_token(token: str) -> bool:
    """
    登出操作：将 Token 加入 Redis 黑名单

    TTL 与 token 有效期一致，过期后自动清除无需手动维护

    Args:
        token: 要吊销的 JWT token

    Returns:
        始终返回 True（即使 Redis 不可用也允许前端清除本地 token）
    """
    from app.services.redis_service import redis_service
    result = await redis_service.blacklist_token(token)
    if result:
        logger.info(f"Token 登出成功，已加入黑名单: {token[:20]}...")
    else:
        logger.warning(f"Token 登出降级（Redis 不可用）: {token[:20]}...")
    return True
