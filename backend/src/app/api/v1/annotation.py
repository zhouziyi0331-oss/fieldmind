"""
用户标注API端点

提供用户对数据的标注、分类和质量反馈接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.user_engagement import AnnotationType
from app.services.annotation_service import AnnotationService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class AnnotationCreate(BaseModel):
    """创建标注请求"""
    project_id: int = Field(..., description="项目ID")
    target_type: str = Field(..., description="标注目标类型")
    target_id: int = Field(..., description="标注目标ID")
    annotation_type: AnnotationType = Field(..., description="标注类型")
    annotation_content: Dict[str, Any] = Field(..., description="标注内容")
    confidence: float = Field(1.0, description="置信度（0-1）", ge=0, le=1)


class AnnotationUpdate(BaseModel):
    """更新标注请求"""
    annotation_content: Optional[Dict[str, Any]] = Field(None, description="新的标注内容")
    confidence: Optional[float] = Field(None, description="新的置信度", ge=0, le=1)


class AnnotationResponse(BaseModel):
    """标注响应"""
    id: int
    user_id: int
    project_id: int
    target_type: str
    target_id: int
    annotation_type: str
    annotation_content: Dict[str, Any]
    confidence: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AnnotationStatisticsResponse(BaseModel):
    """标注统计响应"""
    period_days: int
    total_annotations: int
    by_annotation_type: Dict[str, int]
    by_target_type: Dict[str, int]
    avg_confidence: float
    by_user: Dict[int, int]
    start_date: str
    end_date: str


class UserAnnotationSummaryResponse(BaseModel):
    """用户标注摘要响应"""
    period_days: int
    total_annotations: int
    by_type: Dict[str, int]
    avg_confidence: float
    start_date: str
    end_date: str


class AnnotationTrendPoint(BaseModel):
    """标注趋势点"""
    date: str
    count: int
    by_type: Dict[str, int]


# ==================== 依赖项 ====================

def get_annotation_service(db: Session = Depends(get_db)) -> AnnotationService:
    """获取标注服务"""
    return AnnotationService(db)


# ==================== 标注管理 ====================

@router.post("/annotations", response_model=AnnotationResponse, summary="创建标注")
async def create_annotation(
    annotation: AnnotationCreate,
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    创建标注

    - **project_id**: 项目ID
    - **target_type**: 标注目标类型（document, entity, relationship等）
    - **target_id**: 标注目标ID
    - **annotation_type**: 标注类型（label, correction, comment, quality_feedback）
    - **annotation_content**: 标注内容（JSON格式）
    - **confidence**: 置信度（0-1）
    """
    result = service.create_annotation(
        user_id=current_user.id,
        project_id=annotation.project_id,
        target_type=annotation.target_type,
        target_id=annotation.target_id,
        annotation_type=annotation.annotation_type,
        annotation_content=annotation.annotation_content,
        confidence=annotation.confidence
    )

    return AnnotationResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        target_type=result.target_type,
        target_id=result.target_id,
        annotation_type=result.annotation_type.value,
        annotation_content=result.annotation_content,
        confidence=result.confidence,
        created_at=result.created_at.isoformat(),
        updated_at=result.updated_at.isoformat()
    )


@router.get("/annotations", response_model=List[AnnotationResponse], summary="获取标注列表")
async def get_annotations(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    target_type: Optional[str] = Query(None, description="筛选目标类型"),
    target_id: Optional[int] = Query(None, description="筛选目标ID"),
    annotation_type: Optional[AnnotationType] = Query(None, description="筛选标注类型"),
    limit: int = Query(100, description="返回数量", ge=1, le=500),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取标注列表

    可以按项目、目标类型、目标ID和标注类型筛选
    """
    annotations = service.get_annotations(
        user_id=current_user.id,
        project_id=project_id,
        target_type=target_type,
        target_id=target_id,
        annotation_type=annotation_type,
        limit=limit
    )

    return [
        AnnotationResponse(
            id=ann.id,
            user_id=ann.user_id,
            project_id=ann.project_id,
            target_type=ann.target_type,
            target_id=ann.target_id,
            annotation_type=ann.annotation_type.value,
            annotation_content=ann.annotation_content,
            confidence=ann.confidence,
            created_at=ann.created_at.isoformat(),
            updated_at=ann.updated_at.isoformat()
        )
        for ann in annotations
    ]


@router.get("/annotations/{annotation_id}", response_model=AnnotationResponse, summary="获取单个标注")
async def get_annotation(
    annotation_id: int = Path(..., description="标注ID"),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """获取单个标注的详细信息"""
    annotation = service.get_annotation_by_id(annotation_id)

    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    return AnnotationResponse(
        id=annotation.id,
        user_id=annotation.user_id,
        project_id=annotation.project_id,
        target_type=annotation.target_type,
        target_id=annotation.target_id,
        annotation_type=annotation.annotation_type.value,
        annotation_content=annotation.annotation_content,
        confidence=annotation.confidence,
        created_at=annotation.created_at.isoformat(),
        updated_at=annotation.updated_at.isoformat()
    )


@router.put("/annotations/{annotation_id}", response_model=AnnotationResponse, summary="更新标注")
async def update_annotation(
    annotation_id: int = Path(..., description="标注ID"),
    update: AnnotationUpdate = ...,
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    更新标注

    - **annotation_content**: 可选，新的标注内容
    - **confidence**: 可选，新的置信度
    """
    result = service.update_annotation(
        annotation_id=annotation_id,
        annotation_content=update.annotation_content,
        confidence=update.confidence
    )

    return AnnotationResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        target_type=result.target_type,
        target_id=result.target_id,
        annotation_type=result.annotation_type.value,
        annotation_content=result.annotation_content,
        confidence=result.confidence,
        created_at=result.created_at.isoformat(),
        updated_at=result.updated_at.isoformat()
    )


