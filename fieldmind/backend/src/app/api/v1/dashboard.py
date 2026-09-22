"""
Dashboard和指标系统API端点

提供项目指标、趋势分析、工作量计算和价值展示接口
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.metrics_service import MetricsService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class MetricsSnapshotCreate(BaseModel):
    """创建指标快照请求"""
    project_id: int = Field(..., description="项目ID")
    metric_type: str = Field(..., description="指标类型")
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: str = Field(..., description="单位")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="维度信息")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class MetricsSnapshotResponse(BaseModel):
    """指标快照响应"""
    id: int
    project_id: int
    metric_type: str
    metric_name: str
    value: float
    unit: str
    dimensions: Dict[str, Any]
    extra_metadata: Dict[str, Any]
    captured_at: str

    class Config:
        from_attributes = True


class MetricsEventCreate(BaseModel):
    """记录指标事件请求"""
    project_id: int = Field(..., description="项目ID")
    event_type: str = Field(..., description="事件类型")
    event_name: str = Field(..., description="事件名称")
    actor_type: str = Field(..., description="操作者类型")
    actor_id: Optional[int] = Field(None, description="操作者ID")
    impact_score: Optional[float] = Field(None, description="影响分数", ge=0, le=100)
    event_data: Optional[Dict[str, Any]] = Field(None, description="事件数据")


class MetricsEventResponse(BaseModel):
    """指标事件响应"""
    id: int
    project_id: int
    event_type: str
    event_name: str
    actor_type: str
    actor_id: Optional[int]
    impact_score: Optional[float]
    event_data: Dict[str, Any]
    occurred_at: str

    class Config:
        from_attributes = True


class ProjectMetricsResponse(BaseModel):
    """项目指标响应"""
    id: int
    project_id: int
    document_count: int
    entity_count: int
    relationship_count: int
    analysis_count: int
    total_storage_mb: float
    ai_calls_count: int
    avg_processing_time: float
    last_activity_at: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class WorkloadCalculationResponse(BaseModel):
    """工作量计算响应"""
    id: int
    project_id: int
    calculation_period_days: int
    operation_counts: Dict[str, int]
    workload_score: float
    calculated_at: str

    class Config:
        from_attributes = True


class ValueExhibitionCreate(BaseModel):
    """创建价值展示请求"""
    project_id: int = Field(..., description="项目ID")
    exhibition_type: str = Field(..., description="展示类型")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    metrics_summary: Dict[str, Any] = Field(..., description="指标摘要")
    visual_data: Optional[Dict[str, Any]] = Field(None, description="可视化数据")


class ValueExhibitionResponse(BaseModel):
    """价值展示响应"""
    id: int
    project_id: int
    exhibition_type: str
    title: str
    description: str
    metrics_summary: Dict[str, Any]
    visual_data: Dict[str, Any]
    created_by: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    """Dashboard概览响应"""
    project_id: int
    project_metrics: ProjectMetricsResponse
    recent_events: List[MetricsEventResponse]
    workload: Optional[WorkloadCalculationResponse]
    trend_data: Dict[str, List[Dict[str, Any]]]
    value_exhibitions: List[ValueExhibitionResponse]


# ==================== 依赖项 ====================

async def get_metrics_service(db: AsyncSession = Depends(get_db)) -> MetricsService:
    """获取指标服务"""
    return MetricsService(db)


# ==================== 指标快照 ====================

@router.post("/snapshots", response_model=MetricsSnapshotResponse, summary="创建指标快照")
async def create_metrics_snapshot(
    snapshot: MetricsSnapshotCreate,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    创建指标快照

    - **metric_type**: 指标类型（performance, quality, usage, progress）
    - **metric_name**: 指标名称（document_count, entity_count等）
    - **value**: 指标值
    - **unit**: 单位（count, percentage, seconds等）
    """
    result = await metrics_service.create_snapshot(
        project_id=snapshot.project_id,
        metric_type=snapshot.metric_type,
        metric_name=snapshot.metric_name,
        value=snapshot.value,
        unit=snapshot.unit,
        dimensions=snapshot.dimensions,
        extra_metadata=snapshot.extra_metadata
    )

    return MetricsSnapshotResponse(
        id=result.id,
        project_id=result.project_id,
        metric_type=result.metric_type,
        metric_name=result.metric_name,
        value=result.value,
        unit=result.unit,
        dimensions=result.dimensions,
        extra_metadata=result.extra_metadata,
        captured_at=result.captured_at.isoformat()
    )


