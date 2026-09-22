"""项目文档统一上传服务。

所有面向用户的上传入口都写入 ``project_documents`` 主表，并使用同一套
哈希去重、文件分类和本地文件路径规则。旧 API 的响应格式由路由层适配，
不再创建孤立的 ``documents`` 记录。
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectDocument


SUPPORTED_EXTENSIONS = {
    "document": {
        ".pdf", ".doc", ".docx", ".txt", ".md", ".markdown", ".html",
        ".csv", ".json", ".xml", ".ppt", ".pptx", ".xls", ".xlsx",
    },
    "image": {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tif", ".tiff",
        ".heic", ".heif", ".raw", ".avif",
    },
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".webm"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"},
}


def classify_project_file(filename: str, mime_type: Optional[str] = None) -> str:
    """按扩展名分类，并用 MIME 解决 ``.webm`` 音视频歧义。"""
    extension = os.path.splitext(os.path.basename(filename or ""))[1].lower()
    normalized_mime = (mime_type or "").lower()
    if extension == ".webm" and normalized_mime.startswith("video/"):
        return "video"
    for file_type, extensions in SUPPORTED_EXTENSIONS.items():
        if extension in extensions:
            # 文档保留具体扩展名，后台解析器据此选择 PDF/Word/表格插件；
            # 多媒体使用稳定的 image/audio/video 大类。
            return extension.lstrip(".") if file_type == "document" else file_type
    return "unknown"


def supported_extensions() -> list[str]:
    return sorted({ext for extensions in SUPPORTED_EXTENSIONS.values() for ext in extensions})


def upload_project_document(
    db: Session,
    project_id: int,
    original_filename: str,
    content: bytes,
    mime_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    status: str = "pending",
) -> Tuple[ProjectDocument, bool]:
    """创建或读取项目主文档，返回 ``(document, created)``。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ValueError("项目不存在")

    safe_filename = os.path.basename(original_filename or "unnamed")
    file_type = classify_project_file(safe_filename, mime_type)
    if file_type == "unknown":
        raise ValueError(f"不支持的文件类型: {os.path.splitext(safe_filename)[1].lower()}")
    if not content:
        raise ValueError("文件不能为空")

    file_hash = hashlib.sha256(content).hexdigest()
    existing = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.file_hash == file_hash,
    ).first()
    if existing:
        # 数据库记录还在但实体文件被手工删除时，重新上传应修复原记录，
        # 不能只返回一个指向不存在路径的旧对象。
        if not existing.file_path or not os.path.exists(existing.file_path):
            upload_dir = os.path.join(str(settings.UPLOAD_DIR), f"project_{project_id}")
            os.makedirs(upload_dir, exist_ok=True)
            repaired_path = existing.file_path or os.path.join(
                upload_dir,
                f"{file_hash[:12]}_{safe_filename}",
            )
            with open(repaired_path, "wb") as output:
                output.write(content)
            existing.file_path = repaired_path
            existing.filename = os.path.basename(repaired_path)
            existing.original_filename = safe_filename
            existing.file_size = len(content)
            existing.mime_type = mime_type or mimetypes.guess_type(safe_filename)[0] or existing.mime_type
            extra_data = dict(existing.extra_data or {})
            extra_data["storage_repaired_at"] = datetime.utcnow().isoformat()
            existing.extra_data = extra_data
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
        return existing, False

    upload_dir = os.path.join(str(settings.UPLOAD_DIR), f"project_{project_id}")
    os.makedirs(upload_dir, exist_ok=True)
    stored_filename = f"{file_hash[:12]}_{safe_filename}"
    file_path = os.path.join(upload_dir, stored_filename)
    with open(file_path, "wb") as output:
        output.write(content)

    now = datetime.utcnow()
    extra_data = dict(metadata or {})
    ingestion = dict(extra_data.get("ingestion") or {})
    ingestion.update({
        "source": "unified_upload",
        "original_filename": safe_filename,
        "sha256": file_hash,
    })
    extra_data["ingestion"] = ingestion
    document = ProjectDocument(
        project_id=project_id,
        filename=stored_filename,
        original_filename=safe_filename,
        file_type=file_type,
        file_path=file_path,
        file_size=len(content),
        file_hash=file_hash,
        mime_type=mime_type or mimetypes.guess_type(safe_filename)[0] or "application/octet-stream",
        extra_data=extra_data,
        status=status,
        processing_progress=0,
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_hash == file_hash,
        ).first()
        if existing:
            return existing, False
        raise

    project.document_count = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).count()
    project.updated_at = now
    project.last_activity_at = now
    db.commit()
    db.refresh(document)
    return document, True


