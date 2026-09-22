"""
FastAPI Router Template
Resource: projects
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.projects import ProjectsCreate, ProjectsUpdate, Projects
from app.services.projects_service import ProjectsService

router = APIRouter()

@router.get("/", response_model=List[Projects])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: ProjectsService = Depends()
):
    """获取 projects 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Projects, status_code=201)
async def create_projects(
    data: ProjectsCreate,
    service: ProjectsService = Depends()
):
    """创建新的 projects"""
    return await service.create(data)

@router.get("/{id}", response_model=Projects)
async def get_projects(
    id: str,
    service: ProjectsService = Depends()
):
    """获取单个 projects 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Projects not found")
    return result

@router.put("/{id}", response_model=Projects)
async def update_projects(
    id: str,
    data: ProjectsUpdate,
    service: ProjectsService = Depends()
):
    """完整更新 projects"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Projects not found")
    return result

@router.patch("/{id}", response_model=Projects)
async def partial_update_projects(
    id: str,
    data: ProjectsUpdate,
    service: ProjectsService = Depends()
):
    """部分更新 projects"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Projects not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_projects(
    id: str,
    service: ProjectsService = Depends()
):
    """删除 projects"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Projects not found")
