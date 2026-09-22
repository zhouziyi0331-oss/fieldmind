"""
后台学习API端点

提供异步持续学习任务管理接口
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.background_learning import (
    LearningTaskType,
    LearningTaskStatus,
    LearningTaskPriority
)
from app.services.background_learner import BackgroundLearner


router = APIRouter()


# ==================== Pydantic 模型 ====================

class LearningTaskCreateRequest(BaseModel):
    """创建学习任务请求"""
    project_id: int = Field(..., description="项目ID")
    task_type: LearningTaskType = Field(..., description="任务类型")
    task_name: str = Field(..., description="任务名称")
    task_description: str = Field(..., description="任务描述")
    task_config: Dict[str, Any] = Field(..., description="任务配置")
    priority: LearningTaskPriority = Field(LearningTaskPriority.MEDIUM, description="优先级")
    scheduled_at: Optional[str] = Field(None, description="调度时间（ISO格式）")


class LearningScheduleCreateRequest(BaseModel):
    """创建学习调度请求"""
    project_id: int = Field(..., description="项目ID")
    schedule_name: str = Field(..., description="调度名称")
    schedule_description: str = Field(..., description="调度描述")
    task_type: LearningTaskType = Field(..., description="任务类型")
    cron_expression: str = Field(..., description="Cron表达式")
    task_config_template: Dict[str, Any] = Field(..., description="任务配置模板")
    priority: LearningTaskPriority = Field(LearningTaskPriority.MEDIUM, description="优先级")


class BackgroundLearningTaskResponse(BaseModel):
    """后台学习任务响应"""
    id: str
    task_type: str
    task_name: str
    task_description: str
    project_id: int
    task_config: Dict[str, Any]
    priority: str
    scheduled_at: str
    is_recurring: bool
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]
    learning_results: Optional[Dict[str, Any]]
    discoveries: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]
    progress_percentage: float
    progress_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class LearningScheduleResponse(BaseModel):
    """学习调度响应"""
    id: str
    schedule_name: str
    schedule_description: str
    project_id: int
    task_type: str
    cron_expression: str
    task_config_template: Dict[str, Any]
    priority: str
    is_active: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    total_runs: int
    successful_runs: int
    failed_runs: int
    created_at: str

    class Config:
        from_attributes = True


class LearningInsightResponse(BaseModel):
    """学习洞察响应"""
    id: str
    task_id: str
    project_id: int
    insight_type: str
    insight_title: str
    insight_description: str
    insight_data: Dict[str, Any]
    importance_score: float
    actionability_score: float
    confidence_score: float
    suggested_actions: Optional[List[Dict[str, Any]]]
    is_reviewed: bool
    is_acted_upon: bool
    discovered_at: str
    reviewed_at: Optional[str]
    acted_upon_at: Optional[str]

    class Config:
        from_attributes = True


# ==================== 依赖项 ====================

def get_background_learner(db: Session = Depends(get_db)) -> BackgroundLearner:
    """获取后台学习服务"""
    return BackgroundLearner(db)


# ==================== 任务管理 ====================

@router.post("/tasks", response_model=BackgroundLearningTaskResponse, summary="创建学习任务")
async def create_learning_task(
    request: LearningTaskCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    创建后台学习任务

    支持的任务类型：
    - pattern_mining: 模式挖掘
    - skill_optimization: 技能优化
    - knowledge_consolidation: 知识整合
    - performance_analysis: 性能分析
    - anomaly_detection: 异常检测
    """
    scheduled_at = None
    if request.scheduled_at:
        scheduled_at = datetime.fromisoformat(request.scheduled_at)

    task = learner.create_learning_task(
        project_id=request.project_id,
        task_type=request.task_type,
        task_name=request.task_name,
        task_description=request.task_description,
        task_config=request.task_config,
        priority=request.priority,
        scheduled_at=scheduled_at,
        user_id=current_user.id
    )

    # 如果是立即执行，添加到后台任务
    if not scheduled_at or scheduled_at <= datetime.utcnow():
        background_tasks.add_task(learner.execute_task, task.id)

    return BackgroundLearningTaskResponse(
        id=task.id,
        task_type=task.task_type.value,
        task_name=task.task_name,
        task_description=task.task_description,
        project_id=task.project_id,
        task_config=task.task_config,
        priority=task.priority.value,
        scheduled_at=task.scheduled_at.isoformat(),
        is_recurring=task.is_recurring,
        status=task.status.value,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_seconds=task.duration_seconds,
        learning_results=task.learning_results,
        discoveries=task.discoveries,
        error_message=task.error_message,
        progress_percentage=task.progress_percentage,
        progress_message=task.progress_message,
        created_at=task.created_at.isoformat()
    )


