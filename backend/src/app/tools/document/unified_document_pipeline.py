"""
统一文档处理流水线引擎 - Unified Document Processing Pipeline
整合3个版本的文档处理流水线，实现 1+1+1 > 2 的功能增强

整合来源：
- document_processing_pipeline.py (751行) - 完整的6步处理 + 知识图谱 + fact_statements
- document_processing_pipeline_complete.py (746行) - 错误重试 + 检查点恢复 + 数据治理
- document_processing_pipeline_v2.py (241行) - 时间抽取 + 结构化元数据

核心功能：
1. 多格式文档解析 (PDF/DOCX/TXT/Audio/Video)
2. 智能文本清洗和标准化
3. 语义驱动的文档切分
4. 多策略向量化 (Sentence-Transformers优先，TF-IDF降级)
5. 时间信息抽取和标准化 (NEW)
6. 结构化元数据管理 (NEW)
7. 知识图谱自动构建
8. 事实陈述提取 (fact_statements)
9. 数据治理和结构化 (NEW)
10. 错误重试和检查点恢复机制 (NEW)
11. 批处理和进度追踪
12. 多存储后端支持 (ChromaDB + PostgreSQL)

单一入口点 API 设计，简化从3个服务的调用到1个方法。
"""

import logging
import time
import json
import re
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ============================================================================
# 自定义异常
# ============================================================================

class DocumentProcessingError(Exception):
    """文档处理错误基类"""
    pass


class ExtractionError(DocumentProcessingError):
    """内容提取错误"""
    pass


class ChunkingError(DocumentProcessingError):
    """切分错误"""
    pass


class VectorizationError(DocumentProcessingError):
    """向量化错误"""
    pass


class StorageError(DocumentProcessingError):
    """存储错误"""
    pass


# ============================================================================
# 统一文档处理流水线引擎
# ============================================================================

