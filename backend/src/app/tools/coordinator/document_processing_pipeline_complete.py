"""
完整的文档处理流水线 - 带错误处理和重试机制
功能：文档上传 -> 切分 -> 向量化 -> 存储 -> 错误恢复
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import traceback

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

    def _init_services(self):
        """延迟初始化服务"""
        if self.chunker is None:
            from app.tools.document import UnifiedDocumentChunker
            self.chunker = UnifiedDocumentChunker()

        if self.vectorizer is None:
            # 优先使用真实的语义嵌入
            from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend

            logger.info("🔄 加载语义嵌入模型（Sentence-Transformers）")
            self.vectorizer = get_embedding_model()

            if self.vectorizer is None:
                logger.warning("⚠️ 语义嵌入模型加载失败，降级使用TF-IDF")
                from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend
                self.vectorizer = TfidfVectorizationService(embedding_dim=384)
            else:
                logger.info("✅ 使用Sentence-Transformers进行语义向量化")

    def process_document(
        self,
        document_id: int,
        project_id: int,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理文档 - 完整流程

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

        try:
            # 初始化服务
            self._init_services()

            # 检查是否有未完成的checkpoint
            checkpoint = self._load_checkpoint(document_id)
            if checkpoint:
                logger.info(f"📂 检测到未完成的处理，从checkpoint恢复: {checkpoint['stage']}")
                return self._resume_from_checkpoint(checkpoint)

            # 阶段1: 切分文档
            logger.info(f"📄 阶段1: 切分文档 (document_id={document_id})")
            chunks = self._chunk_with_retry(text_content, metadata)
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
                        metadata=structured_data['metadata'],
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

            # 阶段3: 存储到ChromaDB
            logger.info(f"💾 阶段3: 存储到ChromaDB")
            try:
                from app.core.rag_engine import rag_engine

                if rag_engine and rag_engine.collection:
                    # 准备存储到ChromaDB
                    ids = []
                    documents = []
                    metadatas = []

                    for i, chunk in enumerate(vectorized_chunks):
                        chunk_id = f"doc{document_id}_chunk{i}"
                        ids.append(chunk_id)
                        documents.append(chunk['text'])

                        # 元数据（过滤None值和复杂类型）
                        meta = {
                            'document_id': document_id,
                            'chunk_index': i,
                            'total_chunks': len(vectorized_chunks)
                        }
                        if project_id:
                            meta['project_id'] = project_id
                        if metadata:
                            for k, v in metadata.items():
                                if v is not None:
                                    # ChromaDB只接受str/int/float/bool
                                    if isinstance(v, (str, int, float, bool)):
                                        meta[k] = v
                                    elif isinstance(v, (list, dict)):
                                        # 序列化复杂类型为JSON字符串
                                        meta[k] = json.dumps(v, ensure_ascii=False)
                        metadatas.append(meta)

                    # 批量添加到ChromaDB
                    rag_engine.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )

                    logger.info(f"✅ 已存储 {len(vectorized_chunks)} 个块到ChromaDB")
                else:
                    logger.warning(f"⚠️ ChromaDB未初始化，跳过存储")

            except Exception as e:
                logger.error(f"❌ 存储到ChromaDB失败: {e}", exc_info=True)
                # 不抛出异常，允许继续

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

            # ===== 新增：知识图谱构建 =====
            try:
                from app.tools.knowledge.graph import create_knowledge_graph

                logger.info(f"🕸️ 开始构建知识图谱")
                kg_service = create_knowledge_graph()

                # 从完整文本提取实体和关系
                entities, relations = kg_service.extract_entities_and_relations(
                    text_content,
                    document_id=document_id,
                    use_llm=True
                )

                # 添加到图谱并同步到Neo4j
                kg_service.add_entities_and_relations(entities, relations)

                logger.info(f"✅ 知识图谱构建完成: {len(entities)}个实体, {len(relations)}个关系")

            except Exception as e:
                logger.error(f"⚠️ 知识图谱构建失败（非致命）: {e}", exc_info=True)
                # 不抛出异常，允许继续
            # ===== 结束知识图谱构建 =====

            # 清理checkpoint
            self._clear_checkpoint(document_id)

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "document_id": document_id,
                "chunks_count": len(chunks),
                "processing_time": processing_time,
                "stages_completed": ["chunking", "vectorization", "storage"]
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

    def _chunk_with_retry(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """带重试的切分"""
        for attempt in range(self.max_retries):
            try:
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

                    from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend

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

                    logger.info(f"✅ 语义向量化完成：{len(vectorized)}个块，维度384")
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
        """带重试的存储"""
        for attempt in range(self.max_retries):
            try:
                cursor = self.db.cursor()

                # 先清理旧数据（如果重试）
                cursor.execute(
                    "DELETE FROM document_chunks WHERE document_id = ?",
                    (document_id,)
                )

                # 批量插入
                for i, chunk in enumerate(chunks):
                    chunk_id = f"doc{document_id}_chunk{i}"

                    # 获取向量数据
                    embedding_data = chunk.get('embedding', chunk.get('vector', []))

                    cursor.execute("""
                        INSERT INTO document_chunks (
                            chunk_id, document_id, project_id, text, text_length,
                            chunk_index, total_chunks, embedding, embedding_model,
                            chunk_metadata, prev_chunk_id, next_chunk_id,
                            vectorized_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk_id,
                        document_id,
                        project_id,
                        chunk['text'],
                        len(chunk['text']),
                        chunk.get('chunk_index', i),
                        chunk.get('total_chunks', len(chunks)),
                        json.dumps(embedding_data),
                        'tfidf-local',
                        json.dumps(chunk.get('metadata', {})),
                        chunk.get('prev_chunk_id'),
                        chunk.get('next_chunk_id'),
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat()
                    ))

                self.db.commit()
                logger.info(f"✅ 存储成功: {len(chunks)}个块")
                return

            except Exception as e:
                self.db.rollback()
                logger.warning(f"存储失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
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

                # 存储到ChromaDB
                logger.info(f"💾 存储到ChromaDB")
                try:
                    from app.core.rag_engine import rag_engine

                    if rag_engine and rag_engine.collection:
                        ids = []
                        documents = []
                        metadatas = []

                        for i, chunk in enumerate(vectorized_chunks):
                            chunk_id = f"doc{document_id}_chunk{i}"
                            ids.append(chunk_id)
                            documents.append(chunk['text'])

                            # 构建metadata，过滤None值
                            meta = {
                                'document_id': document_id,
                                'chunk_index': i,
                                'total_chunks': len(vectorized_chunks)
                            }
                            if project_id:
                                meta['project_id'] = project_id

                            metadatas.append(meta)

                        rag_engine.collection.add(
                            ids=ids,
                            documents=documents,
                            metadatas=metadatas
                        )

                        logger.info(f"✅ 已存储 {len(vectorized_chunks)} 个块到ChromaDB")
                    else:
                        logger.warning(f"⚠️ ChromaDB未初始化")

                except Exception as e:
                    logger.error(f"❌ 存储到ChromaDB失败: {e}", exc_info=True)

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

                # 存储到ChromaDB
                logger.info(f"💾 存储到ChromaDB ({len(chunks)}个块)")
                try:
                    from app.core.rag_engine import rag_engine

                    if rag_engine and rag_engine.collection:
                        ids = []
                        documents = []
                        metadatas = []

                        for i, chunk in enumerate(chunks):
                            chunk_id = f"doc{document_id}_chunk{i}"
                            ids.append(chunk_id)
                            documents.append(chunk['text'])

                            # 构建metadata，过滤None值
                            meta = {
                                'document_id': document_id,
                                'chunk_index': i,
                                'total_chunks': len(chunks)
                            }
                            if project_id:
                                meta['project_id'] = project_id

                            metadatas.append(meta)

                        rag_engine.collection.add(
                            ids=ids,
                            documents=documents,
                            metadatas=metadatas
                        )

                        logger.info(f"✅ 已存储 {len(chunks)} 个块到ChromaDB")

                except Exception as e:
                    logger.error(f"❌ 存储到ChromaDB失败: {e}", exc_info=True)

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