@router.delete("/annotations/{annotation_id}", summary="删除标注")
async def delete_annotation(
    annotation_id: int = Path(..., description="标注ID"),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """删除标注"""
    success = service.delete_annotation(
        annotation_id=annotation_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="标注不存在或无权删除")

    return {"message": "标注已删除"}


# ==================== 目标相关标注 ====================

@router.get("/annotations/target/{target_type}/{target_id}", response_model=List[AnnotationResponse], summary="获取目标的所有标注")
async def get_target_annotations(
    target_type: str = Path(..., description="目标类型"),
    target_id: int = Path(..., description="目标ID"),
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取特定目标的所有标注

    返回所有用户对该目标的标注
    """
    annotations = service.get_annotations_for_target(
        target_type=target_type,
        target_id=target_id,
        project_id=project_id
    )

    return [
        AnnotationResponse(
            id=ann.id,
            user_id=ann.user_id,
            project_id=ann.project_id,
            target_type=ann.target_type,
            target_id=ann.target_id,
            annotation_type=ann.annotation_type.value,
            annotation_content=ann.annotation_content,
            confidence=ann.confidence,
            created_at=ann.created_at.isoformat(),
            updated_at=ann.updated_at.isoformat()
        )
        for ann in annotations
    ]


# ==================== 统计和分析 ====================

@router.get("/statistics/{project_id}", response_model=AnnotationStatisticsResponse, summary="获取标注统计")
async def get_annotation_statistics(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取项目标注统计

    包含：
    - 标注总数
    - 按标注类型分布
    - 按目标类型分布
    - 平均置信度
    - 按用户分布
    """
    stats = service.get_annotation_statistics(
        project_id=project_id,
        days=days
    )

    return AnnotationStatisticsResponse(**stats)


@router.get("/summary/{project_id}", response_model=UserAnnotationSummaryResponse, summary="获取用户标注摘要")
async def get_user_summary(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取当前用户的标注摘要

    包含用户在该项目的标注统计
    """
    summary = service.get_user_annotation_summary(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return UserAnnotationSummaryResponse(**summary)


@router.get("/search/{project_id}", response_model=List[AnnotationResponse], summary="搜索标注")
async def search_annotations(
    project_id: int = Path(..., description="项目ID"),
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    搜索标注

    在标注内容中搜索关键词
    """
    annotations = service.search_annotations(
        project_id=project_id,
        keyword=keyword,
        limit=limit
    )

    return [
        AnnotationResponse(
            id=ann.id,
            user_id=ann.user_id,
            project_id=ann.project_id,
            target_type=ann.target_type,
            target_id=ann.target_id,
            annotation_type=ann.annotation_type.value,
            annotation_content=ann.annotation_content,
            confidence=ann.confidence,
            created_at=ann.created_at.isoformat(),
            updated_at=ann.updated_at.isoformat()
        )
        for ann in annotations
    ]


@router.get("/trend/{project_id}", response_model=List[AnnotationTrendPoint], summary="获取标注趋势")
async def get_annotation_trend(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取标注趋势

    返回每日标注统计数据
    """
    trend = service.get_annotation_trend(
        project_id=project_id,
        days=days
    )

    return [AnnotationTrendPoint(**point) for point in trend]


# ==================== 特定类型查询 ====================

@router.get("/quality-feedback/{project_id}", response_model=List[AnnotationResponse], summary="获取质量反馈")
async def get_quality_feedback(
    project_id: int = Path(..., description="项目ID"),
    target_type: str = Query(..., description="目标类型"),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取质量反馈标注

    返回用户对特定类型目标的质量反馈
    """
    annotations = service.get_quality_feedback(
        project_id=project_id,
        target_type=target_type
    )

    return [
        AnnotationResponse(
            id=ann.id,
            user_id=ann.user_id,
            project_id=ann.project_id,
            target_type=ann.target_type,
            target_id=ann.target_id,
            annotation_type=ann.annotation_type.value,
            annotation_content=ann.annotation_content,
            confidence=ann.confidence,
            created_at=ann.created_at.isoformat(),
            updated_at=ann.updated_at.isoformat()
        )
        for ann in annotations
    ]


@router.get("/corrections/{project_id}", response_model=List[AnnotationResponse], summary="获取纠正标注")
async def get_corrections(
    project_id: int = Path(..., description="项目ID"),
    target_type: Optional[str] = Query(None, description="筛选目标类型"),
    current_user: User = Depends(get_current_user),
    service: AnnotationService = Depends(get_annotation_service)
):
    """
    获取纠正标注

    返回用户的纠正标注记录
    """
    annotations = service.get_corrections(
        project_id=project_id,
        target_type=target_type
    )

    return [
        AnnotationResponse(
            id=ann.id,
            user_id=ann.user_id,
            project_id=ann.project_id,
            target_type=ann.target_type,
            target_id=ann.target_id,
            annotation_type=ann.annotation_type.value,
            annotation_content=ann.annotation_content,
            confidence=ann.confidence,
            created_at=ann.created_at.isoformat(),
            updated_at=ann.updated_at.isoformat()
        )
        for ann in annotations
    ]
