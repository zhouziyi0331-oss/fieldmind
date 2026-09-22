"""
FastAPI Router Template
Resource: api
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.api import ApiCreate, ApiUpdate, Api
from app.services.api_service import ApiService

router = APIRouter()

@router.get("/", response_model=List[Api])
async def list_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: ApiService = Depends()
):
    """获取 api 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Api, status_code=201)
async def create_api(
    data: ApiCreate,
    service: ApiService = Depends()
):
    """创建新的 api"""
    return await service.create(data)

@router.get("/{id}", response_model=Api)
async def get_api(
    id: str,
    service: ApiService = Depends()
):
    """获取单个 api 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Api not found")
    return result

@router.put("/{id}", response_model=Api)
async def update_api(
    id: str,
    data: ApiUpdate,
    service: ApiService = Depends()
):
    """完整更新 api"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Api not found")
    return result

@router.patch("/{id}", response_model=Api)
async def partial_update_api(
    id: str,
    data: ApiUpdate,
    service: ApiService = Depends()
):
    """部分更新 api"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Api not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_api(
    id: str,
    service: ApiService = Depends()
):
    """删除 api"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Api not found")
