"""
FastAPI Router Template
Resource: project
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.project import ProjectCreate, ProjectUpdate, Project
from app.services.project_service import ProjectService

router = APIRouter()

@router.get("/", response_model=List[Project])
async def list_project(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: ProjectService = Depends()
):
    """获取 project 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Project, status_code=201)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends()
):
    """创建新的 project"""
    return await service.create(data)

@router.get("/{id}", response_model=Project)
async def get_project(
    id: str,
    service: ProjectService = Depends()
):
    """获取单个 project 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Project not found")
    return result

@router.put("/{id}", response_model=Project)
async def update_project(
    id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends()
):
    """完整更新 project"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Project not found")
    return result

@router.patch("/{id}", response_model=Project)
async def partial_update_project(
    id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends()
):
    """部分更新 project"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Project not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_project(
    id: str,
    service: ProjectService = Depends()
):
    """删除 project"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Project not found")
