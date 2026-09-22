"""
文档处理流水线 v2 - 链路十四+十五完整实现
从上传到存储的完整链路，确保每一步都携带完整元数据
链路15新增：时间抽取和标准化
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.document_metadata import (
    DocumentMetadata,
    ChunkMetadata,
    create_metadata_from_upload,
    DocumentType,
    SourceLevel
)
from app.services.document_chunker_v2 import get_document_chunker_v2
from app.services.vectorization_service_complete import VectorizationService
from app.services.temporal_extractor import get_temporal_extractor
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)


class DocumentProcessingPipelineV2:
    """文档处理流水线 v2 - 元数据完整版（含时间抽取）"""

    def __init__(self, db: Session):
        self.db = db
        self.chunker = get_document_chunker_v2()
        self.vectorizer = get_vectorization_service_v2()
        self.temporal_extractor = get_temporal_extractor()  # 链路15：时间抽取器

    def process_document(
        self,
        document_id: int,
        text: str,
        filename: str,
        file_type: str,
        project_id: Optional[int] = None,
        page_number: Optional[int] = None,
        timestamp_start: Optional[float] = None,
        timestamp_end: Optional[float] = None,
        speaker: Optional[str] = None,
        document_date: Optional[datetime] = None,
        source_level: SourceLevel = SourceLevel.RAW_MATERIAL,
        tags: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        完整的文档处理流程（链路十四+十五）

        流程：
        1. 时间抽取（链路15）- 从文本和文件名提取日期
        2. 创建文档元数据（包含提取的日期）
        3. 切分文档为chunks（继承元数据）
        4. 向量化并存储到ChromaDB（元数据完整入库）
        5. 更新数据库记录

        Args:
            document_id: 文档ID
            text: 文档文本内容
            filename: 文件名
            file_type: 文件类型（pdf/docx/audio等）
            project_id: 项目ID
            page_number: 页码（PDF/DOCX）
            timestamp_start: 开始时间戳（音频/视频）
            timestamp_end: 结束时间戳（音频/视频）
            speaker: 说话人（音频）
            document_date: 文档日期（如果已知）
            source_level: 来源层级（原始材料/一度报告/二度报告/三度报告）
            tags: 标签列表

        Returns:
            处理结果统计
        """
        logger.info(f"📄 开始处理文档: {filename} (ID={document_id})")

        try:
            # ========== 步骤1：时间抽取（链路15新增） ==========
            extracted_dates = []
            if not document_date:
                # 如果没有提供文档日期，尝试自动提取
                document_date = self.temporal_extractor.extract_document_date(
                    text=text,
                    filename=filename,
                    upload_time=datetime.now()
                )
                logger.info(f"  📅 自动提取文档日期: {document_date.strftime('%Y-%m-%d') if document_date else 'None'}")

            # 从文本中提取所有时间点
            date_extractions = self.temporal_extractor.extract_dates(
                text=text,
                document_date=document_date
            )

            # 只保留高置信度的日期（>= 0.7）
            extracted_dates = [
                d["date_iso"]
                for d in date_extractions
                if d["confidence"] >= 0.7
            ]

            if extracted_dates:
                logger.info(f"  📅 提取到 {len(extracted_dates)} 个时间点: {extracted_dates[:3]}{'...' if len(extracted_dates) > 3 else ''}")

            # ========== 步骤2：创建文档元数据 ==========
            document_metadata = create_metadata_from_upload(
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                project_id=project_id,
                page_number=page_number,
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                speaker=speaker,
                document_date=document_date,
                source_level=source_level,
                tags=tags or [],
                extracted_dates=extracted_dates,  # 链路15：传入提取的日期
                **kwargs
            )

            logger.info(f"  ✅ 元数据创建完成: type={document_metadata.document_type.value}, level={document_metadata.source_level.value}")

            # 验证元数据
            errors = document_metadata.validate()
            if errors:
                logger.warning(f"  ⚠️ 元数据验证警告: {', '.join(errors)}")

            # ========== 步骤2：文档切分 ==========
            chunks = self.chunker.chunk_document(text, document_metadata)

            if not chunks:
                logger.warning(f"  ⚠️ 文档切分结果为空")
                return {
                    "success": False,
                    "error": "文档切分失败，无有效内容",
                    "document_id": document_id
                }

            logger.info(f"  ✅ 文档切分完成: {len(chunks)} 个chunks")

            # 将文本内容添加到每个chunk的custom_fields
            text_chunks = self._split_text_for_chunks(text, chunks)
            for chunk, chunk_text in zip(chunks, text_chunks):
                chunk.custom_fields["text"] = chunk_text

            # ========== 步骤3：向量化并存储 ==========
            vectorization_result = self.vectorizer.vectorize_chunks(chunks)

            if not vectorization_result.get("success"):
                logger.error(f"  ❌ 向量化失败")
                return {
                    "success": False,
                    "error": "向量化失败",
                    "document_id": document_id
                }

            logger.info(f"  ✅ 向量化完成: 存储了 {vectorization_result['stored_count']} 个chunks")

            # ========== 步骤4：更新数据库记录 ==========
            self._update_document_record(
                document_id,
                project_id,
                len(chunks),
                vectorization_result['stored_count']
            )

            logger.info(f"✅ 文档处理完成: {filename}")

            return {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "total_chunks": len(chunks),
                "stored_chunks": vectorization_result['stored_count'],
                "failed_chunks": vectorization_result.get('failed_count', 0),
                "document_type": document_metadata.document_type.value,
                "source_level": document_metadata.source_level.value,
                "citation_format": document_metadata.format_citation()
            }

        except Exception as e:
            logger.error(f"❌ 文档处理失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }

    def _split_text_for_chunks(
        self,
        full_text: str,
        chunks: list
    ) -> list:
        """
        根据chunks的char_start和char_end提取实际文本
        """
        text_chunks = []
        for chunk in chunks:
            start = chunk.char_start
            end = chunk.char_end
            chunk_text = full_text[start:end]
            text_chunks.append(chunk_text)
        return text_chunks

    def _update_document_record(
        self,
        document_id: int,
        project_id: Optional[int],
        total_chunks: int,
        stored_chunks: int
    ):
        """更新数据库中的文档记录"""
        try:
            if project_id:
                # 更新ProjectDocument表
                doc = self.db.query(ProjectDocument).filter(
                    ProjectDocument.id == document_id,
                    ProjectDocument.project_id == project_id
                ).first()

                if doc:
                    doc.status = "completed"
                    doc.chunk_count = stored_chunks
                    doc.processed_at = datetime.utcnow()
                    self.db.commit()
                    logger.debug(f"  ✅ 更新数据库记录: chunk_count={stored_chunks}")
            else:
                logger.warning(f"  ⚠️ 未提供project_id，跳过数据库更新")

        except Exception as e:
            logger.error(f"  ❌ 更新数据库失败: {e}")


def get_document_processing_pipeline_v2(db: Session) -> DocumentProcessingPipelineV2:
    """获取文档处理流水线实例"""
    return DocumentProcessingPipelineV2(db)
