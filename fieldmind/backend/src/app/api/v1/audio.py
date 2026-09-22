"""
音频API路由 - 统一接入项目文档主链路
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pathlib import Path
import os

from app.core.database import get_db
from app.models.project import ProjectDocument
from app.services.background_tasks import submit_task
from app.services.project_document_upload import upload_project_document, prepare_document_retry
from app.schemas.response import success_response, error_response

router = APIRouter()


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    上传音频文件 - 自动触发完整处理流程

    自动触发（当 auto_process=True）：
    1. 提取音频元数据（ffprobe）
    2. Whisper 转录
    3. HanLP 实体提取
    4. 向量化存储
    5. 知识图谱构建

    Args:
        file: 音频文件
        auto_process: 是否自动处理（默认 True）

    Returns:
        上传结果和任务ID
    """
    # 验证文件类型
    allowed_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".webm"]
    file_ext = Path(file.filename or "").suffix.lower()

    if file_ext not in allowed_extensions:
        return error_response(
            code="INVALID_FILE_FORMAT",
            message=f"不支持的文件格式。允许的格式: {', '.join(allowed_extensions)}"
        )

    content = await file.read()
    try:
        document, created = upload_project_document(
            db=db,
            project_id=project_id,
            original_filename=file.filename or "audio",
            content=content,
            mime_type=file.content_type,
            metadata={"source_module": "audio"},
            status="pending" if auto_process else "uploaded",
        )
    except ValueError as exc:
        return error_response(
            code="UPLOAD_FAILED",
            message=str(exc)
        )

    response = {
        "document_id": document.id,
        "filename": document.filename,
        "original_filename": document.original_filename,
        "file_path": document.file_path,
        "file_type": document.file_type,
        "status": document.status,
        "created": created,
        "uploaded_at": document.created_at.isoformat() if document.created_at else None,
    }

    # 自动触发处理链
    if auto_process:
        if created:
            submit_task(document.id)
        elif document.status in {"failed", "review_needed"}:
            prepare_document_retry(db, document)
            submit_task(document.id, force=True)
        response.update({
            "task_id": str(document.id),
            "status_url": f"/api/v1/audio/status/{document.id}/",
        })
        message = "音频上传成功，已提交统一后台处理链路"
    else:
        message = "音频上传成功（未启用自动处理）"

    return success_response(data=response, message=message)


@router.get("/status/{task_id}/")
async def get_audio_processing_status(
    task_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    查询音频处理状态
    """
    if not task_id.isdigit():
        return error_response(
            code="INVALID_TASK_ID",
            message="task_id应为文档ID"
        )

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == int(task_id),
        ProjectDocument.file_type == "audio",
    ).first()
    if not document:
        return error_response(
            code="DOCUMENT_NOT_FOUND",
            message="音频文档不存在"
        )

    return success_response(
        data={
            "task_id": task_id,
            "document_id": document.id,
            "state": document.status,
            "ready": document.status in {"completed", "failed", "review_needed"},
            "progress": document.processing_progress or 0,
            "error": document.error_message,
            "extra_data": document.extra_data,
        }
    )


@router.get("/list")
async def list_audio_files(
    project_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    列出已上传的音频文件
    """
    try:
        query = db.query(ProjectDocument).filter(ProjectDocument.file_type == "audio")
        if project_id is not None:
            query = query.filter(ProjectDocument.project_id == project_id)

        total = query.count()
        docs = query.order_by(ProjectDocument.created_at.desc()).offset(skip).limit(limit).all()
        audio_files = [
            {
                "document_id": doc.id,
                "project_id": doc.project_id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "size": doc.file_size,
                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                "path": doc.file_path,
                "status": doc.status,
            }
            for doc in docs
        ]

        return success_response(
            data={
                "total": total,
                "skip": skip,
                "limit": limit,
                "audio_files": audio_files,
            }
        )

    except Exception as e:
        return error_response(
            code="LIST_FAILED",
            message=f"列表查询失败: {str(e)}"
        )
