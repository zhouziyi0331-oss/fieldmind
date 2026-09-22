"""
Agent 4: KnowledgeAgent V2 (知识图谱构建专员) - 增强版

新增功能（基于用户需求）：
1. Neo4j + ArangoDB + NetworkX 三数据库集成 ⭐
2. 多维度实体消歧（行为+上下文+时间线+关系网络）⭐
3. 核心关键词提取（5-6个最重要的）⭐
4. Skills集成（知识图谱 ↔ 文件 ↔ Skills三者互动）⭐
5. 时间线支持（历任村支书等）
6. 关系/民俗双发散模式
7. 跨项目统一大图
8. 质量控制（数据不能乱，图谱不能过于简单）

与驾驭工程集成：
- Neo4j作为核心图数据库
- 支持Cypher查询
- 路径发现和关系推理
"""
import logging
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime
from app.models.knowledge_graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    CoreKeyword,
    KnowledgeGraphExport,
    EntityDisambiguationResult,
)
from app.models.enriched_chunk import EnrichedChunk, Entity, Relation
from app.services.entity_disambiguation_service import EntityDisambiguationService
from app.services.core_keyword_extractor import CoreKeywordExtractor
from app.services.graph_database_integration import GraphDatabaseIntegration

logger = logging.getLogger(__name__)


