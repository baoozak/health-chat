"""
用户数据访问对象
处理用户相关的数据库操作(异步版本)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UserDAO:
    """
    用户数据访问类(异步)
    提供用户CRUD操作
    """
    
    @staticmethod
    async def create_user(db: AsyncSession, username: str, email: str, hashed_password: str) -> User:
        """
        创建新用户
        
        Args:
            db: 异步数据库会话
            username: 用户名
            email: 邮箱
            hashed_password: 加密后的密码
            
        Returns:
            创建的用户对象
        """
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"创建用户成功: {username}")
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        根据ID查询用户
        
        Args:
            db: 异步数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名查询用户
        
        Args:
            db: 异步数据库会话
            username: 用户名
            
        Returns:
            用户对象或None
        """
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        根据邮箱查询用户
        
        Args:
            db: 异步数据库会话
            email: 邮箱
            
        Returns:
            用户对象或None
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            db: 异步数据库会话
            user_id: 用户ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的用户对象或None
        """
        user = await UserDAO.get_user_by_id(db, user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await db.commit()
            await db.refresh(user)
            logger.info(f"更新用户成功: {user.username}")
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            db: 异步数据库会话
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        user = await UserDAO.get_user_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.commit()
            logger.info(f"删除用户成功: {user.username}")
            return True
        return False
