"""
会话管理API路由
提供会话相关的API接口
"""
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_mongodb
from app.dao.session_dao import SessionDAO
from app.dao.chat_dao import ChatDAO
from app.utils.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 数据模型
class SessionCreate(BaseModel):
    """创建会话请求"""
    title: str = "新对话"

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

@router.get("/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    获取当前用户的所有会话列表
    
    Returns:
        会话列表
    """
    try:
        sessions = await SessionDAO.get_user_sessions(mongodb, current_user.id)
        
        # 转换日期格式
        for session in sessions:
            session["created_at"] = session["created_at"].isoformat()
            session["updated_at"] = session["updated_at"].isoformat()
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@router.post("/sessions")
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    创建新会话
    
    Args:
        session_data: 会话数据
        
    Returns:
        创建的会话信息
    """
    try:
        session = await SessionDAO.create_session(
            mongodb,
            current_user.id,
            session_data.title
        )
        
        # 转换日期格式
        session["created_at"] = session["created_at"].isoformat()
        session["updated_at"] = session["updated_at"].isoformat()
        
        return session
        
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    删除会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        删除结果
    """
    try:
        success = await SessionDAO.delete_session(mongodb, current_user.id, session_id)
        
        if success:
            # 清除 Redis 中该会话的缓存
            from app.services.redis_service import redis_service
            await redis_service.invalidate_session_cache(current_user.id, session_id)
            return {"message": "会话删除成功"}
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    获取会话的历史消息
    
    Args:
        session_id: 会话ID
        
    Returns:
        消息列表
    """
    try:
        messages = await ChatDAO.get_session_messages(mongodb, current_user.id, session_id)
        
        if messages is None:
            return {"messages": []}
        
        # 转换时间戳格式
        for msg in messages:
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
        
        logger.info(f"返回消息列表: {len(messages)} 条消息")
        return {"messages": messages}
        
    except Exception as e:
        logger.error(f"获取会话消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话消息失败: {str(e)}")

@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    更新会话标题
    
    Args:
        session_id: 会话ID
        session_data: 会话数据
        
    Returns:
        更新结果
    """
    try:
        success = await SessionDAO.update_session(
            mongodb,
            current_user.id,
            session_id,
            title=session_data.title
        )
        
        if success:
            return {"message": "会话更新成功"}
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")
