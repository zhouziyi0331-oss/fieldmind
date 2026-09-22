"""
完整的文档处理流水线 - 带错误处理和重试机制
功能：文档上传 -> 切分 -> 向量化 -> 存储 -> 错误恢复
"""

import logging
import time
import json
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import traceback

from app.config import settings as app_settings

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """文档处理错误基类"""
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


class DocumentProcessingPipeline:
    """文档处理流水线 - 完整版本"""

    def __init__(
        self,
        db_connection,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_checkpoints: bool = True
    ):
        """
        Args:
            db_connection: 数据库连接
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            enable_checkpoints: 是否启用检查点（用于恢复）
        """
        self.db = db_connection
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_checkpoints = enable_checkpoints

        # 延迟导入服务
        self.chunker = None
        self.vectorizer = None

    def _record_plugin_result(
        self,
        document_id: int,
        plugin: str,
        status: str,
        message: str = "",
        result: object = None,
        health: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """统一记录外部插件执行状态，不吞掉真实结果。"""
        from app.services.background_tasks import _record_plugin_result

        return _record_plugin_result(
            self.db,
            document_id=document_id,
            plugin=plugin,
            status=status,
            message=message,
            result=result,
            health=health,
        )

    @staticmethod
    def _api_key_configured(name: str) -> bool:
        """检查外部插件所需密钥，避免在未配置时初始化重量级客户端。"""
        values = [os.getenv(name)]
        values.append(getattr(app_settings, name, None))
        try:
            from app.core.config import settings as core_settings
            ai_settings = getattr(core_settings, "ai", None)
            field_name = {
                "OPENAI_API_KEY": "openai_api_key",
                "ANTHROPIC_API_KEY": "anthropic_api_key",
            }.get(name)
            if ai_settings is not None and field_name:
                values.append(getattr(ai_settings, field_name, None))
        except Exception:
            pass
        return any(isinstance(value, str) and value.strip() for value in values)

    @staticmethod
    def _run_sync_with_timeout(operation, timeout_seconds: float, plugin: str):
        """执行可能阻塞的外部调用；超时后释放等待，不阻塞主文档状态收口。"""
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"fieldmind-{plugin}")
        future = worker.submit(operation)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"{plugin}调用超过{timeout_seconds:.1f}秒") from exc
        finally:
            worker.shutdown(wait=False, cancel_futures=True)

    @classmethod
    def _run_async_with_timeout(cls, coroutine_factory, timeout_seconds: float, plugin: str):
        """在独立事件循环中运行插件异步调用，并限制其最长等待时间。"""
        return cls._run_sync_with_timeout(
            lambda: asyncio.run(coroutine_factory()),
            timeout_seconds,
            plugin,
        )

    def _init_services(self):
        """延迟初始化服务"""
        if self.chunker is None:
            from app.services.document_chunker import DocumentChunker
            self.chunker = DocumentChunker()

        if self.vectorizer is None:
            # 优先使用真实的语义嵌入
            from app.services.semantic_embedding import get_embedding_model

            logger.info("🔄 加载语义嵌入模型（Sentence-Transformers）")
            self.vectorizer = get_embedding_model()

            if self.vectorizer is None:
                logger.warning("⚠️ 语义嵌入模型加载失败，降级使用TF-IDF")
                from app.services.tfidf_vectorization import TfidfVectorizationService
                self.vectorizer = TfidfVectorizationService(embedding_dim=384)
            else:
                logger.info("✅ 使用Sentence-Transformers进行语义向量化")

    def _run_external_enrichment(
        self,
        document_id: int,
        project_id: int,
        text_content: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """执行可选增强插件。

        外部服务属于增强能力，不是主结构化链路的前置条件。每个插件都必须：
        1. 先做本地配置/健康判断；
        2. 在独立线程或事件循环中执行并设置短超时；
        3. 将 unavailable/failed/executed 写入统一资产表；
        4. 单个插件失败不能影响文档完成或进入人工复核。
        """
        results: List[Dict[str, Any]] = []
        timeout_seconds = 8.0

        def record(plugin: str, status: str, message: str = "", result=None, health=None):
            results.append(self._record_plugin_result(
                document_id,
                plugin,
                status,
                message,
                result=result,
                health=health,
            ))

        # 知识图谱：无云端密钥时仍执行本地规则/NER，不制造伪造的LLM结果。
        try:
            from app.services.knowledge_graph_service import get_knowledge_graph_service

            use_llm = self._api_key_configured("ANTHROPIC_API_KEY") or self._api_key_configured("OPENAI_API_KEY")
            def build_knowledge_graph():
                kg_service = get_knowledge_graph_service()
                extracted_entities, extracted_relations = kg_service.extract_entities_and_relations(
                    text_content,
                    document_id=document_id,
                    use_llm=use_llm,
                )
                kg_service.add_entities_and_relations(
                    extracted_entities,
                    extracted_relations,
                    document_id=document_id,
                )
                return extracted_entities, extracted_relations

            entities, relations = self._run_sync_with_timeout(
                build_knowledge_graph,
                timeout_seconds,
                "knowledge-graph",
            )
            from app.models.project import ProjectDocument
            project_document = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()
            if project_document:
                project_document.entities = [entity.to_dict() for entity in entities]
                project_document.extra_data = {
                    **dict(project_document.extra_data or {}),
                    "knowledge_graph": {
                        "entity_count": len(entities),
                        "relation_count": len(relations),
                        "llm_enabled": use_llm,
                    },
                }
                self.db.commit()
            record(
                "knowledge_graph",
                "executed",
                f"提取实体{len(entities)}个、关系{len(relations)}个"
                + ("（含LLM增强）" if use_llm else "（本地规则/NER）"),
                result={"entities": len(entities), "relations": len(relations), "llm_enabled": use_llm},
            )
        except TimeoutError as exc:
            logger.warning("知识图谱增强超时，保留主链路结果: %s", exc)
            record("knowledge_graph", "unavailable", str(exc))
        except Exception as exc:
            logger.warning("知识图谱增强失败，保留主链路结果: %s", exc, exc_info=True)
            record("knowledge_graph", "failed", str(exc))

        # Cognee：先探测Neo4j和SDK，再进入初始化/写入。
        try:
            from app.services.cognee_service import get_cognee_service

            cognee_service = get_cognee_service()
            health = cognee_service.health_check()
            if not health.get("available"):
                record("cognee", "unavailable", health.get("reason", "Cognee不可用"), health=health)
            else:
                cognee_result = self._run_async_with_timeout(
                    lambda: cognee_service.remember_document(
                        content=text_content,
                        document_id=str(document_id),
                        project_id=str(project_id) if project_id else None,
                        metadata=metadata,
                    ),
                    timeout_seconds,
                    "cognee",
                )
                record("cognee", "executed", "文档已写入Cognee", result=str(cognee_result), health=health)
        except TimeoutError as exc:
            logger.warning("Cognee增强超时: %s", exc)
            record("cognee", "unavailable", str(exc))
        except Exception as exc:
            logger.warning("Cognee增强失败: %s", exc, exc_info=True)
            record("cognee", "failed", str(exc))

        # LightRAG依赖OpenAI的LLM和Embedding；没有密钥时明确标记不可用。
        if not self._api_key_configured("OPENAI_API_KEY"):
            record("lightrag", "unavailable", "未配置OPENAI_API_KEY")
        else:
            try:
                from app.services.lightrag_service import get_lightrag_service

                lightrag_result = self._run_async_with_timeout(
                    lambda: get_lightrag_service().insert_document(
                        content=text_content,
                        document_id=str(document_id),
                        project_id=str(project_id) if project_id else None,
                        metadata=metadata,
                    ),
                    timeout_seconds,
                    "lightrag",
                )
                record(
                    "lightrag",
                    "executed" if lightrag_result else "failed",
                    "文档已写入LightRAG" if lightrag_result else "LightRAG返回失败",
                    result=lightrag_result,
                )
            except TimeoutError as exc:
                logger.warning("LightRAG增强超时: %s", exc)
                record("lightrag", "unavailable", str(exc))
            except Exception as exc:
                logger.warning("LightRAG增强失败: %s", exc, exc_info=True)
                record("lightrag", "failed", str(exc))

        # Mem0同时依赖Anthropic和OpenAI配置；初始化/网络调用必须限时。
        if not (
            self._api_key_configured("ANTHROPIC_API_KEY")
            and self._api_key_configured("OPENAI_API_KEY")
        ):
            record("mem0", "unavailable", "未同时配置ANTHROPIC_API_KEY和OPENAI_API_KEY")
        else:
            try:
                from app.services.mem0_service import Mem0Service

                mem0_result = self._run_sync_with_timeout(
                    lambda: Mem0Service().add_document_memory(
                        project_id=project_id if project_id else 0,
                        document_id=document_id,
                        content=text_content,
                        metadata=metadata,
                    ),
                    timeout_seconds,
                    "mem0",
                )
                record(
                    "mem0",
                    "executed" if mem0_result else "unavailable",
                    "文档已写入Mem0" if mem0_result else "Mem0未初始化或未配置",
                    result=mem0_result,
                )
            except TimeoutError as exc:
                logger.warning("Mem0增强超时: %s", exc)
                record("mem0", "unavailable", str(exc))
            except Exception as exc:
                logger.warning("Mem0增强失败: %s", exc, exc_info=True)
                record("mem0", "failed", str(exc))

        # Graphiti依赖Neo4j和OpenAI，构造服务时已经有快速端口探测。
        if not self._api_key_configured("OPENAI_API_KEY"):
            record("graphiti", "unavailable", "未配置OPENAI_API_KEY")
        else:
            try:
                from app.services.graphiti_service import get_graphiti_service

                graphiti_service = get_graphiti_service()
                health = graphiti_service.health_check()
                if not health.get("available"):
                    record("graphiti", "unavailable", health.get("reason", "Graphiti不可用"), health=health)
                else:
                    graphiti_result = self._run_async_with_timeout(
                        lambda: graphiti_service.add_episode(
                            content=text_content,
                            episode_type="text",
                            project_id=str(project_id) if project_id else None,
                            document_id=document_id,
                            source_description=f"Document: {metadata.get('filename', 'unknown')}",
                            reference_time=datetime.now(),
                            metadata=metadata,
                        ),
                        timeout_seconds,
                        "graphiti",
                    )
                    record(
                        "graphiti",
                        "executed" if graphiti_result.get("success") else "failed",
                        "文档已写入Graphiti" if graphiti_result.get("success") else graphiti_result.get("error", "Graphiti返回失败"),
                        result=graphiti_result,
                        health=health,
                    )
            except TimeoutError as exc:
                logger.warning("Graphiti增强超时: %s", exc)
                record("graphiti", "unavailable", str(exc))
            except Exception as exc:
                logger.warning("Graphiti增强失败: %s", exc, exc_info=True)
                record("graphiti", "failed", str(exc))

        # GraphRAG当前是本地写入输入队列，不应被当成同步索引阻塞主流程。
        try:
            from app.services.graphrag_service import get_graphrag_service

            graphrag_result = self._run_async_with_timeout(
                lambda: get_graphrag_service().index_document(
                    content=text_content,
                    project_id=str(project_id) if project_id else None,
                    document_id=document_id,
                    metadata=metadata,
                ),
                3.0,
                "graphrag",
            )
            if graphrag_result.get("status") in {"queued", "success"}:
                record("graphrag", "executed", graphrag_result.get("message", "已加入GraphRAG索引队列"), result=graphrag_result)
            else:
                record("graphrag", "failed", graphrag_result.get("error", "GraphRAG返回失败"), result=graphrag_result)
        except TimeoutError as exc:
            logger.warning("GraphRAG增强超时: %s", exc)
            record("graphrag", "unavailable", str(exc))
        except Exception as exc:
            logger.warning("GraphRAG增强失败: %s", exc, exc_info=True)
            record("graphrag", "failed", str(exc))

        # Khoj和Quivr分别先探测服务/配置，避免默认连接等待30秒或加载大模型。
        try:
            from app.services.khoj_service import get_khoj_service

            khoj_service = get_khoj_service()
            health = self._run_async_with_timeout(khoj_service.health_check, 2.0, "khoj-health")
            if not health.get("available"):
                record("khoj", "unavailable", health.get("message", "Khoj服务不可用"), health=health)
            else:
                khoj_result = self._run_async_with_timeout(
                    lambda: khoj_service.index_document(
                        content=text_content,
                        title=metadata.get("filename") if metadata else "Document",
                        file_type="text",
                        project_id=str(project_id) if project_id else None,
                        metadata=metadata,
                    ),
                    timeout_seconds,
                    "khoj",
                )
                record(
                    "khoj",
                    "executed" if khoj_result.get("indexed") else "failed",
                    "文档已索引到Khoj" if khoj_result.get("indexed") else khoj_result.get("message", "Khoj返回失败"),
                    result=khoj_result,
                    health=health,
                )
        except TimeoutError as exc:
            logger.warning("Khoj增强超时: %s", exc)
            record("khoj", "unavailable", str(exc))
        except Exception as exc:
            logger.warning("Khoj增强失败: %s", exc, exc_info=True)
            record("khoj", "failed", str(exc))

        quivr_key_name = "ANTHROPIC_API_KEY"
        if not self._api_key_configured(quivr_key_name):
            record("quivr", "unavailable", f"未配置{quivr_key_name}")
        else:
            try:
                from app.services.quivr_service import get_quivr_service

                quivr_service = get_quivr_service()
                health = self._run_sync_with_timeout(quivr_service.health_check, 2.0, "quivr-health")
                if not health.get("available"):
                    record("quivr", "unavailable", health.get("message", "Quivr服务不可用"), health=health)
                else:
                    quivr_result = self._run_async_with_timeout(
                        lambda: quivr_service.index_document(
                            project_id=str(project_id) if project_id else "default",
                            content=text_content,
                            metadata=metadata,
                        ),
                        timeout_seconds,
                        "quivr",
                    )
                    record(
                        "quivr",
                        "executed" if quivr_result.get("indexed") else "failed",
                        "文档已索引到Quivr" if quivr_result.get("indexed") else quivr_result.get("message", "Quivr返回失败"),
                        result=quivr_result,
                        health=health,
                    )
            except TimeoutError as exc:
                logger.warning("Quivr增强超时: %s", exc)
                record("quivr", "unavailable", str(exc))
            except Exception as exc:
                logger.warning("Quivr增强失败: %s", exc, exc_info=True)
                record("quivr", "failed", str(exc))

        # 中文NLP是本地插件，也需要限制模型首次加载时间。
        try:
            from app.services.chinese_nlp_service import get_chinese_nlp_service

            chinese_nlp_service = get_chinese_nlp_service()
            nlp_result = self._run_sync_with_timeout(
                lambda: {
                    "analysis": chinese_nlp_service.analyse_text(text_content[:5000]),
                    "entities": chinese_nlp_service.extract_entities(text_content[:3000]),
                },
                4.0,
                "chinese-nlp",
            )
            analysis = nlp_result.get("analysis", {})
            entities = nlp_result.get("entities", [])
            chinese_keywords = []
            jieba_result = analysis.get("jieba", {})
            chinese_keywords.extend(
                item.get("keyword")
                for item in jieba_result.get("keywords", [])
                if isinstance(item, dict) and item.get("keyword")
            )
            record(
                "chinese_nlp",
                "executed",
                f"关键词{len(chinese_keywords)}个、实体{len(entities)}个",
                result={"keywords": chinese_keywords[:10], "entities": entities[:10]},
            )
        except TimeoutError as exc:
            logger.warning("中文NLP增强超时: %s", exc)
            record("chinese_nlp", "unavailable", str(exc))
        except Exception as exc:
            logger.warning("中文NLP增强失败: %s", exc, exc_info=True)
            record("chinese_nlp", "failed", str(exc))

        return results

    def _store_chunks_in_chroma(
        self,
        document_id: int,
        project_id: int,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """将chunks写入Chroma；维度不匹配或未启用时直接跳过。"""
        try:
            from app.core.rag_engine import rag_engine

            if not app_settings.ENABLE_CHROMA_INDEXING:
                return {"status": "skipped", "reason": "disabled_by_config"}

            if not rag_engine or not getattr(rag_engine, "collection", None):
                return {"status": "skipped", "reason": "not_initialized"}

            if not getattr(rag_engine, "chroma_enabled", False):
                return {"status": "skipped", "reason": getattr(rag_engine, "chroma_disabled_reason", "disabled")}

            ids: List[str] = []
            documents: List[str] = []
            metadatas: List[Dict[str, Any]] = []
            embeddings: List[List[float]] = []

            for i, chunk in enumerate(chunks):
                chunk_text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
                if not chunk_text:
                    continue

                embedding = chunk.get("embedding", chunk.get("vector")) if isinstance(chunk, dict) else None
                if embedding is None:
                    return {"status": "skipped", "reason": "missing_embedding"}

                if hasattr(embedding, "tolist"):
                    embedding = embedding.tolist()

                if getattr(rag_engine, "embedding_dim", 0) and len(embedding) != rag_engine.embedding_dim:
                    return {
                        "status": "skipped",
                        "reason": f"dimension_mismatch actual={len(embedding)} expected={rag_engine.embedding_dim}",
                    }

                ids.append(f"doc{document_id}_chunk{i}")
                documents.append(chunk_text)
                embeddings.append(embedding)

                meta = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                if project_id:
                    meta["project_id"] = project_id
                if metadata:
                    for key, value in metadata.items():
                        if value is None:
                            continue
                        if isinstance(value, (str, int, float, bool)):
                            meta[key] = value
                        elif isinstance(value, (list, dict)):
                            meta[key] = json.dumps(value, ensure_ascii=False)
                metadatas.append(meta)

            if not ids:
                return {"status": "skipped", "reason": "empty_chunks"}

            rag_engine.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            return {"status": "success", "chunks": len(ids)}
        except Exception as e:
            logger.warning(f"⚠️ Chroma写入失败，已回退到SQLite主结构化存储: {e}")
            return {"status": "skipped", "reason": str(e)}

    def process_document(
        self,
        document_id: int,
        project_id: int,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None  # ⭐⭐⭐ 新增 sources 参数
    ) -> Dict[str, Any]:
        """
        处理文档 - 完整流程

        Args:
            document_id: 文档ID
            project_id: 项目ID
            text_content: 文档文本内容
            metadata: 元数据
            sources: 来自 IngestionAgent 的结构化数据（表格行、音频 segments 等）

        Returns:
            {
                "success": True/False,
                "document_id": int,
                "chunks_count": int,
                "processing_time": float,
                "error": str (if failed),
                "checkpoint": str (if failed, for resume)
            }
        """
        start_time = time.time()
        metadata = dict(metadata or {})
        sources = sources or []  # ⭐ 确保 sources 不为 None

        try:
            # 初始化服务
            self._init_services()

            # 检查是否有未完成的checkpoint
            checkpoint = self._load_checkpoint(document_id)
            if checkpoint:
                logger.info(f"📂 检测到未完成的处理，从checkpoint恢复: {checkpoint['stage']}")
                return self._resume_from_checkpoint(checkpoint)

            # 阶段1: 切分文档（传递 sources）
            logger.info(f"📄 阶段1: 切分文档 (document_id={document_id}, sources={len(sources)})")
            chunks = self._chunk_with_retry(text_content, metadata, sources)  # ⭐⭐⭐ 传递 sources
            self._save_checkpoint(document_id, "chunked", {"chunks": chunks})

            # ===== 新增：阶段1.5: 数据治理（清洗+结构化） =====
            logger.info(f"🧹 阶段1.5: 数据治理 - 清洗与结构化")
            from app.services.data_curation import DataCurationPipeline
            from app.models.structured_insight import StructuredInsight

            curation_pipeline = DataCurationPipeline()
            structured_records = []

            for i, chunk in enumerate(chunks):
                chunk_text = chunk.get('text', '')
                chunk_metadata = chunk.get('metadata', {})

                # 执行数据治理
                structured_data = curation_pipeline.process(chunk_text, chunk_metadata)

                if structured_data:
                    # 创建结构化记录
                    insight = StructuredInsight(
                        document_id=document_id,
                        project_id=project_id,
                        chunk_index=i,
                        original_text=structured_data['original_text'],
                        cleaned_text=structured_data['cleaned_text'],
                        topics=','.join(structured_data['topics']),  # List转逗号分隔字符串
                        persons=','.join(structured_data['persons']) if structured_data['persons'] else None,
                        locations=','.join(structured_data['locations']) if structured_data['locations'] else None,
                        start_time=chunk_metadata.get('start_sec'),
                        end_time=chunk_metadata.get('end_sec'),
                        word_count=len(structured_data['cleaned_text']),
                        extra_metadata=structured_data['metadata'],
                        processed_at=datetime.now()
                    )

                    structured_records.append(insight)

                    # 使用清洗后的文本替换原文本
                    chunk['text'] = structured_data['cleaned_text']

            # 批量保存到数据库
            if structured_records:
                try:
                    self.db.bulk_save_objects(structured_records)
                    self.db.commit()
                    logger.info(f"✅ 已保存 {len(structured_records)} 条结构化记录到数据库")

                    # 更新统计表
                    self._update_statistics(project_id, structured_records)

                except Exception as e:
                    logger.error(f"❌ 保存结构化记录失败: {e}", exc_info=True)
                    self.db.rollback()
            # ===== 数据治理结束 =====

            # 阶段2: 向量化
            logger.info(f"🧮 阶段2: 向量化 ({len(chunks)}个块)")
            vectorized_chunks = self._vectorize_with_retry(chunks)
            self._save_checkpoint(document_id, "vectorized", {"chunks": vectorized_chunks})

            # 阶段3: 存储到ChromaDB（可选）
            logger.info(f"💾 阶段3: 存储到ChromaDB")
            chroma_result = self._store_chunks_in_chroma(
                document_id=document_id,
                project_id=project_id,
                chunks=vectorized_chunks,
                metadata=metadata,
            )
            if chroma_result.get("status") == "success":
                logger.info(f"✅ 已存储 {chroma_result.get('chunks', 0)} 个块到ChromaDB")
            else:
                logger.info(f"ℹ️ 跳过ChromaDB: {chroma_result.get('reason')}")

            # ===== 新增：保存chunks到SQLite数据库 =====
            logger.info(f"💾 阶段3.5: 保存chunks到SQLite数据库")
            try:
                from app.models.document_chunk import DocumentChunk
                # 清除旧的chunks（如果重新处理）
                self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).delete()

                # 保存新的chunks（包含语义增强字段）
                for i, chunk_data in enumerate(vectorized_chunks):
                    chunk_metadata = chunk_data.get("metadata") or {}
                    semantic_context = chunk_metadata.get("source_summary") or chunk_data.get("semantic_context") or {}

                    # ⭐⭐⭐ 提取语义增强字段
                    key_entities = semantic_context.get("key_entities", [])
                    domain_tags = semantic_context.get("domain_tags", [])

                    # 计算置信度（0-100）
                    confidence = semantic_context.get("confidence", 0.0)
                    confidence_int = int(confidence * 100) if confidence else None

                    # 检查是否为表格 chunk
                    is_table = chunk_metadata.get("chunk_type") == "table_sheet" or chunk_metadata.get("is_table", False)

                    chunk = DocumentChunk(
                        chunk_id=f"doc_{document_id}_chunk_{i}",
                        document_id=document_id,
                        project_id=project_id,
                        text=chunk_data['text'],
                        text_length=len(chunk_data['text']),
                        chunk_index=i,
                        total_chunks=len(vectorized_chunks),
                        embedding=chunk_data.get("embedding", chunk_data.get("vector")),
                        embedding_model=(
                            "sentence-transformers"
                            if chunk_data.get("vector") is not None
                            else "tfidf-local"
                        ),
                        chunk_metadata=dict(chunk_metadata or metadata or {}),

                        # ⭐⭐⭐ 新增：语义增强字段
                        chapter_title=semantic_context.get("chapter"),
                        section_title=semantic_context.get("section"),
                        subsection_title=semantic_context.get("subsection"),
                        key_entities=key_entities if key_entities else None,
                        domain_tags=domain_tags if domain_tags else None,
                        primary_domain=semantic_context.get("primary_domain"),
                        temporal_context=semantic_context.get("temporal_context"),
                        spatial_context=semantic_context.get("spatial_context"),
                        chunk_role=semantic_context.get("chunk_role"),
                        chunk_summary=semantic_context.get("prev_chunk_summary") or semantic_context.get("next_chunk_summary"),
                        enhanced_text=chunk_metadata.get("enhanced_text"),
                        enhancement_confidence=confidence_int,

                        # ⭐⭐⭐ 表格相关字段
                        is_table_chunk=1 if is_table else 0,
                        table_sheet_name=chunk_metadata.get("sheet_name"),
                        table_row_range=chunk_metadata.get("row_range"),
                        structured_data=chunk_metadata.get("structured_data"),

                        created_at=datetime.utcnow(),
                        vectorized_at=datetime.utcnow()
                    )
                    self.db.add(chunk)

                self.db.commit()
                logger.info(f"✅ 已保存 {len(vectorized_chunks)} 个chunks到SQLite数据库")

                # 更新project_documents的word_count
                from app.models.project import ProjectDocument
                doc = self.db.query(ProjectDocument).filter(
                    ProjectDocument.id == document_id
                ).first()
                if doc:
                    from app.services.text_stats import count_words
                    # 分块可能带重叠窗口，按 chunks 求和会重复计算；文档总字数
                    # 必须以原始抽取正文为准，避免中文文件在多次处理后显示不同数字。
                    total_words = count_words(text_content or "")
                    doc.word_count = total_words
                    doc.chunk_count = len(vectorized_chunks)
                    doc.vector_collection = "sqlite:document_chunks"
                    self.db.commit()
                    logger.info(f"✅ 更新文档word_count: {total_words}")

            except Exception as e:
                logger.error(f"❌ 保存chunks到SQLite失败: {e}", exc_info=True)
                self.db.rollback()
            # ===== 结束chunks保存 =====

            # ===== 新增：填充fact_statements表 =====
            try:
                from app.services.fact_statement_populator import FactStatementPopulator

                logger.info(f"📊 开始填充fact_statements表")
                populator = FactStatementPopulator(self.db)

                inserted = populator.populate(
                    document_id=document_id,
                    project_id=project_id,
                    chunks=chunks,
                    metadata=metadata
                )

                logger.info(f"✅ 已填充 {inserted} 条fact_statements记录")

            except Exception as e:
                logger.error(f"⚠️ 填充fact_statements失败: {e}", exc_info=True)
                # 不抛出异常，允许继续
            # ===== 结束fact_statements填充 =====

            # ===== 数据联邦登记：文档 -> 事实，建立可追溯血缘 =====
            try:
                self._sync_federation_objects(
                    document_id=document_id,
                    project_id=project_id,
                    metadata=metadata,
                )
            except Exception as e:
                # 联邦索引是增强层，不能回滚已经完成的主结构化数据。
                logger.warning(f"⚠️ 数据联邦登记失败，保留主链路结果: {e}", exc_info=True)
            # ===== 结束数据联邦登记 =====

            enrichment_results: List[Dict[str, Any]] = []
            if app_settings.ENABLE_EXTERNAL_ENRICHMENT:
                enrichment_results = self._run_external_enrichment(
                    document_id=document_id,
                    project_id=project_id,
                    text_content=text_content,
                    metadata=metadata,
                )

            if not app_settings.ENABLE_EXTERNAL_ENRICHMENT:
                logger.info("ℹ️ 外部增强链路已关闭，仅保留SQLite主结构化存储")

            if enrichment_results:
                doc = self.db.query(
                    __import__("app.models.project", fromlist=["ProjectDocument"]).ProjectDocument
                ).filter_by(id=document_id).first()
                if doc:
                    extra_data = dict(doc.extra_data or {})
                    extra_data["plugin_enrichment"] = enrichment_results
                    doc.extra_data = extra_data
                    self.db.commit()

            # 清理checkpoint
            self._clear_checkpoint(document_id)

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "document_id": document_id,
                "chunks_count": len(chunks),
                "processing_time": processing_time,
                "stages_completed": ["chunking", "vectorization", "storage"],
                "chunks": vectorized_chunks  # ✅ 添加chunks数据，供调用者保存到SQLite
            }

            logger.info(f"✅ 文档处理完成: {len(chunks)}个块, 耗时{processing_time:.2f}秒")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"文档处理失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            result = {
                "success": False,
                "document_id": document_id,
                "processing_time": processing_time,
                "error": error_msg,
                "error_type": type(e).__name__,
                "checkpoint_available": self._has_checkpoint(document_id)
            }

            return result

    def _sync_federation_objects(
        self,
        document_id: int,
        project_id: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """幂等登记文档和事实对象，统一主表与联邦血缘。"""
        from app.models.federation import FieldMindObject, FactStatement
        from app.services.data_federation_service import DataFederationService

        federation = DataFederationService(self.db)

        def find_object(object_type: str, record_id: int):
            candidates = self.db.query(FieldMindObject).filter(
                FieldMindObject.project_id == project_id,
                FieldMindObject.object_type == object_type,
            ).all()
            for candidate in candidates:
                storage = candidate.storage_info or {}
                if str(storage.get("record_id")) == str(record_id):
                    return candidate
            return None

        document_object = find_object("document", document_id)
        if not document_object:
            document_fid = federation.register_document(
                doc_id=document_id,
                project_id=project_id,
                metadata={
                    "title": (metadata or {}).get("filename") or f"document_{document_id}",
                    "document_id": document_id,
                    "source": "document_processing_pipeline",
                },
            )
            document_object = self.db.query(FieldMindObject).filter(
                FieldMindObject.fid == document_fid
            ).first()

        if not document_object:
            return

        facts = self.db.query(FactStatement).filter(
            FactStatement.document_id == document_id,
            FactStatement.project_id == project_id,
        ).all()
        for fact in facts:
            fact_object = find_object("fact", fact.id)
            if fact_object:
                continue
            federation.register_fact(
                fact_id=fact.id,
                project_id=project_id,
                document_id=document_id,
                source_fid=document_object.fid,
                metadata={
                    "statement_type": fact.statement_type,
                    "statement_preview": fact.statement_text[:240],
                    "confidence": fact.confidence_score,
                },
            )

        self.db.commit()
        logger.info(
            "✅ 数据联邦登记完成: document=%s facts=%s",
            document_id,
            len(facts),
        )

    def _chunk_with_retry(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        sources: Optional[List[Dict]] = None  # ⭐⭐⭐ 新增 sources 参数
    ) -> List[Dict]:
        """带重试的切分"""
        for attempt in range(self.max_retries):
            try:
                # ⭐⭐⭐ 传递 sources 给 chunker
                if sources:
                    logger.info(f"   传递 {len(sources)} 个 sources 到 chunker")
                    chunks = self.chunker.chunk_document(text, metadata, sources=sources)
                else:
                    chunks = self.chunker.chunk_document(text, metadata)

                if not chunks:
                    raise ChunkingError("切分结果为空")
                return chunks

            except Exception as e:
                logger.warning(f"切分失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数退避
                else:
                    raise ChunkingError(f"切分失败，已重试{self.max_retries}次: {e}")

    def _vectorize_with_retry(self, chunks: List[Dict]) -> List[Dict]:
        """带重试的向量化（支持语义嵌入和TF-IDF）"""
        for attempt in range(self.max_retries):
            try:
                # 检查vectorizer类型
                from sentence_transformers import SentenceTransformer

                if isinstance(self.vectorizer, SentenceTransformer):
                    # 使用语义嵌入
                    logger.info("📊 使用Sentence-Transformers进行语义向量化")

                    from app.services.semantic_embedding import encode_chunks

                    # 提取文本
                    texts = [chunk.get('text', '') for chunk in chunks]

                    # 批量编码
                    embeddings = encode_chunks(texts, batch_size=32)

                    if not embeddings or len(embeddings) != len(chunks):
                        raise VectorizationError(
                            f"语义编码数量不匹配: {len(embeddings) if embeddings else 0} != {len(chunks)}"
                        )

                    # 将向量添加到chunks
                    vectorized = []
                    for i, chunk in enumerate(chunks):
                        chunk_with_vec = chunk.copy()
                        chunk_with_vec['vector'] = embeddings[i].tolist()  # numpy转list
                        vectorized.append(chunk_with_vec)

                    logger.info(f"✅ 语义向量化完成：{len(vectorized)}个块，维度{len(vectorized[0]['vector']) if vectorized and 'vector' in vectorized[0] else 'unknown'}")
                    return vectorized

                else:
                    # 降级使用TF-IDF
                    logger.info("📊 使用TF-IDF进行向量化（降级模式）")
                    vectorized = self.vectorizer.vectorize_chunks(chunks, batch_size=32)

                    if not vectorized:
                        raise VectorizationError("向量化结果为空")

                    if len(vectorized) != len(chunks):
                        raise VectorizationError(
                            f"向量化数量不匹配: {len(vectorized)} != {len(chunks)}"
                        )

                    return vectorized

            except Exception as e:
                logger.warning(f"向量化失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise VectorizationError(f"向量化失败，已重试{self.max_retries}次: {e}")

    def _store_with_retry(
        self,
        document_id: int,
        project_id: int,
        chunks: List[Dict]
    ) -> None:
        """带重试的存储，统一通过 ORM 写入当前分块模型。"""
        for attempt in range(self.max_retries):
            try:
                from app.models.document_chunk import DocumentChunk
                from app.services.text_structurization_quantifier import create_quantifier
                from app.services.business_dimension_classifier import create_classifier

                self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_id
                ).delete(synchronize_session=False)

                quantifier = create_quantifier()
                dimension_classifier = create_classifier()
                for i, chunk in enumerate(chunks):
                    chunk_text = chunk.get("text", "")
                    if not chunk_text.strip():
                        continue
                    embedding_data = chunk.get("embedding", chunk.get("vector"))
                    metrics = quantifier.quantify(chunk_text)
                    dimension = dimension_classifier.classify(chunk_text)
                    dimension_dict = dimension_classifier.to_dict(dimension)
                    structured_metadata = {
                        **dict(chunk.get("metadata") or {}),
                        "quantification": {
                            "word_count": metrics.word_count,
                            "sentence_count": metrics.sentence_count,
                            "exclamation_count": metrics.exclamation_count,
                            "emotion_polarity": metrics.emotion_polarity,
                            "subjectivity": metrics.subjectivity,
                            "emotion_word_density": metrics.emotion_word_density,
                            "avg_word_length": metrics.avg_word_length,
                        },
                        "business_dimension": dimension_dict,
                    }
                    self.db.add(DocumentChunk(
                        chunk_id=f"doc{document_id}_chunk{i}",
                        document_id=document_id,
                        project_id=project_id,
                        text=chunk_text,
                        text_length=len(chunk_text),
                        chunk_index=chunk.get("chunk_index", i),
                        total_chunks=chunk.get("total_chunks", len(chunks)),
                        embedding=embedding_data,
                        embedding_model="semantic" if embedding_data else None,
                        chunk_metadata=structured_metadata,
                        metadata_json=structured_metadata,
                        prev_chunk_id=chunk.get("prev_chunk_id"),
                        next_chunk_id=chunk.get("next_chunk_id"),
                        vectorized_at=datetime.utcnow() if embedding_data else None,
                        created_at=datetime.utcnow(),
                        page_number=chunk.get("page_number"),
                        speaker=chunk.get("speaker"),
                        timestamp_start=chunk.get("timestamp_start"),
                        timestamp_end=chunk.get("timestamp_end"),
                        structured_data=chunk.get("structured_data"),
                    ))

                self.db.commit()
                logger.info("✅ 存储成功: %s个块", len(chunks))
                return
            except Exception as e:
                self.db.rollback()
                logger.warning("存储失败 (尝试 %s/%s): %s", attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise StorageError(f"存储失败，已重试{self.max_retries}次: {e}")

    def _save_checkpoint(self, document_id: int, stage: str, data: Dict):
        """保存检查点"""
        if not self.enable_checkpoints:
            return

        checkpoint_path = Path(f"/tmp/fieldmind_checkpoint_{document_id}.json")
        checkpoint = {
            "document_id": document_id,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        try:
            checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False))
            logger.debug(f"💾 Checkpoint saved: {stage}")
        except Exception as e:
            logger.warning(f"保存checkpoint失败: {e}")

    def _load_checkpoint(self, document_id: int) -> Optional[Dict]:
        """加载检查点"""
        if not self.enable_checkpoints:
            return None

        checkpoint_path = Path(f"/tmp/fieldmind_checkpoint_{document_id}.json")
        if not checkpoint_path.exists():
            return None

        try:
            checkpoint = json.loads(checkpoint_path.read_text())
            return checkpoint
        except Exception as e:
            logger.warning(f"加载checkpoint失败: {e}")
            return None

    def _has_checkpoint(self, document_id: int) -> bool:
        """检查是否有checkpoint"""
        if not self.enable_checkpoints:
            return False
        checkpoint_path = Path(f"/tmp/fieldmind_checkpoint_{document_id}.json")
        return checkpoint_path.exists()

    def _clear_checkpoint(self, document_id: int):
        """清理检查点"""
        if not self.enable_checkpoints:
            return

        checkpoint_path = Path(f"/tmp/fieldmind_checkpoint_{document_id}.json")
        try:
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                logger.debug(f"🗑️ Checkpoint cleared")
        except Exception as e:
            logger.warning(f"清理checkpoint失败: {e}")

    def _resume_from_checkpoint(self, checkpoint: Dict) -> Dict[str, Any]:
        """从检查点恢复"""
        document_id = checkpoint["document_id"]
        project_id = checkpoint.get("project_id")
        stage = checkpoint["stage"]
        data = checkpoint["data"]

        logger.info(f"♻️ 从 {stage} 阶段恢复 (document_id={document_id})")

        try:
            if stage == "chunked":
                # 从向量化阶段继续
                chunks = data["chunks"]
                logger.info(f"🧮 继续向量化 ({len(chunks)}个块)")
                vectorized_chunks = self._vectorize_with_retry(chunks)

                logger.info(f"💾 存储到ChromaDB")
                chroma_result = self._store_chunks_in_chroma(
                    document_id=document_id,
                    project_id=project_id or 0,
                    chunks=vectorized_chunks,
                )
                if chroma_result.get("status") == "success":
                    logger.info(f"✅ 已存储 {chroma_result.get('chunks', 0)} 个块到ChromaDB")
                else:
                    logger.info(f"ℹ️ 跳过ChromaDB: {chroma_result.get('reason')}")

                # 清理checkpoint
                self._clear_checkpoint(document_id)

                return {
                    "success": True,
                    "document_id": document_id,
                    "chunks_count": len(chunks),
                    "resumed": True,
                    "from_stage": stage
                }

            elif stage == "vectorized":
                # 从存储阶段继续
                chunks = data["chunks"]

                logger.info(f"💾 存储到ChromaDB ({len(chunks)}个块)")
                chroma_result = self._store_chunks_in_chroma(
                    document_id=document_id,
                    project_id=project_id or 0,
                    chunks=chunks,
                )
                if chroma_result.get("status") == "success":
                    logger.info(f"✅ 已存储 {chroma_result.get('chunks', 0)} 个块到ChromaDB")
                else:
                    logger.info(f"ℹ️ 跳过ChromaDB: {chroma_result.get('reason')}")

                # 清理checkpoint
                self._clear_checkpoint(document_id)

                return {
                    "success": True,
                    "document_id": document_id,
                    "chunks_count": len(chunks),
                    "resumed": True,
                    "from_stage": stage
                }

        except Exception as e:
            logger.error(f"从checkpoint恢复失败: {e}")
            raise

    def batch_process_documents(
        self,
        documents: List[Dict[str, Any]],
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        批量处理文档

        Args:
            documents: [{"document_id": int, "project_id": int, "text": str}, ...]
            on_progress: 进度回调 (current, total, result)

        Returns:
            {
                "total": int,
                "success": int,
                "failed": int,
                "results": [...]
            }
        """
        results = []
        success_count = 0
        failed_count = 0

        for i, doc in enumerate(documents):
            logger.info(f"处理文档 {i + 1}/{len(documents)}")

            result = self.process_document(
                document_id=doc["document_id"],
                project_id=doc["project_id"],
                text_content=doc["text"],
                metadata=doc.get("metadata")
            )

            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failed_count += 1

            # 进度回调
            if on_progress:
                on_progress(i + 1, len(documents), result)

        return {
            "total": len(documents),
            "success": success_count,
            "failed": failed_count,
            "results": results
        }

    def _update_statistics(self, project_id: int, structured_records: List):
        """
        更新统计表 - 主题统计和实体统计
        """
        try:
            from app.models.structured_insight import TopicStatistics, EntityStatistics
            from sqlalchemy import func

            # 1. 更新主题统计
            topic_counts = {}
            for record in structured_records:
                if record.topics:
                    topics = record.topics.split(',')
                    for topic in topics:
                        topic = topic.strip()
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

            for topic, count in topic_counts.items():
                # 查找是否已存在
                stat = self.db.query(TopicStatistics).filter(
                    TopicStatistics.project_id == project_id,
                    TopicStatistics.topic == topic
                ).first()

                if stat:
                    stat.count += count
                    stat.last_updated = datetime.now()
                else:
                    stat = TopicStatistics(
                        project_id=project_id,
                        topic=topic,
                        count=count
                    )
                    self.db.add(stat)

            # 2. 更新实体统计
            entity_counts = {'person': {}, 'location': {}}

            for record in structured_records:
                # 人名统计
                if record.persons:
                    persons = record.persons.split(',')
                    for person in persons:
                        person = person.strip()
                        entity_counts['person'][person] = entity_counts['person'].get(person, 0) + 1

                # 地名统计
                if record.locations:
                    locations = record.locations.split(',')
                    for location in locations:
                        location = location.strip()
                        entity_counts['location'][location] = entity_counts['location'].get(location, 0) + 1

            for entity_type, entities in entity_counts.items():
                for entity_name, count in entities.items():
                    # 查找是否已存在
                    stat = self.db.query(EntityStatistics).filter(
                        EntityStatistics.project_id == project_id,
                        EntityStatistics.entity_type == entity_type,
                        EntityStatistics.entity_name == entity_name
                    ).first()

                    if stat:
                        stat.count += count
                        stat.last_updated = datetime.now()
                    else:
                        stat = EntityStatistics(
                            project_id=project_id,
                            entity_type=entity_type,
                            entity_name=entity_name,
                            count=count
                        )
                        self.db.add(stat)

            self.db.commit()
            logger.info(f"✅ 统计表更新完成: {len(topic_counts)}个主题, {sum(len(e) for e in entity_counts.values())}个实体")

        except Exception as e:
            logger.error(f"❌ 更新统计表失败: {e}", exc_info=True)
            self.db.rollback()
