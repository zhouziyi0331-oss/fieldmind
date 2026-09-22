"""
用户标签API端点

提供用户自定义标签、分类和组织接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.tagging_service import TaggingService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class TagCreate(BaseModel):
    """创建标签请求"""
    project_id: int = Field(..., description="项目ID")
    target_type: str = Field(..., description="标签目标类型")
    target_id: int = Field(..., description="标签目标ID")
    tag_name: str = Field(..., description="标签名称")
    tag_color: Optional[str] = Field("#808080", description="标签颜色")
    tag_metadata: Optional[Dict[str, Any]] = Field(None, description="标签元数据")


class BulkTagRequest(BaseModel):
    """批量标签请求"""
    project_id: int = Field(..., description="项目ID")
    target_type: str = Field(..., description="目标类型")
    target_ids: List[int] = Field(..., description="目标ID列表")
    tag_name: str = Field(..., description="标签名称")
    tag_color: Optional[str] = Field("#808080", description="标签颜色")


class TagResponse(BaseModel):
    """标签响应"""
    id: int
    user_id: int
    project_id: int
    target_type: str
    target_id: int
    tag_name: str
    tag_color: str
    tag_metadata: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True


class TagNameResponse(BaseModel):
    """标签名称响应"""
    tag_name: str
    count: int
    color: str


class TargetsByTagResponse(BaseModel):
    """按标签的目标响应"""
    target_type: str
    targets: List[Dict[str, Any]]


class TagStatisticsResponse(BaseModel):
    """标签统计响应"""
    period_days: int
    total_tags: int
    unique_tag_names: int
    by_tag_name: List[tuple]
    by_target_type: Dict[str, int]
    by_user: Dict[int, int]
    start_date: str
    end_date: str


class UserTagSummaryResponse(BaseModel):
    """用户标签摘要响应"""
    period_days: int
    total_tags: int
    unique_tag_names: int
    top_tags: List[tuple]
    by_target_type: Dict[str, int]
    start_date: str
    end_date: str


class TagTrendPoint(BaseModel):
    """标签趋势点"""
    date: str
    count: int
    unique_tag_count: int


# ==================== 依赖项 ====================

def get_tagging_service(db: Session = Depends(get_db)) -> TaggingService:
    """获取标签服务"""
    return TaggingService(db)


# ==================== 标签管理 ====================

@router.post("/tags", response_model=TagResponse, summary="创建标签")
async def create_tag(
    tag: TagCreate,
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    创建标签

    - **project_id**: 项目ID
    - **target_type**: 标签目标类型（document, entity, relationship等）
    - **target_id**: 标签目标ID
    - **tag_name**: 标签名称
    - **tag_color**: 标签颜色（十六进制）
    - **tag_metadata**: 标签元数据
    """
    result = service.create_tag(
        user_id=current_user.id,
        project_id=tag.project_id,
        target_type=tag.target_type,
        target_id=tag.target_id,
        tag_name=tag.tag_name,
        tag_color=tag.tag_color,
        tag_metadata=tag.tag_metadata
    )

    return TagResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        target_type=result.target_type,
        target_id=result.target_id,
        tag_name=result.tag_name,
        tag_color=result.tag_color,
        tag_metadata=result.tag_metadata,
        created_at=result.created_at.isoformat()
    )


