"""
FastAPI Router Template
Resource: metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.metrics import MetricsCreate, MetricsUpdate, Metrics
from app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/", response_model=List[Metrics])
async def list_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: MetricsService = Depends()
):
    """获取 metrics 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Metrics, status_code=201)
async def create_metrics(
    data: MetricsCreate,
    service: MetricsService = Depends()
):
    """创建新的 metrics"""
    return await service.create(data)

@router.get("/{id}", response_model=Metrics)
async def get_metrics(
    id: str,
    service: MetricsService = Depends()
):
    """获取单个 metrics 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Metrics not found")
    return result

@router.put("/{id}", response_model=Metrics)
async def update_metrics(
    id: str,
    data: MetricsUpdate,
    service: MetricsService = Depends()
):
    """完整更新 metrics"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Metrics not found")
    return result

@router.patch("/{id}", response_model=Metrics)
async def partial_update_metrics(
    id: str,
    data: MetricsUpdate,
    service: MetricsService = Depends()
):
    """部分更新 metrics"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Metrics not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_metrics(
    id: str,
    service: MetricsService = Depends()
):
    """删除 metrics"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Metrics not found")
