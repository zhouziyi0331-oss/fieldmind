"""项目文档上传和管理API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
import hashlib
import logging

from app.core.database import get_db
from app.models.project import Project, ProjectDocument
from app.schemas.project import ProjectDocumentResponse
from app.services.memory_service import MemoryService
from app.tools.document import create_converter

router = APIRouter()
logger = logging.getLogger(__name__)

# 创建文档转换器实例
document_converter = create_converter()

# 文件上传目录
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/fieldmind_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

    # 验证文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()

    # Check if file is audio or supported document format
    audio_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
    is_audio = file_ext in audio_formats

    if not is_audio and not document_converter.is_supported(file.filename):
        allowed_extensions = document_converter.supported_formats() + audio_formats
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. 支持: {', '.join(allowed_extensions)}"
        )

    try:
        # 读取文件内容
        content = await file.read()
        file_size = len(content)

        # 计算文件哈希
        file_hash = hashlib.md5(content).hexdigest()

        # 检查是否已上传
        existing = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.file_path.contains(file_hash)
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="文档已存在")

        # 保存文件
        project_dir = os.path.join(UPLOAD_DIR, f"project_{project_id}")
        os.makedirs(project_dir, exist_ok=True)

        filename = f"{file_hash}_{file.filename}"
        file_path = os.path.join(project_dir, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # 创建文档记录
        document = ProjectDocument(
            project_id=project_id,
            filename=filename,
            original_filename=file.filename,
            file_type=file_ext.lstrip('.'),
            file_path=file_path,
            file_size=file_size,
            status="pending",
            processing_progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(document)

        # 更新项目文档计数
        project.document_count += 1
        project.updated_at = datetime.utcnow()
        project.last_activity_at = datetime.utcnow()

        db.commit()
        db.refresh(document)

        # Submit document to background processing pipeline
        from app.services.background_tasks import submit_task
        submit_task(document.id)
        logger.info(f"文档 {document.id} 已提交后台处理")

        return document

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.post("/{project_id}/documents/{document_id}/process")
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
        raise HTTPException(status_code=404, detail="文档不存在")

    if document.status == "completed":
        return {"status": "already_completed", "document_id": document_id}

    try:
        # 更新状态
        document.status = "processing"
        document.processing_progress = 10
        db.commit()

        # TODO: 实现文档处理逻辑
        # 1. 提取文本内容
        # 2. 分块
        # 3. 向量化
        # 4. 提取实体和关键词
        # 5. 生成摘要

        # 模拟处理
        document.status = "completed"
        document.processing_progress = 100
        document.chunk_count = 10
        document.word_count = 5000
        document.summary = f"这是文档 {document.original_filename} 的自动生成摘要。"
        document.keywords = ["关键词1", "关键词2", "关键词3"]
        document.updated_at = datetime.utcnow()

        db.commit()

        # 提取记忆
        memory_service = MemoryService(db, project_id)
        await memory_service.extract_from_document(document_id)

        return {
            "status": "success",
            "document_id": document_id,
            "processing_status": document.status
        }

    except Exception as e:
        document.status = "failed"
        document.updated_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


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


@router.get("/{project_id}/documents/{document_id}/content")
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
        raise HTTPException(status_code=404, detail="文档不存在")

    try:
        if document.text_content:
            return {
                "document_id": document_id,
                "filename": document.original_filename,
                "content": document.text_content,
                "word_count": document.word_count
            }
        else:
            # 读取文件
            if not os.path.exists(document.file_path):
                raise HTTPException(status_code=404, detail="文件不存在")

            with open(document.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "document_id": document_id,
                "filename": document.original_filename,
                "content": content,
                "word_count": len(content)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文档失败: {str(e)}")
