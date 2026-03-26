"""
API数据模型定义
使用Pydantic定义请求和响应的数据结构
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ============ 用户相关模型 ============

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT Token响应"""
    access_token: str
    token_type: str
    user: UserResponse

# ============ 聊天相关模型 ============

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")



# ============ 通用模型 ============

class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")

class SuccessResponse(BaseModel):
    """成功响应"""
    message: str = Field(..., description="成功消息")
