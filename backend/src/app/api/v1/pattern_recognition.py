"""
模式识别API端点

提供模式检测、匹配和管理接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.pattern_library import PatternStatus, PatternType
from app.services.pattern_detector import PatternDetector


router = APIRouter()


# ==================== Pydantic 模型 ====================

class PatternDetectionRequest(BaseModel):
    """模式检测请求"""
    project_id: int = Field(..., description="项目ID")
    min_occurrences: int = Field(3, description="最小出现次数", ge=2)
    min_confidence: float = Field(0.7, description="最小置信度", ge=0, le=1)
    lookback_days: int = Field(30, description="回溯天数", ge=1, le=365)


class PatternLibraryResponse(BaseModel):
    """模式库响应"""
    id: str
    pattern_name: str
    pattern_type: str
    pattern_description: str
    project_id: int
    pattern_definition: Dict[str, Any]
    pattern_features: Dict[str, Any]
    applicable_scenarios: Dict[str, Any]
    detection_count: int
    usage_count: int
    success_count: int
    failure_count: int
    confidence_score: float
    avg_success_rate: Optional[float]
    avg_quality_score: Optional[float]
    avg_duration_seconds: Optional[float]
    status: str
    first_detected_at: str
    last_used_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class PatternMatchRequest(BaseModel):
    """模式匹配请求"""
    execution_id: str = Field(..., description="执行记录ID")
    min_match_score: float = Field(0.7, description="最小匹配分数", ge=0, le=1)


class PatternMatchResponse(BaseModel):
    """模式匹配响应"""
    pattern: PatternLibraryResponse
    match_score: float
    match_reason: Dict[str, Any]


# ==================== 依赖项 ====================

def get_pattern_detector(db: Session = Depends(get_db)) -> PatternDetector:
    """获取模式检测服务"""
    return PatternDetector(db)


# ==================== 模式检测 ====================

@router.post("/detect", response_model=List[PatternLibraryResponse], summary="检测模式")
async def detect_patterns(
    request: PatternDetectionRequest,
    current_user: User = Depends(get_current_user),
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    从执行历史中检测可复用模式

    - **project_id**: 项目ID
    - **min_occurrences**: 最小出现次数（默认3次）
    - **min_confidence**: 最小置信度（默认0.7）
    - **lookback_days**: 回溯天数（默认30天）

    返回检测到的模式列表
    """
    patterns = detector.detect_patterns(
        project_id=request.project_id,
        min_occurrences=request.min_occurrences,
        min_confidence=request.min_confidence,
        lookback_days=request.lookback_days
    )

    return [
        PatternLibraryResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            pattern_type=p.pattern_type.value,
            pattern_description=p.pattern_description,
            project_id=p.project_id,
            pattern_definition=p.pattern_definition,
            pattern_features=p.pattern_features,
            applicable_scenarios=p.applicable_scenarios,
            detection_count=p.detection_count,
            usage_count=p.usage_count,
            success_count=p.success_count,
            failure_count=p.failure_count,
            confidence_score=p.confidence_score,
            avg_success_rate=p.avg_success_rate,
            avg_quality_score=p.avg_quality_score,
            avg_duration_seconds=p.avg_duration_seconds,
            status=p.status.value,
            first_detected_at=p.first_detected_at.isoformat(),
            last_used_at=p.last_used_at.isoformat() if p.last_used_at else None,
            created_at=p.created_at.isoformat()
        )
        for p in patterns
    ]


