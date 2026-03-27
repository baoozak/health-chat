"""
项目配置文件
使用pydantic-settings管理配置,支持从环境变量和.env文件读取
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    应用配置类
    所有配置项都可以通过环境变量或.env文件设置
    """
    
    # 应用基础配置
    APP_NAME: str = "AI聊天网站"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 阿里百炼平台配置
    DASHSCOPE_API_KEY: str = ""  # 需要在.env文件中设置
    
    # MySQL数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_DATABASE: str = "langchain_chat"
    
    # MongoDB数据库配置
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_DATABASE: str = "langchain_chat"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_CHAT_CACHE_TTL: int = 3600        # 会话历史缓存TTL（秒），默认1小时
    REDIS_TOKEN_BLACKLIST_TTL: int = 60 * 24 * 7  # Token黑名单TTL与Token有效期一致

    # RAG配置
    RAG_VECTOR_STORE_DIR: str = "vector_stores"   # FAISS向量库存储根目录
    RAG_CHUNK_SIZE: int = 500                     # 文本切分块大小（字符）
    RAG_CHUNK_OVERLAP: int = 50                   # 相邻块重叠字符数
    RAG_TOP_K: int = 3                            # 检索返回的最相关块数量

    # JWT认证配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost",          # Docker 部署 (Nginx 默认80端口)
        "http://localhost:80",       # Docker 部署 (显式80端口)
        "http://localhost:5173",     # 本地开发 (Vite)
        "http://localhost:5174",
        "http://127.0.0.1:5173",    # 本地开发 (127地址)
    ]
    
    class Config:
        # 从.env文件读取配置
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def mysql_url(self) -> str:
        """生成MySQL连接URL"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def mysql_async_url(self) -> str:
        """生成MySQL异步连接URL"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def mongodb_url(self) -> str:
        """生成MongoDB连接URL"""
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}"

    @property
    def redis_url(self) -> str:
        """生成 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def rag_vector_store_path(self) -> str:
        """RAG向量库绝对路径（相对于backend目录）"""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, self.RAG_VECTOR_STORE_DIR)

# 创建全局配置实例
settings = Settings()
