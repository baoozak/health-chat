"""
数据库初始化脚本
创建MySQL表和MongoDB索引(异步版本)
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_engine, Base, mongodb
from models.user import User
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_mysql():
    """
    初始化MySQL数据库
    创建所有表(异步)
    """
    try:
        logger.info("开始创建MySQL表...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("MySQL表创建成功!")
    except Exception as e:
        logger.error(f"MySQL表创建失败: {str(e)}")
        raise

async def init_mongodb():
    """
    初始化MongoDB
    创建索引
    """
    try:
        logger.info("开始创建MongoDB索引...")
        
        # 聊天会话集合
        chat_collection = mongodb["chat_sessions"]
        
        # 创建索引
        await chat_collection.create_index([("user_id", 1), ("session_id", 1)], unique=True)
        await chat_collection.create_index([("user_id", 1), ("updated_at", -1)])
        
        logger.info("MongoDB索引创建成功!")
    except Exception as e:
        logger.error(f"MongoDB索引创建失败: {str(e)}")
        raise

async def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("开始初始化数据库")
    logger.info("=" * 50)
    
    # 初始化MySQL
    await init_mysql()
    
    # 初始化MongoDB
    await init_mongodb()
    
    logger.info("=" * 50)
    logger.info("数据库初始化完成!")
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
