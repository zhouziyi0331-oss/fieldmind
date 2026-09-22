"""
用户喂养API端点

提供用户主动输入、知识喂养和偏好学习接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.feeding_service import UserFeedingService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class FeedingSessionCreate(BaseModel):
    """创建喂养会话请求"""
    project_id: int = Field(..., description="项目ID")
    session_type: str = Field(..., description="会话类型")
    content: str = Field(..., description="喂养内容")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    importance: float = Field(0.5, description="重要性（0-1）", ge=0, le=1)


class FeedingSessionResponse(BaseModel):
    """喂养会话响应"""
    id: int
    user_id: int
    project_id: int
    session_type: str
    content: str
    context: Dict[str, Any]
    importance: float
    applied_count: int
    last_applied: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ImportanceUpdateRequest(BaseModel):
    """重要性更新请求"""
    importance: float = Field(..., description="新重要性", ge=0, le=1)


class FeedingSummaryResponse(BaseModel):
    """喂养摘要响应"""
    period_days: int
    total_sessions: int
    type_breakdown: Dict[str, int]
    avg_importance: float
    total_applications: int
    applied_count: int
    application_rate: float
    start_date: str
    end_date: str


class ValuableFeedingResponse(BaseModel):
    """有价值喂养响应"""
    id: int
    type: str
    content: str
    value_score: float
    importance: float
    applied_count: int
    created_at: str


class FeedingTrendPoint(BaseModel):
    """喂养趋势点"""
    date: str
    count: int
    by_type: Dict[str, int]


# ==================== 依赖项 ====================

def get_feeding_service(db: Session = Depends(get_db)) -> UserFeedingService:
    """获取用户喂养服务"""
    return UserFeedingService(db)


# ==================== 喂养会话管理 ====================

@router.post("/sessions", response_model=FeedingSessionResponse, summary="创建喂养会话")
async def create_feeding_session(
    session: FeedingSessionCreate,
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    创建喂养会话

    - **project_id**: 项目ID
    - **session_type**: 会话类型（correction, preference, guidance, example）
    - **content**: 喂养内容
    - **context**: 上下文信息
    - **importance**: 重要性（0-1）
    """
    result = service.create_feeding_session(
        user_id=current_user.id,
        project_id=session.project_id,
        session_type=session.session_type,
        content=session.content,
        context=session.context,
        importance=session.importance
    )

    return FeedingSessionResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        session_type=result.session_type,
        content=result.content,
        context=result.context,
        importance=result.importance,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        created_at=result.created_at.isoformat()
    )


