"""
FastAPI Router Template
Resource: document
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.document import DocumentCreate, DocumentUpdate, Document
from app.services.document_service import DocumentService

router = APIRouter()

@router.get("/", response_model=List[Document])
async def list_document(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: DocumentService = Depends()
):
    """获取 document 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model=Document, status_code=201)
async def create_document(
    data: DocumentCreate,
    service: DocumentService = Depends()
):
    """创建新的 document"""
    return await service.create(data)

@router.get("/{id}", response_model=Document)
async def get_document(
    id: str,
    service: DocumentService = Depends()
):
    """获取单个 document 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"Document not found")
    return result

@router.put("/{id}", response_model=Document)
async def update_document(
    id: str,
    data: DocumentUpdate,
    service: DocumentService = Depends()
):
    """完整更新 document"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"Document not found")
    return result

@router.patch("/{id}", response_model=Document)
async def partial_update_document(
    id: str,
    data: DocumentUpdate,
    service: DocumentService = Depends()
):
    """部分更新 document"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"Document not found")
    return result

@router.delete("/{id}", status_code=204)
async def delete_document(
    id: str,
    service: DocumentService = Depends()
):
    """删除 document"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"Document not found")