@router.get("/snapshots/{project_id}", response_model=List[MetricsSnapshotResponse], summary="获取指标快照列表")
async def get_metrics_snapshots(
    project_id: int = Path(..., description="项目ID"),
    metric_type: Optional[str] = Query(None, description="筛选指标类型"),
    metric_name: Optional[str] = Query(None, description="筛选指标名称"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取最新的指标快照"""
    snapshots = await metrics_service.get_latest_snapshots(
        project_id=project_id,
        metric_type=metric_type,
        metric_name=metric_name,
        limit=limit
    )

    return [
        MetricsSnapshotResponse(
            id=s.id,
            project_id=s.project_id,
            metric_type=s.metric_type,
            metric_name=s.metric_name,
            value=s.value,
            unit=s.unit,
            dimensions=s.dimensions,
            extra_metadata=s.extra_metadata,
            captured_at=s.captured_at.isoformat()
        )
        for s in snapshots
    ]


@router.get("/snapshots/{project_id}/trend/{metric_name}", summary="获取指标趋势")
async def get_metric_trend(
    project_id: int = Path(..., description="项目ID"),
    metric_name: str = Path(..., description="指标名称"),
    days: int = Query(7, description="查询天数", ge=1, le=90),
    interval_minutes: int = Query(60, description="聚合间隔（分钟）", ge=5, le=1440),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    获取指标趋势（时间序列）

    返回指定时间范围内的指标变化趋势
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    trend = await metrics_service.get_metric_trend(
        project_id=project_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        interval_minutes=interval_minutes
    )

    return {
        "project_id": project_id,
        "metric_name": metric_name,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "interval_minutes": interval_minutes,
        "data_points": trend
    }


# ==================== 指标事件 ====================

@router.post("/events", response_model=MetricsEventResponse, summary="记录指标事件")
async def record_metrics_event(
    event: MetricsEventCreate,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    记录指标事件

    - **event_type**: 事件类型（user_action, system_event, milestone）
    - **event_name**: 事件名称（document_uploaded, analysis_completed等）
    - **actor_type**: 操作者类型（user, ai, system）
    """
    result = await metrics_service.record_event(
        project_id=event.project_id,
        event_type=event.event_type,
        event_name=event.event_name,
        actor_type=event.actor_type,
        actor_id=event.actor_id or current_user.id,
        impact_score=event.impact_score,
        event_data=event.event_data
    )

    return MetricsEventResponse(
        id=result.id,
        project_id=result.project_id,
        event_type=result.event_type,
        event_name=result.event_name,
        actor_type=result.actor_type,
        actor_id=result.actor_id,
        impact_score=result.impact_score,
        event_data=result.event_data,
        occurred_at=result.occurred_at.isoformat()
    )


@router.get("/events/{project_id}", response_model=List[MetricsEventResponse], summary="获取指标事件列表")
async def get_metrics_events(
    project_id: int = Path(..., description="项目ID"),
    event_type: Optional[str] = Query(None, description="筛选事件类型"),
    days: int = Query(7, description="查询天数", ge=1, le=90),
    limit: int = Query(100, description="返回数量", ge=1, le=500),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取指标事件列表"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    events = await metrics_service.get_events(
        project_id=project_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    return [
        MetricsEventResponse(
            id=e.id,
            project_id=e.project_id,
            event_type=e.event_type,
            event_name=e.event_name,
            actor_type=e.actor_type,
            actor_id=e.actor_id,
            impact_score=e.impact_score,
            event_data=e.event_data,
            occurred_at=e.occurred_at.isoformat()
        )
        for e in events
    ]


@router.get("/events/{project_id}/statistics", summary="获取事件统计")
async def get_event_statistics(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(7, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取事件统计信息"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    stats = await metrics_service.get_event_statistics(
        project_id=project_id,
        start_time=start_time,
        end_time=end_time
    )

    return stats


# ==================== 项目指标 ====================

@router.get("/projects/{project_id}/metrics", response_model=ProjectMetricsResponse, summary="获取项目指标")
async def get_project_metrics(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取项目的聚合指标"""
    metrics = await metrics_service.get_project_metrics(project_id)

    if not metrics:
        raise HTTPException(status_code=404, detail="项目指标不存在")

    return ProjectMetricsResponse(
        id=metrics.id,
        project_id=metrics.project_id,
        document_count=metrics.document_count,
        entity_count=metrics.entity_count,
        relationship_count=metrics.relationship_count,
        analysis_count=metrics.analysis_count,
        total_storage_mb=metrics.total_storage_mb,
        ai_calls_count=metrics.ai_calls_count,
        avg_processing_time=metrics.avg_processing_time,
        last_activity_at=metrics.last_activity_at.isoformat(),
        created_at=metrics.created_at.isoformat(),
        updated_at=metrics.updated_at.isoformat()
    )


@router.post("/projects/{project_id}/metrics/increment", summary="增量更新指标")
async def increment_project_metric(
    project_id: int = Path(..., description="项目ID"),
    metric_name: str = Query(..., description="指标名称"),
    increment: int = Query(1, description="增量值"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    增量更新项目指标

    - **metric_name**: document_count, entity_count, relationship_count等
    - **increment**: 增量值（可以为负数）
    """
    metrics = await metrics_service.increment_metric(
        project_id=project_id,
        metric_name=metric_name,
        increment=increment
    )

    return {
        "project_id": project_id,
        "metric_name": metric_name,
        "increment": increment,
        "new_value": getattr(metrics, metric_name),
        "updated_at": metrics.updated_at.isoformat()
    }


# ==================== 工作量计算 ====================

@router.post("/projects/{project_id}/workload/calculate", response_model=WorkloadCalculationResponse, summary="计算工作量")
async def calculate_project_workload(
    project_id: int = Path(..., description="项目ID"),
    period_days: int = Query(7, description="计算周期（天）", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    计算项目工作量

    基于操作次数和项目指标计算工作量分数（0-100）
    """
    result = await metrics_service.calculate_workload(
        project_id=project_id,
        calculation_period_days=period_days
    )

    return WorkloadCalculationResponse(
        id=result.id,
        project_id=result.project_id,
        calculation_period_days=result.calculation_period_days,
        operation_counts=result.operation_counts,
        workload_score=result.workload_score,
        calculated_at=result.calculated_at.isoformat()
    )


@router.get("/projects/{project_id}/workload/history", response_model=List[WorkloadCalculationResponse], summary="获取工作量历史")
async def get_workload_history(
    project_id: int = Path(..., description="项目ID"),
    limit: int = Query(30, description="返回数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取项目的工作量计算历史"""
    history = await metrics_service.get_workload_history(
        project_id=project_id,
        limit=limit
    )

    return [
        WorkloadCalculationResponse(
            id=w.id,
            project_id=w.project_id,
            calculation_period_days=w.calculation_period_days,
            operation_counts=w.operation_counts,
            workload_score=w.workload_score,
            calculated_at=w.calculated_at.isoformat()
        )
        for w in history
    ]


# ==================== 价值展示 ====================

@router.post("/value-exhibitions", response_model=ValueExhibitionResponse, summary="创建价值展示")
async def create_value_exhibition(
    exhibition: ValueExhibitionCreate,
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    创建价值展示

    - **exhibition_type**: 展示类型（achievement, insight, impact）
    - **title**: 标题
    - **description**: 描述
    - **metrics_summary**: 指标摘要
    """
    result = await metrics_service.create_value_exhibition(
        project_id=exhibition.project_id,
        exhibition_type=exhibition.exhibition_type,
        title=exhibition.title,
        description=exhibition.description,
        metrics_summary=exhibition.metrics_summary,
        visual_data=exhibition.visual_data,
        created_by=current_user.id
    )

    return ValueExhibitionResponse(
        id=result.id,
        project_id=result.project_id,
        exhibition_type=result.exhibition_type,
        title=result.title,
        description=result.description,
        metrics_summary=result.metrics_summary,
        visual_data=result.visual_data,
        created_by=result.created_by,
        created_at=result.created_at.isoformat()
    )


@router.get("/value-exhibitions/{project_id}", response_model=List[ValueExhibitionResponse], summary="获取价值展示列表")
async def list_value_exhibitions(
    project_id: int = Path(..., description="项目ID"),
    exhibition_type: Optional[str] = Query(None, description="筛选展示类型"),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """获取项目的价值展示列表"""
    exhibitions = await metrics_service.list_value_exhibitions(
        project_id=project_id,
        exhibition_type=exhibition_type,
        limit=limit
    )

    return [
        ValueExhibitionResponse(
            id=e.id,
            project_id=e.project_id,
            exhibition_type=e.exhibition_type,
            title=e.title,
            description=e.description,
            metrics_summary=e.metrics_summary,
            visual_data=e.visual_data,
            created_by=e.created_by,
            created_at=e.created_at.isoformat()
        )
        for e in exhibitions
    ]


# ==================== Dashboard概览 ====================

@router.get("/dashboard/{project_id}", response_model=DashboardSummaryResponse, summary="获取Dashboard概览")
async def get_dashboard_summary(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """
    获取项目Dashboard完整概览

    包含项目指标、近期事件、工作量、趋势数据和价值展示
    """
    # 获取项目指标
    metrics = await metrics_service.get_project_metrics(project_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="项目指标不存在")

    # 获取近期事件
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    recent_events = await metrics_service.get_events(
        project_id=project_id,
        start_time=start_time,
        end_time=end_time,
        limit=20
    )

    # 获取最新工作量
    workload_history = await metrics_service.get_workload_history(project_id, limit=1)
    workload = workload_history[0] if workload_history else None

    # 获取趋势数据
    trend_data = {}
    for metric_name in ["document_count", "entity_count", "analysis_count"]:
        trend = await metrics_service.get_metric_trend(
            project_id=project_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=360  # 6小时间隔
        )
        trend_data[metric_name] = trend

    # 获取价值展示
    exhibitions = await metrics_service.list_value_exhibitions(project_id, limit=5)

    return DashboardSummaryResponse(
        project_id=project_id,
        project_metrics=ProjectMetricsResponse(
            id=metrics.id,
            project_id=metrics.project_id,
            document_count=metrics.document_count,
            entity_count=metrics.entity_count,
            relationship_count=metrics.relationship_count,
            analysis_count=metrics.analysis_count,
            total_storage_mb=metrics.total_storage_mb,
            ai_calls_count=metrics.ai_calls_count,
            avg_processing_time=metrics.avg_processing_time,
            last_activity_at=metrics.last_activity_at.isoformat(),
            created_at=metrics.created_at.isoformat(),
            updated_at=metrics.updated_at.isoformat()
        ),
        recent_events=[
            MetricsEventResponse(
                id=e.id,
                project_id=e.project_id,
                event_type=e.event_type,
                event_name=e.event_name,
                actor_type=e.actor_type,
                actor_id=e.actor_id,
                impact_score=e.impact_score,
                event_data=e.event_data,
                occurred_at=e.occurred_at.isoformat()
            )
            for e in recent_events
        ],
        workload=WorkloadCalculationResponse(
            id=workload.id,
            project_id=workload.project_id,
            calculation_period_days=workload.calculation_period_days,
            operation_counts=workload.operation_counts,
            workload_score=workload.workload_score,
            calculated_at=workload.calculated_at.isoformat()
        ) if workload else None,
        trend_data=trend_data,
        value_exhibitions=[
            ValueExhibitionResponse(
                id=ex.id,
                project_id=ex.project_id,
                exhibition_type=ex.exhibition_type,
                title=ex.title,
                description=ex.description,
                metrics_summary=ex.metrics_summary,
                visual_data=ex.visual_data,
                created_by=ex.created_by,
                created_at=ex.created_at.isoformat()
            )
            for ex in exhibitions
        ]
    )
