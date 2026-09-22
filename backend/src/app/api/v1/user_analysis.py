"""
用户分析API端点

提供用户行为分析、兴趣挖掘和个性化推荐接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.user_engagement import PatternType
from app.services.user_analysis_service import UserAnalysisService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class DimensionRecordRequest(BaseModel):
    """记录分析维度请求"""
    project_id: int = Field(..., description="项目ID")
    dimension_name: str = Field(..., description="维度名称")
    interest_score: float = Field(..., description="兴趣分数（0-1）", ge=0, le=1)
    evidence: Optional[Dict[str, Any]] = Field(None, description="证据数据")
    related_entities: Optional[List[str]] = Field(None, description="相关实体")


class DimensionResponse(BaseModel):
    """分析维度响应"""
    id: int
    user_id: int
    project_id: int
    dimension_name: str
    interest_score: float
    evidence: Dict[str, Any]
    related_entities: List[str]
    identified_at: str
    last_updated: str

    class Config:
        from_attributes = True


class ThinkingPatternRecordRequest(BaseModel):
    """记录思维模式请求"""
    project_id: int = Field(..., description="项目ID")
    pattern_type: PatternType = Field(..., description="模式类型")
    pattern_description: str = Field(..., description="模式描述")
    examples: Optional[List[str]] = Field(None, description="示例列表")
    confidence: float = Field(0.5, description="置信度（0-1）", ge=0, le=1)


class ThinkingPatternResponse(BaseModel):
    """思维模式响应"""
    id: int
    user_id: int
    project_id: int
    pattern_type: str
    pattern_description: str
    examples: List[str]
    confidence: float
    identified_at: str
    last_observed: str

    class Config:
        from_attributes = True


class PatternConfidenceUpdateRequest(BaseModel):
    """模式置信度更新请求"""
    confidence: float = Field(..., description="新置信度", ge=0, le=1)
    add_example: Optional[str] = Field(None, description="添加新示例")


class UserFocusAnalysisResponse(BaseModel):
    """用户关注焦点分析响应"""
    period_days: int
    focus_areas: List[Dict[str, Any]]
    thinking_traits: Dict[str, List[Dict[str, Any]]]
    total_dimensions: int
    total_patterns: int
    analysis_date: str


class PersonalizedSuggestion(BaseModel):
    """个性化建议"""
    type: str
    title: str
    reason: str
    actions: List[str]


class BaselineComparisonResponse(BaseModel):
    """基准对比响应"""
    user_avg_interest: float
    baseline_avg_interest: float
    difference: float
    user_focus_count: int
    user_pattern_count: int
    comparison_date: str


# ==================== 依赖项 ====================

def get_analysis_service(db: Session = Depends(get_db)) -> UserAnalysisService:
    """获取用户分析服务"""
    return UserAnalysisService(db)


# ==================== 分析维度管理 ====================

@router.post("/dimensions", response_model=DimensionResponse, summary="记录分析维度")
async def record_dimension(
    dimension: DimensionRecordRequest,
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    记录用户的分析维度

    - **project_id**: 项目ID
    - **dimension_name**: 维度名称（如"权力关系"、"社会结构"）
    - **interest_score**: 兴趣分数（0-1）
    - **evidence**: 证据数据
    - **related_entities**: 相关实体列表
    """
    result = service.record_dimension(
        user_id=current_user.id,
        project_id=dimension.project_id,
        dimension_name=dimension.dimension_name,
        interest_score=dimension.interest_score,
        evidence=dimension.evidence,
        related_entities=dimension.related_entities
    )

    return DimensionResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        dimension_name=result.dimension_name,
        interest_score=result.interest_score,
        evidence=result.evidence,
        related_entities=result.related_entities,
        identified_at=result.identified_at.isoformat(),
        last_updated=result.last_updated.isoformat()
    )


