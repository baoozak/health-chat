"""
健康分析数据访问对象
负责健康数据的聚合、提取和存储
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HealthAnalysisDAO:
    """健康分析数据访问对象"""
    
    @staticmethod
    async def get_user_all_conversations(
        mongodb: AsyncIOMotorDatabase,
        user_id: int,
        days: int = 90
    ) -> List[Dict]:
        """
        获取用户指定时间范围内的所有会话数据
        
        Args:
            mongodb: MongoDB数据库连接
            user_id: 用户ID
            days: 获取最近多少天的数据，默认90天
            
        Returns:
            会话列表，包含所有消息
        """
        try:
            # 计算时间范围
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 查询用户的所有会话
            sessions_collection = mongodb.sessions
            sessions = await sessions_collection.find({
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=None)
            
            if not sessions:
                logger.info(f"用户 {user_id} 在最近{days}天内没有会话记录")
                return []
            
            # 批量获取所有会话的消息（使用 $in 避免 N+1 查询）
            chat_collection = mongodb.chat_sessions
            session_ids = [s["session_id"] for s in sessions]
            
            cursor = chat_collection.find({
                "user_id": user_id,
                "session_id": {"$in": session_ids}
            })
            chat_data_list = await cursor.to_list(length=None)
            
            # 建立 session_id → 消息数据的映射
            chat_data_map = {
                item["session_id"]: item
                for item in chat_data_list
            }
            
            all_conversations = []
            for session in sessions:
                session_data = chat_data_map.get(session["session_id"])
                if session_data and "messages" in session_data:
                    all_conversations.append({
                        "session_id": session["session_id"],
                        "title": session.get("title", "未命名会话"),
                        "created_at": session.get("created_at"),
                        "messages": session_data["messages"]
                    })
            
            logger.info(f"成功获取用户 {user_id} 的 {len(all_conversations)} 个会话")
            return all_conversations
            
        except Exception as e:
            logger.error(f"获取用户会话数据失败: {str(e)}")
            raise Exception(f"数据库查询失败: {str(e)}")
    
    @staticmethod
    async def extract_health_data(conversations: List[Dict]) -> Dict:
        """
        从会话中提取健康相关数据
        
        Args:
            conversations: 会话列表
            
        Returns:
            提取的健康数据摘要
        """
        try:
            health_data = {
                "total_conversations": len(conversations),
                "total_messages": 0,
                "user_messages": [],
                "ai_responses": [],
                "file_uploads": 0,
                "date_range": {
                    "start": None,
                    "end": None
                }
            }
            
            all_dates = []
            
            for conv in conversations:
                messages = conv.get("messages", [])
                health_data["total_messages"] += len(messages)
                
                for msg in messages:
                    # 提取消息内容
                    if msg.get("type") == "user":
                        health_data["user_messages"].append({
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp"),
                            "session_id": conv.get("session_id")
                        })
                    elif msg.get("type") == "ai":
                        health_data["ai_responses"].append({
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp"),
                            "session_id": conv.get("session_id")
                        })
                    
                    # 统计文件上传
                    if "[文件:" in msg.get("content", ""):
                        health_data["file_uploads"] += 1
                    
                    # 收集时间戳
                    if msg.get("timestamp"):
                        all_dates.append(msg["timestamp"])
            
            # 计算时间范围
            if all_dates:
                health_data["date_range"]["start"] = min(all_dates)
                health_data["date_range"]["end"] = max(all_dates)
            
            logger.info(f"提取健康数据完成: {health_data['total_messages']} 条消息")
            return health_data
            
        except Exception as e:
            logger.error(f"提取健康数据失败: {str(e)}")
            raise Exception(f"数据提取失败: {str(e)}")
    
    @staticmethod
    async def save_health_report(
        mongodb: AsyncIOMotorDatabase,
        user_id: int,
        report: Dict
    ) -> str:
        """
        保存健康分析报告
        
        Args:
            mongodb: MongoDB数据库连接
            user_id: 用户ID
            report: 健康报告数据
            
        Returns:
            报告ID
        """
        try:
            collection = mongodb.health_reports
            
            # 添加元数据
            report_data = {
                "user_id": user_id,
                "generated_at": datetime.utcnow(),
                **report
            }
            
            # 插入报告
            result = await collection.insert_one(report_data)
            report_id = str(result.inserted_id)
            
            logger.info(f"保存健康报告成功: user_id={user_id}, report_id={report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"保存健康报告失败: {str(e)}")
            raise Exception(f"保存报告失败: {str(e)}")
    
    @staticmethod
    async def get_latest_health_report(
        mongodb: AsyncIOMotorDatabase,
        user_id: int
    ) -> Optional[Dict]:
        """
        获取用户最新的健康报告
        
        Args:
            mongodb: MongoDB数据库连接
            user_id: 用户ID
            
        Returns:
            最新的健康报告，如果不存在返回None
        """
        try:
            collection = mongodb.health_reports
            
            # 查询最新报告
            report = await collection.find_one(
                {"user_id": user_id},
                sort=[("generated_at", -1)]
            )
            
            if report:
                # 移除MongoDB的_id字段
                report.pop("_id", None)
                logger.info(f"获取最新健康报告成功: user_id={user_id}")
            else:
                logger.info(f"用户 {user_id} 还没有健康报告")
            
            return report
            
        except Exception as e:
            logger.error(f"获取健康报告失败: {str(e)}")
            raise Exception(f"查询报告失败: {str(e)}")
    
    @staticmethod
    async def get_health_report_history(
        mongodb: AsyncIOMotorDatabase,
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取用户的健康报告历史
        
        Args:
            mongodb: MongoDB数据库连接
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            健康报告列表
        """
        try:
            collection = mongodb.health_reports
            
            # 查询历史报告
            cursor = collection.find(
                {"user_id": user_id},
                sort=[("generated_at", -1)],
                limit=limit
            )
            
            reports = await cursor.to_list(length=limit)
            
            # 移除_id字段
            for report in reports:
                report.pop("_id", None)
            
            logger.info(f"获取健康报告历史成功: user_id={user_id}, count={len(reports)}")
            return reports
            
        except Exception as e:
            logger.error(f"获取健康报告历史失败: {str(e)}")
            raise Exception(f"查询历史失败: {str(e)}")
