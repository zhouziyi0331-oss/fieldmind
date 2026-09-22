"""
技能推荐API端点

提供智能技能推荐功能
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db
from app.services.skill_recommendation_service import SkillRecommendationService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class RecommendationContext(BaseModel):
    """推荐上下文"""
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    context: Optional[str] = Field(None, description="上下文描述")
    task_type: Optional[str] = Field(None, description="任务类型")


class SkillRecommendationResponse(BaseModel):
    """技能推荐响应"""
    skill_id: str
    skill_name: str
    description: str
    source: str
    relevance_score: float
    confidence: float
    usage_count: int
    success_rate: float
    metadata: Dict[str, Any]


class ImprovementSuggestion(BaseModel):
    """改进建议"""
    type: str
    title: str
    description: str
    priority: str
    metadata: Optional[Dict[str, Any]] = None


class UsageTrendResponse(BaseModel):
    """使用趋势响应"""
    period_days: int
    total_skills: int
    total_executions: int
    skills: List[Dict[str, Any]]


# ==================== 依赖项 ====================

def get_recommendation_service(db: Session = Depends(get_db)) -> SkillRecommendationService:
    """获取推荐服务"""
    return SkillRecommendationService(db)


# ==================== 技能推荐 ====================

@router.post("/projects/{project_id}/recommendations",
             response_model=List[SkillRecommendationResponse],
             summary="获取项目技能推荐")
async def get_project_recommendations(
    project_id: int = Path(..., description="项目ID"),
    context: Optional[RecommendationContext] = None,
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    service: SkillRecommendationService = Depends(get_recommendation_service)
):
    """
    为项目获取智能技能推荐

    整合多个数据源：
    - 知识蒸馏生成的技能
    - Hermes学习引擎的技能
    - 性能优异的技能

    按相关性排序返回
    """
    context_dict = context.dict() if context else None
    recommendations = service.recommend_for_project(
        project_id=project_id,
        context=context_dict,
        limit=limit
    )

    return [SkillRecommendationResponse(**rec) for rec in recommendations]


@router.get("/projects/{project_id}/recommendations",
            response_model=List[SkillRecommendationResponse],
            summary="获取项目技能推荐（GET）")
async def get_project_recommendations_get(
    project_id: int = Path(..., description="项目ID"),
    keywords: Optional[str] = Query(None, description="关键词（逗号分隔）"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    service: SkillRecommendationService = Depends(get_recommendation_service)
):
    """
    为项目获取智能技能推荐（GET方式）

    支持通过查询参数传递关键词
    """
    context_dict = None
    if keywords:
        context_dict = {
            "keywords": [k.strip() for k in keywords.split(",")]
        }

    recommendations = service.recommend_for_project(
        project_id=project_id,
        context=context_dict,
        limit=limit
    )

    return [SkillRecommendationResponse(**rec) for rec in recommendations]


@router.get("/skills/{skill_id}/improvements",
            response_model=List[ImprovementSuggestion],
            summary="获取技能改进建议")
async def get_skill_improvements(
    skill_id: str = Path(..., description="技能ID"),
    project_id: int = Query(..., description="项目ID"),
    service: SkillRecommendationService = Depends(get_recommendation_service)
):
    """
    获取技能改进建议

    基于性能指标和优化建议分析
    """
    suggestions = service.suggest_skill_improvements(
        skill_id=skill_id,
        project_id=project_id
    )

    return [ImprovementSuggestion(**s) for s in suggestions]


@router.get("/projects/{project_id}/usage-trends",
            response_model=UsageTrendResponse,
            summary="获取技能使用趋势")
async def get_usage_trends(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    service: SkillRecommendationService = Depends(get_recommendation_service)
):
    """
    获取项目的技能使用趋势

    包含：
    - 各技能的使用频率
    - 成功率统计
    - 平均执行时间
    - 每日使用分布
    """
    trends = service.get_skill_usage_trends(
        project_id=project_id,
        days=days
    )

    return UsageTrendResponse(**trends)


@router.get("/health", summary="健康检查")
async def health_check():
    """技能推荐服务健康检查"""
    return {
        "status": "healthy",
        "service": "skill_recommendations"
    }
