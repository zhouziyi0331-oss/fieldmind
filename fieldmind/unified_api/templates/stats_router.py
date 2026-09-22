"""
FastAPI Router Template
Resource: stats
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.stats import StatsCreate, StatsUpdate, Stats
from app.services.stats_service import StatsService

router = APIRouter()

@router.get("/", response_model=List[Stats])
async def list_stats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: StatsService = Depends()
):
    """获取 stats 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Stats, status_code=201)
async def create_stats(
    data: StatsCreate,
    service: StatsService = Depends()
):
    """创建新的 stats"""
    return await service.create(data)

@router.get("/{id}", response_model=Stats)
async def get_stats(
    id: str,
    service: StatsService = Depends()
):
    """获取单个 stats 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Stats not found")
    return result

@router.put("/{id}", response_model=Stats)
async def update_stats(
    id: str,
    data: StatsUpdate,
    service: StatsService = Depends()
):
    """完整更新 stats"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Stats not found")
    return result

@router.patch("/{id}", response_model=Stats)
async def partial_update_stats(
    id: str,
    data: StatsUpdate,
    service: StatsService = Depends()
):
    """部分更新 stats"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Stats not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_stats(
    id: str,
    service: StatsService = Depends()
):
    """删除 stats"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Stats not found")
