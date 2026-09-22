"""
文件上传服务
统一的文件上传入口
"""

import os
import hashlib
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
from pathlib import Path

from app.core.storage import ObjectStorage
from app.core.exceptions import (
    ValidationException,
    StorageException,
    DocumentProcessingException
)
from app.core.errors import ErrorCode
from app.core.logging import logger, log_document_processing, log_storage_operation
from app.models.document import Document, DocumentType, DocumentStatus
from app.schemas.document import DocumentUploadRequest, DocumentUploadResponse


class FileUploadService:
    """文件上传服务"""

    # 支持的文件类型
    SUPPORTED_TYPES = {
        # 文档
        "application/pdf": DocumentType.DOCUMENT,
        "application/msword": DocumentType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCUMENT,
        "text/plain": DocumentType.DOCUMENT,
        "text/markdown": DocumentType.DOCUMENT,

        # 图片
        "image/jpeg": DocumentType.IMAGE,
        "image/png": DocumentType.IMAGE,
        "image/gif": DocumentType.IMAGE,
        "image/webp": DocumentType.IMAGE,
        "image/svg+xml": DocumentType.IMAGE,

        # 音频
        "audio/mpeg": DocumentType.AUDIO,
        "audio/wav": DocumentType.AUDIO,
        "audio/mp4": DocumentType.AUDIO,
        "audio/ogg": DocumentType.AUDIO,
        "audio/webm": DocumentType.AUDIO,

        # 视频
        "video/mp4": DocumentType.VIDEO,
        "video/mpeg": DocumentType.VIDEO,
        "video/quicktime": DocumentType.VIDEO,
        "video/x-msvideo": DocumentType.VIDEO,
        "video/webm": DocumentType.VIDEO,

        # 表格
        "application/vnd.ms-excel": DocumentType.TABLE,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.TABLE,
        "text/csv": DocumentType.TABLE,
    }

    # 文件大小限制（字节）
    MAX_FILE_SIZE = {
        DocumentType.DOCUMENT: 100 * 1024 * 1024,  # 100 MB
        DocumentType.IMAGE: 50 * 1024 * 1024,      # 50 MB
        DocumentType.AUDIO: 500 * 1024 * 1024,     # 500 MB
        DocumentType.VIDEO: 2 * 1024 * 1024 * 1024, # 2 GB
        DocumentType.TABLE: 100 * 1024 * 1024,     # 100 MB
    }

    def __init__(self, storage: ObjectStorage, db_session):
        """
        初始化上传服务

        Args:
            storage: 对象存储客户端
            db_session: 数据库会话
        """
        self.storage = storage
        self.db = db_session

    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        project_id: int,
        mime_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        上传文件（统一入口）

        Args:
            file: 文件对象
            filename: 文件名
            project_id: 项目ID
            mime_type: MIME类型
            user_id: 用户ID
            metadata: 额外元数据

        Returns:
            Document: 文档对象

        Raises:
            ValidationException: 验证失败
            StorageException: 存储失败
        """
        logger.info(f"开始上传文件: {filename}", project_id=project_id, mime_type=mime_type)

        try:
            # 1. 验证文件
            self._validate_file(file, filename, mime_type)

            # 2. 检测文件类型
            doc_type = self._classify_file(mime_type, filename)

            # 3. 计算文件哈希
            file_hash, file_size = self._calculate_hash_and_size(file)
            file.seek(0)  # 重置文件指针

            # 4. 检查重复
            existing_doc = self._check_duplicate(project_id, file_hash)
            if existing_doc:
                logger.info(f"文件已存在: {existing_doc.id}", file_hash=file_hash)
                return existing_doc

            # 5. 生成存储路径
            storage_path = self._generate_storage_path(
                project_id=project_id,
                doc_type=doc_type,
                filename=filename,
                file_hash=file_hash
            )

            # 6. 上传到对象存储
            bucket = self._get_bucket_for_type(doc_type)
            success = self._upload_to_storage(
                bucket=bucket,
                object_name=storage_path,
                file=file,
                mime_type=mime_type
            )

            if not success:
                raise StorageException(
                    error_code=ErrorCode.STORAGE_UPLOAD_FAILED,
                    message=f"Failed to upload file to storage"
                )

            # 7. 创建数据库记录
            document = self._create_document_record(
                project_id=project_id,
                filename=filename,
                doc_type=doc_type,
                mime_type=mime_type,
                file_size=file_size,
                file_hash=file_hash,
                storage_path=f"{bucket}/{storage_path}",
                user_id=user_id,
                metadata=metadata
            )

            log_document_processing(
                document_id=document.id,
                operation="upload",
                status="completed",
                details={
                    "filename": filename,
                    "size": file_size,
                    "type": doc_type.value
                }
            )

            logger.info(f"文件上传成功: {document.id}", document_id=document.id)

            return document

        except Exception as e:
            log_document_processing(
                document_id="unknown",
                operation="upload",
                status="failed",
                details={"filename": filename, "error": str(e)}
            )
            raise

    def _validate_file(self, file: BinaryIO, filename: str, mime_type: str):
        """
        验证文件

        Args:
            file: 文件对象
            filename: 文件名
            mime_type: MIME类型

        Raises:
            ValidationException: 验证失败
        """
        # 检查文件名
        if not filename or len(filename) > 255:
            raise ValidationException(
                message="Invalid filename",
                field="filename",
                details={"filename": filename}
            )

        # 检查MIME类型
        if mime_type not in self.SUPPORTED_TYPES:
            raise ValidationException(
                message=f"Unsupported file type: {mime_type}",
                field="mime_type",
                details={
                    "mime_type": mime_type,
                    "supported_types": list(self.SUPPORTED_TYPES.keys())
                }
            )

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        doc_type = self.SUPPORTED_TYPES[mime_type]
        max_size = self.MAX_FILE_SIZE.get(doc_type, 100 * 1024 * 1024)

        if file_size == 0:
            raise ValidationException(
                message="File is empty",
                field="file",
                details={"filename": filename}
            )

        if file_size > max_size:
            raise ValidationException(
                message=f"File size exceeds limit ({max_size / 1024 / 1024:.1f} MB)",
                field="file",
                details={
                    "filename": filename,
                    "size": file_size,
                    "max_size": max_size
                }
            )

    def _classify_file(self, mime_type: str, filename: str) -> DocumentType:
        """
        分类文件类型

        Args:
            mime_type: MIME类型
            filename: 文件名

        Returns:
            DocumentType: 文档类型
        """
        return self.SUPPORTED_TYPES.get(mime_type, DocumentType.OTHER)

    def _calculate_hash_and_size(self, file: BinaryIO) -> tuple[str, int]:
        """
        计算文件哈希和大小

        Args:
            file: 文件对象

        Returns:
            tuple: (哈希值, 文件大小)
        """
        sha256 = hashlib.sha256()
        file_size = 0

        file.seek(0)
        while chunk := file.read(8192):
            sha256.update(chunk)
            file_size += len(chunk)

        return sha256.hexdigest(), file_size

    def _check_duplicate(self, project_id: int, file_hash: str) -> Optional[Document]:
        """
        检查重复文件

        Args:
            project_id: 项目ID
            file_hash: 文件哈希

        Returns:
            Optional[Document]: 已存在的文档（如果有）
        """
        return self.db.query(Document).filter(
            Document.project_id == project_id,
            Document.hash == file_hash
        ).first()

    def _generate_storage_path(
        self,
        project_id: int,
        doc_type: DocumentType,
        filename: str,
        file_hash: str
    ) -> str:
        """
        生成存储路径

        Args:
            project_id: 项目ID
            doc_type: 文档类型
            filename: 文件名
            file_hash: 文件哈希

        Returns:
            str: 存储路径
        """
        # 格式: projects/{project_id}/{type}/{date}/{hash[:8]}/{filename}
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        hash_prefix = file_hash[:8]

        # 清理文件名（移除特殊字符）
        clean_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")

        return f"projects/{project_id}/{doc_type.value}/{date_path}/{hash_prefix}/{clean_filename}"

    def _get_bucket_for_type(self, doc_type: DocumentType) -> str:
        """
        获取文档类型对应的存储桶

        Args:
            doc_type: 文档类型

        Returns:
            str: 存储桶名称
        """
        bucket_map = {
            DocumentType.DOCUMENT: "documents",
            DocumentType.IMAGE: "images",
            DocumentType.AUDIO: "audio",
            DocumentType.VIDEO: "video",
            DocumentType.TABLE: "tables",
            DocumentType.OTHER: "documents"
        }

        return bucket_map.get(doc_type, "documents")

    def _upload_to_storage(
        self,
        bucket: str,
        object_name: str,
        file: BinaryIO,
        mime_type: str
    ) -> bool:
        """
        上传文件到对象存储

        Args:
            bucket: 存储桶
            object_name: 对象名称
            file: 文件对象
            mime_type: MIME类型

        Returns:
            bool: 是否成功
        """
        import time

        start_time = time.time()

        try:
            # 读取文件数据
            file.seek(0)
            data = file.read()

            # 上传
            success = self.storage.upload_data(
                bucket=bucket,
                object_name=object_name,
                data=data,
                content_type=mime_type
            )

            duration = time.time() - start_time

            log_storage_operation(
                operation="upload",
                bucket=bucket,
                object_name=object_name,
                size=len(data),
                duration=duration,
                success=success
            )

            return success

        except Exception as e:
            logger.error(f"存储上传失败: {e}", bucket=bucket, object_name=object_name)
            return False

    def _create_document_record(
        self,
        project_id: int,
        filename: str,
        doc_type: DocumentType,
        mime_type: str,
        file_size: int,
        file_hash: str,
        storage_path: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        创建文档记录

        Args:
            project_id: 项目ID
            filename: 文件名
            doc_type: 文档类型
            mime_type: MIME类型
            file_size: 文件大小
            file_hash: 文件哈希
            storage_path: 存储路径
            user_id: 用户ID
            metadata: 额外元数据

        Returns:
            Document: 文档对象
        """
        from app.core.database import generate_id

        document = Document(
            id=generate_id("doc"),
            project_id=project_id,
            name=filename,
            type=doc_type,
            mime_type=mime_type,
            size=file_size,
            hash=file_hash,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_download_url(
        self,
        document_id: str,
        expires: int = 3600
    ) -> str:
        """
        获取文件下载URL

        Args:
            document_id: 文档ID
            expires: 过期时间（秒）

        Returns:
            str: 预签名URL

        Raises:
            DocumentNotFoundException: 文档不存在
        """
        from app.core.exceptions import DocumentNotFoundException

        document = self.db.query(Document).filter(
            Document.id == document_id
        ).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 解析存储路径
        bucket, object_name = document.storage_path.split("/", 1)

        # 生成预签名URL
        url = self.storage.get_presigned_url(
            bucket=bucket,
            object_name=object_name,
            expires=expires
        )

        return url