@router.post("/tags/bulk", response_model=List[TagResponse], summary="批量创建标签")
async def bulk_tag(
    request: BulkTagRequest,
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    批量创建标签

    为多个目标添加同一个标签
    """
    results = service.bulk_tag(
        user_id=current_user.id,
        project_id=request.project_id,
        target_type=request.target_type,
        target_ids=request.target_ids,
        tag_name=request.tag_name,
        tag_color=request.tag_color
    )

    return [
        TagResponse(
            id=tag.id,
            user_id=tag.user_id,
            project_id=tag.project_id,
            target_type=tag.target_type,
            target_id=tag.target_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
            tag_metadata=tag.tag_metadata,
            created_at=tag.created_at.isoformat()
        )
        for tag in results
    ]


@router.get("/tags", response_model=List[TagResponse], summary="获取标签列表")
async def get_tags(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    target_type: Optional[str] = Query(None, description="筛选目标类型"),
    target_id: Optional[int] = Query(None, description="筛选目标ID"),
    tag_name: Optional[str] = Query(None, description="筛选标签名称"),
    limit: int = Query(200, description="返回数量", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取标签列表

    可以按项目、目标类型、目标ID和标签名称筛选
    """
    tags = service.get_tags(
        user_id=current_user.id,
        project_id=project_id,
        target_type=target_type,
        target_id=target_id,
        tag_name=tag_name,
        limit=limit
    )

    return [
        TagResponse(
            id=tag.id,
            user_id=tag.user_id,
            project_id=tag.project_id,
            target_type=tag.target_type,
            target_id=tag.target_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
            tag_metadata=tag.tag_metadata,
            created_at=tag.created_at.isoformat()
        )
        for tag in tags
    ]


@router.delete("/tags/{tag_id}", summary="删除标签")
async def delete_tag(
    tag_id: int = Path(..., description="标签ID"),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """删除标签"""
    success = service.delete_tag(
        tag_id=tag_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="标签不存在或无权删除")

    return {"message": "标签已删除"}


@router.delete("/tags/target/{target_type}/{target_id}", summary="移除目标的标签")
async def remove_tags_from_target(
    target_type: str = Path(..., description="目标类型"),
    target_id: int = Path(..., description="目标ID"),
    tag_name: Optional[str] = Query(None, description="指定标签名称"),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    从目标移除标签

    如果不指定tag_name，则移除该目标的所有标签
    """
    count = service.remove_tags_from_target(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        tag_name=tag_name
    )

    return {
        "removed_count": count,
        "message": f"已移除 {count} 个标签"
    }


# ==================== 目标相关标签 ====================

@router.get("/tags/target/{target_type}/{target_id}", response_model=List[TagResponse], summary="获取目标的所有标签")
async def get_target_tags(
    target_type: str = Path(..., description="目标类型"),
    target_id: int = Path(..., description="目标ID"),
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取特定目标的所有标签

    返回所有用户对该目标的标签
    """
    tags = service.get_tags_for_target(
        target_type=target_type,
        target_id=target_id,
        project_id=project_id
    )

    return [
        TagResponse(
            id=tag.id,
            user_id=tag.user_id,
            project_id=tag.project_id,
            target_type=tag.target_type,
            target_id=tag.target_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
            tag_metadata=tag.tag_metadata,
            created_at=tag.created_at.isoformat()
        )
        for tag in tags
    ]


# ==================== 标签名称和组织 ====================

@router.get("/tag-names/{project_id}", response_model=List[TagNameResponse], summary="获取所有标签名称")
async def get_all_tag_names(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取所有标签名称（去重）

    返回标签名称及其使用次数，按使用次数排序
    """
    tag_names = service.get_all_tag_names(
        user_id=current_user.id,
        project_id=project_id
    )

    return [TagNameResponse(**item) for item in tag_names]


@router.get("/targets-by-tag/{project_id}/{tag_name}", response_model=List[TargetsByTagResponse], summary="根据标签获取目标")
async def get_targets_by_tag(
    project_id: int = Path(..., description="项目ID"),
    tag_name: str = Path(..., description="标签名称"),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    根据标签获取所有目标

    返回所有带有该标签的目标，按目标类型分组
    """
    targets = service.get_targets_by_tag(
        user_id=current_user.id,
        project_id=project_id,
        tag_name=tag_name
    )

    return [TargetsByTagResponse(**item) for item in targets]


# ==================== 统计和分析 ====================

@router.get("/statistics/{project_id}", response_model=TagStatisticsResponse, summary="获取标签统计")
async def get_tag_statistics(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取项目标签统计

    包含：
    - 标签总数
    - 唯一标签名称数
    - 按标签名称分布
    - 按目标类型分布
    - 按用户分布
    """
    stats = service.get_tag_statistics(
        project_id=project_id,
        days=days
    )

    return TagStatisticsResponse(**stats)


@router.get("/summary/{project_id}", response_model=UserTagSummaryResponse, summary="获取用户标签摘要")
async def get_user_summary(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取当前用户的标签摘要

    包含用户在该项目的标签使用统计
    """
    summary = service.get_user_tag_summary(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return UserTagSummaryResponse(**summary)


@router.get("/search/{project_id}", response_model=List[TagResponse], summary="搜索标签")
async def search_tags(
    project_id: int = Path(..., description="项目ID"),
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    搜索标签

    在标签名称中搜索关键词
    """
    tags = service.search_tags(
        user_id=current_user.id,
        project_id=project_id,
        keyword=keyword,
        limit=limit
    )

    return [
        TagResponse(
            id=tag.id,
            user_id=tag.user_id,
            project_id=tag.project_id,
            target_type=tag.target_type,
            target_id=tag.target_id,
            tag_name=tag.tag_name,
            tag_color=tag.tag_color,
            tag_metadata=tag.tag_metadata,
            created_at=tag.created_at.isoformat()
        )
        for tag in tags
    ]


@router.get("/trend/{project_id}", response_model=List[TagTrendPoint], summary="获取标签趋势")
async def get_tag_trend(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(30, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: TaggingService = Depends(get_tagging_service)
):
    """
    获取标签趋势

    返回每日标签统计数据
    """
    trend = service.get_tag_trend(
        project_id=project_id,
        days=days
    )

    return [TagTrendPoint(**point) for point in trend]