def is_retryable_document(document: ProjectDocument) -> bool:
    """判断重复文件是否需要重新进入主处理链路。

    同哈希的已完成文件仍然去重；只有上次处理失败或因解析能力不足进入
    review_needed 的记录才允许再次上传时自动重试，避免生成第二份文件记录。
    """
    if not document or document.status not in {"failed", "review_needed"}:
        return False
    extra_data = document.extra_data or {}
    extraction_status = extra_data.get("extraction_status")
    return document.status == "failed" or extraction_status in {"failed", "empty"}


def prepare_document_retry(db: Session, document: ProjectDocument) -> None:
    """重置可重试文档，保留历史资产和错误信息以便审计。"""
    if not is_retryable_document(document):
        return

    extra_data = dict(document.extra_data or {})
    retry_count = int(extra_data.get("retry_count") or 0) + 1
    extra_data["retry_count"] = retry_count
    extra_data["last_retry_at"] = datetime.utcnow().isoformat()
    extra_data.pop("extraction_error", None)
    extra_data.pop("pipeline_error", None)
    extra_data.pop("error", None)
    document.extra_data = extra_data
    document.status = "pending"
    document.processing_progress = 0
    document.error_message = None
    document.processed_at = None
    document.updated_at = datetime.utcnow()
    db.commit()



# ==================== WorkflowEngine 包装类 ====================

class ProjectDocumentUploadWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_classify_file(self, filename: str, _context: dict) -> dict:
        """任务: 分类项目文件"""
        mime_type = _context.get('mime_type')
        file_type = classify_project_file(filename, mime_type)
        return {"file_type": file_type}

    def _task_upload_document(self, _context: dict) -> dict:
        """任务: 上传项目文档"""
        db = _context.get('db')
        project_id = _context.get('project_id')
        original_filename = _context.get('original_filename')
        content = _context.get('content')
        mime_type = _context.get('mime_type')
        metadata = _context.get('metadata')
        status = _context.get('status', 'pending')

        document, created = upload_project_document(
            db, project_id, original_filename, content, mime_type, metadata, status
        )
        return {
            "document_id": document.id,
            "created": created,
            "file_path": document.file_path,
            "file_type": document.file_type
        }

    def classify_file_workflow(self, filename: str, mime_type: Optional[str] = None) -> str:
        """工作流: 使用 WorkflowEngine 分类文件"""
        if not self.use_workflow_engine:
            return classify_project_file(filename, mime_type)

        tasks = {
            "classify": {
                "function": self._task_classify_file,
                "args": {"filename": filename},
                "context": {"mime_type": mime_type}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["classify"]["file_type"]

    def upload_document_workflow(self, db: Session, project_id: int, original_filename: str,
                                 content: bytes, mime_type: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None,
                                 status: str = "pending") -> Tuple[int, bool]:
        """工作流: 使用 WorkflowEngine 上传文档"""
        if not self.use_workflow_engine:
            doc, created = upload_project_document(db, project_id, original_filename, content, mime_type, metadata, status)
            return (doc.id, created)

        tasks = {
            "upload": {
                "function": self._task_upload_document,
                "args": {},
                "context": {
                    "db": db,
                    "project_id": project_id,
                    "original_filename": original_filename,
                    "content": content,
                    "mime_type": mime_type,
                    "metadata": metadata,
                    "status": status
                }
            }
        }

        results = self.workflow_engine.execute(tasks)
        return (results["upload"]["document_id"], results["upload"]["created"])
