"""
优化的文档处理管道 - Week 1 Day 5-7 性能优化
集成并行处理、缓存、性能监控
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.parallel_processor import ParallelProcessor, ProcessingMode, BatchResult
from app.core.cache_manager import get_cache_manager
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)


class OptimizedDocumentPipeline:
    """优化的文档处理管道"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化管道"""
        self.parallel_processor = ParallelProcessor(max_workers=20)
        self.cache_manager = get_cache_manager()

        logger.info("✅ 优化文档处理管道已初始化")

    async def process_documents_batch(
        self,
        document_ids: List[int],
        project_id: int,
        db: Session,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        批量处理文档（并行化）

        Args:
            document_ids: 文档ID列表
            project_id: 项目ID
            db: 数据库会话
            progress_callback: 进度回调函数

        Returns:
            处理结果
        """
        start_time = time.time()
        total_docs = len(document_ids)

        logger.info(f"🚀 开始批量处理 {total_docs} 个文档 (项目: {project_id})")

        # 1. 并行提取文本
        if progress_callback:
            progress_callback("text_extraction", 0.0, "开始提取文本...")

        text_results = await self._extract_texts_parallel(
            document_ids,
            db,
            progress_callback
        )

        # 2. 并行分块
        if progress_callback:
            progress_callback("chunking", 0.3, "开始文档分块...")

        chunk_results = await self._chunk_documents_parallel(
            text_results,
            progress_callback
        )

        # 3. 批量向量化
        if progress_callback:
            progress_callback("vectorization", 0.6, "开始向量化...")

        vector_results = await self._vectorize_chunks_batch(
            chunk_results,
            project_id,
            progress_callback
        )

        # 4. 并行实体提取
        if progress_callback:
            progress_callback("entity_extraction", 0.8, "开始提取实体...")

        entity_results = await self._extract_entities_parallel(
            chunk_results,
            project_id,
            progress_callback
        )

        # 5. 保存结果
        if progress_callback:
            progress_callback("saving", 0.9, "保存处理结果...")

        saved = self._save_results_to_db(
            document_ids,
            chunk_results,
            vector_results,
            entity_results,
            db
        )

        duration = time.time() - start_time

        if progress_callback:
            progress_callback("completed", 1.0, "处理完成")

        result = {
            "success": True,
            "total_documents": total_docs,
            "documents_processed": len([r for r in text_results.results if r]),
            "total_chunks": sum(len(chunks) for chunks in chunk_results.results if chunks),
            "total_entities": sum(len(entities) for entities in entity_results.results if entities),
            "duration": duration,
            "avg_time_per_doc": duration / total_docs if total_docs > 0 else 0,
            "errors": {
                "text_extraction": text_results.errors,
                "chunking": chunk_results.errors,
                "entity_extraction": entity_results.errors
            }
        }

        logger.info(
            f"✅ 批量处理完成: {result['documents_processed']}/{total_docs} 文档, "
            f"{result['total_chunks']} 分块, {result['total_entities']} 实体, "
            f"耗时: {duration:.2f}s"
        )

        return result

    async def _extract_texts_parallel(
        self,
        document_ids: List[int],
        db: Session,
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """并行提取文本"""

        def extract_text(doc_id: int) -> Dict[str, Any]:
            """提取单个文档的文本"""
            try:
                # 查询文档
                doc = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
                if not doc:
                    raise ValueError(f"Document {doc_id} not found")

                # 检查缓存
                cache_key = f"doc_text:{doc_id}"
                cached = self.cache_manager.get(cache_key)
                if cached:
                    logger.debug(f"文本提取缓存命中: {doc_id}")
                    return cached

                # 根据文件类型提取文本
                file_path = Path(doc.file_path)
                text = self._extract_text_by_type(file_path)

                result = {
                    "document_id": doc_id,
                    "text": text,
                    "length": len(text)
                }

                # 缓存结果
                self.cache_manager.set(cache_key, result, ttl=3600)

                return result

            except Exception as e:
                logger.error(f"提取文本失败 (doc_id={doc_id}): {e}")
                raise

        # 并行处理
        result = await self.parallel_processor.process_batch_async(
            document_ids,
            extract_text,
            batch_size=10,
            mode=ProcessingMode.THREAD
        )

        return result

    def _extract_text_by_type(self, file_path: Path) -> str:
        """根据文件类型提取文本"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self._extract_pdf_text(file_path)
        elif suffix in ['.docx', '.doc']:
            return self._extract_docx_text(file_path)
        elif suffix == '.txt':
            return file_path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"不支持的文件类型: {suffix}")

    def _extract_pdf_text(self, file_path: Path) -> str:
        """提取 PDF 文本"""
        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.warning(f"PyMuPDF 失败，尝试 pdfplumber: {e}")
            # 备选方案
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            return text

    def _extract_docx_text(self, file_path: Path) -> str:
        """提取 DOCX 文本"""
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    async def _chunk_documents_parallel(
        self,
        text_results: BatchResult,
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """并行分块文档"""

        def chunk_text(text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
            """分块单个文档"""
            if not text_data:
                return []

            try:
                text = text_data["text"]
                doc_id = text_data["document_id"]

                # 简单的分块策略：按段落和长度
                chunks = self._simple_chunk(text, chunk_size=500, overlap=50)

                return [
                    {
                        "document_id": doc_id,
                        "chunk_index": idx,
                        "text": chunk,
                        "length": len(chunk)
                    }
                    for idx, chunk in enumerate(chunks)
                ]

            except Exception as e:
                logger.error(f"分块失败: {e}")
                raise

        # 并行处理
        result = await self.parallel_processor.process_batch_async(
            [r for r in text_results.results if r],
            chunk_text,
            batch_size=10,
            mode=ProcessingMode.THREAD
        )

        return result

    def _simple_chunk(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """简单的文本分块"""
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # 尝试在句号、问号、感叹号处断开
            if end < len(text):
                for separator in ["。", "！", "？", ".", "!", "?"]:
                    pos = text.rfind(separator, start, end)
                    if pos != -1:
                        end = pos + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    async def _vectorize_chunks_batch(
        self,
        chunk_results: BatchResult,
        project_id: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """批量向量化分块"""
        # 收集所有分块
        all_chunks = []
        for chunks in chunk_results.results:
            if chunks:
                all_chunks.extend(chunks)

        if not all_chunks:
            return {"vectors_created": 0}

        logger.info(f"开始向量化 {len(all_chunks)} 个分块...")

        # TODO: 实际的向量化逻辑
        # 这里暂时模拟
        return {
            "vectors_created": len(all_chunks),
            "collection": f"project_{project_id}"
        }

    async def _extract_entities_parallel(
        self,
        chunk_results: BatchResult,
        project_id: int,
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """并行提取实体"""

        def extract_entities(chunks: List[Dict]) -> List[Dict[str, Any]]:
            """提取单个文档的实体"""
            if not chunks:
                return []

            try:
                # TODO: 实际的实体提取逻辑
                # 这里暂时模拟
                entities = []
                for chunk in chunks:
                    # 简单的模拟
                    text = chunk["text"]
                    words = text.split()
                    if len(words) > 5:
                        entities.append({
                            "name": words[0],
                            "type": "ENTITY",
                            "chunk_id": chunk["chunk_index"]
                        })

                return entities

            except Exception as e:
                logger.error(f"实体提取失败: {e}")
                raise

        # 并行处理
        result = await self.parallel_processor.process_batch_async(
            [r for r in chunk_results.results if r],
            extract_entities,
            batch_size=5,
            mode=ProcessingMode.THREAD
        )

        return result

    def _save_results_to_db(
        self,
        document_ids: List[int],
        chunk_results: BatchResult,
        vector_results: Dict,
        entity_results: BatchResult,
        db: Session
    ) -> bool:
        """保存处理结果到数据库"""
        try:
            # 更新文档状态
            for doc_id in document_ids:
                doc = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
                if doc:
                    doc.status = "completed"
                    doc.processing_progress = 100

            # TODO: 保存分块和实体到数据库
            # 这里暂时跳过详细实现

            db.commit()
            return True

        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            db.rollback()
            return False

    def shutdown(self):
        """关闭管道"""
        self.parallel_processor.shutdown()


# 全局实例
_pipeline: Optional[OptimizedDocumentPipeline] = None


def get_optimized_pipeline() -> OptimizedDocumentPipeline:
    """获取全局管道实例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = OptimizedDocumentPipeline()
    return _pipeline
