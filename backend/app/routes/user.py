"""
用户API路由
提供用户注册、登录、信息管理等接口
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserRegister, UserLogin, Token, UserResponse, ErrorResponse
from app.database import get_async_db
from app.dao.user_dao import UserDAO
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    logout_token,
    oauth2_scheme
)
from models.user import User
import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

@router.post("/register", response_model=Token, responses={
    400: {"model": ErrorResponse, "description": "注册失败"}
})
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户注册
    
    Args:
        user_data: 注册信息
        db: 数据库会话
        
    Returns:
        Token: JWT token和用户信息
        
    Raises:
        HTTPException: 用户名或邮箱已存在时
    """
    try:
        logger.info(f"收到注册请求: username={user_data.username}, email={user_data.email}")
        
        # 检查用户名是否已存在
        existing_user = await UserDAO.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await UserDAO.get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        user = await UserDAO.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        # 生成token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"用户注册成功: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.post("/login", response_model=Token, responses={
    401: {"model": ErrorResponse, "description": "登录失败"}
})
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """
    用户登录
    
    Args:
        login_data: 登录信息
        db: 数据库会话
        
    Returns:
        Token: JWT token和用户信息
        
    Raises:
        HTTPException: 用户名或密码错误时
    """
    try:
        logger.info(f"收到登录请求: username={login_data.username}")
        
        # 查询用户
        user = await UserDAO.get_user_by_username(db, login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"用户登录成功: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    
    Args:
        current_user: 当前用户(从token中获取)
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    用户登出（服务端真正吊销 Token）

    将当前 JWT Token 写入 Redis 黑名单，TTL 与 Token 有效期一致。
    即使 Token 尚未自然过期，也无法再通过认证。

    Args:
        current_user: 当前用户（同时校验 Token 有效性）
        token: 当前请求的 JWT Token

    Returns:
        登出成功消息
    """
    await logout_token(token)
    logger.info(f"用户 {current_user.username} 已登出，Token 已加入黑名单")
    return {"message": "登出成功", "username": current_user.username}
