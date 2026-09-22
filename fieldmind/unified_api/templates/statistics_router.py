"""
FastAPI Router Template
Resource: statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.statistics import StatisticsCreate, StatisticsUpdate, Statistics
from app.services.statistics_service import StatisticsService

router = APIRouter()

@router.get("/", response_model=List[Statistics])
async def list_statistics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: StatisticsService = Depends()
):
    """获取 statistics 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Statistics, status_code=201)
async def create_statistics(
    data: StatisticsCreate,
    service: StatisticsService = Depends()
):
    """创建新的 statistics"""
    return await service.create(data)

@router.get("/{id}", response_model=Statistics)
async def get_statistics(
    id: str,
    service: StatisticsService = Depends()
):
    """获取单个 statistics 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Statistics not found")
    return result

@router.put("/{id}", response_model=Statistics)
async def update_statistics(
    id: str,
    data: StatisticsUpdate,
    service: StatisticsService = Depends()
):
    """完整更新 statistics"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Statistics not found")
    return result

@router.patch("/{id}", response_model=Statistics)
async def partial_update_statistics(
    id: str,
    data: StatisticsUpdate,
    service: StatisticsService = Depends()
):
    """部分更新 statistics"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Statistics not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_statistics(
    id: str,
    service: StatisticsService = Depends()
):
    """删除 statistics"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Statistics not found")