@router.post("/match", response_model=List[PatternMatchResponse], summary="匹配模式")
async def match_pattern(
    request: PatternMatchRequest,
    current_user: User = Depends(get_current_user),
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    为执行记录匹配合适的模式

    - **execution_id**: 执行记录ID
    - **min_match_score**: 最小匹配分数（默认0.7）

    返回匹配的模式列表，按匹配分数排序
    """
    matches = detector.match_pattern(
        execution_id=request.execution_id,
        min_match_score=request.min_match_score
    )

    return [
        PatternMatchResponse(
            pattern=PatternLibraryResponse(
                id=pattern.id,
                pattern_name=pattern.pattern_name,
                pattern_type=pattern.pattern_type.value,
                pattern_description=pattern.pattern_description,
                project_id=pattern.project_id,
                pattern_definition=pattern.pattern_definition,
                pattern_features=pattern.pattern_features,
                applicable_scenarios=pattern.applicable_scenarios,
                detection_count=pattern.detection_count,
                usage_count=pattern.usage_count,
                success_count=pattern.success_count,
                failure_count=pattern.failure_count,
                confidence_score=pattern.confidence_score,
                avg_success_rate=pattern.avg_success_rate,
                avg_quality_score=pattern.avg_quality_score,
                avg_duration_seconds=pattern.avg_duration_seconds,
                status=pattern.status.value,
                first_detected_at=pattern.first_detected_at.isoformat(),
                last_used_at=pattern.last_used_at.isoformat() if pattern.last_used_at else None,
                created_at=pattern.created_at.isoformat()
            ),
            match_score=score,
            match_reason={
                'matched_features': ['execution_type', 'complexity'],
                'overall_similarity': score
            }
        )
        for pattern, score in matches
    ]


# ==================== 模式管理 ====================

@router.get("/patterns", response_model=List[PatternLibraryResponse], summary="获取模式列表")
async def get_patterns(
    project_id: int = Query(..., description="项目ID"),
    pattern_type: Optional[PatternType] = Query(None, description="模式类型"),
    status: Optional[PatternStatus] = Query(None, description="模式状态"),
    min_confidence: float = Query(0.0, description="最小置信度", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    获取模式列表

    按置信度倒序返回
    """
    patterns = detector.get_patterns(
        project_id=project_id,
        pattern_type=pattern_type,
        status=status,
        min_confidence=min_confidence
    )

    return [
        PatternLibraryResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            pattern_type=p.pattern_type.value,
            pattern_description=p.pattern_description,
            project_id=p.project_id,
            pattern_definition=p.pattern_definition,
            pattern_features=p.pattern_features,
            applicable_scenarios=p.applicable_scenarios,
            detection_count=p.detection_count,
            usage_count=p.usage_count,
            success_count=p.success_count,
            failure_count=p.failure_count,
            confidence_score=p.confidence_score,
            avg_success_rate=p.avg_success_rate,
            avg_quality_score=p.avg_quality_score,
            avg_duration_seconds=p.avg_duration_seconds,
            status=p.status.value,
            first_detected_at=p.first_detected_at.isoformat(),
            last_used_at=p.last_used_at.isoformat() if p.last_used_at else None,
            created_at=p.created_at.isoformat()
        )
        for p in patterns
    ]


@router.put("/patterns/{pattern_id}/validate", response_model=PatternLibraryResponse, summary="验证模式")
async def validate_pattern(
    pattern_id: str = Path(..., description="模式ID"),
    current_user: User = Depends(get_current_user),
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    验证模式

    将模式状态从 detected 更新为 validated
    """
    pattern = detector.validate_pattern(pattern_id)

    return PatternLibraryResponse(
        id=pattern.id,
        pattern_name=pattern.pattern_name,
        pattern_type=pattern.pattern_type.value,
        pattern_description=pattern.pattern_description,
        project_id=pattern.project_id,
        pattern_definition=pattern.pattern_definition,
        pattern_features=pattern.pattern_features,
        applicable_scenarios=pattern.applicable_scenarios,
        detection_count=pattern.detection_count,
        usage_count=pattern.usage_count,
        success_count=pattern.success_count,
        failure_count=pattern.failure_count,
        confidence_score=pattern.confidence_score,
        avg_success_rate=pattern.avg_success_rate,
        avg_quality_score=pattern.avg_quality_score,
        avg_duration_seconds=pattern.avg_duration_seconds,
        status=pattern.status.value,
        first_detected_at=pattern.first_detected_at.isoformat(),
        last_used_at=pattern.last_used_at.isoformat() if pattern.last_used_at else None,
        created_at=pattern.created_at.isoformat()
    )


@router.put("/patterns/{pattern_id}/activate", response_model=PatternLibraryResponse, summary="激活模式")
async def activate_pattern(
    pattern_id: str = Path(..., description="模式ID"),
    current_user: User = Depends(get_current_user),
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    激活模式

    将模式状态更新为 active，系统将开始自动应用此模式
    """
    pattern = detector.activate_pattern(pattern_id)

    return PatternLibraryResponse(
        id=pattern.id,
        pattern_name=pattern.pattern_name,
        pattern_type=pattern.pattern_type.value,
        pattern_description=pattern.pattern_description,
        project_id=pattern.project_id,
        pattern_definition=pattern.pattern_definition,
        pattern_features=pattern.pattern_features,
        applicable_scenarios=pattern.applicable_scenarios,
        detection_count=pattern.detection_count,
        usage_count=pattern.usage_count,
        success_count=pattern.success_count,
        failure_count=pattern.failure_count,
        confidence_score=pattern.confidence_score,
        avg_success_rate=pattern.avg_success_rate,
        avg_quality_score=pattern.avg_quality_score,
        avg_duration_seconds=pattern.avg_duration_seconds,
        status=pattern.status.value,
        first_detected_at=pattern.first_detected_at.isoformat(),
        last_used_at=pattern.last_used_at.isoformat() if pattern.last_used_at else None,
        created_at=pattern.created_at.isoformat()
    )
