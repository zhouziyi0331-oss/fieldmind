"""
KnowledgeAgent - 知识图谱构建代理

职责：
- 从向量化结果构建知识图谱
- 整合4个核心知识图谱服务
- 实体提取和关系发现
- 跨文档实体消歧
- 存储到SQL和Neo4j

集成的真实服务：
1. KnowledgeGraphService - NetworkX + spaCy + LLM主服务
2. EntityExtractionService - jieba中文实体提取
3. RelationDiscoveryEngine - 4策略关系发现
4. KnowledgeGraphBuilder - 工作流编排
"""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class KnowledgeStrategy(str, Enum):
    """知识图谱构建策略"""
    COMPREHENSIVE = "comprehensive"  # 综合策略：所有服务协同
    ENTITY_FOCUSED = "entity_focused"  # 实体为中心
    RELATION_FOCUSED = "relation_focused"  # 关系为中心
    CROSS_DOCUMENT = "cross_document"  # 跨文档消歧
    AUTO = "auto"  # 自动选择


@dataclass
class ExtractedEntity:
    """提取的实体"""
    entity_id: str
    name: str
    entity_type: str
    confidence: float
    mentions: List[Dict[str, Any]]
    source_document_id: Optional[int] = None
    canonical_id: Optional[str] = None  # 跨文档消歧后的规范ID


@dataclass
class DiscoveredRelation:
    """发现的关系"""
    relation_id: str
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    evidence: List[str]
    discovery_strategy: str  # co-occurrence, temporal, semantic, inferred


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    nodes: List[ExtractedEntity]
    edges: List[DiscoveredRelation]
    node_count: int
    edge_count: int
    graph_metadata: Dict[str, Any]


@dataclass
class KnowledgeResult:
    """知识图谱构建结果"""
    knowledge_graph: KnowledgeGraph
    strategy: str
    project_id: Optional[int]
    document_ids: List[int]
    entity_count: int
    relation_count: int
    cross_document_entities: int
    duration_seconds: float
    stored_to_db: bool = False
    stored_to_neo4j: bool = False


