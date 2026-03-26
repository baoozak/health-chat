"""
会话数据访问对象
管理用户的聊天会话
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class SessionDAO:
    """会话数据访问对象"""
    
    @staticmethod
    async def create_session(
        db: AsyncIOMotorDatabase,
        user_id: int,
        title: str = "新对话"
    ) -> dict:
        """
        创建新会话
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            title: 会话标题
            
        Returns:
            创建的会话信息
        """
        try:
            session_id = str(uuid.uuid4())
            session = {
                "user_id": user_id,
                "session_id": session_id,
                "title": title,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "message_count": 0
            }
            
            collection = db["sessions"]
            await collection.insert_one(session)
            
            # 移除MongoDB的_id字段
            session.pop("_id", None)
            
            logger.info(f"创建会话成功: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncIOMotorDatabase,
        user_id: int
    ) -> list:
        """
        获取用户的所有会话
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            
        Returns:
            会话列表
        """
        try:
            collection = db["sessions"]
            cursor = collection.find(
                {"user_id": user_id}
            ).sort("updated_at", -1)  # 按更新时间倒序
            
            sessions = await cursor.to_list(length=100)  # 最多返回100个会话
            
            # 移除MongoDB的_id字段
            for session in sessions:
                session.pop("_id", None)
            
            logger.info(f"获取用户 {user_id} 的会话列表,共 {len(sessions)} 个")
            return sessions
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {str(e)}")
            raise
    
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
            # 删除会话记录
            sessions_collection = db["sessions"]
            result = await sessions_collection.delete_one({
                "user_id": user_id,
                "session_id": session_id
            })
            
            # 删除会话的聊天记录
            chat_collection = db["chat_sessions"]
            await chat_collection.delete_many({
                "user_id": user_id,
                "session_id": session_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"删除会话成功: {session_id}")
                return True
            else:
                logger.warning(f"会话不存在: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            raise
    
    @staticmethod
    async def update_session(
        db: AsyncIOMotorDatabase,
        user_id: int,
        session_id: str,
        title: str = None,
        increment_message_count: bool = False
    ) -> bool:
        """
        更新会话信息
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            session_id: 会话ID
            title: 新标题(可选)
            increment_message_count: 是否增加消息计数
            
        Returns:
            是否更新成功
        """
        try:
            collection = db["sessions"]
            update_data = {
                "updated_at": datetime.utcnow()
            }
            
            if title:
                update_data["title"] = title
            
            if increment_message_count:
                # 使用$inc增加消息计数
                result = await collection.update_one(
                    {"user_id": user_id, "session_id": session_id},
                    {
                        "$set": update_data,
                        "$inc": {"message_count": 1}
                    }
                )
            else:
                result = await collection.update_one(
                    {"user_id": user_id, "session_id": session_id},
                    {"$set": update_data}
                )
            
            if result.modified_count > 0:
                logger.info(f"更新会话成功: {session_id}")
                return True
            else:
                logger.warning(f"会话不存在或无需更新: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新会话失败: {str(e)}")
            raise
    
    @staticmethod
    async def get_session(
        db: AsyncIOMotorDatabase,
        user_id: int,
        session_id: str
    ) -> dict:
        """
        获取单个会话信息
        
        Args:
            db: MongoDB数据库实例
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            会话信息,不存在则返回None
        """
        try:
            collection = db["sessions"]
            session = await collection.find_one({
                "user_id": user_id,
                "session_id": session_id
            })
            
            if session:
                session.pop("_id", None)
            
            return session
            
        except Exception as e:
            logger.error(f"获取会话失败: {str(e)}")
            raise
