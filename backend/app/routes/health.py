"""
健康分析API路由
提供健康状态分析和报告生成接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.database import get_mongodb
from app.utils.auth import get_current_user
from app.dao.health_analysis_dao import HealthAnalysisDAO
from app.services.health_analysis_service import health_analysis_service
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

@router.get("/analysis")
async def get_health_analysis(
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    获取用户最新的健康分析报告
    如果没有报告或报告过期（超过24小时），则自动生成新报告
    
    Returns:
        健康分析报告
    """
    try:
        logger.info(f"用户 {current_user.username} 请求健康分析报告")
        
        # 尝试获取最新报告
        latest_report = await HealthAnalysisDAO.get_latest_health_report(
            mongodb,
            current_user.id
        )
        
        # 如果有报告且在24小时内，直接返回
        if latest_report:
            from datetime import datetime, timedelta
            generated_at = latest_report.get("generated_at")
            if generated_at and (datetime.utcnow() - generated_at) < timedelta(hours=24):
                logger.info(f"返回缓存的健康报告")
                return {
                    "success": True,
                    "data": latest_report,
                    "cached": True
                }
        
        # 否则生成新报告
        logger.info("缓存报告不存在或已过期，生成新报告")
        return await generate_new_health_analysis(current_user, mongodb)
        
    except Exception as e:
        logger.error(f"获取健康分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取健康分析失败: {str(e)}"
        )

@router.post("/analysis/generate")
async def generate_health_analysis(
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    强制重新生成健康分析报告
    
    Returns:
        新生成的健康分析报告
    """
    try:
        logger.info(f"用户 {current_user.username} 请求重新生成健康报告")
        return await generate_new_health_analysis(current_user, mongodb)
        
    except Exception as e:
        logger.error(f"生成健康分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成健康分析失败: {str(e)}"
        )

async def generate_new_health_analysis(
    current_user: User,
    mongodb: AsyncIOMotorDatabase
):
    """
    生成新的健康分析报告（内部方法）
    
    Args:
        current_user: 当前用户
        mongodb: 数据库连接
        
    Returns:
        健康分析报告
    """
    # 1. 获取用户所有会话数据
    conversations = await HealthAnalysisDAO.get_user_all_conversations(
        mongodb,
        current_user.id,
        days=90  # 分析最近90天的数据
    )
    
    # 检查数据是否足够
    if not conversations or len(conversations) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="数据不足，请至少进行一次健康咨询后再生成报告"
        )
    
    # 2. 提取健康数据
    health_data = await HealthAnalysisDAO.extract_health_data(conversations)
    
    # 3. 使用AI生成分析报告
    analysis_result = await health_analysis_service.generate_health_analysis(health_data)
    
    # 4. 保存报告
    report_id = await HealthAnalysisDAO.save_health_report(
        mongodb,
        current_user.id,
        analysis_result
    )
    
    # 5. 返回结果
    analysis_result["report_id"] = report_id
    
    logger.info(f"健康报告生成成功: user_id={current_user.id}, report_id={report_id}")
    
    return {
        "success": True,
        "data": analysis_result,
        "cached": False
    }

@router.get("/analysis/history")
async def get_health_analysis_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    获取用户的健康分析报告历史
    
    Args:
        limit: 返回数量限制，默认10条
        
    Returns:
        健康报告历史列表
    """
    try:
        logger.info(f"用户 {current_user.username} 请求健康报告历史")
        
        reports = await HealthAnalysisDAO.get_health_report_history(
            mongodb,
            current_user.id,
            limit=min(limit, 20)  # 最多返回20条
        )
        
        return {
            "success": True,
            "data": reports,
            "count": len(reports)
        }
        
    except Exception as e:
        logger.error(f"获取健康报告历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史失败: {str(e)}"
        )

@router.get("/trends")
async def get_health_trends(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """
    获取健康趋势数据（基于历史报告）
    
    Args:
        limit: 返回的报告数量，默认10条
        
    Returns:
        健康趋势数据，包含各维度评分的变化
    """
    try:
        logger.info(f"用户 {current_user.username} 请求健康趋势数据")
        
        # 获取历史报告（按时间倒序）
        reports = await HealthAnalysisDAO.get_health_report_history(
            mongodb,
            current_user.id,
            limit=min(limit, 10)  # 最多返回10条用于趋势分析
        )
        
        if not reports or len(reports) < 1:
            return {
                "success": True,
                "data": {
                    "report_count": 0,
                    "trends": [],
                    "summary": {
                        "overall_change": 0,
                        "physical_change": 0,
                        "mental_change": 0,
                        "lifestyle_change": 0
                    },
                    "message": "暂无历史报告"
                }
            }
        
        # 提取趋势数据（按时间正序排列，方便展示趋势）
        trend_data = []
        for report in reversed(reports):
            health_score = report.get("health_score", {})
            trend_data.append({
                "date": report.get("generated_at"),
                "overall": health_score.get("overall", 0),
                "physical": health_score.get("physical", 0),
                "mental": health_score.get("mental", 0),
                "lifestyle": health_score.get("lifestyle", 0)
            })
        
        # 计算变化趋势（最新报告与最早报告的差值）
        if len(trend_data) >= 2:
            first = trend_data[0]
            last = trend_data[-1]
            summary = {
                "overall_change": last["overall"] - first["overall"],
                "physical_change": last["physical"] - first["physical"],
                "mental_change": last["mental"] - first["mental"],
                "lifestyle_change": last["lifestyle"] - first["lifestyle"]
            }
        else:
            summary = {
                "overall_change": 0,
                "physical_change": 0,
                "mental_change": 0,
                "lifestyle_change": 0
            }
        
        return {
            "success": True,
            "data": {
                "report_count": len(reports),
                "trends": trend_data,
                "summary": summary
            }
        }
        
    except Exception as e:
        logger.error(f"获取健康趋势失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取趋势失败: {str(e)}"
        )
