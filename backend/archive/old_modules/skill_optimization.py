"""
技能优化API端点

提供性能监控、优化建议和优化管理接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.skill_optimization import OptimizationType, OptimizationStatus
from app.services.skill_optimizer import SkillOptimizer


router = APIRouter()


# ==================== Pydantic 模型 ====================

class PerformanceRecordRequest(BaseModel):
    """性能记录请求"""
    skill_id: str = Field(..., description="技能ID")
    execution_id: str = Field(..., description="执行记录ID")
    project_id: int = Field(..., description="项目ID")
    execution_time: float = Field(..., description="执行时间（秒）")
    success: bool = Field(..., description="是否成功")
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用（MB）")
    api_calls: int = Field(0, description="API调用次数")
    tokens_used: int = Field(0, description="Token使用量")
    quality_score: Optional[float] = Field(None, description="质量分数")
    error_type: Optional[str] = Field(None, description="错误类型")
    input_size: Optional[int] = Field(None, description="输入大小")
    output_size: Optional[int] = Field(None, description="输出大小")
    complexity_level: Optional[str] = Field(None, description="复杂度级别")


class OptimizationCreateRequest(BaseModel):
    """创建优化请求"""
    skill_id: str = Field(..., description="技能ID")
    project_id: int = Field(..., description="项目ID")
    optimization_type: OptimizationType = Field(..., description="优化类型")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    identified_issues: Dict[str, Any] = Field(..., description="识别的问题")
    proposed_changes: Dict[str, Any] = Field(..., description="提议的改变")


class OptimizationValidateRequest(BaseModel):
    """优化验证请求"""
    after_metrics: Dict[str, Any] = Field(..., description="优化后的指标")
    ab_test_data: Optional[Dict[str, Any]] = Field(None, description="A/B测试数据")


class OptimizationRevertRequest(BaseModel):
    """优化回滚请求"""
    reason: str = Field(..., description="回滚原因")


class PerformanceMetricResponse(BaseModel):
    """性能指标响应"""
    id: str
    skill_id: str
    execution_id: Optional[str]
    execution_time: float
    cpu_usage_percent: Optional[float]
    memory_usage_mb: Optional[float]
    api_calls_count: int
    tokens_used: int
    success: bool
    quality_score: Optional[float]
    error_type: Optional[str]
    measured_at: str

    class Config:
        from_attributes = True


class SkillOptimizationResponse(BaseModel):
    """技能优化响应"""
    id: str
    skill_id: str
    project_id: int
    optimization_type: str
    optimization_title: str
    optimization_description: str
    identified_issues: Dict[str, Any]
    proposed_changes: Dict[str, Any]
    before_metrics: Optional[Dict[str, Any]]
    after_metrics: Optional[Dict[str, Any]]
    improvement_percentage: Optional[float]
    is_effective: bool
    validation_score: Optional[float]
    ab_test_data: Optional[Dict[str, Any]]
    status: str
    proposed_at: str
    tested_at: Optional[str]
    validated_at: Optional[str]
    applied_at: Optional[str]
    reverted_at: Optional[str]
    can_revert: bool
    revert_reason: Optional[str]

    class Config:
        from_attributes = True


class OptimizationRecommendationResponse(BaseModel):
    """优化建议响应"""
    id: str
    skill_id: str
    recommendation_type: str
    recommendation_title: str
    recommendation_description: str
    analysis_data: Dict[str, Any]
    suggested_solution: Dict[str, Any]
    priority_score: float
    potential_improvement: Optional[float]
    is_accepted: Optional[bool]
    is_applied: bool
    generated_at: str

    class Config:
        from_attributes = True


class PerformanceSummaryResponse(BaseModel):
    """性能摘要响应"""
    period_days: int
    total_executions: int
    success_rate: float
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    std_execution_time: float
    p50_execution_time: float
    p95_execution_time: float
    p99_execution_time: float


# ==================== 依赖项 ====================

def get_optimizer(db: Session = Depends(get_db)) -> SkillOptimizer:
    """获取技能优化服务"""
    return SkillOptimizer(db)


# ==================== 性能监控 ====================

@router.post("/performance", response_model=PerformanceMetricResponse, summary="记录性能指标")
async def record_performance(
    request: PerformanceRecordRequest,
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    记录技能执行的性能指标

    系统将自动分析性能数据，并在检测到问题时生成优化建议
    """
    metric = optimizer.record_performance(
        skill_id=request.skill_id,
        execution_id=request.execution_id,
        project_id=request.project_id,
        execution_time=request.execution_time,
        success=request.success,
        cpu_usage=request.cpu_usage,
        memory_usage=request.memory_usage,
        api_calls=request.api_calls,
        tokens_used=request.tokens_used,
        quality_score=request.quality_score,
        error_type=request.error_type,
        input_size=request.input_size,
        output_size=request.output_size,
        complexity_level=request.complexity_level
    )

    return PerformanceMetricResponse(
        id=metric.id,
        skill_id=metric.skill_id,
        execution_id=metric.execution_id,
        execution_time=metric.execution_time,
        cpu_usage_percent=metric.cpu_usage_percent,
        memory_usage_mb=metric.memory_usage_mb,
        api_calls_count=metric.api_calls_count,
        tokens_used=metric.tokens_used,
        success=metric.success,
        quality_score=metric.quality_score,
        error_type=metric.error_type,
        measured_at=metric.measured_at.isoformat()
    )


