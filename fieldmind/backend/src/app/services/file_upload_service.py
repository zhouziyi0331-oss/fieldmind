"""
文件批量上传服务 (File Upload Service)
支持一次上传 50+ 个文件，自动排队处理
"""
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
from pathlib import Path
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUploadService:
    """
    批量文件上传服务

    功能：
    1. 批量接收文件
    2. 文件队列管理
    3. 自动触发后台处理
    4. 进度追踪
    """

    def __init__(self):
        self.upload_queue = []
        self.processing_tasks = {}

    async def upload_batch(
        self,
        files: List[UploadFile],
        project_id: int,
        user_id: int,
        db
    ) -> Dict[str, Any]:
        """
        批量上传文件

        Args:
            files: 文件列表
            project_id: 项目 ID
            user_id: 用户 ID
            db: 数据库会话

        Returns:
            {
                "total": int,
                "success": int,
                "failed": int,
                "documents": [
                    {
                        "id": int,
                        "filename": str,
                        "status": str
                    }
                ]
            }
        """
        from app.models.project import ProjectDocument
        from app.services.file_storage import save_upload_file

        total = len(files)
        success_count = 0
        failed_count = 0
        documents = []

        logger.info(f"开始批量上传 {total} 个文件到项目 {project_id}")

        for i, file in enumerate(files):
            try:
                # 1. 保存文件到存储
                file_path = await save_upload_file(file, project_id)

                # 2. 获取文件信息
                file_size = 0
                if hasattr(file, 'file'):
                    file.file.seek(0, 2)  # 移到文件末尾
                    file_size = file.file.tell()
                    file.file.seek(0)  # 重置到开头

                # 3. 创建文档记录
                doc = ProjectDocument(
                    project_id=project_id,
                    user_id=user_id,
                    original_filename=file.filename,
                    file_path=str(file_path),
                    file_type=self._get_file_type(file.filename),
                    file_size=file_size,
                    status="pending",
                    upload_time=datetime.now(),
                )

                db.add(doc)
                db.flush()  # 获取 ID

                documents.append({
                    "id": doc.id,
                    "filename": file.filename,
                    "status": "pending",
                    "order": i + 1,
                })

                success_count += 1

                # 4. 自动触发后台处理
                self._trigger_background_processing(doc.id)

                logger.info(f"文件上传成功 [{i+1}/{total}]: {file.filename} (ID: {doc.id})")

            except Exception as e:
                failed_count += 1
                logger.error(f"文件上传失败 [{i+1}/{total}]: {file.filename}, 错误: {e}")

                documents.append({
                    "id": None,
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e),
                    "order": i + 1,
                })

        # 提交所有成功的文档
        db.commit()

        logger.info(f"批量上传完成：总数 {total}, 成功 {success_count}, 失败 {failed_count}")

        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "documents": documents,
        }

    def _get_file_type(self, filename: str) -> str:
        """根据文件名获取文件类型"""
        ext = Path(filename).suffix.lower()

        type_map = {
            '.pdf': 'pdf',
            '.doc': 'word',
            '.docx': 'word',
            '.txt': 'text',
            '.md': 'markdown',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.mp3': 'audio',
            '.wav': 'audio',
            '.m4a': 'audio',
            '.mp4': 'video',
            '.mov': 'video',
            '.xls': 'excel',
            '.xlsx': 'excel',
        }

        return type_map.get(ext, 'unknown')

    def _trigger_background_processing(self, document_id: int):
        """
        触发后台处理
        使用 Celery 或后台任务队列
        """
        try:
            from app.services.background_tasks import process_document_async

            # 触发异步任务
            process_document_async.delay(document_id)

            logger.info(f"文档 {document_id} 已加入处理队列")

        except Exception as e:
            logger.error(f"触发后台处理失败 (文档 {document_id}): {e}")

    def get_upload_progress(self, project_id: int, db) -> Dict[str, Any]:
        """
        获取上传进度

        Returns:
            {
                "total": int,
                "pending": int,
                "processing": int,
                "completed": int,
                "failed": int
            }
        """
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }

        for doc in documents:
            status = doc.status or "pending"
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total": len(documents),
            **status_counts
        }


# 全局实例
file_upload_service = FileUploadService()
