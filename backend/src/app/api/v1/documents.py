"""
文档上传 API 端点
"""

from typing import Optional
import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import get_storage
from app.core.exceptions import ValidationException, DocumentNotFoundException
from app.schemas.response import success_response, paginated_response, ApiResponse
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentListQuery,
    DocumentUpdateRequest,
    DocumentDownloadResponse,
    FileClassificationResult
)
from app.services.file_classifier import FileClassifier
from app.models.project import ProjectDocument
from app.models.document import DocumentType, DocumentStatus
from app.services.project_document_upload import upload_project_document, prepare_document_retry
from app.services.background_tasks import submit_task


router = APIRouter(prefix="/documents", tags=["documents"])


def _legacy_type(file_type: str) -> DocumentType:
    if file_type == "image":
        return DocumentType.IMAGE
    if file_type == "audio":
        return DocumentType.AUDIO
    if file_type == "video":
        return DocumentType.VIDEO
    if file_type in {"csv", "xls", "xlsx"}:
        return DocumentType.TABLE
    return DocumentType.DOCUMENT


def _legacy_status(status: str) -> DocumentStatus:
    mapping = {
        "pending": DocumentStatus.UPLOADED,
        "uploaded": DocumentStatus.UPLOADED,
        "processing": DocumentStatus.PROCESSING,
        "completed": DocumentStatus.COMPLETED,
        "failed": DocumentStatus.FAILED,
    }
    return mapping.get(status, DocumentStatus.UPLOADED)


def _legacy_upload_payload(document: ProjectDocument) -> dict:
    return {
        "id": str(document.id),
        "name": document.original_filename,
        "type": _legacy_type(document.file_type),
        "size": document.file_size or 0,
        "mime_type": document.mime_type or "application/octet-stream",
        "hash": document.file_hash or "",
        "status": _legacy_status(document.status),
        "storage_path": document.file_path,
        "created_at": document.created_at,
    }


def _legacy_detail_payload(document: ProjectDocument, db: Session) -> dict:
    from app.models.document_chunk import DocumentChunk
    from app.models.project import ProjectDocumentTag
    return {
        **_legacy_upload_payload(document),
        "project_id": document.project_id,
        "uploaded_by": None,
        "processed_at": document.processed_at,
        "updated_at": document.updated_at,
        "chunk_count": db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).count(),
        "entity_count": len(document.entities or []),
        "tag_count": db.query(ProjectDocumentTag).filter(
            ProjectDocumentTag.document_id == document.id
        ).count(),
    }


