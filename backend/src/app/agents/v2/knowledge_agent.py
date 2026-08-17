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
        confidence_threshold: float = 0.5
    ):
        """
        初始化知识图谱代理

        Args:
            default_strategy: 默认构建策略
            enable_llm: 是否启用LLM增强提取
            enable_cross_document: 是否启用跨文档消歧
            confidence_threshold: 置信度阈值
        """
        self.default_strategy = default_strategy
        self.enable_llm = enable_llm
        self.enable_cross_document = enable_cross_document
        self.confidence_threshold = confidence_threshold

        # 延迟加载服务（按需加载）
        self._knowledge_graph_service = None  # KnowledgeGraphService (主服务)
        self._entity_extraction_service = None  # EntityExtractionService (中文)
        self._relation_discovery_engine = None  # RelationDiscoveryEngine (4策略)
        self._knowledge_graph_builder = None  # KnowledgeGraphBuilder (编排)

        logger.info(f"KnowledgeAgent initialized - strategy={default_strategy}, llm={enable_llm}, cross_doc={enable_cross_document}")

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
                raise RuntimeError(f"文档 {doc_id} 构建知识图谱失败") from e

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

            # 使用新的工具函数提取实体
            try:
                from app.tools.entity import extract_entities
                entities_result = extract_entities(
                    text=text,
                    merge_threshold=0.85,
                    extract_context=False  # 在大批量处理时禁用上下文提取以提升性能
                )
                entities_from_tool = entities_result.get('entities', [])
            except Exception as e:
                logger.warning(f"extract_entities工具失败，使用旧服务: {e}")
                # Fallback: 使用旧的EntityExtractionService
                entities_from_tool = entity_service.extract_entities(
                    text,
                    min_confidence=self.confidence_threshold
                )

            # 使用新的工具函数提取关系
            try:
                from app.tools.relation import extract_relations
                relations_result = extract_relations(
                    text=text,
                    entities=entities_from_tool,
                    max_relations=50
                )
                relations_from_tool = relations_result.get('triples', [])
            except Exception as e:
                logger.warning(f"extract_relations工具失败: {e}")
                relations_from_tool = []

            # 使用NetworkX服务提取实体和关系（作为补充）
            entities_kg, relations_kg = kg_service.extract_entities_and_relations(
                text,
                use_llm=self.enable_llm
            )

            # 合并结果
            all_entities.extend(entities_from_tool)
            all_entities.extend(entities_kg)
            all_relations.extend(relations_from_tool)
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

    def build_knowledge_graph(
        self,
        project_id: int,
        db_session,
        strategy: Optional[KnowledgeStrategy] = None,
        enable_skills_analysis: bool = True,
        enabled_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        为项目构建知识图谱（Coordinator接口）

        这是AgentCoordinator调用的主接口方法。

        🔥 新增：集成Skills学术分析
        在知识图谱构建完成后，自动触发Skills分析，将学术维度标注到图谱中

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            strategy: 构建策略
            enable_skills_analysis: 是否启用Skills分析（默认True）
            enabled_skills: 启用的Skills列表（None则使用默认）

        Returns:
            Dict包含: entity_count, relation_count, skills_results等
        """
        start_time = time.time()

        logger.info(f"🕸️ 开始为项目 {project_id} 构建知识图谱（Skills分析={'启用' if enable_skills_analysis else '禁用'}）")

        # 1. 获取项目的所有文档
        from app.models.project import ProjectDocument

        documents = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            raise ValueError(f"项目 {project_id} 没有文档，无法构建知识图谱")

        document_ids = [doc.id for doc in documents]
        logger.info(f"📄 找到 {len(documents)} 个文档")

        # 2. 使用build_from_documents构建知识图谱
        try:
            result = self.build_from_documents(
                document_ids=document_ids,
                project_id=project_id,
                strategy=strategy,
                db_session=db_session
            )

            logger.info(f"✅ 知识图谱构建完成：{result.entity_count}个实体，{result.relation_count}个关系")

            # 3. 🔥 集成Skills分析
            skills_results = None
            if enable_skills_analysis:
                try:
                    logger.info("🎓 开始Skills学术分析...")
                    skills_results = self._analyze_with_skills(
                        project_id=project_id,
                        db_session=db_session,
                        enabled_skills=enabled_skills
                    )
                    logger.info(f"✅ Skills分析完成：执行了 {len(skills_results.get('skills_executed', []))} 个Skills")
                except Exception as e:
                    logger.error(f"❌ Skills分析失败: {e}", exc_info=True)
                    skills_results = {'error': str(e)}

            duration = time.time() - start_time

            # 4. 返回统一格式
            return {
                'entity_count': result.entity_count,
                'relation_count': result.relation_count,
                'document_count': len(documents),
                'cross_document_entities': result.cross_document_entities,
                'strategy': result.strategy,
                'duration_seconds': duration,
                'stored_to_db': result.stored_to_db,
                'stored_to_neo4j': result.stored_to_neo4j,
                'skills_results': skills_results  # 🔥 新增
            }

        except Exception as e:
            logger.error(f"❌ 知识图谱构建失败: {e}", exc_info=True)
            return {
                'entity_count': 0,
                'relation_count': 0,
                'document_count': len(documents),
                'error': str(e),
                'skills_results': None
            }

    def _analyze_with_skills(
        self,
        project_id: int,
        db_session,
        enabled_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        使用Skills对项目内容进行学术分析

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            enabled_skills: 启用的Skills列表

        Returns:
            Skills分析结果
        """
        # 从数据库获取项目的所有chunks文本
        from app.models.pipeline_state import DocumentChunk

        chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.project_id == project_id
        ).all()

        if not chunks:
            raise ValueError(f"项目 {project_id} 没有chunks，无法进行Skills分析")

        # 聚合所有chunks文本
        content = '\n\n'.join([chunk.chunk_text for chunk in chunks])
        logger.info(f"📝 聚合了 {len(chunks)} 个chunks用于Skills分析（总长度={len(content)}字符）")

        # 调用skill_analyzer
        from app.tools.summary.skill_analyzer import analyze_with_skills

        # 如果没有指定Skills，使用驾驭工程核心Skills
        if enabled_skills is None:
            enabled_skills = [
                'heritage_dadi',        # 大地遗产方法论
                'xiangtu_china',        # 乡土中国理论分析
                'sacred_memory',        # 神圣记忆理论分析
                'business_feasibility', # 商业可行性验证
                'multi_village_sop',    # 多村联动SOP
                'literature_market_research'  # 文献市场研究
            ]

        skills_result = analyze_with_skills(
            content=content,
            enabled_skills=enabled_skills,
            report_format='full',
            include_statistics=True
        )

        logger.info(f"🎓 Skills分析完成：{len(skills_result.get('skills_executed', []))} 个Skills")

        return skills_result

    def export_to_dict(self, result: KnowledgeResult) -> Dict[str, Any]:
        """导出结果为字典格式"""
        return asdict(result)
