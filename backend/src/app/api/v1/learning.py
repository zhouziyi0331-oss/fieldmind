"""
学习日志API端点

提供AI学习记录、状态追踪和成果展示接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.user_engagement import LearningStatus
from app.services.learning_service import LearningLogService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class LearningLogCreate(BaseModel):
    """创建学习日志请求"""
    project_id: int = Field(..., description="项目ID")
    learning_content: str = Field(..., description="学习内容描述")
    learning_source: str = Field(..., description="学习来源")
    user_feedback: Optional[str] = Field(None, description="用户反馈")
    confidence_before: float = Field(0.0, description="学习前置信度", ge=0, le=1)
    confidence_after: float = Field(0.0, description="学习后置信度", ge=0, le=1)
    applied_count: int = Field(0, description="应用次数", ge=0)


class LearningLogResponse(BaseModel):
    """学习日志响应"""
    id: int
    user_id: int
    project_id: int
    learning_content: str
    learning_source: str
    user_feedback: Optional[str]
    confidence_before: Optional[float]
    confidence_after: Optional[float]
    status: str
    applied_count: int
    last_applied: Optional[str]
    learned_at: str

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    """状态更新请求"""
    status: LearningStatus = Field(..., description="新状态")
    user_feedback: Optional[str] = Field(None, description="用户反馈")


class LearningSummaryResponse(BaseModel):
    """学习摘要响应"""
    period_days: int
    total_learnings: int
    status_breakdown: Dict[str, int]
    source_breakdown: Dict[str, int]
    avg_confidence_gain: float
    total_applications: int
    applied_count: int
    application_rate: float
    start_date: str
    end_date: str


class TopLearningResponse(BaseModel):
    """顶级学习响应"""
    id: int
    content: str
    source: str
    value_score: float
    applied_count: int
    confidence_gain: float
    status: str
    learned_at: str


class LearningTrendPoint(BaseModel):
    """学习趋势点"""
    date: str
    count: int
    applications: int


# ==================== 依赖项 ====================

def get_learning_service(db: Session = Depends(get_db)) -> LearningLogService:
    """获取学习日志服务"""
    return LearningLogService(db)


# ==================== 学习日志管理 ====================

@router.post("/logs", response_model=LearningLogResponse, summary="创建学习日志")
async def create_learning_log(
    log: LearningLogCreate,
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    创建学习日志记录

    - **project_id**: 项目ID
    - **learning_content**: 学习内容描述
    - **learning_source**: 学习来源（user_correction, pattern_observation等）
    - **user_feedback**: 用户反馈
    - **confidence_before**: 学习前置信度（0-1）
    - **confidence_after**: 学习后置信度（0-1）
    - **applied_count**: 应用次数
    """
    result = service.create_learning_log(
        user_id=current_user.id,
        project_id=log.project_id,
        learning_content=log.learning_content,
        learning_source=log.learning_source,
        user_feedback=log.user_feedback,
        confidence_before=log.confidence_before,
        confidence_after=log.confidence_after,
        applied_count=log.applied_count
    )

    return LearningLogResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        learning_content=result.learning_content,
        learning_source=result.learning_source,
        user_feedback=result.user_feedback,
        confidence_before=result.confidence_before,
        confidence_after=result.confidence_after,
        status=result.status.value,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        learned_at=result.learned_at.isoformat()
    )