@router.post("/tasks/{task_id}/execute", response_model=BackgroundLearningTaskResponse, summary="执行学习任务")
async def execute_learning_task(
    task_id: str = Path(..., description="任务ID"),
    background_tasks: BackgroundTasks = ...,
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    手动执行学习任务

    将任务添加到后台队列执行
    """
    # 添加到后台任务
    background_tasks.add_task(learner.execute_task, task_id)

    # 返回当前任务状态
    from app.models.background_learning import BackgroundLearningTask
    task = learner.db.query(BackgroundLearningTask).filter(
        BackgroundLearningTask.id == task_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return BackgroundLearningTaskResponse(
        id=task.id,
        task_type=task.task_type.value,
        task_name=task.task_name,
        task_description=task.task_description,
        project_id=task.project_id,
        task_config=task.task_config,
        priority=task.priority.value,
        scheduled_at=task.scheduled_at.isoformat(),
        is_recurring=task.is_recurring,
        status=task.status.value,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_seconds=task.duration_seconds,
        learning_results=task.learning_results,
        discoveries=task.discoveries,
        error_message=task.error_message,
        progress_percentage=task.progress_percentage,
        progress_message=task.progress_message,
        created_at=task.created_at.isoformat()
    )


@router.get("/tasks", response_model=List[BackgroundLearningTaskResponse], summary="获取学习任务列表")
async def get_learning_tasks(
    project_id: int = Query(..., description="项目ID"),
    status: Optional[LearningTaskStatus] = Query(None, description="任务状态"),
    task_type: Optional[LearningTaskType] = Query(None, description="任务类型"),
    limit: int = Query(100, description="返回数量", ge=1, le=500),
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    获取学习任务列表

    按创建时间倒序返回
    """
    tasks = learner.get_tasks(
        project_id=project_id,
        status=status,
        task_type=task_type,
        limit=limit
    )

    return [
        BackgroundLearningTaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            task_name=task.task_name,
            task_description=task.task_description,
            project_id=task.project_id,
            task_config=task.task_config,
            priority=task.priority.value,
            scheduled_at=task.scheduled_at.isoformat(),
            is_recurring=task.is_recurring,
            status=task.status.value,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            duration_seconds=task.duration_seconds,
            learning_results=task.learning_results,
            discoveries=task.discoveries,
            error_message=task.error_message,
            progress_percentage=task.progress_percentage,
            progress_message=task.progress_message,
            created_at=task.created_at.isoformat()
        )
        for task in tasks
    ]


# ==================== 调度管理 ====================

@router.post("/schedules", response_model=LearningScheduleResponse, summary="创建学习调度")
async def create_learning_schedule(
    request: LearningScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    创建定期学习调度

    使用Cron表达式定义执行频率：
    - "0 2 * * *" - 每天凌晨2点
    - "0 */6 * * *" - 每6小时
    - "0 0 * * 0" - 每周日午夜
    """
    schedule = learner.create_schedule(
        project_id=request.project_id,
        schedule_name=request.schedule_name,
        schedule_description=request.schedule_description,
        task_type=request.task_type,
        cron_expression=request.cron_expression,
        task_config_template=request.task_config_template,
        priority=request.priority
    )

    return LearningScheduleResponse(
        id=schedule.id,
        schedule_name=schedule.schedule_name,
        schedule_description=schedule.schedule_description,
        project_id=schedule.project_id,
        task_type=schedule.task_type.value,
        cron_expression=schedule.cron_expression,
        task_config_template=schedule.task_config_template,
        priority=schedule.priority.value,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        next_run_at=schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        total_runs=schedule.total_runs,
        successful_runs=schedule.successful_runs,
        failed_runs=schedule.failed_runs,
        created_at=schedule.created_at.isoformat()
    )


# ==================== 洞察管理 ====================

@router.get("/insights", response_model=List[LearningInsightResponse], summary="获取学习洞察")
async def get_learning_insights(
    project_id: int = Query(..., description="项目ID"),
    insight_type: Optional[str] = Query(None, description="洞察类型"),
    is_reviewed: Optional[bool] = Query(None, description="是否已审核"),
    min_importance: float = Query(0.0, description="最小重要性分数", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    获取学习洞察列表

    后台学习任务产生的发现和建议
    """
    insights = learner.get_insights(
        project_id=project_id,
        insight_type=insight_type,
        is_reviewed=is_reviewed,
        min_importance=min_importance
    )

    return [
        LearningInsightResponse(
            id=insight.id,
            task_id=insight.task_id,
            project_id=insight.project_id,
            insight_type=insight.insight_type,
            insight_title=insight.insight_title,
            insight_description=insight.insight_description,
            insight_data=insight.insight_data,
            importance_score=insight.importance_score,
            actionability_score=insight.actionability_score,
            confidence_score=insight.confidence_score,
            suggested_actions=insight.suggested_actions,
            is_reviewed=insight.is_reviewed,
            is_acted_upon=insight.is_acted_upon,
            discovered_at=insight.discovered_at.isoformat(),
            reviewed_at=insight.reviewed_at.isoformat() if insight.reviewed_at else None,
            acted_upon_at=insight.acted_upon_at.isoformat() if insight.acted_upon_at else None
        )
        for insight in insights
    ]


@router.put("/insights/{insight_id}/review", response_model=LearningInsightResponse, summary="审核洞察")
async def review_insight(
    insight_id: str = Path(..., description="洞察ID"),
    current_user: User = Depends(get_current_user),
    learner: BackgroundLearner = Depends(get_background_learner)
):
    """
    标记洞察为已审核
    """
    from app.models.background_learning import LearningInsight

    insight = learner.db.query(LearningInsight).filter(
        LearningInsight.id == insight_id
    ).first()

    if not insight:
        raise HTTPException(status_code=404, detail="洞察不存在")

    insight.is_reviewed = True
    insight.reviewed_at = datetime.utcnow()

    learner.db.commit()
    learner.db.refresh(insight)

    return LearningInsightResponse(
        id=insight.id,
        task_id=insight.task_id,
        project_id=insight.project_id,
        insight_type=insight.insight_type,
        insight_title=insight.insight_title,
        insight_description=insight.insight_description,
        insight_data=insight.insight_data,
        importance_score=insight.importance_score,
        actionability_score=insight.actionability_score,
        confidence_score=insight.confidence_score,
        suggested_actions=insight.suggested_actions,
        is_reviewed=insight.is_reviewed,
        is_acted_upon=insight.is_acted_upon,
        discovered_at=insight.discovered_at.isoformat(),
        reviewed_at=insight.reviewed_at.isoformat() if insight.reviewed_at else None,
        acted_upon_at=insight.acted_upon_at.isoformat() if insight.acted_upon_at else None
    )
