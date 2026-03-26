"""
聊天记录数据访问对象
处理聊天记录相关的MongoDB操作
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

class ChatDAO:
    """
    聊天记录数据访问类
    提供聊天记录的CRUD操作
    """
    
    COLLECTION_NAME = "chat_sessions"
    
    @staticmethod
    async def save_message(
        db: AsyncIOMotorDatabase,
        user_id: int,
        session_id: str,
        message_type: str,
        content: str,
        image_data: str = None,
        image_filename: str = None,
        image_mime_type: str = None
    ) -> bool:
        """
        保存单条消息到会话
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            session_id: 会话ID
            message_type: 消息类型(user/ai)
            content: 消息内容
            
        Returns:
            是否保存成功
        """
        try:
            collection = db[ChatDAO.COLLECTION_NAME]
            
            # 构造消息对象
            message = {
                "id": str(uuid.uuid4()),
                "type": message_type,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            
            # 如果有图片数据，添加到消息对象中
            if image_data:
                message["image_data"] = image_data
                message["image_filename"] = image_filename or "image.png"
                message["image_mime_type"] = image_mime_type or "image/png"
            
            # 更新或创建会话
            result = await collection.update_one(
                {
                    "user_id": user_id,
                    "session_id": session_id
                },
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"保存消息成功: user_id={user_id}, session_id={session_id}, type={message_type}")
            return True
            
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
            return False
    
    @staticmethod
    async def get_session_messages(
        db: AsyncIOMotorDatabase,
        user_id: int,
        session_id: str
    ) -> Optional[List[Dict]]:
        """
        获取会话的所有消息
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            消息列表或None
        """
        try:
            collection = db[ChatDAO.COLLECTION_NAME]
            
            session = await collection.find_one({
                "user_id": user_id,
                "session_id": session_id
            })
            
            if session and "messages" in session:
                logger.info(f"查询会话消息成功: user_id={user_id}, session_id={session_id}, count={len(session['messages'])}")
                return session["messages"]
            
            return []
            
        except Exception as e:
            logger.error(f"查询会话消息失败: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncIOMotorDatabase,
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取用户的所有会话列表
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        try:
            collection = db[ChatDAO.COLLECTION_NAME]
            
            cursor = collection.find(
                {"user_id": user_id}
            ).sort("updated_at", -1).limit(limit)
            
            sessions = await cursor.to_list(length=limit)
            
            logger.info(f"查询用户会话成功: user_id={user_id}, count={len(sessions)}")
            return sessions
            
        except Exception as e:
            logger.error(f"查询用户会话失败: {str(e)}")
            return []
    
    @staticmethod
    async def delete_session(
        db: AsyncIOMotorDatabase,
        user_id: int,
        session_id: str
    ) -> bool:
        """
        删除会话
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            collection = db[ChatDAO.COLLECTION_NAME]
            
            result = await collection.delete_one({
                "user_id": user_id,
                "session_id": session_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"删除会话成功: user_id={user_id}, session_id={session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            return False