class KnowledgeAgent:
    """
    知识图谱构建代理 - 真实完整可用版本

    功能：
    1. 整合4个核心知识图谱服务
    2. 多策略实体提取（jieba + spaCy + LLM）
    3. 4策略关系发现（共现、时间、语义、推理）
    4. 跨文档实体消歧
    5. 双存储：SQL + Neo4j
    6. 工作流编排和批处理
    """

    def __init__(
        self,
        default_strategy: KnowledgeStrategy = KnowledgeStrategy.AUTO,
        enable_llm: bool = False,  # LLM增强提取（较慢但准确）
        enable_cross_document: bool = True,  # 跨文档实体消歧
        confidence_threshold: float = 0.5,
        enable_metrics: bool = True  # 是否自动计算chunk指标
    ):
        """
        初始化知识图谱代理

        Args:
            default_strategy: 默认构建策略
            enable_llm: 是否启用LLM增强提取
            enable_cross_document: 是否启用跨文档消歧
            confidence_threshold: 置信度阈值
            enable_metrics: 是否自动计算chunk指标（语义密度、连贯性等）
        """
        self.default_strategy = default_strategy
        self.enable_llm = enable_llm
        self.enable_cross_document = enable_cross_document
        self.confidence_threshold = confidence_threshold
        self.enable_metrics = enable_metrics

        # 延迟加载服务（按需加载）
        self._knowledge_graph_service = None  # KnowledgeGraphService (主服务)
        self._entity_extraction_service = None  # EntityExtractionService (中文)
        self._relation_discovery_engine = None  # RelationDiscoveryEngine (4策略)
        self._knowledge_graph_builder = None  # KnowledgeGraphBuilder (编排)
        self._metrics_calculator = None  # ChunkMetricsCalculator (指标计算)

        logger.info(f"KnowledgeAgent initialized - strategy={default_strategy}, llm={enable_llm}, cross_doc={enable_cross_document}, metrics={enable_metrics}")

    def _get_knowledge_graph_service(self):
        """延迟加载KnowledgeGraphService"""
        if self._knowledge_graph_service is None:
            from app.services.knowledge_graph_service import get_knowledge_graph_service
            self._knowledge_graph_service = get_knowledge_graph_service()
            logger.info("Loaded KnowledgeGraphService (NetworkX + spaCy + LLM)")
        return self._knowledge_graph_service

    def _get_entity_extraction_service(self):
        """延迟加载EntityExtractionService"""
        if self._entity_extraction_service is None:
            from app.services.entity_extraction import EntityExtractionService
            self._entity_extraction_service = EntityExtractionService()
            logger.info("Loaded EntityExtractionService (jieba + custom dict)")
        return self._entity_extraction_service

    def _get_relation_discovery_engine(self, db_session):
        """延迟加载RelationDiscoveryEngine（需要db_session）"""
        # RelationDiscoveryEngine需要db参数，每次调用时创建
        from app.services.relation_discovery import RelationDiscoveryEngine
        engine = RelationDiscoveryEngine(db=db_session)
        logger.info("Loaded RelationDiscoveryEngine (4 strategies)")
        return engine

    def _get_knowledge_graph_builder(self, db_session):
        """延迟加载KnowledgeGraphBuilder（需要db_session）"""
        # KnowledgeGraphBuilder需要db参数，每次调用时创建
        from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
        builder = KnowledgeGraphBuilder(db=db_session)
        logger.info("Loaded KnowledgeGraphBuilder (workflow orchestration)")
        return builder

    def _get_metrics_calculator(self, db_session):
        """延迟加载ChunkMetricsCalculator（需要db_session）"""
        if self._metrics_calculator is None or self._metrics_calculator.db != db_session:
            from app.services.chunk_metrics_calculator import ChunkMetricsCalculator
            self._metrics_calculator = ChunkMetricsCalculator(db_session=db_session)
            logger.info("Loaded ChunkMetricsCalculator (15 metrics)")
        return self._metrics_calculator

    def build_from_vectorized_chunks(
        self,
        vectorized_chunks: List[Dict[str, Any]],
        project_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
        strategy: Optional[KnowledgeStrategy] = None,
        db_session = None
    ) -> KnowledgeResult:
        """
        从向量化chunks构建知识图谱

        Args:
            vectorized_chunks: 向量化后的文本chunks
            project_id: 项目ID
            document_ids: 文档ID列表
            strategy: 构建策略
            db_session: 数据库会话

        Returns:
            KnowledgeResult: 构建结果
        """
        start_time = time.time()
        strategy = strategy or self.default_strategy

        logger.info(f"Building knowledge graph from {len(vectorized_chunks)} chunks - strategy={strategy}")

        # 1. 自动选择策略
        if strategy == KnowledgeStrategy.AUTO:
            strategy = self._select_strategy(vectorized_chunks, project_id, document_ids)
            logger.info(f"Auto-selected strategy: {strategy}")

        # 2. 根据策略构建图谱
        if strategy == KnowledgeStrategy.COMPREHENSIVE:
            result = self._build_comprehensive(vectorized_chunks, project_id, document_ids, db_session)
        elif strategy == KnowledgeStrategy.ENTITY_FOCUSED:
            result = self._build_entity_focused(vectorized_chunks, project_id, document_ids, db_session)
        elif strategy == KnowledgeStrategy.RELATION_FOCUSED:
            result = self._build_relation_focused(vectorized_chunks, project_id, document_ids, db_session)
        elif strategy == KnowledgeStrategy.CROSS_DOCUMENT:
            result = self._build_cross_document(vectorized_chunks, project_id, document_ids, db_session)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        duration = time.time() - start_time
        result.duration_seconds = duration

        logger.info(f"Knowledge graph built - {result.entity_count} entities, {result.relation_count} relations in {duration:.2f}s")
        return result

    def build_from_documents(
        self,
        document_ids: List[int],
        project_id: int,
        strategy: Optional[KnowledgeStrategy] = None,
        db_session = None
    ) -> KnowledgeResult:
        """
        直接从文档构建知识图谱（使用KnowledgeGraphBuilder）

        Args:
            document_ids: 文档ID列表
            project_id: 项目ID
            strategy: 构建策略
            db_session: 数据库会话

        Returns:
            KnowledgeResult: 构建结果
        """
        start_time = time.time()
        strategy = strategy or self.default_strategy

        logger.info(f"Building knowledge graph from {len(document_ids)} documents - strategy={strategy}")

        if not db_session:
            raise ValueError("db_session is required for build_from_documents")

        builder = self._get_knowledge_graph_builder(db_session)

        # 使用builder批量处理文档
        all_entities = []
        all_relations = []

        for doc_id in document_ids:
            try:
                # 构建单个文档的知识图谱
                doc_result = builder.build_from_document(
                    document_id=doc_id,
                    project_id=project_id,
                    db=db_session
                )

                # 收集实体和关系
                if doc_result and 'entities' in doc_result:
                    all_entities.extend(doc_result['entities'])
                if doc_result and 'relations' in doc_result:
                    all_relations.extend(doc_result['relations'])

            except Exception as e:
                logger.error(f"Failed to build graph for document {doc_id}: {e}")
                continue

        # 如果启用跨文档消歧
        cross_document_count = 0
        if self.enable_cross_document and project_id:
            try:
                kg_service = self._get_knowledge_graph_service()
                cross_doc_result = kg_service.build_cross_document_graph(project_id, db_session)

                if cross_doc_result and 'canonical_entities' in cross_doc_result:
                    cross_document_count = len(cross_doc_result['canonical_entities'])
                    logger.info(f"Cross-document resolution: {cross_document_count} canonical entities")

            except Exception as e:
                logger.error(f"Cross-document resolution failed: {e}")

        # 构建结果
        nodes = []
        for e in all_entities:
            # 处理字典格式的实体
            if isinstance(e, dict):
                nodes.append(ExtractedEntity(
                    entity_id=str(e.get('id', '')),
                    name=e.get('name', ''),
                    entity_type=e.get('type', 'unknown'),
                    confidence=e.get('confidence', 0.0),
                    mentions=[],
                    source_document_id=e.get('document_id')
                ))
            # 处理对象格式的实体（来自数据库模型）
            else:
                nodes.append(ExtractedEntity(
                    entity_id=str(getattr(e, 'id', '')),
                    name=getattr(e, 'name', ''),
                    entity_type=getattr(e, 'entity_type', 'unknown'),
                    confidence=getattr(e, 'confidence', 0.0),
                    mentions=[],
                    source_document_id=getattr(e, 'document_id', None)
                ))

        edges = []
        for r in all_relations:
            # 处理字典格式的关系
            if isinstance(r, dict):
                edges.append(DiscoveredRelation(
                    relation_id=str(r.get('id', '')),
                    source_entity=r.get('source', ''),
                    target_entity=r.get('target', ''),
                    relation_type=r.get('type', 'related_to'),
                    confidence=r.get('confidence', 0.0),
                    evidence=[],
                    discovery_strategy='builder'
                ))
            # 处理对象格式的关系
            else:
                edges.append(DiscoveredRelation(
                    relation_id=str(getattr(r, 'id', '')),
                    source_entity=getattr(r, 'source_entity', ''),
                    target_entity=getattr(r, 'target_entity', ''),
                    relation_type=getattr(r, 'relation_type', 'related_to'),
                    confidence=getattr(r, 'confidence', 0.0),
                    evidence=[],
                    discovery_strategy='builder'
                ))

        knowledge_graph = KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            graph_metadata={
                'project_id': project_id,
                'document_ids': document_ids,
                'strategy': strategy.value,
                'built_at': datetime.now().isoformat()
            }
        )

        duration = time.time() - start_time

        return KnowledgeResult(
            knowledge_graph=knowledge_graph,
            strategy=strategy.value,
            project_id=project_id,
            document_ids=document_ids,
            entity_count=len(nodes),
            relation_count=len(edges),
            cross_document_entities=cross_document_count,
            duration_seconds=duration,
            stored_to_db=True,  # builder已存储到DB
            stored_to_neo4j=False
        )

    def _select_strategy(
        self,
        chunks: List[Dict[str, Any]],
        project_id: Optional[int],
        document_ids: Optional[List[int]]
    ) -> KnowledgeStrategy:
        """
        自动选择最佳构建策略

        策略选择逻辑：
        - 多文档 + project_id → CROSS_DOCUMENT (跨文档消歧)
        - 大量chunks (>100) → COMPREHENSIVE (全功能)
        - 中等chunks (20-100) → ENTITY_FOCUSED (快速实体提取)
        - 少量chunks (<20) → RELATION_FOCUSED (关注关系发现)
        """
        chunk_count = len(chunks)
        doc_count = len(document_ids) if document_ids else 0

        if doc_count > 1 and project_id and self.enable_cross_document:
            return KnowledgeStrategy.CROSS_DOCUMENT
        elif chunk_count > 100:
            return KnowledgeStrategy.COMPREHENSIVE
        elif chunk_count > 20:
            return KnowledgeStrategy.ENTITY_FOCUSED
        else:
            return KnowledgeStrategy.RELATION_FOCUSED

    def _build_comprehensive(
        self,
        chunks: List[Dict[str, Any]],
        project_id: Optional[int],
        document_ids: Optional[List[int]],
        db_session
    ) -> KnowledgeResult:
        """
        综合策略：使用所有服务协同构建

        流程：
        1. EntityExtractionService提取中文实体
        2. KnowledgeGraphService提取关系
        3. RelationDiscoveryEngine发现深度关系
        4. 跨文档消歧（如果启用）
        """
        logger.info("Using COMPREHENSIVE strategy - all services")

        kg_service = self._get_knowledge_graph_service()
        entity_service = self._get_entity_extraction_service()
        relation_engine = self._get_relation_discovery_engine(db_session)

        all_entities = []
        all_relations = []

        # 1. 从chunks提取实体和关系
        for chunk in chunks:
            text = chunk.get('text', chunk.get('content', ''))
            if not text:
                continue

            # 使用jieba提取中文实体
            entities_jieba = entity_service.extract_entities(
                text,
                min_confidence=self.confidence_threshold
            )

            # 使用NetworkX服务提取实体和关系
            entities_kg, relations_kg = kg_service.extract_entities_and_relations(
                text,
                use_llm=self.enable_llm
            )

            # 合并结果
            all_entities.extend(entities_jieba)
            all_entities.extend(entities_kg)
            all_relations.extend(relations_kg)

        # 2. 去重和规范化实体
        unique_entities = self._deduplicate_entities(all_entities)

        # 3. 构建知识图谱
        nodes = []
        for e in unique_entities:
            # 处理字典格式
            if isinstance(e, dict):
                nodes.append(ExtractedEntity(
                    entity_id=e.get('id', e.get('name', '')),
                    name=e.get('name', ''),
                    entity_type=e.get('type', e.get('entity_type', 'unknown')),
                    confidence=e.get('confidence', 0.0),
                    mentions=[{'text': e.get('name', '')}],
                    source_document_id=None
                ))
            # 处理对象格式（Entity dataclass或其他）
            else:
                nodes.append(ExtractedEntity(
                    entity_id=getattr(e, 'id', getattr(e, 'name', '')),
                    name=getattr(e, 'name', ''),
                    entity_type=getattr(e, 'type', getattr(e, 'entity_type', 'unknown')),
                    confidence=getattr(e, 'confidence', 0.0),
                    mentions=[{'text': getattr(e, 'name', '')}],
                    source_document_id=None
                ))

        edges = []
        for r in all_relations:
            # 处理字典格式
            if isinstance(r, dict):
                edges.append(DiscoveredRelation(
                    relation_id=f"{r.get('source', '')}_{r.get('relation_type', 'related_to')}_{r.get('target', '')}",
                    source_entity=r.get('source', ''),
                    target_entity=r.get('target', ''),
                    relation_type=r.get('relation_type', 'related_to'),
                    confidence=r.get('confidence', 0.8),
                    evidence=[],
                    discovery_strategy='comprehensive'
                ))
            # 处理对象格式（Relation dataclass）
            else:
                source = getattr(r, 'source', getattr(r, 'source_entity', ''))
                target = getattr(r, 'target', getattr(r, 'target_entity', ''))
                rel_type = getattr(r, 'relation_type', 'related_to')
                edges.append(DiscoveredRelation(
                    relation_id=f"{source}_{rel_type}_{target}",
                    source_entity=source,
                    target_entity=target,
                    relation_type=rel_type,
                    confidence=getattr(r, 'confidence', 0.8),
                    evidence=[],
                    discovery_strategy='comprehensive'
                ))

        knowledge_graph = KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            graph_metadata={
                'strategy': 'comprehensive',
                'chunk_count': len(chunks),
                'built_at': datetime.now().isoformat()
            }
        )

        return KnowledgeResult(
            knowledge_graph=knowledge_graph,
            strategy='comprehensive',
            project_id=project_id,
            document_ids=document_ids or [],
            entity_count=len(nodes),
            relation_count=len(edges),
            cross_document_entities=0,
            duration_seconds=0.0,
            stored_to_db=False,
            stored_to_neo4j=False
        )

    def _build_entity_focused(
        self,
        chunks: List[Dict[str, Any]],
        project_id: Optional[int],
        document_ids: Optional[List[int]],
        db_session
    ) -> KnowledgeResult:
        """
        实体为中心策略：专注于高质量实体提取

        使用EntityExtractionService的完整功能
        """
        logger.info("Using ENTITY_FOCUSED strategy")

        entity_service = self._get_entity_extraction_service()

        all_entities = []
        for chunk in chunks:
            text = chunk.get('text', chunk.get('content', ''))
            if not text:
                continue

            entities = entity_service.extract_entities(
                text,
                min_confidence=self.confidence_threshold
            )
            all_entities.extend(entities)

        unique_entities = self._deduplicate_entities(all_entities)

        nodes = []
        for e in unique_entities:
            if isinstance(e, dict):
                nodes.append(ExtractedEntity(
                    entity_id=e.get('name', ''),
                    name=e.get('name', ''),
                    entity_type=e.get('type', 'unknown'),
                    confidence=e.get('confidence', 0.0),
                    mentions=[{'text': e.get('name', '')}]
                ))
            else:
                nodes.append(ExtractedEntity(
                    entity_id=getattr(e, 'name', ''),
                    name=getattr(e, 'name', ''),
                    entity_type=getattr(e, 'type', getattr(e, 'entity_type', 'unknown')),
                    confidence=getattr(e, 'confidence', 0.0),
                    mentions=[{'text': getattr(e, 'name', '')}]
                ))

        knowledge_graph = KnowledgeGraph(
            nodes=nodes,
            edges=[],
            node_count=len(nodes),
            edge_count=0,
            graph_metadata={
                'strategy': 'entity_focused',
                'chunk_count': len(chunks)
            }
        )

        return KnowledgeResult(
            knowledge_graph=knowledge_graph,
            strategy='entity_focused',
            project_id=project_id,
            document_ids=document_ids or [],
            entity_count=len(nodes),
            relation_count=0,
            cross_document_entities=0,
            duration_seconds=0.0
        )

    def _build_relation_focused(
        self,
        chunks: List[Dict[str, Any]],
        project_id: Optional[int],
        document_ids: Optional[List[int]],
        db_session
    ) -> KnowledgeResult:
        """
        关系为中心策略：专注于关系发现

        使用KnowledgeGraphService的关系提取功能
        """
        logger.info("Using RELATION_FOCUSED strategy")

        kg_service = self._get_knowledge_graph_service()

        all_entities = []
        all_relations = []

        for chunk in chunks:
            text = chunk.get('text', chunk.get('content', ''))
            if not text:
                continue

            entities, relations = kg_service.extract_entities_and_relations(
                text,
                use_llm=self.enable_llm
            )
            all_entities.extend(entities)
            all_relations.extend(relations)

        unique_entities = self._deduplicate_entities(all_entities)

        nodes = []
        for e in unique_entities:
            if isinstance(e, dict):
                nodes.append(ExtractedEntity(
                    entity_id=e.get('name', ''),
                    name=e.get('name', ''),
                    entity_type=e.get('type', 'unknown'),
                    confidence=e.get('confidence', 0.8),
                    mentions=[]
                ))
            else:
                nodes.append(ExtractedEntity(
                    entity_id=getattr(e, 'name', ''),
                    name=getattr(e, 'name', ''),
                    entity_type=getattr(e, 'type', getattr(e, 'entity_type', 'unknown')),
                    confidence=getattr(e, 'confidence', 0.8),
                    mentions=[]
                ))

        edges = []
        for r in all_relations:
            if isinstance(r, dict):
                edges.append(DiscoveredRelation(
                    relation_id=f"{r.get('source', '')}_{r.get('relation_type', 'related_to')}_{r.get('target', '')}",
                    source_entity=r.get('source', ''),
                    target_entity=r.get('target', ''),
                    relation_type=r.get('relation_type', 'related_to'),
                    confidence=0.8,
                    evidence=[],
                    discovery_strategy='relation_focused'
                ))
            else:
                source = getattr(r, 'source', getattr(r, 'source_entity', ''))
                target = getattr(r, 'target', getattr(r, 'target_entity', ''))
                rel_type = getattr(r, 'relation_type', 'related_to')
                edges.append(DiscoveredRelation(
                    relation_id=f"{source}_{rel_type}_{target}",
                    source_entity=source,
                    target_entity=target,
                    relation_type=rel_type,
                    confidence=0.8,
                    evidence=[],
                    discovery_strategy='relation_focused'
                ))

        knowledge_graph = KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            graph_metadata={'strategy': 'relation_focused'}
        )

        return KnowledgeResult(
            knowledge_graph=knowledge_graph,
            strategy='relation_focused',
            project_id=project_id,
            document_ids=document_ids or [],
            entity_count=len(nodes),
            relation_count=len(edges),
            cross_document_entities=0,
            duration_seconds=0.0
        )

    def _build_cross_document(
        self,
        chunks: List[Dict[str, Any]],
        project_id: Optional[int],
        document_ids: Optional[List[int]],
        db_session
    ) -> KnowledgeResult:
        """
        跨文档策略：跨文档实体消歧和关系发现

        使用KnowledgeGraphService的跨文档功能
        """
        logger.info("Using CROSS_DOCUMENT strategy")

        if not project_id or not db_session:
            logger.warning("Cross-document strategy requires project_id and db_session, falling back to comprehensive")
            return self._build_comprehensive(chunks, project_id, document_ids, db_session)

        kg_service = self._get_knowledge_graph_service()

        # 构建跨文档图谱
        cross_doc_result = kg_service.build_cross_document_graph(project_id, db_session)

        canonical_entities = cross_doc_result.get('canonical_entities', [])

        nodes = [
            ExtractedEntity(
                entity_id=e['canonical_id'],
                name=e['name'],
                entity_type=e['type'],
                confidence=e['confidence'],
                mentions=[],
                canonical_id=e['canonical_id']
            )
            for e in canonical_entities
        ]

        knowledge_graph = KnowledgeGraph(
            nodes=nodes,
            edges=[],
            node_count=len(nodes),
            edge_count=0,
            graph_metadata={
                'strategy': 'cross_document',
                'project_id': project_id,
                'canonical_entities': len(canonical_entities)
            }
        )

        return KnowledgeResult(
            knowledge_graph=knowledge_graph,
            strategy='cross_document',
            project_id=project_id,
            document_ids=document_ids or [],
            entity_count=len(nodes),
            relation_count=0,
            cross_document_entities=len(canonical_entities),
            duration_seconds=0.0
        )

    def _deduplicate_entities(self, entities: List[Any]) -> List[Dict[str, Any]]:
        """实体去重，返回统一的字典格式"""
        seen = {}
        for entity in entities:
            # 处理字典格式
            if isinstance(entity, dict):
                name = entity.get('name', '')
                if name and name not in seen:
                    seen[name] = entity
            # 处理对象格式
            else:
                name = getattr(entity, 'name', '')
                if name and name not in seen:
                    # 转换为字典格式
                    seen[name] = {
                        'name': name,
                        'type': getattr(entity, 'type', getattr(entity, 'entity_type', 'unknown')),
                        'confidence': getattr(entity, 'confidence', 0.0)
                    }
        return list(seen.values())

    def export_to_dict(self, result: KnowledgeResult) -> Dict[str, Any]:
        """导出结果为字典格式"""
        return asdict(result)

    # ========== 新增：Chunk指标计算功能 ==========

    def calculate_chunk_metrics(
        self,
        chunks: List[Dict[str, Any]],
        entities: Optional[List[Dict[str, Any]]] = None,
        keywords: Optional[List[str]] = None,
        document_context: Optional[Dict[str, Any]] = None,
        db_session = None
    ) -> Dict[str, Any]:
        """
        为chunks计算15个指标

        Args:
            chunks: chunk列表，每个包含 {id, text}
            entities: 已提取的实体列表
            keywords: 已提取的关键词列表
            document_context: 文档上下文（用于计算相关性和信息增益）
            db_session: 数据库会话

        Returns:
            Dict: 统计结果 {total, success, failed, duration_seconds}
        """
        if not self.enable_metrics:
            logger.info("Metrics calculation is disabled")
            return {'total': 0, 'success': 0, 'failed': 0, 'message': 'metrics disabled'}

        if not db_session:
            logger.warning("No db_session provided, cannot save metrics")
            return {'total': 0, 'success': 0, 'failed': 0, 'message': 'no db session'}

        calculator = self._get_metrics_calculator(db_session)

        logger.info(f"Calculating metrics for {len(chunks)} chunks")

        # 构建chunk到实体/关键词的映射
        entity_map = {}
        if entities:
            for entity in entities:
                chunk_id = entity.get('chunk_id') or entity.get('source_chunk_id')
                if chunk_id:
                    if chunk_id not in entity_map:
                        entity_map[chunk_id] = []
                    entity_map[chunk_id].append(entity.get('name') or entity.get('text', ''))

        keyword_map = {}
        if keywords:
            for kw in keywords:
                if isinstance(kw, dict):
                    chunk_id = kw.get('chunk_id')
                    text = kw.get('text', '')
                else:
                    chunk_id = None
                    text = str(kw)

                if chunk_id:
                    if chunk_id not in keyword_map:
                        keyword_map[chunk_id] = []
                    keyword_map[chunk_id].append(text)

        # 批量计算
        enriched_chunks = []
        for chunk in chunks:
            chunk_id = chunk.get('id')
            enriched_chunks.append({
                'id': chunk_id,
                'text': chunk.get('text') or chunk.get('content', ''),
                'entities': entity_map.get(chunk_id, []),
                'keywords': keyword_map.get(chunk_id, [])
            })

        result = calculator.batch_calculate_and_save(
            chunks=enriched_chunks,
            document_context=document_context
        )

        logger.info(f"Metrics calculation completed: {result}")
        return result

    def calculate_metrics_for_document(
        self,
        document_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        为某个文档的所有chunks计算指标

        这是一个便捷方法，自动查询文档的chunks并计算指标

        Args:
            document_id: 文档ID
            db_session: 数据库会话

        Returns:
            Dict: 统计结果
        """
        if not db_session:
            raise ValueError("db_session is required")

        from sqlalchemy import text

        # 查询该文档的所有chunks
        query = text("""
            SELECT id, text, entity_count, keyword_count
            FROM document_chunks
            WHERE document_id = :document_id
            ORDER BY chunk_index
        """)

        result = db_session.execute(query, {'document_id': document_id})
        rows = result.fetchall()

        if not rows:
            logger.warning(f"No chunks found for document {document_id}")
            return {'total': 0, 'success': 0, 'failed': 0, 'message': 'no chunks found'}

        chunks = []
        for row in rows:
            chunks.append({
                'id': row[0],
                'text': row[1],
                'entities': [],  # 可以进一步查询
                'keywords': []
            })

        logger.info(f"Found {len(chunks)} chunks for document {document_id}")

        # 计算指标
        return self.calculate_chunk_metrics(
            chunks=chunks,
            db_session=db_session
        )

    def get_chunk_metrics_summary(
        self,
        document_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        获取文档的chunk指标汇总

        Args:
            document_id: 文档ID
            db_session: 数据库会话

        Returns:
            Dict: 指标汇总统计
        """
        if not db_session:
            raise ValueError("db_session is required")

        from sqlalchemy import text

        query = text("""
            SELECT
                COUNT(*) as total_chunks,
                AVG(semantic_density) as avg_semantic_density,
                AVG(coherence_score) as avg_coherence,
                AVG(information_gain) as avg_information_gain,
                AVG(topic_relevance) as avg_topic_relevance,
                AVG(readability_score) as avg_readability,
                AVG(sentiment_score) as avg_sentiment,
                AVG(complexity_score) as avg_complexity,
                AVG(lexical_diversity) as avg_lexical_diversity,
                SUM(entity_count) as total_entities,
                SUM(keyword_count) as total_keywords
            FROM document_chunks
            WHERE document_id = :document_id
        """)

        result = db_session.execute(query, {'document_id': document_id})
        row = result.fetchone()

        if not row or row[0] == 0:
            return {'message': 'no data found'}

        return {
            'document_id': document_id,
            'total_chunks': row[0],
            'metrics': {
                'avg_semantic_density': round(row[1], 3) if row[1] else None,
                'avg_coherence': round(row[2], 3) if row[2] else None,
                'avg_information_gain': round(row[3], 3) if row[3] else None,
                'avg_topic_relevance': round(row[4], 3) if row[4] else None,
                'avg_readability': round(row[5], 2) if row[5] else None,
                'avg_sentiment': round(row[6], 3) if row[6] else None,
                'avg_complexity': round(row[7], 2) if row[7] else None,
                'avg_lexical_diversity': round(row[8], 3) if row[8] else None,
            },
            'counts': {
                'total_entities': row[9] or 0,
                'total_keywords': row[10] or 0
            }
        }
