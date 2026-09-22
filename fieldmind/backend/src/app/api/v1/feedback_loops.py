"""
反馈闭环API端点

提供完整的执行-反馈-学习-改进循环接口
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.feedback_loop import FeedbackSentiment, ImprovementPriority
from app.services.feedback_loop_manager import FeedbackLoopManager


router = APIRouter()


# ==================== Pydantic 模型 ====================

class FeedbackLoopStartRequest(BaseModel):
    """启动反馈闭环请求"""
    execution_id: str = Field(..., description="执行记录ID")
    project_id: int = Field(..., description="项目ID")
    skill_id: Optional[str] = Field(None, description="技能ID")
    pattern_id: Optional[str] = Field(None, description="模式ID")


class FeedbackCollectRequest(BaseModel):
    """收集反馈请求"""
    user_rating: Optional[int] = Field(None, description="用户评分（1-5）", ge=1, le=5)
    user_comment: Optional[str] = Field(None, description="用户评论")
    automatic_metrics: Optional[Dict[str, Any]] = Field(None, description="自动指标")


class FeedbackLoopResponse(BaseModel):
    """反馈闭环响应"""
    id: str
    execution_id: str
    skill_id: Optional[str]
    pattern_id: Optional[str]
    project_id: int
    execution_context: Dict[str, Any]
    execution_result: Dict[str, Any]
    feedback_collected: Dict[str, Any]
    feedback_sentiment: str
    feedback_score: float
    insights_learned: Optional[Dict[str, Any]]
    lessons_extracted: Optional[Dict[str, Any]]
    improvements_proposed: Optional[List[Dict[str, Any]]]
    improvements_applied: Optional[List[Dict[str, Any]]]
    loop_completed: bool
    completion_percentage: float
    execution_started_at: str
    feedback_received_at: Optional[str]
    learning_completed_at: Optional[str]
    improvements_proposed_at: Optional[str]
    loop_closed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ImprovementTaskResponse(BaseModel):
    """改进任务响应"""
    id: str
    feedback_loop_id: str
    skill_id: Optional[str]
    task_title: str
    task_description: str
    improvement_type: str
    priority: str
    expected_impact: Optional[str]
    estimated_effort: Optional[str]
    implementation_plan: Optional[Dict[str, Any]]
    status: str
    progress_percentage: float
    completion_result: Optional[Dict[str, Any]]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True


class LoopMetricsResponse(BaseModel):
    """闭环指标响应"""
    id: str
    project_id: int
    period_start: str
    period_end: str
    total_loops: int
    completed_loops: int
    avg_loop_duration_hours: Optional[float]
    total_feedback_received: int
    positive_feedback_count: int
    negative_feedback_count: int
    avg_feedback_score: Optional[float]
    insights_generated: int
    patterns_discovered: int
    lessons_learned: int
    improvements_proposed: int
    improvements_implemented: int
    avg_improvement_impact: Optional[float]
    calculated_at: str

    class Config:
        from_attributes = True


# ==================== 依赖项 ====================

def get_loop_manager(db: Session = Depends(get_db)) -> FeedbackLoopManager:
    """获取反馈闭环管理服务"""
    return FeedbackLoopManager(db)


# ==================== 闭环管理 ====================

@router.post("/loops", response_model=FeedbackLoopResponse, summary="启动反馈闭环")
async def start_feedback_loop(
    request: FeedbackLoopStartRequest,
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    启动反馈闭环

    从一次执行开始，创建完整的反馈学习循环
    """
    loop = manager.start_feedback_loop(
        execution_id=request.execution_id,
        project_id=request.project_id,
        user_id=current_user.id,
        skill_id=request.skill_id,
        pattern_id=request.pattern_id
    )

    return FeedbackLoopResponse(
        id=loop.id,
        execution_id=loop.execution_id,
        skill_id=loop.skill_id,
        pattern_id=loop.pattern_id,
        project_id=loop.project_id,
        execution_context=loop.execution_context,
        execution_result=loop.execution_result,
        feedback_collected=loop.feedback_collected,
        feedback_sentiment=loop.feedback_sentiment.value,
        feedback_score=loop.feedback_score,
        insights_learned=loop.insights_learned,
        lessons_extracted=loop.lessons_extracted,
        improvements_proposed=loop.improvements_proposed,
        improvements_applied=loop.improvements_applied,
        loop_completed=loop.loop_completed,
        completion_percentage=loop.completion_percentage,
        execution_started_at=loop.execution_started_at.isoformat(),
        feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
        learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
        improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
        loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
        created_at=loop.created_at.isoformat()
    )


