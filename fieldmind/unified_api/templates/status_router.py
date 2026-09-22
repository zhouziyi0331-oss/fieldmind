"""
FastAPI Router Template
Resource: status
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.status import StatusCreate, StatusUpdate, Status
from app.services.status_service import StatusService

router = APIRouter()

@router.get("/", response_model=List[Status])
async def list_status(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: StatusService = Depends()
):
    """获取 status 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Status, status_code=201)
async def create_status(
    data: StatusCreate,
    service: StatusService = Depends()
):
    """创建新的 status"""
    return await service.create(data)

@router.get("/{id}", response_model=Status)
async def get_status(
    id: str,
    service: StatusService = Depends()
):
    """获取单个 status 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Status not found")
    return result

@router.put("/{id}", response_model=Status)
async def update_status(
    id: str,
    data: StatusUpdate,
    service: StatusService = Depends()
):
    """完整更新 status"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Status not found")
    return result

@router.patch("/{id}", response_model=Status)
async def partial_update_status(
    id: str,
    data: StatusUpdate,
    service: StatusService = Depends()
):
    """部分更新 status"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Status not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_status(
    id: str,
    service: StatusService = Depends()
):
    """删除 status"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Status not found")
