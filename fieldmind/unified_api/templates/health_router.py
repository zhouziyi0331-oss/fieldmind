"""
FastAPI Router Template
Resource: health
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.health import HealthCreate, HealthUpdate, Health
from app.services.health_service import HealthService

router = APIRouter()

@router.get("/", response_model=List[Health])
async def list_health(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: HealthService = Depends()
):
    """获取 health 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Health, status_code=201)
async def create_health(
    data: HealthCreate,
    service: HealthService = Depends()
):
    """创建新的 health"""
    return await service.create(data)

@router.get("/{id}", response_model=Health)
async def get_health(
    id: str,
    service: HealthService = Depends()
):
    """获取单个 health 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Health not found")
    return result

@router.put("/{id}", response_model=Health)
async def update_health(
    id: str,
    data: HealthUpdate,
    service: HealthService = Depends()
):
    """完整更新 health"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Health not found")
    return result

@router.patch("/{id}", response_model=Health)
async def partial_update_health(
    id: str,
    data: HealthUpdate,
    service: HealthService = Depends()
):
    """部分更新 health"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Health not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_health(
    id: str,
    service: HealthService = Depends()
):
    """删除 health"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Health not found")
