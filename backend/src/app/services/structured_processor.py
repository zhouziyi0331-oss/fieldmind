"""
结构化处理服务 - 核心3函数
将文件转换为可检索、可拼接、可溯源的结构化数据块
"""

import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from app.core.logging import logger, log_document_processing
from app.core.database import get_db_session, generate_id
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.processors.document_extractor import DocumentExtractor
from app.processors.image_processor import ImageProcessor
from app.processors.audio_processor import AudioProcessor
from app.processors.video_processor import VideoProcessor
from app.processors.table_processor import TableProcessor
from app.processors.text_chunker import TextChunker
from app.processors.vector_generator import get_vector_generator


class StructuredProcessor:
    """结构化处理器 - 实现核心3函数"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        self.vector_generator = get_vector_generator()

    # ============================================
    # 核心函数 1: 文件入库 + 切分
    # ============================================

    def process_uploaded_file(self, file_id: str) -> Dict[str, Any]:
        """
        函数 1: 文件入库 + 切分（数据治理增强版）

        输入: file_id
        做了什么:
        1. 根据 file_id 找到 files 表里的路径
        2. 根据 filetype 调用不同解析器（音频→Whisper，PDF→PyPDF2）
        3. 【新增】提取内容级元数据（字数、句数、段落数、语言）
        4. 把解析出来的纯文本按 200-500 字切分成 chunks
        5. 【新增】记录血缘关系（file → chunk）
        6. 把每个 chunk 插入 chunks 表（带溯源信息）
        7. 更新 files.status = 'done' + 处理耗时

        Args:
            file_id: 文档ID

        Returns:
            Dict: 处理结果
                {
                    "file_id": str,
                    "chunks_created": int,
                    "total_text_length": int,
                    "status": "success"
                }
        """
        start_time = time.time()

        logger.info(f"[核心函数1-治理增强] 开始处理文件: {file_id}")

        db = get_db_session()

        try:
            # 1. 获取文件记录
            document = db.query(Document).filter(Document.id == file_id).first()

            if not document:
                raise ValueError(f"Document not found: {file_id}")

            # 更新状态为处理中 + 记录开始时间
            document.status = DocumentStatus.PROCESSING
            document.processing_started = datetime.utcnow()
            db.commit()

            # 2. 下载文件到临时目录
            temp_file = self._download_file(document)

            # 3. 根据文件类型调用不同解析器
            extraction_result = self._extract_content(
                file_path=temp_file,
                mime_type=document.mime_type,
                doc_type=document.type.value
            )

            text_content = extraction_result["text"]
            metadata = extraction_result.get("metadata", {})

            # 【新增】4. 提取内容级元数据
            from app.services.metadata_collector import MetadataCollector
            content_metadata = MetadataCollector.extract_content_metadata(
                text=text_content,
                doc_type=document.type.value
            )

            # 更新文档的内容元数据
            document.total_words = content_metadata.get('total_words')
            document.total_sentences = content_metadata.get('total_sentences')
            document.total_paragraphs = content_metadata.get('total_paragraphs')
            document.language = content_metadata.get('language')
            document.speaker_count = content_metadata.get('speaker_count')
            db.commit()

            log_document_processing(
                document_id=file_id,
                operation="extract",
                status="completed",
                details={
                    "text_length": len(text_content),
                    "word_count": extraction_result.get("word_count", 0),
                    "total_words": content_metadata.get('total_words'),
                    "total_sentences": content_metadata.get('total_sentences')
                }
            )

            # 5. 文本切分成 chunks（200-500字）
            chunks = self.chunker.chunk(text=text_content, metadata=metadata)

            # 【新增】6. 记录血缘关系（file → chunk）并插入 chunks
            chunks_created = self._save_chunks_with_lineage(
                db=db,
                document=document,
                chunks=chunks,
                extraction_result=extraction_result
            )

            # 7. 更新文件状态 + 处理耗时
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.utcnow()
            document.processing_ended = datetime.utcnow()
            document.processing_duration = time.time() - start_time
            db.commit()

            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

            duration = time.time() - start_time

            result = {
                "file_id": file_id,
                "chunks_created": chunks_created,
                "total_text_length": len(text_content),
                "status": "success",
                "duration": duration
            }

            log_document_processing(
                document_id=file_id,
                operation="process_file",
                status="completed",
                duration=duration,
                details=result
            )

            logger.info(
                f"[核心函数1] 处理完成: {file_id}, "
                f"创建 {chunks_created} 个块, "
                f"耗时 {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"[核心函数1] 处理失败: {e}", file_id=file_id)

            if document:
                document.status = DocumentStatus.FAILED
                db.commit()

            raise

        finally:
            db.close()

    def _download_file(self, document: Document) -> str:
        """下载文件到临时目录"""
        from app.core.storage import get_storage

        storage = get_storage()

        # 解析存储路径
        bucket, object_name = document.storage_path.split("/", 1)

        # 临时目录
        temp_dir = Path("/tmp/fieldmind/processing")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir / f"{document.id}_{document.name}"

        # 下载
        storage.download_file(
            bucket=bucket,
            object_name=object_name,
            file_path=str(temp_file)
        )

        return str(temp_file)

    def _extract_content(
        self,
        file_path: str,
        mime_type: str,
        doc_type: str
    ) -> Dict[str, Any]:
        """
        根据文件类型提取内容（使用 IngestionAgent 统一入口）

        Args:
            file_path: 文件路径
            mime_type: MIME类型
            doc_type: 文档类型

        Returns:
            Dict: 提取结果
        """
        from app.agents.ingestion_agent import get_ingestion_agent
        from pathlib import Path

        # 使用 IngestionAgent 统一采集
        ingestion_agent = get_ingestion_agent()

        result = ingestion_agent.ingest_file(
            file_path=file_path,
            filename=Path(file_path).name,
            mime_type=mime_type,
            file_metadata=None
        )

        # 转换为旧格式（保持兼容性）
        return {
            "text": result["raw_text"],
            "metadata": result["structured_metadata"],
            "word_count": result["structured_metadata"].get("total_words", 0),
            "pages": result["structured_metadata"].get("pages"),
            "duration": result["structured_metadata"].get("duration")
        }

    def _save_chunks_with_lineage(
        self,
        db,
        document: Document,
        chunks,
        extraction_result: Dict[str, Any]
    ) -> int:
        """
        保存 chunks 到数据库（带溯源信息 + 血缘记录）

        Args:
            db: 数据库会话
            document: 文档对象
            chunks: 文本块列表
            extraction_result: 提取结果

        Returns:
            int: 保存的块数量
        """
        from app.services.lineage_tracker import LineageTracker

        # 提取溯源信息
        pages = extraction_result.get("pages")
        duration = extraction_result.get("duration")

        for chunk in chunks:
            chunk_id = generate_id("chunk")

            # 构建 chunk 记录
            chunk_record = DocumentChunk(
                id=chunk_id,
                document_id=document.id,
                project_id=document.project_id,
                chunk_index=chunk.sequence,
                text=chunk.content,
                token_count=chunk.token_count,
                start_pos=chunk.start_index,
                end_pos=chunk.end_index,
                metadata=chunk.metadata
            )

            # 添加溯源信息（根据文件类型）
            if pages and chunk.sequence < pages:
                chunk_record.page_number = chunk.sequence + 1

            if duration and document.type.value in ["audio", "video"]:
                # 估算时间戳（均匀分配）
                chunk_duration = duration / len(chunks)
                chunk_record.timestamp_start = int(chunk.sequence * chunk_duration)
                chunk_record.timestamp_end = int((chunk.sequence + 1) * chunk_duration)
                chunk_record.duration_seconds = chunk_duration

            # 说话人（如果有）
            if "speaker" in chunk.metadata:
                chunk_record.speaker = chunk.metadata["speaker"]

            db.add(chunk_record)

            # 【新增】记录血缘关系：file → chunk
            LineageTracker.record_lineage(
                project_id=document.project_id,
                source_type="file",
                source_id=document.id,
                target_type="chunk",
                target_id=chunk_id,
                transform_type="extract",
                transform_description=f"从文档提取第 {chunk.sequence} 个文本块",
                confidence=1.0
            )

        db.commit()

        logger.info(
            f"保存chunks+血缘记录完成: {len(chunks)} 个块",
            document_id=document.id
        )

        return len(chunks)

    # ============================================
    # 核心函数 2: 向量化
    # ============================================

    def vectorize_chunks(self, project_id: int) -> Dict[str, Any]:
        """
        函数 2: 向量化

        输入: project_id
        做了什么:
        1. 查出该项目所有 embedding 为空的 chunks
        2. 调用 Sentence-BERT/OpenAI 转成向量
        3. 更新到向量数据库

        Args:
            project_id: 项目ID

        Returns:
            Dict: 向量化结果
                {
                    "project_id": int,
                    "chunks_vectorized": int,
                    "status": "success"
                }
        """
        start_time = time.time()

        logger.info(f"[核心函数2] 开始向量化: project_id={project_id}")

        db = get_db_session()

        try:
            # 1. 查询该项目所有未向量化的 chunks
            from app.core.vector_store import get_vector_store
            vector_store = get_vector_store()

            # 获取所有 chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project_id
            ).all()

            if not chunks:
                logger.warning(f"项目 {project_id} 没有 chunks")
                return {
                    "project_id": project_id,
                    "chunks_vectorized": 0,
                    "status": "no_chunks"
                }

            # 2. 筛选出未向量化的（检查向量库）
            chunks_to_vectorize = []
            for chunk in chunks:
                if not vector_store.vector_exists(chunk.id):
                    chunks_to_vectorize.append(chunk)

            if not chunks_to_vectorize:
                logger.info(f"项目 {project_id} 所有 chunks 已向量化")
                return {
                    "project_id": project_id,
                    "chunks_vectorized": 0,
                    "status": "already_done"
                }

            logger.info(f"需要向量化 {len(chunks_to_vectorize)} 个 chunks")

            # 3. 批量生成向量
            texts = [chunk.text for chunk in chunks_to_vectorize]
            embeddings = self.vector_generator.generate(texts, batch_size=100)

            # 4. 保存到向量数据库
            for i, chunk in enumerate(chunks_to_vectorize):
                if i < len(embeddings):
                    vector_store.insert_vector(
                        document_id=chunk.document_id,
                        chunk_id=chunk.id,
                        embedding=embeddings[i]
                    )

            duration = time.time() - start_time

            result = {
                "project_id": project_id,
                "chunks_vectorized": len(chunks_to_vectorize),
                "status": "success",
                "duration": duration
            }

            logger.info(
                f"[核心函数2] 向量化完成: project_id={project_id}, "
                f"向量化 {len(chunks_to_vectorize)} 个块, "
                f"耗时 {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"[核心函数2] 向量化失败: {e}", project_id=project_id)
            raise

        finally:
            db.close()

    # ============================================
    # 核心函数 3: FTS 索引同步
    # ============================================

    def rebuild_fts_index(self, project_id: int) -> Dict[str, Any]:
        """
        函数 3: FTS 索引同步

        输入: project_id
        做了什么:
        1. 查出该项目所有已结构化的 chunks
        2. 同步到 FTS 全文搜索索引
        3. 让用户能通过关键词快速搜索

        Args:
            project_id: 项目ID

        Returns:
            Dict: 索引结果
                {
                    "project_id": int,
                    "chunks_indexed": int,
                    "status": "success"
                }
        """
        start_time = time.time()

        logger.info(f"[核心函数3] 重建FTS索引: project_id={project_id}")

        db = get_db_session()

        try:
            # 1. 查询该项目所有 chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project_id
            ).all()

            if not chunks:
                logger.warning(f"项目 {project_id} 没有 chunks")
                return {
                    "project_id": project_id,
                    "chunks_indexed": 0,
                    "status": "no_chunks"
                }

            # 2. MySQL 使用 FULLTEXT 索引（已在表结构中创建）
            # SQLite 使用 FTS5 虚拟表
            # 这里不需要额外操作，索引会自动更新

            # 验证索引可用性（执行一次测试查询）
            from sqlalchemy import text

            test_query = text("""
                SELECT COUNT(*) FROM document_chunks
                WHERE project_id = :project_id
                AND MATCH(text) AGAINST('测试' IN BOOLEAN MODE)
            """)

            try:
                db.execute(test_query, {"project_id": project_id})
                index_status = "available"
            except:
                index_status = "not_available"

            duration = time.time() - start_time

            result = {
                "project_id": project_id,
                "chunks_indexed": len(chunks),
                "index_status": index_status,
                "status": "success",
                "duration": duration
            }

            logger.info(
                f"[核心函数3] FTS索引完成: project_id={project_id}, "
                f"索引 {len(chunks)} 个块, "
                f"耗时 {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"[核心函数3] FTS索引失败: {e}", project_id=project_id)
            raise

        finally:
            db.close()


# 便捷函数（模块级别）
_processor = StructuredProcessor()

def process_uploaded_file(file_id: str) -> Dict[str, Any]:
    """处理上传的文件"""
    return _processor.process_uploaded_file(file_id)

def vectorize_chunks(project_id: int) -> Dict[str, Any]:
    """向量化项目的所有chunks"""
    return _processor.vectorize_chunks(project_id)

def rebuild_fts_index(project_id: int) -> Dict[str, Any]:
    """重建FTS全文搜索索引"""
    return _processor.rebuild_fts_index(project_id)