@router.get("/dimensions", response_model=List[DimensionResponse], summary="获取用户分析维度")
async def get_user_dimensions(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    min_score: float = Query(0.0, description="最小兴趣分数", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    获取用户的所有分析维度

    按兴趣分数倒序返回
    """
    dimensions = service.get_user_dimensions(
        user_id=current_user.id,
        project_id=project_id,
        min_score=min_score
    )

    return [
        DimensionResponse(
            id=d.id,
            user_id=d.user_id,
            project_id=d.project_id,
            dimension_name=d.dimension_name,
            interest_score=d.interest_score,
            evidence=d.evidence,
            related_entities=d.related_entities,
            identified_at=d.identified_at.isoformat(),
            last_updated=d.last_updated.isoformat()
        )
        for d in dimensions
    ]


@router.get("/dimensions/top/{project_id}", summary="获取核心兴趣点")
async def get_top_interests(
    project_id: int = Path(..., description="项目ID"),
    limit: int = Query(5, description="返回数量", ge=1, le=20),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    获取用户的核心兴趣点

    返回兴趣分数最高的维度
    """
    interests = service.get_top_interests(
        user_id=current_user.id,
        project_id=project_id,
        limit=limit
    )

    return {
        "project_id": project_id,
        "top_interests": interests
    }


# ==================== 思维模式管理 ====================

@router.post("/patterns", response_model=ThinkingPatternResponse, summary="记录思维模式")
async def record_thinking_pattern(
    pattern: ThinkingPatternRecordRequest,
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    记录用户的思维模式

    - **project_id**: 项目ID
    - **pattern_type**: 模式类型（analytical, intuitive, systematic等）
    - **pattern_description**: 模式描述
    - **examples**: 示例列表
    - **confidence**: 置信度（0-1）
    """
    result = service.record_thinking_pattern(
        user_id=current_user.id,
        project_id=pattern.project_id,
        pattern_type=pattern.pattern_type,
        pattern_description=pattern.pattern_description,
        examples=pattern.examples,
        confidence=pattern.confidence
    )

    return ThinkingPatternResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        pattern_type=result.pattern_type.value,
        pattern_description=result.pattern_description,
        examples=result.examples,
        confidence=result.confidence,
        identified_at=result.identified_at.isoformat(),
        last_observed=result.last_observed.isoformat()
    )


@router.get("/patterns", response_model=List[ThinkingPatternResponse], summary="获取思维模式")
async def get_thinking_patterns(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    pattern_type: Optional[PatternType] = Query(None, description="筛选模式类型"),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    获取用户的思维模式

    按置信度倒序返回
    """
    patterns = service.get_thinking_patterns(
        user_id=current_user.id,
        project_id=project_id,
        pattern_type=pattern_type
    )

    return [
        ThinkingPatternResponse(
            id=p.id,
            user_id=p.user_id,
            project_id=p.project_id,
            pattern_type=p.pattern_type.value,
            pattern_description=p.pattern_description,
            examples=p.examples,
            confidence=p.confidence,
            identified_at=p.identified_at.isoformat(),
            last_observed=p.last_observed.isoformat()
        )
        for p in patterns
    ]


@router.put("/patterns/{pattern_id}/confidence", response_model=ThinkingPatternResponse, summary="更新模式置信度")
async def update_pattern_confidence(
    pattern_id: int = Path(..., description="模式ID"),
    update: PatternConfidenceUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    更新思维模式的置信度

    - **confidence**: 新置信度（0-1）
    - **add_example**: 可选，添加新示例
    """
    result = service.update_pattern_confidence(
        pattern_id=pattern_id,
        confidence=update.confidence,
        add_example=update.add_example
    )

    return ThinkingPatternResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        pattern_type=result.pattern_type.value,
        pattern_description=result.pattern_description,
        examples=result.examples,
        confidence=result.confidence,
        identified_at=result.identified_at.isoformat(),
        last_observed=result.last_observed.isoformat()
    )


# ==================== 用户行为分析 ====================

@router.get("/focus/{project_id}", response_model=UserFocusAnalysisResponse, summary="分析用户关注焦点")
async def analyze_user_focus(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="分析天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    分析用户的关注焦点

    包含：
    - 主要关注领域
    - 思维特征
    - 维度和模式统计
    """
    analysis = service.analyze_user_focus(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return UserFocusAnalysisResponse(**analysis)


@router.get("/suggestions/{project_id}", response_model=List[PersonalizedSuggestion], summary="获取个性化建议")
async def get_personalized_suggestions(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    获取个性化建议

    基于用户的兴趣维度和思维模式生成建议
    """
    suggestions = service.get_personalized_suggestions(
        user_id=current_user.id,
        project_id=project_id
    )

    return [PersonalizedSuggestion(**s) for s in suggestions]


@router.get("/baseline/{project_id}", response_model=BaselineComparisonResponse, summary="与基准对比")
async def compare_with_baseline(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    service: UserAnalysisService = Depends(get_analysis_service)
):
    """
    与基准对比用户特征

    对比用户与所有用户平均水平的差异
    """
    comparison = service.compare_with_baseline(
        user_id=current_user.id,
        project_id=project_id
    )

    if comparison.get("status") == "insufficient_data":
        raise HTTPException(status_code=404, detail=comparison.get("message"))

    return BaselineComparisonResponse(**comparison)