@router.get("/logs", response_model=List[LearningLogResponse], summary="获取学习日志列表")
async def get_learning_logs(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    status: Optional[LearningStatus] = Query(None, description="筛选状态"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    获取学习日志列表

    按时间倒序返回
    """
    logs = service.get_learning_logs(
        user_id=current_user.id,
        project_id=project_id,
        status=status,
        limit=limit
    )

    return [
        LearningLogResponse(
            id=log.id,
            user_id=log.user_id,
            project_id=log.project_id,
            learning_content=log.learning_content,
            learning_source=log.learning_source,
            user_feedback=log.user_feedback,
            confidence_before=log.confidence_before,
            confidence_after=log.confidence_after,
            status=log.status.value,
            applied_count=log.applied_count,
            last_applied=log.last_applied.isoformat() if log.last_applied else None,
            learned_at=log.learned_at.isoformat()
        )
        for log in logs
    ]


@router.post("/logs/{log_id}/apply", response_model=LearningLogResponse, summary="记录学习应用")
async def record_application(
    log_id: int = Path(..., description="学习日志ID"),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    记录学习内容的应用

    增加应用计数并更新最后应用时间
    """
    result = service.record_application(log_id=log_id)

    return LearningLogResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        learning_content=result.learning_content,
        learning_source=result.learning_source,
        user_feedback=result.user_feedback,
        confidence_before=result.confidence_before,
        confidence_after=result.confidence_after,
        status=result.status.value,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        learned_at=result.learned_at.isoformat()
    )


@router.put("/logs/{log_id}/status", response_model=LearningLogResponse, summary="更新学习状态")
async def update_status(
    log_id: int = Path(..., description="学习日志ID"),
    update: StatusUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    更新学习状态

    - **status**: 新状态（learned, applied, verified, rejected）
    - **user_feedback**: 可选，用户反馈
    """
    result = service.update_status(
        log_id=log_id,
        status=update.status,
        user_feedback=update.user_feedback
    )

    return LearningLogResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        learning_content=result.learning_content,
        learning_source=result.learning_source,
        user_feedback=result.user_feedback,
        confidence_before=result.confidence_before,
        confidence_after=result.confidence_after,
        status=result.status.value,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        learned_at=result.learned_at.isoformat()
    )


@router.delete("/logs/{log_id}", summary="删除学习日志")
async def delete_learning(
    log_id: int = Path(..., description="学习日志ID"),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """删除学习日志"""
    success = service.delete_learning(
        log_id=log_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="学习日志不存在或无权删除")

    return {"message": "学习日志已删除"}


# ==================== 学习分析 ====================

@router.get("/summary/{project_id}", response_model=LearningSummaryResponse, summary="获取学习摘要")
async def get_learning_summary(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    获取学习摘要统计

    包含：
    - 学习总数
    - 状态分布
    - 来源分布
    - 平均置信度提升
    - 应用统计
    """
    summary = service.get_learning_summary(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return LearningSummaryResponse(**summary)


@router.get("/top/{project_id}", response_model=List[TopLearningResponse], summary="获取顶级学习")
async def get_top_learnings(
    project_id: int = Path(..., description="项目ID"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    获取最有价值的学习记录

    基于置信度提升、应用次数和状态计算价值分数
    """
    top = service.get_top_learnings(
        user_id=current_user.id,
        project_id=project_id,
        limit=limit
    )

    return [TopLearningResponse(**item) for item in top]


@router.get("/search", response_model=List[LearningLogResponse], summary="搜索学习日志")
async def search_learnings(
    keyword: str = Query(..., description="搜索关键词"),
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    搜索学习日志

    在学习内容和用户反馈中搜索关键词
    """
    logs = service.search_learnings(
        user_id=current_user.id,
        keyword=keyword,
        project_id=project_id,
        limit=limit
    )

    return [
        LearningLogResponse(
            id=log.id,
            user_id=log.user_id,
            project_id=log.project_id,
            learning_content=log.learning_content,
            learning_source=log.learning_source,
            user_feedback=log.user_feedback,
            confidence_before=log.confidence_before,
            confidence_after=log.confidence_after,
            status=log.status.value,
            applied_count=log.applied_count,
            last_applied=log.last_applied.isoformat() if log.last_applied else None,
            learned_at=log.learned_at.isoformat()
        )
        for log in logs
    ]


@router.get("/trend/{project_id}", response_model=List[LearningTrendPoint], summary="获取学习趋势")
async def get_learning_trend(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: LearningLogService = Depends(get_learning_service)
):
    """
    获取学习趋势

    返回每日学习统计数据
    """
    trend = service.get_learning_trend(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return [LearningTrendPoint(**point) for point in trend]
