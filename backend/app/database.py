"""
数据库连接配置
使用异步SQLAlchemy和MongoDB连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging
import pymysql

logger = logging.getLogger(__name__)

def ensure_database_exists():
    """
    确保MySQL数据库存在，如果不存在则自动创建
    """
    try:
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        # 校验数据库名（防止 SQL 注入）
        import re
        db_name = settings.MYSQL_DATABASE
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            raise ValueError(f"不合法的数据库名: {db_name}")
        
        # 创建数据库（如果不存在）
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        
        logger.info(f"数据库 '{settings.MYSQL_DATABASE}' 已确保存在")
        
        cursor.close()
        connection.close()
    except Exception as e:
        logger.error(f"创建数据库时出错: {e}")
        raise

# 在创建引擎之前确保数据库存在
ensure_database_exists()

# 异步SQLAlchemy配置 - MySQL
# 使用aiomysql驱动: mysql+aiomysql://
async_engine = create_async_engine(
    settings.mysql_async_url,
    pool_pre_ping=True,  # 连接池预检查
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    echo=settings.DEBUG  # 是否打印SQL语句
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基类
Base = declarative_base()

logger.info("MySQL异步数据库引擎已创建")

# MongoDB配置
mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
mongodb = mongodb_client[settings.MONGODB_DATABASE]

logger.info(f"MongoDB客户端已创建,数据库: {settings.MONGODB_DATABASE}")

# 异步依赖注入 - 获取数据库会话
async def get_async_db():
    """
    获取异步数据库会话
    用于FastAPI依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 获取MongoDB数据库
def get_mongodb():
    """
    获取MongoDB数据库实例
    用于FastAPI依赖注入
    """
    return mongodb
