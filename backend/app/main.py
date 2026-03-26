"""
FastAPI主应用入口
这是后端服务的核心文件,负责初始化FastAPI应用和配置路由
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入数据库相关
from app.database import async_engine, Base
# 导入所有模型以确保它们被注册到 Base.metadata
from models.user import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：创建数据库表 + 预热 Redis 连接 + 创建 MongoDB 索引
    关闭时：优雅关闭 Redis / MongoDB 连接
    """
    # 启动时：创建所有 MySQL 表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表已自动创建/检查完成")

    # 启动时：创建 MongoDB 索引（加速常用查询）
    from app.database import mongodb
    await mongodb.chat_sessions.create_index([("user_id", 1), ("session_id", 1)])
    await mongodb.sessions.create_index([("user_id", 1), ("session_id", 1)])
    await mongodb.sessions.create_index([("user_id", 1), ("updated_at", -1)])
    await mongodb.health_reports.create_index([("user_id", 1), ("generated_at", -1)])
    logger.info("MongoDB 索引已创建/检查完成")

    # 启动时：预热 Redis 连接（连接失败不阻断启动，自动降级）
    from app.services.redis_service import redis_service
    redis_ok = await redis_service.ping()
    if redis_ok:
        logger.info("Redis 连接预热成功 ✅")
    else:
        logger.warning("Redis 连接失败，将降级运行（无缓存 + 无 Token 黑名单）⚠️")

    yield  # 应用运行中

    # 关闭时：优雅关闭 Redis 连接
    await redis_service.close()
    # 关闭时：优雅关闭 MongoDB 连接
    from app.database import mongodb_client
    mongodb_client.close()
    logger.info("应用正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title="个人健康管理咨询API",
    description="基于AI的个人健康管理和咨询服务",
    version="1.0.0",
    lifespan=lifespan  # 添加生命周期管理
)

# 引入配置
from config.settings import settings

# CORS 来源列表（已经是列表格式）
cors_origins = settings.CORS_ORIGINS
logger.info(f"CORS allowed origins: {cors_origins}")

# 配置CORS中间件,允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 引入路由
from app.routes import chat, user, session, upload, health

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["聊天"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(session.router, prefix="/api", tags=["会话"])
app.include_router(upload.router, prefix="/api", tags=["文件上传"])
app.include_router(health.router, prefix="/api", tags=["健康分析"])

logger.info("路由注册完成")

# 根路径测试接口
@app.get("/")
async def root():
    """
    API根路径,用于测试服务是否正常运行
    """
    return {
        "message": "欢迎使用个人健康管理咨询系统API",
        "status": "running",
        "version": "1.0.0",
        "description": "您的智能健康助手"
    }

# 健康检查接口
@app.get("/health")
async def health_check():
    """
    健康检查接口,用于监控服务状态
    """
    return {"status": "healthy"}