@router.get("/performance/{skill_id}/summary", response_model=PerformanceSummaryResponse, summary="获取性能摘要")
async def get_performance_summary(
    skill_id: str = Path(..., description="技能ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    获取技能的性能摘要

    包含平均执行时间、成功率、百分位数等统计信息
    """
    summary = optimizer.get_performance_summary(
        skill_id=skill_id,
        days=days
    )

    if not summary:
        raise HTTPException(status_code=404, detail="暂无性能数据")

    return PerformanceSummaryResponse(**summary)


# ==================== 优化建议 ====================

@router.get("/recommendations", response_model=List[OptimizationRecommendationResponse], summary="获取优化建议")
async def get_recommendations(
    skill_id: Optional[str] = Query(None, description="技能ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    is_applied: Optional[bool] = Query(None, description="是否已应用"),
    min_priority: float = Query(0.0, description="最小优先级", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    获取优化建议列表

    系统自动生成的优化建议，按优先级排序
    """
    recommendations = optimizer.get_recommendations(
        skill_id=skill_id,
        project_id=project_id,
        is_applied=is_applied,
        min_priority=min_priority
    )

    return [
        OptimizationRecommendationResponse(
            id=r.id,
            skill_id=r.skill_id,
            recommendation_type=r.recommendation_type.value,
            recommendation_title=r.recommendation_title,
            recommendation_description=r.recommendation_description,
            analysis_data=r.analysis_data,
            suggested_solution=r.suggested_solution,
            priority_score=r.priority_score,
            potential_improvement=r.potential_improvement,
            is_accepted=r.is_accepted,
            is_applied=r.is_applied,
            generated_at=r.generated_at.isoformat()
        )
        for r in recommendations
    ]


# ==================== 优化管理 ====================

@router.post("/optimizations", response_model=SkillOptimizationResponse, summary="创建优化")
async def create_optimization(
    request: OptimizationCreateRequest,
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    创建优化记录

    手动创建或从建议转换为优化记录
    """
    optimization = optimizer.create_optimization(
        skill_id=request.skill_id,
        project_id=request.project_id,
        optimization_type=request.optimization_type,
        title=request.title,
        description=request.description,
        identified_issues=request.identified_issues,
        proposed_changes=request.proposed_changes,
        user_id=current_user.id
    )

    return SkillOptimizationResponse(
        id=optimization.id,
        skill_id=optimization.skill_id,
        project_id=optimization.project_id,
        optimization_type=optimization.optimization_type.value,
        optimization_title=optimization.optimization_title,
        optimization_description=optimization.optimization_description,
        identified_issues=optimization.identified_issues,
        proposed_changes=optimization.proposed_changes,
        before_metrics=optimization.before_metrics,
        after_metrics=optimization.after_metrics,
        improvement_percentage=optimization.improvement_percentage,
        is_effective=optimization.is_effective,
        validation_score=optimization.validation_score,
        ab_test_data=optimization.ab_test_data,
        status=optimization.status.value,
        proposed_at=optimization.proposed_at.isoformat(),
        tested_at=optimization.tested_at.isoformat() if optimization.tested_at else None,
        validated_at=optimization.validated_at.isoformat() if optimization.validated_at else None,
        applied_at=optimization.applied_at.isoformat() if optimization.applied_at else None,
        reverted_at=optimization.reverted_at.isoformat() if optimization.reverted_at else None,
        can_revert=optimization.can_revert,
        revert_reason=optimization.revert_reason
    )


@router.get("/optimizations", response_model=List[SkillOptimizationResponse], summary="获取优化列表")
async def get_optimizations(
    skill_id: Optional[str] = Query(None, description="技能ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[OptimizationStatus] = Query(None, description="优化状态"),
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    获取优化记录列表

    按提议时间倒序返回
    """
    optimizations = optimizer.get_optimizations(
        skill_id=skill_id,
        project_id=project_id,
        status=status
    )

    return [
        SkillOptimizationResponse(
            id=opt.id,
            skill_id=opt.skill_id,
            project_id=opt.project_id,
            optimization_type=opt.optimization_type.value,
            optimization_title=opt.optimization_title,
            optimization_description=opt.optimization_description,
            identified_issues=opt.identified_issues,
            proposed_changes=opt.proposed_changes,
            before_metrics=opt.before_metrics,
            after_metrics=opt.after_metrics,
            improvement_percentage=opt.improvement_percentage,
            is_effective=opt.is_effective,
            validation_score=opt.validation_score,
            ab_test_data=opt.ab_test_data,
            status=opt.status.value,
            proposed_at=opt.proposed_at.isoformat(),
            tested_at=opt.tested_at.isoformat() if opt.tested_at else None,
            validated_at=opt.validated_at.isoformat() if opt.validated_at else None,
            applied_at=opt.applied_at.isoformat() if opt.applied_at else None,
            reverted_at=opt.reverted_at.isoformat() if opt.reverted_at else None,
            can_revert=opt.can_revert,
            revert_reason=opt.revert_reason
        )
        for opt in optimizations
    ]


@router.post("/optimizations/{optimization_id}/validate", response_model=SkillOptimizationResponse, summary="验证优化")
async def validate_optimization(
    optimization_id: str = Path(..., description="优化ID"),
    request: OptimizationValidateRequest = ...,
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    验证优化效果

    提交优化后的性能指标和A/B测试数据
    """
    optimization = optimizer.validate_optimization(
        optimization_id=optimization_id,
        after_metrics=request.after_metrics,
        ab_test_data=request.ab_test_data
    )

    return SkillOptimizationResponse(
        id=optimization.id,
        skill_id=optimization.skill_id,
        project_id=optimization.project_id,
        optimization_type=optimization.optimization_type.value,
        optimization_title=optimization.optimization_title,
        optimization_description=optimization.optimization_description,
        identified_issues=optimization.identified_issues,
        proposed_changes=optimization.proposed_changes,
        before_metrics=optimization.before_metrics,
        after_metrics=optimization.after_metrics,
        improvement_percentage=optimization.improvement_percentage,
        is_effective=optimization.is_effective,
        validation_score=optimization.validation_score,
        ab_test_data=optimization.ab_test_data,
        status=optimization.status.value,
        proposed_at=optimization.proposed_at.isoformat(),
        tested_at=optimization.tested_at.isoformat() if optimization.tested_at else None,
        validated_at=optimization.validated_at.isoformat() if optimization.validated_at else None,
        applied_at=optimization.applied_at.isoformat() if optimization.applied_at else None,
        reverted_at=optimization.reverted_at.isoformat() if optimization.reverted_at else None,
        can_revert=optimization.can_revert,
        revert_reason=optimization.revert_reason
    )


@router.post("/optimizations/{optimization_id}/apply", response_model=SkillOptimizationResponse, summary="应用优化")
async def apply_optimization(
    optimization_id: str = Path(..., description="优化ID"),
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    应用优化

    将验证通过的优化应用到生产环境
    """
    optimization = optimizer.apply_optimization(optimization_id=optimization_id)

    return SkillOptimizationResponse(
        id=optimization.id,
        skill_id=optimization.skill_id,
        project_id=optimization.project_id,
        optimization_type=optimization.optimization_type.value,
        optimization_title=optimization.optimization_title,
        optimization_description=optimization.optimization_description,
        identified_issues=optimization.identified_issues,
        proposed_changes=optimization.proposed_changes,
        before_metrics=optimization.before_metrics,
        after_metrics=optimization.after_metrics,
        improvement_percentage=optimization.improvement_percentage,
        is_effective=optimization.is_effective,
        validation_score=optimization.validation_score,
        ab_test_data=optimization.ab_test_data,
        status=optimization.status.value,
        proposed_at=optimization.proposed_at.isoformat(),
        tested_at=optimization.tested_at.isoformat() if optimization.tested_at else None,
        validated_at=optimization.validated_at.isoformat() if optimization.validated_at else None,
        applied_at=optimization.applied_at.isoformat() if optimization.applied_at else None,
        reverted_at=optimization.reverted_at.isoformat() if optimization.reverted_at else None,
        can_revert=optimization.can_revert,
        revert_reason=optimization.revert_reason
    )


@router.post("/optimizations/{optimization_id}/revert", response_model=SkillOptimizationResponse, summary="回滚优化")
async def revert_optimization(
    optimization_id: str = Path(..., description="优化ID"),
    request: OptimizationRevertRequest = ...,
    current_user: User = Depends(get_current_user),
    optimizer: SkillOptimizer = Depends(get_optimizer)
):
    """
    回滚优化

    如果优化效果不佳，可以回滚到之前的版本
    """
    optimization = optimizer.revert_optimization(
        optimization_id=optimization_id,
        reason=request.reason
    )

    return SkillOptimizationResponse(
        id=optimization.id,
        skill_id=optimization.skill_id,
        project_id=optimization.project_id,
        optimization_type=optimization.optimization_type.value,
        optimization_title=optimization.optimization_title,
        optimization_description=optimization.optimization_description,
        identified_issues=optimization.identified_issues,
        proposed_changes=optimization.proposed_changes,
        before_metrics=optimization.before_metrics,
        after_metrics=optimization.after_metrics,
        improvement_percentage=optimization.improvement_percentage,
        is_effective=optimization.is_effective,
        validation_score=optimization.validation_score,
        ab_test_data=optimization.ab_test_data,
        status=optimization.status.value,
        proposed_at=optimization.proposed_at.isoformat(),
        tested_at=optimization.tested_at.isoformat() if optimization.tested_at else None,
        validated_at=optimization.validated_at.isoformat() if optimization.validated_at else None,
        applied_at=optimization.applied_at.isoformat() if optimization.applied_at else None,
        reverted_at=optimization.reverted_at.isoformat() if optimization.reverted_at else None,
        can_revert=optimization.can_revert,
        revert_reason=optimization.revert_reason
    )
