"""
执行追踪API端点

提供执行记录、结果分析和模式识别接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.execution_record import ExecutionStatus, ExecutionType
from app.services.execution_analyzer import ExecutionAnalyzer


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ExecutionRecordCreate(BaseModel):
    """创建执行记录请求"""
    project_id: int = Field(..., description="项目ID")
    execution_type: ExecutionType = Field(..., description="执行类型")
    execution_name: str = Field(..., description="执行名称")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    skill_id: Optional[int] = Field(None, description="技能ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    execution_description: Optional[str] = Field(None, description="执行描述")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外信息")


class ExecutionProgressUpdate(BaseModel):
    """执行进度更新请求"""
    execution_steps: List[Dict[str, Any]] = Field(..., description="执行步骤")


class ExecutionComplete(BaseModel):
    """执行完成请求"""
    status: ExecutionStatus = Field(..., description="执行状态")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_stack: Optional[str] = Field(None, description="错误堆栈")
    metrics: Optional[Dict[str, Any]] = Field(None, description="执行指标")


class ExecutionRecordResponse(BaseModel):
    """执行记录响应"""
    id: str
    user_id: int
    project_id: int
    execution_type: str
    execution_name: str
    execution_description: Optional[str]
    workflow_id: Optional[str]
    skill_id: Optional[int]
    task_id: Optional[str]
    input_data: Dict[str, Any]
    execution_steps: Optional[List[Dict[str, Any]]]
    status: str
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    duration_seconds: Optional[float]
    quality_score: Optional[float]
    user_rating: Optional[int]
    user_feedback: Optional[str]
    extracted_features: Optional[Dict[str, Any]]
    started_at: str
    completed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class SuccessPatternResponse(BaseModel):
    """成功模式响应"""
    id: str
    pattern_name: str
    pattern_description: str
    pattern_type: str
    project_id: int
    pattern_signature: Dict[str, Any]
    applicable_contexts: Dict[str, Any]
    occurrence_count: int
    success_count: int
    confidence_score: float
    avg_quality_score: Optional[float]
    source_execution_ids: List[str]
    first_observed_at: str
    last_observed_at: str

    class Config:
        from_attributes = True


class UserFeedbackRequest(BaseModel):
    """用户反馈请求"""
    user_rating: int = Field(..., description="用户评分（1-5）", ge=1, le=5)
    user_feedback: Optional[str] = Field(None, description="用户反馈")


# ==================== 依赖项 ====================

def get_analyzer(db: Session = Depends(get_db)) -> ExecutionAnalyzer:
    """获取执行分析服务"""
    return ExecutionAnalyzer(db)


# ==================== 执行记录管理 ====================

@router.post("/executions", response_model=ExecutionRecordResponse, summary="创建执行记录")
async def create_execution_record(
    record: ExecutionRecordCreate,
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    创建执行记录（开始追踪）

    - **project_id**: 项目ID
    - **execution_type**: 执行类型（workflow, skill, task等）
    - **execution_name**: 执行名称
    - **input_data**: 输入数据
    - **workflow_id**: 可选，工作流ID
    - **skill_id**: 可选，技能ID
    - **task_id**: 可选，任务ID
    """
    result = analyzer.record_execution(
        user_id=current_user.id,
        project_id=record.project_id,
        execution_type=record.execution_type,
        execution_name=record.execution_name,
        input_data=record.input_data,
        workflow_id=record.workflow_id,
        skill_id=record.skill_id,
        task_id=record.task_id,
        execution_description=record.execution_description,
        metadata=record.extra_metadata
    )

    return ExecutionRecordResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        execution_type=result.execution_type.value,
        execution_name=result.execution_name,
        execution_description=result.execution_description,
        workflow_id=result.workflow_id,
        skill_id=result.skill_id,
        task_id=result.task_id,
        input_data=result.input_data,
        execution_steps=result.execution_steps,
        status=result.status.value,
        output_data=result.output_data,
        error_message=result.error_message,
        duration_seconds=result.duration_seconds,
        quality_score=result.quality_score,
        user_rating=result.user_rating,
        user_feedback=result.user_feedback,
        extracted_features=result.extracted_features,
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.put("/executions/{execution_id}/progress", response_model=ExecutionRecordResponse, summary="更新执行进度")
async def update_execution_progress(
    execution_id: str = Path(..., description="执行记录ID"),
    update: ExecutionProgressUpdate = ...,
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    更新执行进度

    - **execution_steps**: 执行步骤列表
    """
    result = analyzer.update_execution_progress(
        execution_id=execution_id,
        execution_steps=update.execution_steps
    )

    return ExecutionRecordResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        execution_type=result.execution_type.value,
        execution_name=result.execution_name,
        execution_description=result.execution_description,
        workflow_id=result.workflow_id,
        skill_id=result.skill_id,
        task_id=result.task_id,
        input_data=result.input_data,
        execution_steps=result.execution_steps,
        status=result.status.value,
        output_data=result.output_data,
        error_message=result.error_message,
        duration_seconds=result.duration_seconds,
        quality_score=result.quality_score,
        user_rating=result.user_rating,
        user_feedback=result.user_feedback,
        extracted_features=result.extracted_features,
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.put("/executions/{execution_id}/complete", response_model=ExecutionRecordResponse, summary="完成执行")
async def complete_execution(
    execution_id: str = Path(..., description="执行记录ID"),
    complete: ExecutionComplete = ...,
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    完成执行并记录结果

    - **status**: 执行状态（success, failed等）
    - **output_data**: 输出数据
    - **error_message**: 错误信息（如果失败）
    - **metrics**: 执行指标（duration, cpu_usage等）
    """
    result = analyzer.complete_execution(
        execution_id=execution_id,
        status=complete.status,
        output_data=complete.output_data,
        error_message=complete.error_message,
        error_stack=complete.error_stack,
        metrics=complete.metrics
    )

    return ExecutionRecordResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        execution_type=result.execution_type.value,
        execution_name=result.execution_name,
        execution_description=result.execution_description,
        workflow_id=result.workflow_id,
        skill_id=result.skill_id,
        task_id=result.task_id,
        input_data=result.input_data,
        execution_steps=result.execution_steps,
        status=result.status.value,
        output_data=result.output_data,
        error_message=result.error_message,
        duration_seconds=result.duration_seconds,
        quality_score=result.quality_score,
        user_rating=result.user_rating,
        user_feedback=result.user_feedback,
        extracted_features=result.extracted_features,
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.put("/executions/{execution_id}/feedback", response_model=ExecutionRecordResponse, summary="提交用户反馈")
async def submit_user_feedback(
    execution_id: str = Path(..., description="执行记录ID"),
    feedback: UserFeedbackRequest = ...,
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    提交用户反馈

    - **user_rating**: 用户评分（1-5）
    - **user_feedback**: 用户反馈文本
    """
    # 获取执行记录
    from app.models.execution_record import ExecutionRecord
    record = analyzer.db.query(ExecutionRecord).filter(
        ExecutionRecord.id == execution_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 更新反馈
    record.user_rating = feedback.user_rating
    record.user_feedback = feedback.user_feedback

    analyzer.db.commit()
    analyzer.db.refresh(record)

    return ExecutionRecordResponse(
        id=record.id,
        user_id=record.user_id,
        project_id=record.project_id,
        execution_type=record.execution_type.value,
        execution_name=record.execution_name,
        execution_description=record.execution_description,
        workflow_id=record.workflow_id,
        skill_id=record.skill_id,
        task_id=record.task_id,
        input_data=record.input_data,
        execution_steps=record.execution_steps,
        status=record.status.value,
        output_data=record.output_data,
        error_message=record.error_message,
        duration_seconds=record.duration_seconds,
        quality_score=record.quality_score,
        user_rating=record.user_rating,
        user_feedback=record.user_feedback,
        extracted_features=record.extracted_features,
        started_at=record.started_at.isoformat(),
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
        created_at=record.created_at.isoformat()
    )


# ==================== 查询接口 ====================

@router.get("/executions", response_model=List[ExecutionRecordResponse], summary="获取执行记录列表")
async def get_execution_records(
    project_id: int = Query(..., description="项目ID"),
    execution_type: Optional[ExecutionType] = Query(None, description="执行类型"),
    status: Optional[ExecutionStatus] = Query(None, description="执行状态"),
    limit: int = Query(100, description="返回数量", ge=1, le=500),
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    获取执行记录列表

    按开始时间倒序返回
    """
    records = analyzer.get_execution_records(
        project_id=project_id,
        execution_type=execution_type,
        status=status,
        limit=limit
    )

    return [
        ExecutionRecordResponse(
            id=r.id,
            user_id=r.user_id,
            project_id=r.project_id,
            execution_type=r.execution_type.value,
            execution_name=r.execution_name,
            execution_description=r.execution_description,
            workflow_id=r.workflow_id,
            skill_id=r.skill_id,
            task_id=r.task_id,
            input_data=r.input_data,
            execution_steps=r.execution_steps,
            status=r.status.value,
            output_data=r.output_data,
            error_message=r.error_message,
            duration_seconds=r.duration_seconds,
            quality_score=r.quality_score,
            user_rating=r.user_rating,
            user_feedback=r.user_feedback,
            extracted_features=r.extracted_features,
            started_at=r.started_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            created_at=r.created_at.isoformat()
        )
        for r in records
    ]


@router.get("/patterns", response_model=List[SuccessPatternResponse], summary="获取成功模式")
async def get_success_patterns(
    project_id: int = Query(..., description="项目ID"),
    pattern_type: Optional[str] = Query(None, description="模式类型"),
    min_confidence: float = Query(0.7, description="最小置信度", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    analyzer: ExecutionAnalyzer = Depends(get_analyzer)
):
    """
    获取成功模式列表

    返回从执行历史中识别出的成功模式
    """
    patterns = analyzer.get_success_patterns(
        project_id=project_id,
        pattern_type=pattern_type,
        min_confidence=min_confidence
    )

    return [
        SuccessPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            pattern_description=p.pattern_description,
            pattern_type=p.pattern_type,
            project_id=p.project_id,
            pattern_signature=p.pattern_signature,
            applicable_contexts=p.applicable_contexts,
            occurrence_count=p.occurrence_count,
            success_count=p.success_count,
            confidence_score=p.confidence_score,
            avg_quality_score=p.avg_quality_score,
            source_execution_ids=p.source_execution_ids,
            first_observed_at=p.first_observed_at.isoformat(),
            last_observed_at=p.last_observed_at.isoformat()
        )
        for p in patterns
    ]
