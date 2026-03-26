"""
用户数据模型
定义用户表结构
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """
    用户表模型
    存储用户基本信息和认证数据
    """
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 用户名(唯一)
    username = Column(String(50), unique=True, nullable=False, index=True)
    
    # 邮箱(唯一)
    email = Column(String(100), unique=True, nullable=False, index=True)
    
    # 加密后的密码
    hashed_password = Column(String(255), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