class KnowledgeAgentV2:
    """
    Agent 4: 知识图谱构建专员 V2

    输入：Agent 3的enriched_chunks
    输出：统一的跨项目知识图谱

    核心特性：
    - 三数据库集成（Neo4j + ArangoDB + NetworkX）
    - 多维度实体消歧
    - 核心关键词驱动（5-6个）
    - Skills集成
    - 全中文
    """

    def __init__(self):
        # 初始化服务
        self.disambiguation_service = EntityDisambiguationService()
        self.keyword_extractor = CoreKeywordExtractor()
        self.db_integration = GraphDatabaseIntegration()

        # 内存中的图谱（临时）
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}

        # 统计信息
        self.stats = {
            "total_chunks_processed": 0,
            "total_entities_extracted": 0,
            "total_relations_extracted": 0,
            "entities_merged": 0,
            "nodes_created": 0,
            "edges_created": 0,
        }

        logger.info("KnowledgeAgentV2 initialized - 三数据库集成模式")

    def build_knowledge_graph(
        self,
        enriched_chunks: List[EnrichedChunk],
        project_name: str,
        mode: str = "auto"  # "auto", "relationship", "folklore"
    ) -> KnowledgeGraphExport:
        """
        构建知识图谱

        Args:
            enriched_chunks: Agent 3的输出
            project_name: 项目名称
            mode: 发散模式（auto/relationship/folklore）

        Returns:
            KnowledgeGraphExport: 完整的知识图谱
        """
        print(f"\n🚀 开始构建知识图谱（项目：{project_name}）")
        print(f"   模式：{mode}")
        print(f"   数据库：Neo4j + ArangoDB + NetworkX")

        # 阶段1：提取节点和边
        print("\n📊 阶段1：从enriched_chunks提取节点和边")
        self._extract_nodes_and_edges(enriched_chunks, project_name)

        # 阶段2：实体消歧（合并同名实体）
        print("\n🔍 阶段2：实体消歧（多文档同名实体合并）")
        merge_results = self._disambiguate_entities()

        # 阶段3：计算关系网络指纹
        print("\n🕸️  阶段3：计算关系网络指纹")
        self._calculate_relationship_fingerprints()

        # 阶段4：提取核心关键词（5-6个）
        print("\n⭐ 阶段4：提取核心关键词（5-6个最重要的）")
        core_keywords = self._extract_core_keywords(mode)

        # 阶段5：质量验证
        print("\n✅ 阶段5：质量验证")
        validation_result = self._validate_graph_quality(core_keywords)

        # 阶段6：写入数据库
        print("\n💾 阶段6：写入三数据库（Neo4j + ArangoDB + NetworkX）")
        self._write_to_databases()

        # 阶段7：导出
        print("\n📤 阶段7：导出知识图谱")
        export = self._export_graph(core_keywords, project_name)

        print(f"\n✅ 知识图谱构建完成！")
        print(f"   节点数：{len(self.nodes)}")
        print(f"   边数：{len(self.edges)}")
        print(f"   核心关键词：{len(core_keywords)}")
        print(f"   实体合并：{self.stats['entities_merged']}")
        print(f"   质量验证：{'通过✓' if validation_result['valid'] else '未通过✗'}")

        if validation_result.get('warnings'):
            print(f"   ⚠️  警告：{len(validation_result['warnings'])}条")

        return export

    def _extract_nodes_and_edges(
        self,
        enriched_chunks: List[EnrichedChunk],
        project_name: str
    ):
        """阶段1：从enriched_chunks提取节点和边"""
        for chunk in enriched_chunks:
            self.stats["total_chunks_processed"] += 1

            # 1. 提取实体节点
            for entity in chunk.entities:
                self._add_entity_node(entity, chunk, project_name)
                self.stats["total_entities_extracted"] += 1

            # 2. 提取关系边
            for relation in chunk.relations:
                self._add_relation_edge(relation, chunk, project_name)
                self.stats["total_relations_extracted"] += 1

    def _add_entity_node(
        self,
        entity: Entity,
        chunk: EnrichedChunk,
        project_name: str
    ):
        """添加实体节点"""
        # 生成节点ID
        node_id = self._generate_node_id(entity.text, entity.type)

        # 如果节点已存在，更新它
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # 更新来源
            if chunk.source_file not in node.source_documents:
                node.source_documents.append(chunk.source_file)
            if project_name not in node.source_projects:
                node.source_projects.append(project_name)
            return

        # 创建新节点
        node = GraphNode(
            id=node_id,
            name=entity.text,
            type=self._map_entity_type(entity.type),
            description=entity.context,
            importance_score=entity.confidence,
            actions=[],  # 稍后从关系中提取
            context_summary=chunk.text[:200],  # 上下文摘要
            timeline=[],  # 稍后从时间线中提取
            region=chunk.region or entity.cultural_context.get("region"),
            ethnic_group=entity.cultural_context.get("ethnic_group"),
            category=entity.cultural_context.get("category"),
            subcategory=entity.cultural_context.get("subcategory"),
            source_documents=[chunk.source_file],
            source_projects=[project_name],
            context_vector=chunk.text_vector,  # Agent 3的文本向量
            confidence=entity.confidence,
        )

        self.nodes[node_id] = node
        self.stats["nodes_created"] += 1

    def _add_relation_edge(
        self,
        relation: Relation,
        chunk: EnrichedChunk,
        project_name: str
    ):
        """添加关系边"""
        # 生成源和目标节点ID
        source_id = self._generate_node_id(relation.subject, relation.subject_type)
        target_id = self._generate_node_id(relation.object, relation.object_type)

        # 生成边ID
        edge_id = self._generate_edge_id(source_id, target_id, relation.predicate)

        # 如果边已存在，更新它
        if edge_id in self.edges:
            edge = self.edges[edge_id]
            if chunk.source_file not in edge.source_documents:
                edge.source_documents.append(chunk.source_file)
            edge.evidence.append(chunk.text[:100])
            return

        # 创建新边
        edge = GraphEdge(
            id=edge_id,
            source=source_id,
            target=target_id,
            type=self._map_relation_type(relation.relation_type),
            description=relation.context,
            weight=relation.confidence,
            confidence=relation.confidence,
            start_time=relation.temporal_info.get("start_time"),
            end_time=relation.temporal_info.get("end_time"),
            source_documents=[chunk.source_file],
            evidence=[chunk.text[:100]],
        )

        self.edges[edge_id] = edge
        self.stats["edges_created"] += 1

        # 更新节点的actions（用于消歧）
        if source_id in self.nodes and relation.predicate:
            self.nodes[source_id].actions.append(relation.predicate)

    def _disambiguate_entities(self) -> Dict[str, List[str]]:
        """阶段2：实体消歧"""
        # 按名称和类型分组
        entity_groups = {}
        for node_id, node in self.nodes.items():
            key = (node.name, node.type)
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(node)

        # 对每组进行消歧
        merge_results = {}
        for (name, node_type), nodes in entity_groups.items():
            if len(nodes) <= 1:
                continue

            print(f"   消歧实体：{name} ({node_type}) - {len(nodes)}个候选")

            # 批量消歧
            merge_groups = self.disambiguation_service.batch_disambiguate(nodes)

            for canonical_id, duplicate_ids in merge_groups.items():
                print(f"      合并：{canonical_id} ← {duplicate_ids}")
                self._merge_nodes(canonical_id, duplicate_ids)
                merge_results[canonical_id] = duplicate_ids
                self.stats["entities_merged"] += len(duplicate_ids)

        return merge_results

    def _merge_nodes(self, canonical_id: str, duplicate_ids: List[str]):
        """合并节点"""
        if canonical_id not in self.nodes:
            return

        canonical_node = self.nodes[canonical_id]

        for dup_id in duplicate_ids:
            if dup_id not in self.nodes:
                continue

            dup_node = self.nodes[dup_id]

            # 合并属性
            canonical_node.source_documents.extend(dup_node.source_documents)
            canonical_node.source_projects.extend(dup_node.source_projects)
            canonical_node.actions.extend(dup_node.actions)
            canonical_node.timeline.extend(dup_node.timeline)

            # 去重
            canonical_node.source_documents = list(set(canonical_node.source_documents))
            canonical_node.source_projects = list(set(canonical_node.source_projects))
            canonical_node.actions = list(set(canonical_node.actions))

            # 更新importance_score（取最大值）
            canonical_node.importance_score = max(
                canonical_node.importance_score,
                dup_node.importance_score
            )

            # 重定向边
            for edge_id, edge in self.edges.items():
                if edge.source == dup_id:
                    edge.source = canonical_id
                if edge.target == dup_id:
                    edge.target = canonical_id

            # 删除重复节点
            del self.nodes[dup_id]

    def _calculate_relationship_fingerprints(self):
        """阶段3：计算关系网络指纹"""
        for node_id, node in self.nodes.items():
            # 找出所有相关节点
            related_nodes = set()

            for edge in self.edges.values():
                if edge.source == node_id:
                    related_nodes.add(edge.target)
                if edge.target == node_id:
                    related_nodes.add(edge.source)

            # 生成指纹（逗号分隔的ID列表）
            node.relationship_fingerprint = ",".join(sorted(related_nodes))

    def _extract_core_keywords(self, mode: str) -> List[CoreKeyword]:
        """阶段4：提取核心关键词"""
        nodes_list = list(self.nodes.values())
        edges_list = list(self.edges.values())

        core_keywords = self.keyword_extractor.extract_core_keywords(
            nodes_list,
            edges_list,
            mode=mode
        )

        print(f"   提取到{len(core_keywords)}个核心关键词：")
        for kw in core_keywords:
            print(f"      • {kw.keyword} ({kw.category}) - 重要性: {kw.importance:.3f}")

        # 标记核心关键词节点
        for kw in core_keywords:
            if kw.node_id in self.nodes:
                self.nodes[kw.node_id].is_core_keyword = True
                self.nodes[kw.node_id].layer = 1  # 第1层（核心）

        # 标记衍生关键词节点
        for kw in core_keywords:
            for derived_name in kw.derived_keywords:
                # 找到对应节点
                for node in self.nodes.values():
                    if node.name == derived_name and not node.is_core_keyword:
                        node.layer = 2  # 第2层（次要）

        return core_keywords

    def _validate_graph_quality(self, core_keywords: List[CoreKeyword]) -> Dict[str, Any]:
        """阶段5：质量验证"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 1. 核心关键词验证
        kw_validation = self.keyword_extractor.validate_core_keywords(core_keywords)
        validation["errors"].extend(kw_validation.get("errors", []))
        validation["warnings"].extend(kw_validation.get("warnings", []))

        if kw_validation.get("errors"):
            validation["valid"] = False

        # 2. 图谱复杂度验证（不能过于简单）
        min_nodes = 10
        min_edges = 15

        if len(self.nodes) < min_nodes:
            validation["errors"].append(
                f"图谱节点数不足：{len(self.nodes)} < {min_nodes}（图谱过于简单）"
            )
            validation["valid"] = False

        if len(self.edges) < min_edges:
            validation["errors"].append(
                f"图谱边数不足：{len(self.edges)} < {min_edges}（图谱过于简单）"
            )
            validation["valid"] = False

        # 3. 数据一致性验证（数据不能乱）
        orphan_edges = []
        for edge_id, edge in self.edges.items():
            if edge.source not in self.nodes:
                orphan_edges.append(f"{edge_id} (source缺失)")
            if edge.target not in self.nodes:
                orphan_edges.append(f"{edge_id} (target缺失)")

        if orphan_edges:
            validation["errors"].append(
                f"发现{len(orphan_edges)}条孤立边（数据不一致）：{orphan_edges[:5]}"
            )
            validation["valid"] = False

        # 4. 打印验证结果
        if validation["errors"]:
            print("   ❌ 验证错误：")
            for error in validation["errors"]:
                print(f"      • {error}")

        if validation["warnings"]:
            print("   ⚠️  验证警告：")
            for warning in validation["warnings"]:
                print(f"      • {warning}")

        return validation

    def _write_to_databases(self):
        """阶段6：写入三数据库"""
        print(f"   写入节点：{len(self.nodes)}个")
        # 1. 写入节点
        for node in self.nodes.values():
            self.db_integration.add_node(node, quality_score=node.confidence)

        print(f"   写入边：{len(self.edges)}条")
        # 2. 写入边
        for edge in self.edges.values():
            self.db_integration.add_edge(edge, quality_score=edge.confidence)

    def _export_graph(
        self,
        core_keywords: List[CoreKeyword],
        project_name: str
    ) -> KnowledgeGraphExport:
        """阶段7：导出知识图谱"""
        # 统计Skills
        all_skills = set()
        for node in self.nodes.values():
            all_skills.update(node.source_skills)

        # 统计文档
        all_documents = set()
        for node in self.nodes.values():
            all_documents.update(node.source_documents)

        # 统计项目
        all_projects = set()
        for node in self.nodes.values():
            all_projects.update(node.source_projects)

        export = KnowledgeGraphExport(
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            core_keywords=core_keywords,
            total_projects=len(all_projects),
            total_documents=len(all_documents),
            total_skills=len(all_skills),
            statistics=self.stats,
        )

        return export

    def query_cypher(self, cypher: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询（Neo4j）

        例如：
        MATCH (n:Entity)-[r:RELATED]->(m:Entity)
        WHERE n.is_core_keyword = true
        RETURN n, r, m
        """
        return self.db_integration.query_cypher(cypher, params)

    def find_shortest_path(self, source_name: str, target_name: str) -> List[str]:
        """
        查找最短路径（NetworkX）

        Returns:
            路径中的节点名称列表
        """
        # 找到节点ID
        source_id = None
        target_id = None

        for node_id, node in self.nodes.items():
            if node.name == source_name:
                source_id = node_id
            if node.name == target_name:
                target_id = node_id

        if not source_id or not target_id:
            return []

        path_ids = self.db_integration.find_shortest_path(source_id, target_id)

        # 转换为名称
        path_names = []
        for node_id in path_ids:
            if node_id in self.nodes:
                path_names.append(self.nodes[node_id].name)

        return path_names

    def export_for_visualization(self) -> Dict[str, Any]:
        """
        导出可视化数据（前端G6使用）

        Returns:
            {
                "nodes": [...],  # G6节点格式
                "edges": [...],  # G6边格式
                "core_keywords": [...]
            }
        """
        viz_data = self.db_integration.export_for_visualization()

        # 添加核心关键词信息
        core_keyword_ids = [
            node.id for node in self.nodes.values() if node.is_core_keyword
        ]

        viz_data["core_keywords"] = core_keyword_ids

        return viz_data

    def _generate_node_id(self, name: str, entity_type: str) -> str:
        """生成节点ID"""
        raw = f"{name}|{entity_type}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _generate_edge_id(self, source: str, target: str, predicate: str) -> str:
        """生成边ID"""
        raw = f"{source}|{predicate}|{target}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _map_entity_type(self, entity_type: str) -> NodeType:
        """映射实体类型"""
        mapping = {
            "person": NodeType.PERSON,
            "location": NodeType.LOCATION,
            "organization": NodeType.ORGANIZATION,
            "tangible_heritage": NodeType.TANGIBLE_HERITAGE,
            "intangible_heritage": NodeType.INTANGIBLE_HERITAGE,
            "natural_heritage": NodeType.NATURAL_HERITAGE,
            "custom": NodeType.CUSTOM,
            "ritual": NodeType.RITUAL,
            "festival": NodeType.FESTIVAL,
            "ceremony": NodeType.CEREMONY,
            "clothing": NodeType.CLOTHING,
            "food": NodeType.FOOD,
            "housing": NodeType.HOUSING,
            "transportation": NodeType.TRANSPORTATION,
            "dialect_term": NodeType.DIALECT_TERM,
            "local_knowledge": NodeType.LOCAL_KNOWLEDGE,
        }
        return mapping.get(entity_type, NodeType.PERSON)

    def _map_relation_type(self, relation_type: str) -> EdgeType:
        """映射关系类型"""
        mapping = {
            "organizational_succession": EdgeType.ORGANIZATIONAL_SUCCESSION,
            "organizational_hierarchy": EdgeType.ORGANIZATIONAL_HIERARCHY,
            "organizational_membership": EdgeType.ORGANIZATIONAL_MEMBERSHIP,
            "foundation_support": EdgeType.FOUNDATION_SUPPORT,
            "association_help": EdgeType.ASSOCIATION_HELP,
            "ngo_partnership": EdgeType.NGO_PARTNERSHIP,
            "government_funding": EdgeType.GOVERNMENT_FUNDING,
            "cultural_inheritance": EdgeType.CULTURAL_INHERITANCE,
            "skill_transmission": EdgeType.SKILL_TRANSMISSION,
        }
        return mapping.get(relation_type, EdgeType.RELATED_TO)

    def close(self):
        """关闭数据库连接"""
        self.db_integration.close()
