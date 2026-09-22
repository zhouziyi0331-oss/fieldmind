"""
FastAPI Router Template
Resource: documents
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.documents import DocumentsCreate, DocumentsUpdate, Documents
from app.services.documents_service import DocumentsService

router = APIRouter()

@router.get("/", response_model=List[Documents])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: DocumentsService = Depends()
):
    """获取 documents 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Documents, status_code=201)
async def create_documents(
    data: DocumentsCreate,
    service: DocumentsService = Depends()
):
    """创建新的 documents"""
    return await service.create(data)

@router.get("/{id}", response_model=Documents)
async def get_documents(
    id: str,
    service: DocumentsService = Depends()
):
    """获取单个 documents 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Documents not found")
    return result

@router.put("/{id}", response_model=Documents)
async def update_documents(
    id: str,
    data: DocumentsUpdate,
    service: DocumentsService = Depends()
):
    """完整更新 documents"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Documents not found")
    return result

@router.patch("/{id}", response_model=Documents)
async def partial_update_documents(
    id: str,
    data: DocumentsUpdate,
    service: DocumentsService = Depends()
):
    """部分更新 documents"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Documents not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_documents(
    id: str,
    service: DocumentsService = Depends()
):
    """删除 documents"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Documents not found")