@router.get("/sessions", response_model=List[FeedingSessionResponse], summary="获取喂养会话列表")
async def get_feeding_sessions(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    session_type: Optional[str] = Query(None, description="筛选会话类型"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取喂养会话列表

    按时间倒序返回
    """
    sessions = service.get_feeding_sessions(
        user_id=current_user.id,
        project_id=project_id,
        session_type=session_type,
        limit=limit
    )

    return [
        FeedingSessionResponse(
            id=s.id,
            user_id=s.user_id,
            project_id=s.project_id,
            session_type=s.session_type,
            content=s.content,
            context=s.context,
            importance=s.importance,
            applied_count=s.applied_count,
            last_applied=s.last_applied.isoformat() if s.last_applied else None,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.post("/sessions/{session_id}/apply", response_model=FeedingSessionResponse, summary="记录喂养应用")
async def record_application(
    session_id: int = Path(..., description="会话ID"),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    记录喂养内容的应用

    增加应用计数并更新最后应用时间
    """
    result = service.record_application(session_id=session_id)

    return FeedingSessionResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        session_type=result.session_type,
        content=result.content,
        context=result.context,
        importance=result.importance,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        created_at=result.created_at.isoformat()
    )


@router.put("/sessions/{session_id}/importance", response_model=FeedingSessionResponse, summary="更新会话重要性")
async def update_importance(
    session_id: int = Path(..., description="会话ID"),
    update: ImportanceUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    更新会话重要性

    - **importance**: 新重要性（0-1）
    """
    result = service.update_importance(
        session_id=session_id,
        importance=update.importance
    )

    return FeedingSessionResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        session_type=result.session_type,
        content=result.content,
        context=result.context,
        importance=result.importance,
        applied_count=result.applied_count,
        last_applied=result.last_applied.isoformat() if result.last_applied else None,
        created_at=result.created_at.isoformat()
    )


@router.delete("/sessions/{session_id}", summary="删除喂养会话")
async def delete_feeding(
    session_id: int = Path(..., description="会话ID"),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """删除喂养会话"""
    success = service.delete_feeding(
        session_id=session_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="喂养会话不存在或无权删除")

    return {"message": "喂养会话已删除"}


# ==================== 喂养分析 ====================

@router.get("/summary/{project_id}", response_model=FeedingSummaryResponse, summary="获取喂养摘要")
async def get_feeding_summary(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取喂养摘要统计

    包含：
    - 喂养总数
    - 类型分布
    - 平均重要性
    - 应用统计
    """
    summary = service.get_feeding_summary(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return FeedingSummaryResponse(**summary)


@router.get("/valuable/{project_id}", response_model=List[ValuableFeedingResponse], summary="获取最有价值喂养")
async def get_valuable_feedings(
    project_id: int = Path(..., description="项目ID"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取最有价值的喂养内容

    基于重要性和应用次数计算价值分数
    """
    valuable = service.get_most_valuable_feedings(
        user_id=current_user.id,
        project_id=project_id,
        limit=limit
    )

    return [ValuableFeedingResponse(**item) for item in valuable]


@router.get("/search", response_model=List[FeedingSessionResponse], summary="搜索喂养内容")
async def search_feedings(
    keyword: str = Query(..., description="搜索关键词"),
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    搜索喂养内容

    在喂养内容中搜索关键词
    """
    sessions = service.search_feedings(
        user_id=current_user.id,
        keyword=keyword,
        project_id=project_id,
        limit=limit
    )

    return [
        FeedingSessionResponse(
            id=s.id,
            user_id=s.user_id,
            project_id=s.project_id,
            session_type=s.session_type,
            content=s.content,
            context=s.context,
            importance=s.importance,
            applied_count=s.applied_count,
            last_applied=s.last_applied.isoformat() if s.last_applied else None,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.get("/trend/{project_id}", response_model=List[FeedingTrendPoint], summary="获取喂养趋势")
async def get_feeding_trend(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取喂养趋势

    返回每日喂养统计数据
    """
    trend = service.get_feeding_trend(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return [FeedingTrendPoint(**point) for point in trend]


# ==================== 特定类型查询 ====================

@router.get("/corrections/{project_id}", response_model=List[FeedingSessionResponse], summary="获取用户纠正")
async def get_recent_corrections(
    project_id: int = Path(..., description="项目ID"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取最近的用户纠正

    按重要性和时间排序
    """
    sessions = service.get_recent_corrections(
        user_id=current_user.id,
        project_id=project_id,
        limit=limit
    )

    return [
        FeedingSessionResponse(
            id=s.id,
            user_id=s.user_id,
            project_id=s.project_id,
            session_type=s.session_type,
            content=s.content,
            context=s.context,
            importance=s.importance,
            applied_count=s.applied_count,
            last_applied=s.last_applied.isoformat() if s.last_applied else None,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.get("/preferences/{project_id}", response_model=List[FeedingSessionResponse], summary="获取用户偏好")
async def get_user_preferences(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    service: UserFeedingService = Depends(get_feeding_service)
):
    """
    获取用户偏好设置

    按重要性和时间排序
    """
    sessions = service.get_user_preferences(
        user_id=current_user.id,
        project_id=project_id
    )

    return [
        FeedingSessionResponse(
            id=s.id,
            user_id=s.user_id,
            project_id=s.project_id,
            session_type=s.session_type,
            content=s.content,
            context=s.context,
            importance=s.importance,
            applied_count=s.applied_count,
            last_applied=s.last_applied.isoformat() if s.last_applied else None,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]
