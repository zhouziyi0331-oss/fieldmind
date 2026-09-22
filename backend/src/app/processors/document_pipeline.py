"""
文档处理管线
完整的文档处理流程：下载 → 提取 → 分块 → 生成向量 → 存储
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.logging import logger, log_document_processing
from app.core.storage import ObjectStorage
from app.core.vector_store import VectorStore
from app.core.database import get_db_session
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.processors.document_extractor import DocumentExtractor
from app.processors.text_chunker import TextChunker
from app.processors.vector_generator import get_vector_generator
from app.core.exceptions import DocumentProcessingException


class DocumentPipeline:
    """文档处理管线"""

    def __init__(
        self,
        storage: ObjectStorage,
        vector_store: VectorStore,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        初始化文档处理管线

        Args:
            storage: 对象存储
            vector_store: 向量存储
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
        """
        self.storage = storage
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 初始化处理器
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.vector_generator = get_vector_generator()

    def process(self, document_id: str) -> Dict[str, Any]:
        """
        处理文档（完整流程）

        流程:
        1. 从对象存储下载文件
        2. 提取文本内容
        3. 文本分块
        4. 生成向量
        5. 存储分块和向量
        6. 更新文档状态

        Args:
            document_id: 文档ID

        Returns:
            Dict: 处理结果
        """
        start_time = time.time()

        logger.info(f"开始处理文档: {document_id}")

        db = get_db_session()

        try:
            # 1. 获取文档记录
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                raise DocumentProcessingException(
                    message=f"Document not found: {document_id}"
                )

            # 2. 下载文件
            temp_file = self._download_file(document)

            log_document_processing(
                document_id=document_id,
                operation="download",
                status="completed"
            )

            # 3. 提取内容
            extraction_result = DocumentExtractor.extract(
                file_path=temp_file,
                mime_type=document.mime_type
            )

            text_content = extraction_result["text"]
            metadata = extraction_result["metadata"]

            log_document_processing(
                document_id=document_id,
                operation="extract",
                status="completed",
                details={
                    "word_count": extraction_result["word_count"],
                    "pages": extraction_result.get("pages")
                }
            )

            # 4. 文本分块
            chunks = self.chunker.chunk(
                text=text_content,
                metadata=metadata
            )

            log_document_processing(
                document_id=document_id,
                operation="chunk",
                status="completed",
                details={"chunk_count": len(chunks)}
            )

            # 5. 生成向量
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.vector_generator.generate(chunk_texts)

            log_document_processing(
                document_id=document_id,
                operation="embed",
                status="completed",
                details={"vector_count": len(embeddings)}
            )

            # 6. 保存分块和向量
            self._save_chunks_and_vectors(
                db=db,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings
            )

            # 7. 更新文档状态
            from datetime import datetime
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.utcnow()
            db.commit()

            # 8. 清理临时文件
            os.remove(temp_file)

            duration = time.time() - start_time

            log_document_processing(
                document_id=document_id,
                operation="process_complete",
                status="completed",
                duration=duration,
                details={
                    "chunks": len(chunks),
                    "vectors": len(embeddings)
                }
            )

            return {
                "document_id": document_id,
                "status": "processed",
                "chunks": len(chunks),
                "vectors": len(embeddings),
                "duration": duration
            }

        except Exception as e:
            logger.error(f"文档处理失败: {e}", document_id=document_id)

            # 更新文档状态为失败
            if document:
                document.status = DocumentStatus.FAILED
                db.commit()

            log_document_processing(
                document_id=document_id,
                operation="process",
                status="failed",
                details={"error": str(e)}
            )

            raise

        finally:
            db.close()

    def _download_file(self, document: Document) -> str:
        """
        从对象存储下载文件

        Args:
            document: 文档对象

        Returns:
            str: 临时文件路径
        """
        # 解析存储路径
        bucket, object_name = document.storage_path.split("/", 1)

        # 创建临时目录
        temp_dir = Path("/tmp/fieldmind/downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 生成临时文件路径
        temp_file = temp_dir / f"{document.id}_{document.name}"

        # 下载文件
        success = self.storage.download_file(
            bucket=bucket,
            object_name=object_name,
            file_path=str(temp_file)
        )

        if not success:
            raise DocumentProcessingException(
                message=f"Failed to download file: {document.storage_path}"
            )

        return str(temp_file)

    def _save_chunks_and_vectors(
        self,
        db,
        document_id: str,
        chunks,
        embeddings
    ):
        """
        保存分块和向量

        Args:
            db: 数据库会话
            document_id: 文档ID
            chunks: 文本块列表
            embeddings: 向量列表
        """
        from app.core.database import generate_id

        # 保存分块到数据库
        for i, chunk in enumerate(chunks):
            chunk_id = generate_id("chunk")

            # 创建分块记录
            chunk_record = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                content=chunk.content,
                sequence=chunk.sequence,
                token_count=chunk.token_count,
                metadata=chunk.metadata
            )

            db.add(chunk_record)

            # 保存向量
            if i < len(embeddings):
                self.vector_store.insert_vector(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    embedding=embeddings[i]
                )

        db.commit()

        logger.info(
            f"保存分块和向量: {len(chunks)} 个分块",
            document_id=document_id
        )