class UnifiedDocumentPipeline:
    """
    统一文档处理流水线引擎

    处理流程：
    1. 文档解析（支持PDF/DOCX/TXT/Audio/Video）
    2. 时间抽取（自动提取文档日期和文本中的时间点）
    3. 文本清洗和标准化
    4. 数据治理和结构化
    5. 文档切分（语义感知）
    6. 向量化（多策略）
    7. 知识图谱构建
    8. 事实陈述提取
    9. 存储到多个后端

    特性：
    - 错误重试机制
    - 检查点恢复（断点续传）
    - 批处理支持
    - 进度追踪
    - 性能统计
    """

    def __init__(
        self,
        db: Session,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_checkpoints: bool = True,
        enable_knowledge_graph: bool = True,
        enable_fact_extraction: bool = True,
        enable_data_curation: bool = True,
        enable_temporal_extraction: bool = True
    ):
        """
        初始化统一流水线

        Args:
            db: 数据库会话
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            enable_checkpoints: 是否启用检查点恢复
            enable_knowledge_graph: 是否启用知识图谱构建
            enable_fact_extraction: 是否启用事实陈述提取
            enable_data_curation: 是否启用数据治理
            enable_temporal_extraction: 是否启用时间抽取
        """
        self.db = db
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_checkpoints = enable_checkpoints
        self.enable_knowledge_graph = enable_knowledge_graph
        self.enable_fact_extraction = enable_fact_extraction
        self.enable_data_curation = enable_data_curation
        self.enable_temporal_extraction = enable_temporal_extraction

        # 延迟加载的服务（按需初始化）
        self._converter = None
        self._chunker = None
        self._vectorizer = None
        self._kg_service = None
        self._temporal_extractor = None
        self._data_curator = None

        # 检查点存储路径
        self._checkpoint_dir = Path.home() / ".fieldmind" / "checkpoints"
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # 服务初始化（延迟加载）
    # ========================================================================

    def _get_converter(self):
        """获取文档转换器"""
        if self._converter is None:
            from app.tools.document import UnifiedDocumentConverter
            self._converter = UnifiedDocumentConverter()
        return self._converter

    def _get_chunker(self):
        """获取文档切分器"""
        if self._chunker is None:
            from app.tools.document import create_document_chunker
            self._chunker = create_document_chunker()
        return self._chunker

    def _get_vectorizer(self):
        """获取向量化服务（多策略：Sentence-Transformers优先，TF-IDF降级）"""
        if self._vectorizer is None:
            try:
                from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend
                logger.info("🔄 加载语义嵌入模型（Sentence-Transformers）")
                self._vectorizer = get_embedding_model()

                if self._vectorizer is None:
                    raise ImportError("Sentence-Transformers不可用")

                logger.info("✅ 使用Sentence-Transformers进行语义向量化")
            except Exception as e:
                logger.warning(f"⚠️ 语义嵌入模型加载失败: {e}，降级使用TF-IDF")
                self._vectorizer = TfidfVectorizationService(embedding_dim=384)

        return self._vectorizer

    def _get_kg_service(self):
        """获取知识图谱服务"""
        if self._kg_service is None and self.enable_knowledge_graph:
            try:
                from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine
                self._kg_service = UnifiedKnowledgeGraphEngine()
            except Exception as e:
                logger.warning(f"⚠️ 知识图谱服务初始化失败: {e}")
                self.enable_knowledge_graph = False
        return self._kg_service

    def _get_temporal_extractor(self):
        """获取时间抽取器"""
        if self._temporal_extractor is None and self.enable_temporal_extraction:
            try:
                from app.services.temporal_extractor import get_temporal_extractor
                self._temporal_extractor = get_temporal_extractor()
            except Exception as e:
                logger.warning(f"⚠️ 时间抽取器初始化失败: {e}")
                self.enable_temporal_extraction = False
        return self._temporal_extractor

    def _get_data_curator(self):
        """获取数据治理管道"""
        if self._data_curator is None and self.enable_data_curation:
            try:
                from app.services.data_curation import DataCurationPipeline
                self._data_curator = DataCurationPipeline()
            except Exception as e:
                logger.warning(f"⚠️ 数据治理管道初始化失败: {e}")
                self.enable_data_curation = False
        return self._data_curator

    # ========================================================================
    # 主处理流程
    # ========================================================================

    def process_document(
        self,
        document_id: int,
        project_id: int,
        file_path: Optional[str] = None,
        text_content: Optional[str] = None,
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, float, str], None]] = None,
        resume_from_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """
        统一的文档处理入口点

        Args:
            document_id: 文档ID
            project_id: 项目ID
            file_path: 文件路径（如果从文件处理）
            text_content: 文本内容（如果直接提供文本）
            filename: 文件名
            file_type: 文件类型（pdf/docx/txt/audio/video）
            metadata: 额外元数据
            progress_callback: 进度回调 callback(stage, progress, message)
            resume_from_checkpoint: 是否从检查点恢复

        Returns:
            {
                "success": True/False,
                "document_id": int,
                "project_id": int,
                "stages": {
                    "extraction": {...},
                    "temporal": {...},
                    "cleaning": {...},
                    "curation": {...},
                    "chunking": {...},
                    "vectorization": {...},
                    "knowledge_graph": {...},
                    "fact_extraction": {...},
                    "storage": {...}
                },
                "statistics": {
                    "total_chunks": int,
                    "processing_time": float,
                    "entities_count": int,
                    "relations_count": int,
                    "facts_count": int
                },
                "error": str (if failed)
            }
        """
        start_time = time.time()
        result = {
            "success": False,
            "document_id": document_id,
            "project_id": project_id,
            "stages": {},
            "statistics": {},
            "error": None
        }

        try:
            # 检查检查点
            if resume_from_checkpoint and self.enable_checkpoints:
                checkpoint = self._load_checkpoint(document_id)
                if checkpoint:
                    logger.info(f"📂 检测到检查点，从 {checkpoint['stage']} 阶段恢复")
                    return self._resume_from_checkpoint(checkpoint, progress_callback)

            # 【阶段1】内容提取
            logger.info(f"📄 阶段1：内容提取 (document_id={document_id})")
            if progress_callback:
                progress_callback("extraction", 0.05, "提取文档内容...")

            extracted_text, extraction_metadata = self._extract_content_with_retry(
                file_path, text_content, file_type, document_id
            )

            result["stages"]["extraction"] = {
                "success": True,
                "text_length": len(extracted_text),
                "metadata": extraction_metadata
            }

            self._save_checkpoint(document_id, "extracted", {
                "text": extracted_text,
                "metadata": extraction_metadata
            })

            if progress_callback:
                progress_callback("extraction", 0.10, "内容提取完成")

            # 【阶段2】时间抽取（NEW）
            extracted_dates = []
            document_date = None

            if self.enable_temporal_extraction:
                logger.info(f"📅 阶段2：时间信息抽取")
                if progress_callback:
                    progress_callback("temporal", 0.12, "提取时间信息...")

                try:
                    temporal_extractor = self._get_temporal_extractor()
                    if temporal_extractor:
                        # 提取文档日期
                        document_date = temporal_extractor.extract_document_date(
                            text=extracted_text,
                            filename=filename or "",
                            upload_time=datetime.now()
                        )

                        # 提取文本中的时间点
                        date_extractions = temporal_extractor.extract_dates(
                            text=extracted_text,
                            document_date=document_date
                        )

                        # 过滤高置信度的日期
                        extracted_dates = [
                            d["date_iso"] for d in date_extractions
                            if d.get("confidence", 0) >= 0.7
                        ]

                        result["stages"]["temporal"] = {
                            "success": True,
                            "document_date": document_date.isoformat() if document_date else None,
                            "extracted_dates_count": len(extracted_dates),
                            "sample_dates": extracted_dates[:5]
                        }

                        logger.info(f"  ✅ 提取到文档日期: {document_date}")
                        logger.info(f"  ✅ 提取到 {len(extracted_dates)} 个时间点")
                except Exception as e:
                    logger.warning(f"⚠️ 时间抽取失败（非致命）: {e}")
                    result["stages"]["temporal"] = {"success": False, "error": str(e)}

                if progress_callback:
                    progress_callback("temporal", 0.15, "时间信息提取完成")

            # 合并元数据
            merged_metadata = {
                **(metadata or {}),
                **extraction_metadata,
                "document_date": document_date,
                "extracted_dates": extracted_dates,
                "filename": filename,
                "file_type": file_type
            }

            # 【阶段3】文本清洗
            logger.info(f"🧹 阶段3：文本清洗")
            if progress_callback:
                progress_callback("cleaning", 0.20, "清洗文本数据...")

            cleaned_text, clean_metadata = self._clean_text(extracted_text, merged_metadata)

            result["stages"]["cleaning"] = {
                "success": True,
                "original_length": len(extracted_text),
                "cleaned_length": len(cleaned_text),
                "removed_chars": len(extracted_text) - len(cleaned_text)
            }

            self._save_checkpoint(document_id, "cleaned", {
                "text": cleaned_text,
                "metadata": clean_metadata
            })

            if progress_callback:
                progress_callback("cleaning", 0.25, "文本清洗完成")

            # 【阶段4】数据治理和结构化（NEW）
            structured_records = []

            if self.enable_data_curation:
                logger.info(f"📊 阶段4：数据治理和结构化")
                if progress_callback:
                    progress_callback("curation", 0.28, "执行数据治理...")

                try:
                    curator = self._get_data_curator()
                    if curator:
                        structured_data = curator.process(cleaned_text, clean_metadata)

                        if structured_data:
                            from app.models.structured_insight import StructuredInsight

                            insight = StructuredInsight(
                                document_id=document_id,
                                project_id=project_id,
                                chunk_index=0,
                                original_text=structured_data['original_text'],
                                cleaned_text=structured_data['cleaned_text'],
                                topics=','.join(structured_data['topics']),
                                persons=','.join(structured_data['persons']) if structured_data.get('persons') else None,
                                locations=','.join(structured_data['locations']) if structured_data.get('locations') else None,
                                word_count=len(structured_data['cleaned_text']),
                                metadata=structured_data.get('metadata', {}),
                                processed_at=datetime.now()
                            )

                            structured_records.append(insight)

                            # 使用清洗后的文本
                            cleaned_text = structured_data['cleaned_text']

                            result["stages"]["curation"] = {
                                "success": True,
                                "topics_count": len(structured_data['topics']),
                                "persons_count": len(structured_data.get('persons', [])),
                                "locations_count": len(structured_data.get('locations', []))
                            }

                            logger.info(f"  ✅ 数据治理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 数据治理失败（非致命）: {e}")
                    result["stages"]["curation"] = {"success": False, "error": str(e)}

                if progress_callback:
                    progress_callback("curation", 0.30, "数据治理完成")

            # 【阶段5】文档切分
            logger.info(f"✂️ 阶段5：文档切分")
            if progress_callback:
                progress_callback("chunking", 0.35, "切分文档...")

            chunks = self._chunk_with_retry(cleaned_text, clean_metadata)

            result["stages"]["chunking"] = {
                "success": True,
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(len(c.get("text", "")) for c in chunks) // len(chunks) if chunks else 0
            }

            self._save_checkpoint(document_id, "chunked", {"chunks": chunks})

            if progress_callback:
                progress_callback("chunking", 0.45, f"切分完成：{len(chunks)} 个chunks")

            # 【阶段6】向量化
            logger.info(f"🧮 阶段6：向量化 ({len(chunks)} 个块)")
            if progress_callback:
                progress_callback("vectorization", 0.50, "向量化文本...")

            vectorized_chunks = self._vectorize_with_retry(chunks)

            vectorizer = self._get_vectorizer()
            result["stages"]["vectorization"] = {
                "success": True,
                "vectorized_chunks": len(vectorized_chunks),
                "embedding_model": getattr(vectorizer, 'model_name', 'unknown'),
                "embedding_dim": getattr(vectorizer, 'embedding_dim', 384)
            }

            self._save_checkpoint(document_id, "vectorized", {"chunks": vectorized_chunks})

            if progress_callback:
                progress_callback("vectorization", 0.65, "向量化完成")

            # 【阶段7】知识图谱构建
            entities_count = 0
            relations_count = 0

            if self.enable_knowledge_graph:
                logger.info(f"🕸️ 阶段7：知识图谱构建")
                if progress_callback:
                    progress_callback("knowledge_graph", 0.70, "构建知识图谱...")

                try:
                    kg_service = self._get_kg_service()
                    if kg_service:
                        graph_result = kg_service.build_graph_from_document(
                            doc_id=str(document_id),
                            content=cleaned_text,
                            metadata=clean_metadata
                        )

                        entities_count = graph_result.get("entities_count", 0)
                        relations_count = graph_result.get("relations_count", 0)

                        result["stages"]["knowledge_graph"] = {
                            "success": True,
                            "entities_count": entities_count,
                            "relations_count": relations_count,
                            "entity_types": graph_result.get("entity_types", {})
                        }

                        logger.info(f"  ✅ 知识图谱构建完成: {entities_count}个实体, {relations_count}个关系")
                except Exception as e:
                    logger.warning(f"⚠️ 知识图谱构建失败（非致命）: {e}")
                    result["stages"]["knowledge_graph"] = {"success": False, "error": str(e)}

                if progress_callback:
                    progress_callback("knowledge_graph", 0.75, "知识图谱构建完成")

            # 【阶段8】事实陈述提取
            facts_count = 0

            if self.enable_fact_extraction:
                logger.info(f"📋 阶段8：事实陈述提取")
                if progress_callback:
                    progress_callback("fact_extraction", 0.78, "提取事实陈述...")

                try:
                    # 根据是否有segments决定提取方式
                    if extraction_metadata.get('segments'):
                        facts_count = self._insert_fact_statements_from_segments(
                            extraction_metadata['segments'],
                            document_id,
                            project_id,
                            filename or 'unknown'
                        )
                    else:
                        facts_count = self._insert_fact_statements(
                            cleaned_text,
                            document_id,
                            project_id,
                            filename or 'unknown'
                        )

                    result["stages"]["fact_extraction"] = {
                        "success": True,
                        "facts_count": facts_count
                    }

                    logger.info(f"  ✅ 提取了 {facts_count} 条事实陈述")
                except Exception as e:
                    logger.warning(f"⚠️ 事实陈述提取失败（非致命）: {e}")
                    result["stages"]["fact_extraction"] = {"success": False, "error": str(e)}

                if progress_callback:
                    progress_callback("fact_extraction", 0.82, "事实陈述提取完成")

            # 【阶段9】存储
            logger.info(f"💾 阶段9：存储到数据库")
            if progress_callback:
                progress_callback("storage", 0.85, "存储到数据库...")

            stored_count = self._store_with_retry(
                vectorized_chunks,
                document_id,
                project_id,
                clean_metadata
            )

            result["stages"]["storage"] = {
                "success": True,
                "stored_chunks": stored_count
            }

            # 保存结构化记录
            if structured_records:
                try:
                    self.db.bulk_save_objects(structured_records)
                    self.db.commit()
                    logger.info(f"  ✅ 已保存 {len(structured_records)} 条结构化记录")
                except Exception as e:
                    logger.error(f"  ❌ 保存结构化记录失败: {e}")
                    self.db.rollback()

            if progress_callback:
                progress_callback("storage", 0.92, "存储完成")

            # 更新文档记录
            self._update_document_record(
                document_id,
                project_id,
                cleaned_text,
                len(chunks),
                result
            )

            # 统计信息
            processing_time = time.time() - start_time
            result["statistics"] = {
                "total_chunks": len(chunks),
                "stored_chunks": stored_count,
                "processing_time": round(processing_time, 2),
                "entities_count": entities_count,
                "relations_count": relations_count,
                "facts_count": facts_count,
                "text_length": len(cleaned_text)
            }

            result["success"] = True

            # 清除检查点
            self._clear_checkpoint(document_id)

            if progress_callback:
                progress_callback("complete", 1.0, "处理完成")

            logger.info(f"✅ 文档 {document_id} 处理完成 (耗时: {processing_time:.2f}秒)")

        except Exception as e:
            logger.error(f"❌ 文档 {document_id} 处理失败: {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)

            # 更新文档为失败状态
            self._mark_document_failed(document_id, str(e))

        return result

    # ========================================================================
    # 辅助方法：内容提取
    # ========================================================================

    def _extract_content_with_retry(
        self,
        file_path: Optional[str],
        text_content: Optional[str],
        file_type: Optional[str],
        document_id: int
    ) -> tuple[str, Dict[str, Any]]:
        """带重试的内容提取"""
        if text_content:
            # 直接提供了文本内容
            return text_content, {}

        if not file_path:
            raise ExtractionError("必须提供 file_path 或 text_content")

        # 从文件提取
        for attempt in range(self.max_retries):
            try:
                converter = self._get_converter()
                result = converter.convert_document(file_path)

                if not result.get("success"):
                    raise ExtractionError(f"文档转换失败: {result.get('error')}")

                text = result.get("text", "")
                metadata = result.get("metadata", {})

                return text, metadata

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ 内容提取失败（尝试 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise ExtractionError(f"内容提取失败（重试{self.max_retries}次后）: {e}")

    def _clean_text(self, text: str, metadata: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        文本清洗和标准化

        清洗规则：
        1. 删除多余空白字符
        2. 统一换行符
        3. 删除特殊控制字符
        4. 标准化标点符号
        """
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 删除控制字符（保留换行和制表符）
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        # 压缩多余空白
        text = re.sub(r' +', ' ', text)  # 多个空格 -> 单个空格
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行 -> 双换行

        # 去除首尾空白
        text = text.strip()

        # 更新元数据
        clean_metadata = metadata.copy()
        clean_metadata['cleaned'] = True
        clean_metadata['original_length'] = len(metadata.get('original_text', text))
        clean_metadata['cleaned_length'] = len(text)

        return text, clean_metadata

    # ========================================================================
    # 辅助方法：切分、向量化、存储（带重试）
    # ========================================================================

    def _chunk_with_retry(self, text: str, metadata: Dict[str, Any]) -> List[Dict]:
        """带重试的文档切分"""
        for attempt in range(self.max_retries):
            try:
                # 使用基础chunker（兼容性最好）
                from app.tools.document import UnifiedDocumentChunker
                basic_chunker = UnifiedDocumentChunker(
                    min_chunk_size=200,
                    max_chunk_size=500,
                    target_chunk_size=350
                )
                chunks = basic_chunker.chunk_document(text, metadata)

                # 确保chunks是字典格式
                if chunks and isinstance(chunks[0], dict):
                    return chunks
                else:
                    # 如果返回的是对象，转换为字典
                    result = []
                    for i, chunk in enumerate(chunks):
                        if hasattr(chunk, 'text'):
                            chunk_text = chunk.text
                        elif isinstance(chunk, dict):
                            chunk_text = chunk.get('text', '')
                        else:
                            chunk_text = str(chunk)

                        result.append({
                            "text": chunk_text,
                            "metadata": {
                                **metadata,
                                "chunk_index": i
                            }
                        })
                    return result

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ 文档切分失败（尝试 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise ChunkingError(f"文档切分失败（重试{self.max_retries}次后）: {e}")

    def _split_text_for_chunks(self, full_text: str, chunks: list) -> list:
        """根据chunk位置分割文本（已废弃，保留用于兼容）"""
        # 这个方法已经不需要了，因为chunker直接返回文本
        return [chunk.get('text', '') if isinstance(chunk, dict) else str(chunk) for chunk in chunks]

    def _vectorize_with_retry(self, chunks: List[Dict]) -> List[Dict]:
        """带重试的向量化"""
        for attempt in range(self.max_retries):
            try:
                vectorizer = self._get_vectorizer()

                # 不同vectorizer有不同的接口
                if hasattr(vectorizer, 'vectorize_chunks'):
                    return vectorizer.vectorize_chunks(chunks)
                elif hasattr(vectorizer, 'encode'):
                    # Sentence-Transformers接口
                    vectorized = []
                    for chunk in chunks:
                        text = chunk.get('text', '')
                        embedding = vectorizer.encode(text, convert_to_numpy=True)
                        vectorized.append({
                            **chunk,
                            'embedding': embedding.tolist()
                        })
                    return vectorized
                else:
                    raise VectorizationError(f"Vectorizer没有合适的方法")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ 向量化失败（尝试 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise VectorizationError(f"向量化失败（重试{self.max_retries}次后）: {e}")

    def _store_with_retry(
        self,
        chunks: List[Dict],
        document_id: int,
        project_id: int,
        metadata: Dict[str, Any]
    ) -> int:
        """带重试的存储到ChromaDB"""
        for attempt in range(self.max_retries):
            try:
                from app.core.rag_engine import rag_engine

                if not rag_engine or not rag_engine.collection:
                    logger.warning("⚠️ ChromaDB未初始化，跳过存储")
                    return 0

                ids = []
                documents = []
                metadatas = []
                embeddings = []

                for i, chunk in enumerate(chunks):
                    chunk_id = f"doc{document_id}_chunk{i}"
                    ids.append(chunk_id)
                    documents.append(chunk['text'])

                    # 准备元数据
                    meta = {
                        'document_id': document_id,
                        'project_id': project_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }

                    # 添加额外元数据
                    if metadata:
                        for k, v in metadata.items():
                            if v is not None and isinstance(v, (str, int, float, bool)):
                                meta[k] = v
                            elif isinstance(v, (list, dict)):
                                meta[k] = json.dumps(v, ensure_ascii=False)

                    metadatas.append(meta)

                    # 提取embedding
                    if 'embedding' in chunk:
                        embeddings.append(chunk['embedding'])

                # 批量添加到ChromaDB
                if embeddings:
                    rag_engine.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                else:
                    rag_engine.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )

                logger.info(f"  ✅ 已存储 {len(chunks)} 个块到ChromaDB")
                return len(chunks)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ 存储失败（尝试 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise StorageError(f"存储失败（重试{self.max_retries}次后）: {e}")

    # ========================================================================
    # 辅助方法：事实陈述提取
    # ========================================================================

    def _insert_fact_statements(
        self,
        text: str,
        document_id: int,
        project_id: int,
        source_file: str
    ) -> int:
        """提取并插入事实陈述（普通文本）"""
        try:
            # 简单句子分割
            sentences = re.split(r'[。！？\n]', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

            if not sentences:
                return 0

            # 逐条插入（避免批量插入的兼容性问题）
            insert_query = text("""
                INSERT INTO fact_statements
                (document_id, project_id, fact_text, source_file, confidence_score, created_at)
                VALUES (:document_id, :project_id, :fact_text, :source_file, :confidence_score, :created_at)
            """)

            inserted_count = 0
            for sentence in sentences:
                try:
                    self.db.execute(insert_query, {
                        'document_id': document_id,
                        'project_id': project_id,
                        'fact_text': sentence,
                        'source_file': source_file,
                        'confidence_score': 0.8,
                        'created_at': datetime.now()
                    })
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"插入单条fact_statement失败: {e}")
                    continue

            self.db.commit()
            return inserted_count

        except Exception as e:
            logger.error(f"插入fact_statements失败: {e}")
            self.db.rollback()
            return 0  # 不抛出异常，返回0

    def _insert_fact_statements_from_segments(
        self,
        segments: List[Dict],
        document_id: int,
        project_id: int,
        source_file: str
    ) -> int:
        """提取并插入事实陈述（从音频/视频segments）"""
        try:
            if not segments:
                return 0

            insert_query = text("""
                INSERT INTO fact_statements
                (document_id, project_id, fact_text, source_file, start_time, end_time,
                 confidence_score, created_at)
                VALUES (:document_id, :project_id, :fact_text, :source_file, :start_time,
                        :end_time, :confidence_score, :created_at)
            """)

            inserted_count = 0
            for seg in segments:
                fact_text = seg.get('text', '').strip()
                if len(fact_text) < 10:
                    continue

                try:
                    self.db.execute(insert_query, {
                        'document_id': document_id,
                        'project_id': project_id,
                        'fact_text': fact_text,
                        'source_file': source_file,
                        'start_time': seg.get('start'),
                        'end_time': seg.get('end'),
                        'confidence_score': 0.8,
                        'created_at': datetime.now()
                    })
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"插入单条fact_statement失败: {e}")
                    continue

            self.db.commit()
            return inserted_count

        except Exception as e:
            logger.error(f"从segments插入fact_statements失败: {e}")
            self.db.rollback()
            return 0  # 不抛出异常，返回0

    # ========================================================================
    # 辅助方法：数据库更新
    # ========================================================================

    def _update_document_record(
        self,
        document_id: int,
        project_id: int,
        cleaned_text: str,
        chunk_count: int,
        result: Dict[str, Any]
    ):
        """更新文档记录"""
        try:
            from app.models.project import ProjectDocument

            doc = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if doc:
                doc.text_content = cleaned_text
                doc.chunk_count = chunk_count
                doc.status = "completed"
                doc.processing_progress = 100
                doc.extra_data = doc.extra_data or {}
                doc.extra_data["processing_result"] = result["stages"]
                doc.extra_data["statistics"] = result.get("statistics", {})
                self.db.commit()

        except Exception as e:
            logger.error(f"更新文档记录失败: {e}")
            self.db.rollback()

    def _mark_document_failed(self, document_id: int, error: str):
        """标记文档处理失败"""
        try:
            from app.models.project import ProjectDocument

            doc = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if doc:
                doc.status = "failed"
                doc.extra_data = doc.extra_data or {}
                doc.extra_data["error"] = error
                self.db.commit()

        except Exception as e:
            logger.error(f"标记文档失败状态时出错: {e}")
            self.db.rollback()

    # ========================================================================
    # 检查点管理（断点续传）
    # ========================================================================

    def _save_checkpoint(self, document_id: int, stage: str, data: Dict):
        """保存检查点"""
        if not self.enable_checkpoints:
            return

        try:
            checkpoint_file = self._checkpoint_dir / f"doc{document_id}.json"
            checkpoint = {
                "document_id": document_id,
                "stage": stage,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"保存检查点失败: {e}")

    def _load_checkpoint(self, document_id: int) -> Optional[Dict]:
        """加载检查点"""
        if not self.enable_checkpoints:
            return None

        try:
            checkpoint_file = self._checkpoint_dir / f"doc{document_id}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载检查点失败: {e}")

        return None

    def _clear_checkpoint(self, document_id: int):
        """清除检查点"""
        if not self.enable_checkpoints:
            return

        try:
            checkpoint_file = self._checkpoint_dir / f"doc{document_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
        except Exception as e:
            logger.warning(f"清除检查点失败: {e}")

    def _resume_from_checkpoint(
        self,
        checkpoint: Dict,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """从检查点恢复处理"""
        # TODO: 实现从不同阶段恢复的逻辑
        # 目前简化处理，重新执行完整流程
        document_id = checkpoint['document_id']
        stage = checkpoint['stage']

        logger.warning(f"检查点恢复功能尚未完全实现，从 {stage} 阶段重新开始")

        # 清除检查点，重新处理
        self._clear_checkpoint(document_id)

        return {
            "success": False,
            "error": "检查点恢复功能尚未完全实现，请重新提交文档"
        }

    # ========================================================================
    # 批处理
    # ========================================================================

    def batch_process_documents(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        批量处理文档

        Args:
            documents: 文档列表，每个文档包含 process_document 所需的参数
            progress_callback: 进度回调

        Returns:
            处理结果列表
        """
        results = []
        total = len(documents)

        for i, doc_params in enumerate(documents):
            logger.info(f"📦 批处理进度: {i + 1}/{total}")

            if progress_callback:
                progress_callback("batch", (i + 1) / total, f"处理文档 {i + 1}/{total}")

            try:
                result = self.process_document(**doc_params)
                results.append(result)
            except Exception as e:
                logger.error(f"批处理文档 {i + 1} 失败: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "document_id": doc_params.get('document_id')
                })

        logger.info(f"✅ 批处理完成: {total} 个文档")
        return results


# ============================================================================
# 便捷函数
# ============================================================================

def create_document_pipeline(db: Session, **kwargs) -> UnifiedDocumentPipeline:
    """
    创建统一文档处理流水线实例（便捷函数）

    Args:
        db: 数据库会话
        **kwargs: 传递给 UnifiedDocumentPipeline 的其他参数

    Returns:
        UnifiedDocumentPipeline实例
    """
    return UnifiedDocumentPipeline(db=db, **kwargs)


def process_single_document(
    db: Session,
    document_id: int,
    project_id: int,
    file_path: Optional[str] = None,
    text_content: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    快速处理单个文档（便捷函数）

    旧方式（3步，多个服务）:
        converter = DocumentConverter()
        result = converter.convert_document(file_path)

        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(result['text'], metadata)

        vectorizer = VectorizationService()
        vectorizer.vectorize_chunks(chunks)

    新方式（1步，单一入口）:
        result = process_single_document(
            db=db,
            document_id=doc_id,
            project_id=proj_id,
            file_path=path
        )

    Args:
        db: 数据库会话
        document_id: 文档ID
        project_id: 项目ID
        file_path: 文件路径
        text_content: 文本内容
        **kwargs: 其他参数

    Returns:
        处理结果
    """
    pipeline = UnifiedDocumentPipeline(db=db)
    return pipeline.process_document(
        document_id=document_id,
        project_id=project_id,
        file_path=file_path,
        text_content=text_content,
        **kwargs
    )
