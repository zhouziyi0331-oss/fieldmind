"""项目文档上传和管理API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import logging

from app.core.database import get_db
from app.models.project import Project, ProjectDocument, ProjectDocumentTag
from app.schemas.project import ProjectDocumentResponse
from app.schemas.response import success_response, error_response
from app.services.memory_service import MemoryService
from app.services.project_document_upload import upload_project_document, prepare_document_retry

router = APIRouter()
logger = logging.getLogger(__name__)

class ProjectDocumentTagCreate(BaseModel):
    name: str
    category: str = "manual"
    confidence: Optional[int] = None


def document_payload(document: ProjectDocument) -> dict:
    return {
        "id": document.id,
        "project_id": document.project_id,
        "filename": document.filename,
        "original_filename": document.original_filename,
        "file_type": document.file_type,
        "file_hash": document.file_hash,
        "mime_type": document.mime_type,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "status": document.status,
        "processing_progress": document.processing_progress or 0,
        "chunk_count": document.chunk_count or 0,
        "word_count": document.word_count or 0,
        "summary": document.summary,
        "entities": document.entities,
        "keywords": document.keywords,
        "extra_data": document.extra_data,
        "assets": [
            {
                "id": asset.id,
                "asset_type": asset.asset_type,
                "storage_path": asset.storage_path,
                "metadata": asset.asset_metadata,
                "status": asset.status,
            }
            for asset in (document.assets or [])
        ],
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
                "category": tag.category,
                "source": tag.source,
                "confidence": tag.confidence,
            }
            for tag in (document.tags or [])
        ],
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


@router.post("/{project_id}/documents/upload", response_model=ProjectDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传项目文档"""

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    original_filename = os.path.basename(file.filename or "unnamed")

    try:
        content = await file.read()
        document, created = upload_project_document(
            db,
            project_id=project_id,
            original_filename=original_filename,
            content=content,
            mime_type=file.content_type,
        )
        if not created:
            if document.status in {"failed", "review_needed"}:
                prepare_document_retry(db, document)
                from app.services.background_tasks import submit_task
                submit_task(document.id, force=True)
            return document_payload(document)

        # 🚀 使用现有的完整处理流程
        logger.info(f"🚀 文档 {document.id} 上传成功，启动完整处理流程")

        from app.services.background_tasks import submit_task

        # 所有上传入口统一经过去重任务调度器
        if created:
            submit_task(document.id)

        logger.info(f"✅ 文档 {document.id} 已提交后台处理（包含音频转录、向量化、分析等完整流程）")

        return document_payload(document)

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"文档上传失败: {e}")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="文件已存在，但重复记录无法读取")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/{project_id}/documents/{document_id}", response_model=ProjectDocumentResponse)
async def get_document_detail(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    return document_payload(document)


@router.get("/{project_id}/documents/{document_id}/tags/")
async def list_document_tags(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    return document_payload(document)["tags"]


@router.post("/{project_id}/documents/{document_id}/tags/")
async def add_document_tag(
    project_id: int,
    document_id: int,
    request: ProjectDocumentTagCreate,
    db: Session = Depends(get_db)
):
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    existing = db.query(ProjectDocumentTag).filter(
        ProjectDocumentTag.document_id == document_id,
        ProjectDocumentTag.name == request.name
    ).first()
    if existing:
        return success_response(
            data={"id": existing.id, "name": existing.name, "category": existing.category}
        )

    tag = ProjectDocumentTag(
        document_id=document_id,
        name=request.name,
        category=request.category,
        source="manual",
        confidence=request.confidence,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return success_response(
        data={"id": tag.id, "name": tag.name, "category": tag.category, "source": tag.source}
    )


@router.delete("/{project_id}/documents/{document_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_tag(
    project_id: int,
    document_id: int,
    tag_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    tag = db.query(ProjectDocumentTag).filter(
        ProjectDocumentTag.id == tag_id,
        ProjectDocumentTag.document_id == document_id,
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    db.delete(tag)
    db.commit()
    return None


@router.post("/{project_id}/documents/{document_id}/process/")
async def process_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """处理文档（提取文本、向量化、提取实体）"""

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        return error_response(
            code="DOCUMENT_NOT_FOUND",
            message="文档不存在"
        )

    if document.status == "completed":
        return success_response(data={"status": "already_completed", "document_id": document_id})
    if document.status == "processing":
        return success_response(data={"status": "already_processing", "document_id": document_id})

    try:
        from app.services.background_tasks import submit_task

        document.status = "pending"
        document.processing_progress = 0
        document.error_message = None
        document.updated_at = datetime.utcnow()
        db.commit()

        future = submit_task(document_id)
        if future is None:
            return success_response(data={"status": "already_completed", "document_id": document_id})

        return success_response(
            data={
                "status": "queued",
                "document_id": document_id,
                "processing_status": "pending",
            }
        )
    except Exception as e:
        db.rollback()
        return error_response(
            code="DOCUMENT_PROCESSING_FAILED",
            message=f"文档处理提交失败: {str(e)}"
        )


@router.delete("/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """删除项目文档"""

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    try:
        # 删除文件
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        # 删除数据库记录
        db.delete(document)

        # 更新项目文档计数
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.document_count = max(0, project.document_count - 1)
            project.updated_at = datetime.utcnow()

        db.commit()
        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")


@router.get("/{project_id}/documents/{document_id}/content/")
async def get_document_content(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档内容"""

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        return error_response(
            code="DOCUMENT_NOT_FOUND",
            message="文档不存在"
        )

    try:
        if document.text_content:
            return success_response(
                data={
                    "document_id": document_id,
                    "filename": document.original_filename,
                    "content": document.text_content,
                    "word_count": document.word_count
                }
            )
        else:
            # 读取文件
            if not os.path.exists(document.file_path):
                return error_response(
                    code="FILE_NOT_FOUND",
                    message="文件不存在"
                )

            with open(document.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return success_response(
                data={
                    "document_id": document_id,
                    "filename": document.original_filename,
                    "content": content,
                    "word_count": len(content)
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文档失败: {str(e)}")