@router.post("/upload", response_model=ApiResponse[DocumentUploadResponse])
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="要上传的文件"),
    project_id: int = Form(..., description="项目ID"),
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """
    上传文档（统一入口）

    支持的文件类型：
    - 文档: PDF, DOC, DOCX, TXT, MD
    - 图片: JPG, PNG, GIF, WEBP, SVG
    - 音频: MP3, WAV, M4A, FLAC, OGG
    - 视频: MP4, AVI, MOV, MKV, WEBM
    - 表格: XLS, XLSX, CSV

    文件大小限制：
    - 文档/表格: 100 MB
    - 图片: 50 MB
    - 音频: 500 MB
    - 视频: 2 GB
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        content = await file.read()
        document, created = upload_project_document(
            db=db,
            project_id=project_id,
            original_filename=file.filename or "unnamed",
            content=content,
            mime_type=file.content_type,
        )
        if created and document.status in {"pending", "uploaded"}:
            submit_task(document.id)
        elif not created and document.status in {"failed", "review_needed"}:
            prepare_document_retry(db, document)
            submit_task(document.id, force=True)

        response_data = DocumentUploadResponse.model_validate(
            _legacy_upload_payload(document)
        )

        return success_response(
            data=response_data.model_dump(),
            request_id=request_id,
            message="File uploaded successfully"
        )

    except ValidationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=ApiResponse[DocumentDetailResponse])
async def get_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取文档详情

    返回文档的完整信息，包括：
    - 基本信息（ID、名称、类型、大小等）
    - 处理状态
    - 统计信息（分块数、实体数、标签数）
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        document_key = int(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id)

    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_key).first()

    if not document:
        raise DocumentNotFoundException(document_id)

    response_data = DocumentDetailResponse.model_validate(
        _legacy_detail_payload(document, db)
    )

    return success_response(
        data=response_data.model_dump(),
        request_id=request_id
    )


@router.get("", response_model=ApiResponse)
async def list_documents(
    request: Request,
    project_id: Optional[int] = None,
    type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取文档列表（分页）

    支持筛选：
    - project_id: 按项目筛选
    - type: 按文档类型筛选
    - status: 按处理状态筛选
    - search: 按文件名搜索
    """
    request_id = getattr(request.state, "request_id", None)

    query = db.query(ProjectDocument)

    if project_id:
        query = query.filter(ProjectDocument.project_id == project_id)

    if type:
        type_values = {
            DocumentType.IMAGE: "image",
            DocumentType.AUDIO: "audio",
            DocumentType.VIDEO: "video",
            DocumentType.TABLE: "xlsx",
        }
        if type in type_values:
            query = query.filter(ProjectDocument.file_type == type_values[type])
        else:
            query = query.filter(ProjectDocument.file_type.notin_(["image", "audio", "video", "xlsx", "csv"]))

    if status:
        status_values = {
            DocumentStatus.UPLOADED: ["uploaded", "pending"],
            DocumentStatus.PROCESSING: ["processing"],
            DocumentStatus.COMPLETED: ["completed"],
            DocumentStatus.FAILED: ["failed"],
        }
        query = query.filter(ProjectDocument.status.in_(status_values.get(status, [status.value])))

    if search:
        query = query.filter(ProjectDocument.original_filename.like(f"%{search}%"))

    # 总数
    total = query.count()

    # 分页
    documents = query.order_by(ProjectDocument.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 转换为响应格式
    data = [
        DocumentUploadResponse.model_validate(_legacy_upload_payload(doc)).model_dump()
        for doc in documents
    ]

    return paginated_response(
        data=data,
        page=page,
        page_size=page_size,
        total=total,
        request_id=request_id
    )


@router.get("/projects/{project_id}/documents/simple")
async def list_documents_simple(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取文档列表（简化版，专为桌面应用设计）

    只返回基本字段，不包含复杂的嵌套对象（entities, extra_data 等）
    """
    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    total = query.count()

    documents = query.order_by(ProjectDocument.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 只返回简单字段
    simple_docs = []
    for doc in documents:
        simple_docs.append({
            "id": doc.id,
            "project_id": doc.project_id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "processing_progress": doc.processing_progress if hasattr(doc, 'processing_progress') else 0,
            "chunk_count": doc.chunk_count if hasattr(doc, 'chunk_count') else 0,
            "word_count": doc.word_count if hasattr(doc, 'word_count') else 0,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        })

    return success_response(
        data={
            "total": total,
            "documents": simple_docs,
            "page": page,
            "page_size": page_size
        }
    )


@router.patch("/{document_id}", response_model=ApiResponse[DocumentDetailResponse])
async def update_document(
    document_id: str,
    request: Request,
    update_data: DocumentUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新文档信息

    可更新：
    - name: 文件名
    - metadata: 元数据
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        document_key = int(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id)
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_key).first()

    if not document:
        raise DocumentNotFoundException(document_id)

    # 更新字段
    if update_data.name:
        document.original_filename = os.path.basename(update_data.name)
        document.filename = os.path.basename(update_data.name)

    if update_data.metadata:
        document.extra_data = {
            **dict(document.extra_data or {}),
            **update_data.metadata,
        }

    document.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(document)

    response_data = DocumentDetailResponse.model_validate(
        _legacy_detail_payload(document, db)
    )

    return success_response(
        data=response_data.model_dump(),
        request_id=request_id,
        message="Document updated successfully"
    )


@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """
    删除文档

    将同时删除：
    - 数据库记录
    - 对象存储中的文件
    - 相关的分块、实体、标签等
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        document_key = int(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id)
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_key).first()

    if not document:
        raise DocumentNotFoundException(document_id)

    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    # 删除数据库记录（级联删除相关数据）
    db.delete(document)
    db.commit()

    return success_response(
        data={"document_id": document_id, "deleted": True},
        request_id=request_id,
        message="Document deleted successfully"
    )


@router.get("/{document_id}/download", response_model=ApiResponse[DocumentDownloadResponse])
async def get_download_url(
    document_id: str,
    request: Request,
    expires: int = 3600,
    db: Session = Depends(get_db),
    storage = Depends(get_storage)
):
    """
    获取文档下载链接

    生成预签名URL，用于直接下载文件

    Args:
        document_id: 文档ID
        expires: 链接过期时间（秒），默认3600秒（1小时）
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        document_key = int(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id)
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_key).first()
    if not document:
        raise DocumentNotFoundException(document_id)

    url = f"/api/v1/documents/{document.id}/content"

    response_data = {
        "url": url,
        "expires_in": expires,
        "filename": document.original_filename,
        "size": document.file_size or 0
    }

    return success_response(
        data=response_data,
        request_id=request_id
    )


@router.get("/{document_id}/content/")
async def get_document_content(
    document_id: str,
    db: Session = Depends(get_db),
):
    """兼容下载链接的实际文件内容端点。"""
    try:
        document_key = int(document_id)
    except ValueError:
        raise DocumentNotFoundException(document_id)
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_key).first()
    if not document or not document.file_path or not os.path.exists(document.file_path):
        raise DocumentNotFoundException(document_id)
    return FileResponse(
        document.file_path,
        media_type=document.mime_type or "application/octet-stream",
        filename=document.original_filename,
    )


@router.post("/classify", response_model=ApiResponse[FileClassificationResult])
async def classify_file(
    request: Request,
    filename: str = Form(..., description="文件名"),
    mime_type: Optional[str] = Form(None, description="MIME类型")
):
    """
    文件分类（不上传文件）

    用于在上传前检查文件是否支持

    返回：
    - type: 识别的文档类型
    - confidence: 置信度（0-1）
    - method: 分类方法
    - details: 详细信息
    """
    request_id = getattr(request.state, "request_id", None)

    # 分类
    result = FileClassifier.classify(
        filename=filename,
        mime_type=mime_type
    )

    return success_response(
        data=result,
        request_id=request_id
    )


@router.post("/upload-batch", response_model=ApiResponse)
async def upload_documents_batch(
    request: Request,
    files: list[UploadFile] = File(..., description="要上传的文件列表（最多50个）"),
    project_id: int = Form(..., description="项目ID"),
    db: Session = Depends(get_db),
):
    """
    批量上传文档

    支持一次上传多个文件（最多50个），自动排队处理

    特性：
    - 自动文件类型识别
    - 自动触发后台处理
    - 实时进度追踪
    - 失败重试机制

    返回：
    - total: 总文件数
    - success: 成功上传数
    - failed: 失败数
    - documents: 每个文件的详细信息
    """
    request_id = getattr(request.state, "request_id", None)

    # 限制文件数量
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="一次最多上传50个文件"
        )

    try:
        from app.services.file_upload_service import file_upload_service

        # 获取用户 ID（如果有认证）
        user_id = getattr(request.state, "user_id", None) or 1

        # 批量上传
        result = await file_upload_service.upload_batch(
            files=files,
            project_id=project_id,
            user_id=user_id,
            db=db
        )

        return success_response(
            data=result,
            request_id=request_id,
            message=f"批量上传完成：{result['success']}/{result['total']} 成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload-progress/{project_id}", response_model=ApiResponse)
async def get_upload_progress(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取批量上传进度

    返回指定项目的文档处理进度
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.file_upload_service import file_upload_service

        progress = file_upload_service.get_upload_progress(project_id, db)

        return success_response(
            data=progress,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
