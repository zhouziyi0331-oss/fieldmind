"""
Agent 3: VectorizationAgent V2 增强版
不仅仅是向量化，而是：深度理解 + 多维标注 + 智能融合
专为田野调查、文化遗产、民族志研究设计

核心能力：
1. 实体识别（遗产、文化、方言）
2. 关系抽取（组织架构、外部支持）
3. 领域标注（UNESCO分类）
4. 方言处理（文化背景）
5. 多向量生成（4×1024维）
6. 向量融合（协同增强）⭐⭐⭐
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from app.models.enriched_chunk import (
    EnrichedChunk,
    VectorizedChunk,
    MultiVectorResult,
    FusedVectorResult
)
from app.models.entity import Entity
from app.models.chunk_entity import ChunkEntity
from app.services.entity_recognition_service import EntityRecognitionService
from app.services.relation_extraction_service import RelationExtractionService
from app.services.domain_tagging_service import DomainTaggingService
from app.services.dialect_normalization_service import DialectNormalizationService
from app.services.multi_vector_generator import MultiVectorGenerator
from app.services.vector_fusion_service import VectorFusionService

logger = logging.getLogger(__name__)


class VectorizationAgent:
    """Agent 3: VectorizationAgent V2 增强版

    工作流程：
    1. 接收 chunks（来自Agent 2）
    2. 阶段1: 深度标注（实体、关系、领域、方言）
    3. 阶段2: 多向量生成（4个1024维向量）
    4. 阶段3: 向量融合（协同增强）
    5. 阶段4: 质量验证
    6. 阶段5: 双存储（SQL + ChromaDB）
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        fusion_strategy: str = "gated_concat"  # "concat" | "weighted_concat" | "gated_concat" | "attention_concat"
    ):
        """初始化VectorizationAgent

        Args:
            model_name: FlagEmbedding模型名称
            fusion_strategy: 向量融合策略（推荐gated_concat）
        """
        self.model_name = model_name
        self.fusion_strategy = fusion_strategy

        # 阶段1: 深度标注服务 ⭐
        self.entity_recognizer = EntityRecognitionService()
        self.relation_extractor = RelationExtractionService()
        self.domain_tagger = DomainTaggingService()
        self.dialect_processor = DialectNormalizationService()

        # 阶段2: 多向量生成器 ⭐
        self.vector_generator = MultiVectorGenerator(model_name=model_name)

        # 阶段3: 向量融合服务 ⭐⭐⭐
        self.vector_fusion = VectorFusionService()

        logger.info(
            f"VectorizationAgent V2 初始化完成 - "
            f"模型: {model_name}, 融合策略: {fusion_strategy}"
        )

    def vectorize_chunks(
        self,
        chunks: List[Dict[str, Any]],
        region: Optional[str] = None,
        store_to_db: bool = False,
        document_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """向量化chunks（完整流程）

        Args:
            chunks: chunks列表（来自Agent 2）
            region: 地域（用于方言识别）
            store_to_db: 是否存储到数据库
            document_id: 文档ID
            project_id: 项目ID
            db_session: 数据库会话

        Returns:
            向量化结果
        """
        logger.info(f"开始向量化 {len(chunks)} 个chunks")

        vectorized_chunks = []
        enrichment_stats = {
            "total_entities": 0,
            "total_relations": 0,
            "total_domain_tags": 0,
            "total_dialect_terms": 0,
            "avg_coherence": 0.0,
            "avg_enhancement": 0.0,
            "quality_passed": 0
        }

        for i, chunk in enumerate(chunks):
            try:
                # ============================================================
                # 阶段1: 深度标注 ⭐
                # ============================================================
                enriched_chunk = self._enrich_chunk(chunk, region)

                # 统计
                enrichment_stats["total_entities"] += len(enriched_chunk.entities)
                enrichment_stats["total_relations"] += len(enriched_chunk.relations)
                enrichment_stats["total_domain_tags"] += len(enriched_chunk.domain_tags)
                if enriched_chunk.dialect_result:
                    enrichment_stats["total_dialect_terms"] += len(enriched_chunk.dialect_result.dialect_terms)

                # ============================================================
                # 阶段2: 多向量生成 ⭐
                # ============================================================
                multi_vector = self.vector_generator.generate_multi_vectors(enriched_chunk)

                # ============================================================
                # 阶段3: 向量融合 ⭐⭐⭐
                # ============================================================
                fused_vector = self.vector_fusion.fuse_vectors(
                    multi_vector,
                    strategy=self.fusion_strategy
                )

                # 统计
                enrichment_stats["avg_coherence"] += fused_vector.coherence_score
                enrichment_stats["avg_enhancement"] += fused_vector.enhancement_score
                if fused_vector.quality_passed:
                    enrichment_stats["quality_passed"] += 1

                # ============================================================
                # 阶段4: 构建VectorizedChunk
                # ============================================================
                vectorized_chunk = self._build_vectorized_chunk(
                    enriched_chunk,
                    multi_vector,
                    fused_vector
                )

                vectorized_chunks.append(vectorized_chunk)

                logger.info(
                    f"Chunk {i+1}/{len(chunks)} 向量化完成 - "
                    f"实体: {len(enriched_chunk.entities)}, "
                    f"关系: {len(enriched_chunk.relations)}, "
                    f"一致性: {fused_vector.coherence_score:.3f}, "
                    f"增强度: {fused_vector.enhancement_score:.3f}"
                )

            except Exception as e:
                logger.error(f"Chunk {i+1} 向量化失败: {e}", exc_info=True)
                continue

        # 计算平均值
        if vectorized_chunks:
            enrichment_stats["avg_coherence"] /= len(vectorized_chunks)
            enrichment_stats["avg_enhancement"] /= len(vectorized_chunks)

        logger.info(
            f"向量化完成 - 总计: {len(vectorized_chunks)}/{len(chunks)} 个chunks, "
            f"实体: {enrichment_stats['total_entities']}, "
            f"关系: {enrichment_stats['total_relations']}, "
            f"平均一致性: {enrichment_stats['avg_coherence']:.3f}, "
            f"平均增强度: {enrichment_stats['avg_enhancement']:.3f}, "
            f"质量通过: {enrichment_stats['quality_passed']}/{len(vectorized_chunks)}"
        )

        # ============================================================
        # 阶段5: 存储到数据库（如果需要）
        # ============================================================
        if store_to_db and document_id and project_id and db_session:
            self._store_to_database(
                vectorized_chunks,
                document_id,
                project_id,
                db_session
            )

        return {
            "vectorized_chunks": vectorized_chunks,
            "statistics": enrichment_stats,
            "model": self.model_name,
            "fusion_strategy": self.fusion_strategy
        }

    def _enrich_chunk(
        self,
        chunk: Dict[str, Any],
        region: Optional[str] = None
    ) -> EnrichedChunk:
        """阶段1: 深度标注 ⭐

        Args:
            chunk: 原始chunk
            region: 地域

        Returns:
            增强后的chunk
        """
        text = chunk.get("text", "")
        chunk_id = chunk.get("chunk_id", "")
        sources = chunk.get("sources", [])
        chunk_metadata = chunk.get("metadata", {})

        # 1. 实体识别 ⭐
        entities = self.entity_recognizer.recognize_entities(text, region)

        # 2. 关系抽取 ⭐
        relations = self.relation_extractor.extract_relations(text, entities)

        # 3. 领域标注 ⭐
        domain_tags = self.domain_tagger.tag_domains(text, entities)

        # 4. 方言处理 ⭐
        dialect_result = None
        if any(e.type.value == "dialect_term" for e in entities):
            dialect_result = self.dialect_processor.process_dialect(text, region)

        # 构建EnrichedChunk
        enriched_chunk = EnrichedChunk(
            chunk_id=chunk_id,
            text=text,
            sources=sources,
            chunk_metadata=chunk_metadata,
            entities=entities,
            relations=relations,
            domain_tags=domain_tags,
            dialect_result=dialect_result,
            enrichment_metadata={
                "enriched_at": datetime.utcnow().isoformat(),
                "num_entities": len(entities),
                "num_relations": len(relations),
                "num_domain_tags": len(domain_tags),
                "num_dialect_terms": len(dialect_result.dialect_terms) if dialect_result else 0
            }
        )

        return enriched_chunk

    def _build_vectorized_chunk(
        self,
        enriched_chunk: EnrichedChunk,
        multi_vector: MultiVectorResult,
        fused_vector: FusedVectorResult
    ) -> VectorizedChunk:
        """构建VectorizedChunk

        Args:
            enriched_chunk: 增强后的chunk
            multi_vector: 多向量结果
            fused_vector: 融合向量结果

        Returns:
            向量化chunk
        """
        # 构建metadata（包含所有标签）⭐⭐⭐
        metadata = {
            # 原始metadata
            **enriched_chunk.chunk_metadata,

            # 实体标签 ⭐
            "entities": [
                {
                    "text": e.text,
                    "type": e.type.value,
                    "confidence": e.confidence,
                    "category": e.category,
                    "subcategory": e.subcategory,
                    "region": e.region,
                    "ethnic_group": e.ethnic_group,
                    "heritage_level": e.heritage_level,
                    "cultural_context": e.cultural_context,
                    "standard_term": e.standard_term,
                }
                for e in enriched_chunk.entities
            ],

            # 关系标签 ⭐
            "relations": [
                {
                    "subject": r.subject,
                    "relation": r.relation.value,
                    "object": r.object,
                    "confidence": r.confidence,
                    "position": r.position,
                    "support_type": r.support_type,
                    "project_name": r.project_name,
                }
                for r in enriched_chunk.relations
            ],

            # 领域标签 ⭐
            "domain_tags": [
                {
                    "category": t.category.value,
                    "subcategory": t.subcategory,
                    "sub_subcategory": t.sub_subcategory,
                    "confidence": t.confidence,
                    "keywords": t.keywords,
                    "unesco_domain": t.unesco_domain,
                }
                for t in enriched_chunk.domain_tags
            ],

            # 方言信息 ⭐
            "dialect_terms": [
                {
                    "term": dt.term,
                    "standard": dt.standard,
                    "region": dt.region,
                    "cultural_meaning": dt.cultural_meaning,
                }
                for dt in enriched_chunk.dialect_result.dialect_terms
            ] if enriched_chunk.dialect_result else [],

            # 向量质量指标 ⭐
            "vector_quality": {
                "text_quality": multi_vector.quality_scores.get("text", 0.0),
                "entity_quality": multi_vector.quality_scores.get("entity", 0.0),
                "relation_quality": multi_vector.quality_scores.get("relation", 0.0),
                "domain_quality": multi_vector.quality_scores.get("domain", 0.0),
                "coherence": fused_vector.coherence_score,
                "enhancement": fused_vector.enhancement_score,
            },

            # 溯源信息（零拷贝）⭐
            "sources": enriched_chunk.sources,
        }

        # 构建VectorizedChunk
        vectorized_chunk = VectorizedChunk(
            chunk_id=enriched_chunk.chunk_id,
            text=enriched_chunk.text,
            text_embedding=multi_vector.text_embedding,
            entity_embedding=multi_vector.entity_embedding,
            relation_embedding=multi_vector.relation_embedding,
            domain_embedding=multi_vector.domain_embedding,
            fused_embedding=fused_vector.fused_embedding,
            embedding_model=self.model_name,
            embedding_dim=fused_vector.dimensions,
            fusion_strategy=fused_vector.strategy,
            metadata=metadata,
            vectorized_at=datetime.utcnow().isoformat(),
            quality_metrics={
                "coherence_score": fused_vector.coherence_score,
                "enhancement_score": fused_vector.enhancement_score,
                "quality_passed": fused_vector.quality_passed,
            }
        )

        return vectorized_chunk

    def _store_to_database(
        self,
        vectorized_chunks: List[VectorizedChunk],
        document_id: int,
        project_id: int,
        db_session: Any
    ):
        """阶段5: 存储到数据库（SQL + ChromaDB）

        Args:
            vectorized_chunks: 向量化chunks
            document_id: 文档ID
            project_id: 项目ID
            db_session: 数据库会话
        """
        try:
            logger.info(f"开始存储 {len(vectorized_chunks)} 个向量化chunks的Entity数据到数据库")

            stored_entity_count = 0
            stored_relation_count = 0

            for vectorized_chunk in vectorized_chunks:
                chunk_id = vectorized_chunk.chunk_id

                # 从enriched_chunk中提取entities
                if hasattr(vectorized_chunk, 'enriched_chunk') and vectorized_chunk.enriched_chunk:
                    enriched = vectorized_chunk.enriched_chunk

                    # 🔥 断点修复：存储Entity到entities表
                    if hasattr(enriched, 'entities') and enriched.entities:
                        for entity_data in enriched.entities:
                            # 检查Entity是否已存在（根据name和type）
                            existing_entity = db_session.query(Entity).filter(
                                Entity.name == entity_data.name,
                                Entity.entity_type == entity_data.entity_type.value
                            ).first()

                            if existing_entity:
                                # 更新现有Entity的document_ids和mention_count
                                doc_ids = existing_entity.document_ids or []
                                if document_id not in doc_ids:
                                    doc_ids.append(document_id)
                                    existing_entity.document_ids = doc_ids
                                existing_entity.mention_count = (existing_entity.mention_count or 0) + 1
                                entity = existing_entity
                            else:
                                # 创建新Entity
                                entity = Entity(
                                    entity_type=entity_data.entity_type.value,
                                    name=entity_data.name,
                                    document_ids=[document_id],
                                    confidence=entity_data.confidence,
                                    mention_count=1,
                                    attributes=entity_data.attributes or {}
                                )
                                db_session.add(entity)
                                db_session.flush()  # 获取entity.id

                            # 🔥 断点修复：创建Chunk-Entity关联
                            chunk_entity = ChunkEntity(
                                chunk_id=chunk_id,
                                entity_id=entity.id,
                                confidence=entity_data.confidence,
                                mention_context=entity_data.context if hasattr(entity_data, 'context') else None,
                                position_start=entity_data.start_pos if hasattr(entity_data, 'start_pos') else None,
                                position_end=entity_data.end_pos if hasattr(entity_data, 'end_pos') else None
                            )
                            db_session.add(chunk_entity)
                            stored_entity_count += 1

                    # Relations的存储（保留到metadata，未来可扩展为独立表）
                    if hasattr(enriched, 'relations') and enriched.relations:
                        stored_relation_count += len(enriched.relations)

            # 提交所有更改
            db_session.commit()

            logger.info(f"✅ 成功存储 {stored_entity_count} 个Entity关联, {stored_relation_count} 个Relations（metadata）")

        except Exception as e:
            logger.error(f"数据库存储失败: {e}", exc_info=True)
            db_session.rollback()
            raise

    def query_similar(
        self,
        query_text: str,
        top_k: int = 5,
        project_id: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """语义检索（查询相似chunks）

        Args:
            query_text: 查询文本
            top_k: 返回top-k结果
            project_id: 项目ID（过滤）
            filter_metadata: 额外的过滤条件

        Returns:
            相似chunks列表
        """
        # TODO: 实现语义检索逻辑
        # 1. 将query_text向量化
        # 2. 在ChromaDB中检索相似向量
        # 3. 返回结果
        logger.info(f"语义检索: {query_text}, top_k={top_k}")
        pass

    def get_statistics(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        return {
            "agent_name": "VectorizationAgent V2",
            "model": self.model_name,
            "fusion_strategy": self.fusion_strategy,
            "embedding_dim": 1024,
            "fused_dim": 4096,
            "capabilities": [
                "实体识别（遗产、文化、方言）",
                "关系抽取（组织架构、外部支持）",
                "领域标注（UNESCO分类）",
                "方言处理（文化背景）",
                "多向量生成（4×1024维）",
                "向量融合（协同增强）",
            ]
        }


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    # 初始化Agent
    agent = VectorizationAgent(
        model_name="BAAI/bge-large-zh-v1.5",
        fusion_strategy="gated_concat"  # 推荐：门控融合
    )

    # 示例chunk（来自Agent 2）
    test_chunks = [
        {
            "chunk_id": "chunk_001",
            "text": "布依族蜡染是国家级非物质文化遗产，第一代传承人是张师傅，第二代传承人是李师傅。中国文化遗产保护协会资助了10万元用于蜡染保护项目。当地人喜欢去赶场买洋芋。",
            "sources": [],
            "metadata": {
                "chunk_type": "semantic"
            }
        }
    ]

    # 向量化
    result = agent.vectorize_chunks(
        chunks=test_chunks,
        region="贵州"
    )

    # 打印结果
    print(f"向量化完成: {len(result['vectorized_chunks'])} 个chunks")
    print(f"统计信息: {result['statistics']}")