@router.post("/loops/{loop_id}/feedback", response_model=FeedbackLoopResponse, summary="收集反馈")
async def collect_feedback(
    loop_id: str = Path(..., description="闭环ID"),
    feedback: FeedbackCollectRequest = ...,
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    收集反馈

    接收用户评分、评论和自动收集的指标
    """
    loop = manager.collect_feedback(
        loop_id=loop_id,
        user_rating=feedback.user_rating,
        user_comment=feedback.user_comment,
        automatic_metrics=feedback.automatic_metrics
    )

    return FeedbackLoopResponse(
        id=loop.id,
        execution_id=loop.execution_id,
        skill_id=loop.skill_id,
        pattern_id=loop.pattern_id,
        project_id=loop.project_id,
        execution_context=loop.execution_context,
        execution_result=loop.execution_result,
        feedback_collected=loop.feedback_collected,
        feedback_sentiment=loop.feedback_sentiment.value,
        feedback_score=loop.feedback_score,
        insights_learned=loop.insights_learned,
        lessons_extracted=loop.lessons_extracted,
        improvements_proposed=loop.improvements_proposed,
        improvements_applied=loop.improvements_applied,
        loop_completed=loop.loop_completed,
        completion_percentage=loop.completion_percentage,
        execution_started_at=loop.execution_started_at.isoformat(),
        feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
        learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
        improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
        loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
        created_at=loop.created_at.isoformat()
    )


@router.post("/loops/{loop_id}/learn", response_model=FeedbackLoopResponse, summary="执行学习")
async def perform_learning(
    loop_id: str = Path(..., description="闭环ID"),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    执行学习阶段

    从反馈中提取洞察和经验教训
    """
    loop = manager.perform_learning(loop_id=loop_id)

    return FeedbackLoopResponse(
        id=loop.id,
        execution_id=loop.execution_id,
        skill_id=loop.skill_id,
        pattern_id=loop.pattern_id,
        project_id=loop.project_id,
        execution_context=loop.execution_context,
        execution_result=loop.execution_result,
        feedback_collected=loop.feedback_collected,
        feedback_sentiment=loop.feedback_sentiment.value,
        feedback_score=loop.feedback_score,
        insights_learned=loop.insights_learned,
        lessons_extracted=loop.lessons_extracted,
        improvements_proposed=loop.improvements_proposed,
        improvements_applied=loop.improvements_applied,
        loop_completed=loop.loop_completed,
        completion_percentage=loop.completion_percentage,
        execution_started_at=loop.execution_started_at.isoformat(),
        feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
        learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
        improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
        loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
        created_at=loop.created_at.isoformat()
    )


@router.post("/loops/{loop_id}/improve", response_model=FeedbackLoopResponse, summary="提出改进")
async def propose_improvements(
    loop_id: str = Path(..., description="闭环ID"),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    提出改进建议

    基于学习结果生成改进任务
    """
    loop = manager.propose_improvements(loop_id=loop_id)

    return FeedbackLoopResponse(
        id=loop.id,
        execution_id=loop.execution_id,
        skill_id=loop.skill_id,
        pattern_id=loop.pattern_id,
        project_id=loop.project_id,
        execution_context=loop.execution_context,
        execution_result=loop.execution_result,
        feedback_collected=loop.feedback_collected,
        feedback_sentiment=loop.feedback_sentiment.value,
        feedback_score=loop.feedback_score,
        insights_learned=loop.insights_learned,
        lessons_extracted=loop.lessons_extracted,
        improvements_proposed=loop.improvements_proposed,
        improvements_applied=loop.improvements_applied,
        loop_completed=loop.loop_completed,
        completion_percentage=loop.completion_percentage,
        execution_started_at=loop.execution_started_at.isoformat(),
        feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
        learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
        improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
        loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
        created_at=loop.created_at.isoformat()
    )


@router.post("/loops/{loop_id}/complete", response_model=FeedbackLoopResponse, summary="完成闭环")
async def complete_loop(
    loop_id: str = Path(..., description="闭环ID"),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    完成闭环

    标记闭环已完成
    """
    loop = manager.complete_loop(loop_id=loop_id)

    return FeedbackLoopResponse(
        id=loop.id,
        execution_id=loop.execution_id,
        skill_id=loop.skill_id,
        pattern_id=loop.pattern_id,
        project_id=loop.project_id,
        execution_context=loop.execution_context,
        execution_result=loop.execution_result,
        feedback_collected=loop.feedback_collected,
        feedback_sentiment=loop.feedback_sentiment.value,
        feedback_score=loop.feedback_score,
        insights_learned=loop.insights_learned,
        lessons_extracted=loop.lessons_extracted,
        improvements_proposed=loop.improvements_proposed,
        improvements_applied=loop.improvements_applied,
        loop_completed=loop.loop_completed,
        completion_percentage=loop.completion_percentage,
        execution_started_at=loop.execution_started_at.isoformat(),
        feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
        learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
        improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
        loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
        created_at=loop.created_at.isoformat()
    )


# ==================== 查询接口 ====================

@router.get("/loops", response_model=List[FeedbackLoopResponse], summary="获取反馈闭环列表")
async def get_feedback_loops(
    project_id: int = Query(..., description="项目ID"),
    completed: Optional[bool] = Query(None, description="是否已完成"),
    min_feedback_score: float = Query(0.0, description="最小反馈分数", ge=0, le=1),
    limit: int = Query(100, description="返回数量", ge=1, le=500),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    获取反馈闭环列表

    按创建时间倒序返回
    """
    loops = manager.get_feedback_loops(
        project_id=project_id,
        completed=completed,
        min_feedback_score=min_feedback_score,
        limit=limit
    )

    return [
        FeedbackLoopResponse(
            id=loop.id,
            execution_id=loop.execution_id,
            skill_id=loop.skill_id,
            pattern_id=loop.pattern_id,
            project_id=loop.project_id,
            execution_context=loop.execution_context,
            execution_result=loop.execution_result,
            feedback_collected=loop.feedback_collected,
            feedback_sentiment=loop.feedback_sentiment.value,
            feedback_score=loop.feedback_score,
            insights_learned=loop.insights_learned,
            lessons_extracted=loop.lessons_extracted,
            improvements_proposed=loop.improvements_proposed,
            improvements_applied=loop.improvements_applied,
            loop_completed=loop.loop_completed,
            completion_percentage=loop.completion_percentage,
            execution_started_at=loop.execution_started_at.isoformat(),
            feedback_received_at=loop.feedback_received_at.isoformat() if loop.feedback_received_at else None,
            learning_completed_at=loop.learning_completed_at.isoformat() if loop.learning_completed_at else None,
            improvements_proposed_at=loop.improvements_proposed_at.isoformat() if loop.improvements_proposed_at else None,
            loop_closed_at=loop.loop_closed_at.isoformat() if loop.loop_closed_at else None,
            created_at=loop.created_at.isoformat()
        )
        for loop in loops
    ]


@router.get("/tasks", response_model=List[ImprovementTaskResponse], summary="获取改进任务列表")
async def get_improvement_tasks(
    project_id: int = Query(..., description="项目ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    priority: Optional[ImprovementPriority] = Query(None, description="优先级"),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    获取改进任务列表

    按优先级和创建时间排序
    """
    tasks = manager.get_improvement_tasks(
        project_id=project_id,
        status=status,
        priority=priority
    )

    return [
        ImprovementTaskResponse(
            id=task.id,
            feedback_loop_id=task.feedback_loop_id,
            skill_id=task.skill_id,
            task_title=task.task_title,
            task_description=task.task_description,
            improvement_type=task.improvement_type,
            priority=task.priority.value,
            expected_impact=task.expected_impact,
            estimated_effort=task.estimated_effort,
            implementation_plan=task.implementation_plan,
            status=task.status,
            progress_percentage=task.progress_percentage,
            completion_result=task.completion_result,
            created_at=task.created_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]


@router.get("/metrics/{project_id}", response_model=LoopMetricsResponse, summary="获取闭环指标")
async def get_loop_metrics(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    manager: FeedbackLoopManager = Depends(get_loop_manager)
):
    """
    获取闭环指标

    统计指定时间范围内的闭环效果
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    metrics = manager.calculate_loop_metrics(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )

    return LoopMetricsResponse(
        id=metrics.id,
        project_id=metrics.project_id,
        period_start=metrics.period_start.isoformat(),
        period_end=metrics.period_end.isoformat(),
        total_loops=metrics.total_loops,
        completed_loops=metrics.completed_loops,
        avg_loop_duration_hours=metrics.avg_loop_duration_hours,
        total_feedback_received=metrics.total_feedback_received,
        positive_feedback_count=metrics.positive_feedback_count,
        negative_feedback_count=metrics.negative_feedback_count,
        avg_feedback_score=metrics.avg_feedback_score,
        insights_generated=metrics.insights_generated,
        patterns_discovered=metrics.patterns_discovered,
        lessons_learned=metrics.lessons_learned,
        improvements_proposed=metrics.improvements_proposed,
        improvements_implemented=metrics.improvements_implemented,
        avg_improvement_impact=metrics.avg_improvement_impact,
        calculated_at=metrics.calculated_at.isoformat()
    )
