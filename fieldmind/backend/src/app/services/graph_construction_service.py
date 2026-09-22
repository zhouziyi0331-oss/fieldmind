"""
图谱构建服务 - 统一的知识图谱构建入口

🎯 核心功能：
1. 节点创建（实体）
2. 边创建（关系）
3. 跨项目节点合并
4. 属性附加
5. 质量验证

架构：
┌─────────────────────────────────────────────────────────────┐
│                 GraphConstructionService                     │
│                                                               │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐      │
│  │ Node        │   │ Edge         │   │ Cross-      │      │
│  │ Creation    │   │ Creation     │   │ Project     │      │
│  │ (节点创建)   │   │ (边创建)      │   │ Merge       │      │
│  └─────────────┘   └──────────────┘   └─────────────┘      │
│         │                  │                   │             │
│         └──────────────────┴───────────────────┘             │
│                           ▼                                  │
│              ┌────────────────────────┐                      │
│              │ Quality Validation     │                      │
│              │ (质量验证)              │                      │
│              └────────────────────────┘                      │
│                           ▼                                  │
│              ┌────────────────────────┐                      │
│              │ GraphDatabaseIntegration│                     │
│              │ (三数据库集成)          │                      │
│              └────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘

整合来源：
- knowledge_agent_v2.py 中的构建逻辑
- graph_database_integration.py 中的存储逻辑
- entity_disambiguation_service.py 中的消歧逻辑

作者：FieldMind Team
日期：2024
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from app.core.logging import logger
from app.models.knowledge_graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    KnowledgeGraphExport,
)
from app.models.enriched_chunk import EnrichedChunk, Entity, Relation
from app.services.entity_disambiguation_service import (
    EntityDisambiguationService,
    get_entity_disambiguation_service,
)
from app.services.graph_database_integration_v2 import (
    GraphDatabaseIntegrationV2,
    get_graph_database_integration,
)
from pydantic import BaseModel, Field
import hashlib
import uuid


class NodeCreationResult(BaseModel):
    """节点创建结果"""
    node_id: str
    node_name: str
    node_type: NodeType
    is_new: bool  # True=新创建，False=已存在/合并
    merged_with: Optional[str] = None  # 如果合并，记录合并到的节点ID
    quality_score: float
    quality_tier: str  # HIGH/MEDIUM/LOW


class EdgeCreationResult(BaseModel):
    """边创建结果"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    is_new: bool
    quality_score: float
    quality_tier: str


class GraphConstructionResult(BaseModel):
    """图谱构建结果"""
    project_name: str
    nodes_created: int
    nodes_merged: int
    edges_created: int
    total_nodes: int
    total_edges: int
    quality_distribution: Dict[str, int]  # {"HIGH": 10, "MEDIUM": 5, "LOW": 2}
    core_keywords: List[str]  # 核心关键词（PageRank提取）
    construction_time: float  # 秒


class GraphConstructionService:
    """
    图谱构建服务（统一版）

    核心职责：
    1. 从enriched_chunks提取实体和关系
    2. 实体消歧和合并
    3. 创建图谱节点和边
    4. 跨项目统一大图
    5. 质量验证和控制
    6. 写入三数据库
    """

    def __init__(self):
        # 依赖服务
        self.disambiguation_service = get_entity_disambiguation_service()
        self.db_integration = get_graph_database_integration()

        # 内存中的图谱（临时，用于构建过程）
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}

        # 实体指纹缓存（用于消歧）
        self.entity_fingerprints: Dict[str, Dict[str, Any]] = {}

        # 统计
        self.stats = {
            "nodes_created": 0,
            "nodes_merged": 0,
            "edges_created": 0,
            "quality_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
        }

        logger.info("✅ GraphConstructionService initialized")

    def build_graph_from_chunks(
        self,
        enriched_chunks: List[EnrichedChunk],
        project_name: str,
        mode: str = "auto"
    ) -> GraphConstructionResult:
        """
        从enriched_chunks构建知识图谱

        Args:
            enriched_chunks: Agent 3的输出（富化的文本块）
            project_name: 项目名称
            mode: 构建模式（auto/relationship/folklore）

        Returns:
            构建结果
        """
        start_time = datetime.now()
        logger.info(f"🚀 开始构建知识图谱：项目={project_name}, 模式={mode}")

        # 阶段1：提取实体
        logger.info("📊 阶段1：提取实体")
        entities_by_name = self._extract_entities_from_chunks(enriched_chunks, project_name)

        # 阶段2：实体消歧
        logger.info("🔍 阶段2：实体消歧")
        disambiguated_entities = self._disambiguate_entities(entities_by_name)

        # 阶段3：创建节点
        logger.info("📐 阶段3：创建节点")
        node_creation_results = self._create_nodes_from_entities(
            disambiguated_entities, project_name
        )

        # 阶段4：提取关系
        logger.info("🔗 阶段4：提取关系")
        relations = self._extract_relations_from_chunks(enriched_chunks)

        # 阶段5：创建边
        logger.info("🌉 阶段5：创建边")
        edge_creation_results = self._create_edges_from_relations(relations, project_name)

        # 阶段6：写入数据库
        logger.info("💾 阶段6：写入三数据库")
        self._write_to_databases()

        # 阶段7：提取核心关键词
        logger.info("🎯 阶段7：提取核心关键词")
        core_keywords = self._extract_core_keywords()

        # 计算构建时间
        construction_time = (datetime.now() - start_time).total_seconds()

        # 构建结果
        result = GraphConstructionResult(
            project_name=project_name,
            nodes_created=self.stats["nodes_created"],
            nodes_merged=self.stats["nodes_merged"],
            edges_created=self.stats["edges_created"],
            total_nodes=len(self.nodes),
            total_edges=len(self.edges),
            quality_distribution=self.stats["quality_distribution"],
            core_keywords=core_keywords,
            construction_time=construction_time,
        )

        logger.success(f"✅ 图谱构建完成：{result.total_nodes}节点，{result.total_edges}边，核心关键词{len(core_keywords)}个，耗时{construction_time:.2f}秒")
        return result

    def create_node(
        self,
        name: str,
        node_type: NodeType,
        description: Optional[str] = None,
        importance_score: float = 0.5,
        is_core_keyword: bool = False,
        project_name: str = "default",
        source_documents: List[str] = None,
        **kwargs
    ) -> NodeCreationResult:
        """
        创建单个节点

        Args:
            name: 节点名称
            node_type: 节点类型
            description: 描述
            importance_score: 重要性分数
            is_core_keyword: 是否核心关键词
            project_name: 项目名称
            source_documents: 来源文档列表
            **kwargs: 其他属性

        Returns:
            节点创建结果
        """
        # 生成节点ID
        node_id = self._generate_node_id(name, node_type)

        # 检查是否已存在
        if node_id in self.nodes:
            existing_node = self.nodes[node_id]
            logger.debug(f"节点'{name}'已存在，跳过创建")
            return NodeCreationResult(
                node_id=node_id,
                node_name=name,
                node_type=node_type,
                is_new=False,
                quality_score=existing_node.confidence,
                quality_tier="MEDIUM",
            )

        # 创建节点
        node = GraphNode(
            id=node_id,
            name=name,
            type=node_type,
            description=description,
            importance_score=importance_score,
            is_core_keyword=is_core_keyword,
            source_projects=[project_name],
            source_documents=source_documents or [],
            **kwargs
        )

        # 计算质量分数
        quality_score = self._calculate_node_quality(node)

        # 保存节点
        self.nodes[node_id] = node
        self.stats["nodes_created"] += 1

        # 质量分级
        if quality_score >= 0.75:
            quality_tier = "HIGH"
            self.stats["quality_distribution"]["HIGH"] += 1
        elif quality_score >= 0.5:
            quality_tier = "MEDIUM"
            self.stats["quality_distribution"]["MEDIUM"] += 1
        else:
            quality_tier = "LOW"
            self.stats["quality_distribution"]["LOW"] += 1

        logger.debug(f"创建节点'{name}' (类型={node_type}, 质量={quality_tier})")

        return NodeCreationResult(
            node_id=node_id,
            node_name=name,
            node_type=node_type,
            is_new=True,
            quality_score=quality_score,
            quality_tier=quality_tier,
        )

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        description: Optional[str] = None,
        weight: float = 1.0,
        confidence: float = 1.0,
        source_documents: List[str] = None,
        evidence: List[str] = None,
        **kwargs
    ) -> EdgeCreationResult:
        """
        创建单个边

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            edge_type: 边类型
            description: 描述
            weight: 权重
            confidence: 置信度
            source_documents: 来源文档
            evidence: 证据列表
            **kwargs: 其他属性

        Returns:
            边创建结果
        """
        # 验证节点存在
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"节点不存在：{source_id} 或 {target_id}，跳过边创建")
            return EdgeCreationResult(
                edge_id="",
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                is_new=False,
                quality_score=0.0,
                quality_tier="LOW",
            )

        # 生成边ID
        edge_id = self._generate_edge_id(source_id, target_id, edge_type)

        # 检查是否已存在
        if edge_id in self.edges:
            logger.debug(f"边'{source_id}→{target_id}'已存在，跳过创建")
            return EdgeCreationResult(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                is_new=False,
                quality_score=self.edges[edge_id].confidence,
                quality_tier="MEDIUM",
            )

        # 创建边
        edge = GraphEdge(
            id=edge_id,
            source=source_id,
            target=target_id,
            type=edge_type,
            description=description,
            weight=weight,
            confidence=confidence,
            source_documents=source_documents or [],
            evidence=evidence or [],
            **kwargs
        )

        # 计算质量分数
        quality_score = confidence  # 简化版，使用置信度作为质量分数

        # 保存边
        self.edges[edge_id] = edge
        self.stats["edges_created"] += 1

        # 质量分级
        if quality_score >= 0.75:
            quality_tier = "HIGH"
        elif quality_score >= 0.5:
            quality_tier = "MEDIUM"
        else:
            quality_tier = "LOW"

        logger.debug(f"创建边'{self.nodes[source_id].name}→{self.nodes[target_id].name}' (类型={edge_type})")

        return EdgeCreationResult(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            is_new=True,
            quality_score=quality_score,
            quality_tier=quality_tier,
        )

    def merge_nodes_cross_project(
        self,
        node_ids: List[str],
        target_name: str,
        reasoning: str = "跨项目合并"
    ) -> str:
        """
        跨项目节点合并

        Args:
            node_ids: 要合并的节点ID列表
            target_name: 合并后的节点名称
            reasoning: 合并理由

        Returns:
            合并后的节点ID
        """
        if len(node_ids) < 2:
            logger.warning("合并节点数量少于2个，跳过")
            return node_ids[0] if node_ids else ""

        # 选择第一个节点作为主节点
        primary_node_id = node_ids[0]
        primary_node = self.nodes.get(primary_node_id)

        if not primary_node:
            logger.error(f"主节点{primary_node_id}不存在")
            return ""

        # 合并其他节点的信息到主节点
        for node_id in node_ids[1:]:
            if node_id not in self.nodes:
                continue

            merge_node = self.nodes[node_id]

            # 合并来源项目
            primary_node.source_projects.extend(merge_node.source_projects)
            primary_node.source_projects = list(set(primary_node.source_projects))

            # 合并来源文档
            primary_node.source_documents.extend(merge_node.source_documents)
            primary_node.source_documents = list(set(primary_node.source_documents))

            # 合并行为
            primary_node.actions.extend(merge_node.actions)

            # 合并时间线
            primary_node.timeline.extend(merge_node.timeline)

            # 更新重要性分数（取最大值）
            primary_node.importance_score = max(
                primary_node.importance_score,
                merge_node.importance_score
            )

            # 删除被合并的节点
            del self.nodes[node_id]

            logger.debug(f"节点'{merge_node.name}'合并到'{primary_node.name}'")
            self.stats["nodes_merged"] += 1

        # 更新名称
        primary_node.name = target_name
        primary_node.updated_at = datetime.now()

        logger.info(f"✅ 跨项目合并完成：{len(node_ids)}个节点 → '{target_name}'")
        return primary_node_id

    def _extract_entities_from_chunks(
        self,
        enriched_chunks: List[EnrichedChunk],
        project_name: str
    ) -> Dict[str, List[Entity]]:
        """
        从enriched_chunks提取实体

        Returns:
            Dict[实体名称, List[Entity实例]]
        """
        entities_by_name: Dict[str, List[Entity]] = {}

        for chunk in enriched_chunks:
            for entity in chunk.entities:
                if entity.text not in entities_by_name:
                    entities_by_name[entity.text] = []
                entities_by_name[entity.text].append(entity)

        logger.info(f"提取到{len(entities_by_name)}个不同实体名称")
        return entities_by_name

    def _disambiguate_entities(
        self,
        entities_by_name: Dict[str, List[Entity]]
    ) -> Dict[str, Entity]:
        """
        实体消歧

        Returns:
            Dict[消歧后的实体ID, Entity代表]
        """
        disambiguated: Dict[str, Entity] = {}

        for entity_name, entity_instances in entities_by_name.items():
            if len(entity_instances) == 1:
                # 只有一个实例，无需消歧
                disambiguated[entity_name] = entity_instances[0]
            else:
                # 多个实例，需要消歧
                # 简化版：选择confidence最高的作为代表
                best_entity = max(entity_instances, key=lambda e: e.confidence if hasattr(e, 'confidence') else 0.5)
                disambiguated[entity_name] = best_entity

        logger.info(f"消歧后{len(disambiguated)}个唯一实体")
        return disambiguated

    def _create_nodes_from_entities(
        self,
        disambiguated_entities: Dict[str, Entity],
        project_name: str
    ) -> List[NodeCreationResult]:
        """从消歧后的实体创建节点"""
        results = []

        for entity_name, entity in disambiguated_entities.items():
            # 映射实体类型到节点类型
            node_type = self._map_entity_type_to_node_type(entity.type)

            result = self.create_node(
                name=entity.text,
                node_type=node_type,
                description=None,
                importance_score=0.5,
                is_core_keyword=False,
                project_name=project_name,
                source_documents=[],
            )
            results.append(result)

        return results

    def _extract_relations_from_chunks(
        self,
        enriched_chunks: List[EnrichedChunk]
    ) -> List[Relation]:
        """从enriched_chunks提取关系"""
        relations = []

        for chunk in enriched_chunks:
            relations.extend(chunk.relations)

        logger.info(f"提取到{len(relations)}个关系")
        return relations

    def _create_edges_from_relations(
        self,
        relations: List[Relation],
        project_name: str
    ) -> List[EdgeCreationResult]:
        """从关系创建边"""
        results = []

        for relation in relations:
            # 查找源节点和目标节点
            source_node = self._find_node_by_name(relation.subject)
            target_node = self._find_node_by_name(relation.object)

            if not source_node or not target_node:
                continue

            # 映射关系类型到边类型
            edge_type = self._map_relation_type_to_edge_type(relation.relation)

            result = self.create_edge(
                source_id=source_node.id,
                target_id=target_node.id,
                edge_type=edge_type,
                description=None,
                weight=1.0,
                confidence=relation.confidence if hasattr(relation, 'confidence') else 0.8,
                source_documents=[],
                evidence=[],
            )
            results.append(result)

        return results

    def _write_to_databases(self):
        """将构建的图谱写入三数据库"""
        logger.info("写入节点到三数据库...")

        for node in self.nodes.values():
            quality_score = self._calculate_node_quality(node)
            self.db_integration.add_node_with_enhancement(
                node=node,
                quality_score=quality_score,
                enable_verification=True,
            )

        logger.info("写入边到三数据库...")

        for edge in self.edges.values():
            quality_score = edge.confidence
            self.db_integration.add_edge_with_enhancement(
                edge=edge,
                quality_score=quality_score,
                enable_verification=True,
            )

        logger.success("✅ 三数据库写入完成")

    def _extract_core_keywords(self) -> List[str]:
        """
        提取核心关键词（使用PageRank）

        Returns:
            核心关键词列表（5-10个）
        """
        try:
            from app.services.core_keyword_extractor import get_core_keyword_extractor

            extractor = get_core_keyword_extractor()

            # 收集所有is_core_keyword=True的节点
            core_nodes = [
                node for node in self.nodes.values()
                if node.is_core_keyword
            ]

            # 如果没有标记的核心节点，从所有节点中提取
            if not core_nodes:
                core_nodes = list(self.nodes.values())

            # 按PageRank排序（从properties中获取）
            nodes_with_pagerank = []
            for node in core_nodes:
                pagerank = node.properties.get("pagerank", 0.0)
                nodes_with_pagerank.append((node.name, pagerank))

            # 排序并取前10个
            nodes_with_pagerank.sort(key=lambda x: x[1], reverse=True)
            core_keywords = [name for name, _ in nodes_with_pagerank[:10]]

            logger.info(f"✅ 提取核心关键词：{len(core_keywords)}个")
            return core_keywords

        except Exception as e:
            logger.warning(f"⚠️ 提取核心关键词失败: {e}")
            # 降级方案：返回importance_score最高的节点
            sorted_nodes = sorted(
                self.nodes.values(),
                key=lambda n: n.importance_score,
                reverse=True
            )
            return [n.name for n in sorted_nodes[:10]]

    def _calculate_node_quality(self, node: GraphNode) -> float:
        """
        计算节点质量分数

        维度：
        1. 置信度（40%）
        2. 来源文档数量（20%）
        3. 是否核心关键词（20%）
        4. 重要性分数（20%）
        """
        score = 0.0

        # 1. 置信度
        score += node.confidence * 0.4

        # 2. 来源文档数量
        doc_score = min(len(node.source_documents) / 3.0, 1.0)  # 3个文档=满分
        score += doc_score * 0.2

        # 3. 是否核心关键词
        if node.is_core_keyword:
            score += 0.2

        # 4. 重要性分数
        score += node.importance_score * 0.2

        return min(score, 1.0)

    def _generate_node_id(self, name: str, node_type: NodeType) -> str:
        """生成节点ID（基于名称和类型的MD5）"""
        raw = f"{name}_{node_type}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _generate_edge_id(self, source_id: str, target_id: str, edge_type: EdgeType) -> str:
        """生成边ID"""
        raw = f"{source_id}_{target_id}_{edge_type}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _map_entity_type_to_node_type(self, entity_type: str) -> NodeType:
        """映射实体类型到节点类型"""
        mapping = {
            "PERSON": NodeType.PERSON,
            "ORG": NodeType.ORGANIZATION,
            "ORGANIZATION": NodeType.ORGANIZATION,
            "GPE": NodeType.VILLAGE_COMMITTEE,
            "LOC": NodeType.ORGANIZATION,
            "EVENT": NodeType.RITUAL,
            "DATE": NodeType.CORE_KEYWORD,
        }
        return mapping.get(entity_type.upper(), NodeType.PERSON)

    def _map_relation_type_to_edge_type(self, relation_type: str) -> EdgeType:
        """映射关系类型到边类型"""
        mapping = {
            "家族关系": EdgeType.FAMILY_KINSHIP,
            "继任": EdgeType.ORGANIZATIONAL_SUCCESSION,
            "传承": EdgeType.CULTURAL_INHERITANCE,
            "技艺传授": EdgeType.SKILL_TRANSMISSION,
            "师徒": EdgeType.MENTOR_STUDENT,
            "记录": EdgeType.RECORDED_IN,
        }
        return mapping.get(relation_type, EdgeType.FAMILY_KINSHIP)

    def _find_node_by_name(self, name: str) -> Optional[GraphNode]:
        """根据名称查找节点"""
        for node in self.nodes.values():
            if node.name == name:
                return node
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "stats": self.stats,
            "database_stats": self.db_integration.get_statistics(),
        }

    def export_graph(self, project_name: str) -> KnowledgeGraphExport:
        """导出图谱"""
        return KnowledgeGraphExport(
            project_name=project_name,
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            core_keywords=[],
            total_nodes=len(self.nodes),
            total_edges=len(self.edges),
            total_core_keywords=0,
        )

    def export_graph_data(
        self, project_name: Optional[str] = None, include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        导出图谱数据（JSON格式）

        Args:
            project_name: 项目名称（为空则导出全部）
            include_metrics: 是否包含NetworkX计算的指标

        Returns:
            完整的图谱数据字典
        """
        # 筛选节点
        nodes_to_export = []
        for node in self.nodes.values():
            if project_name and node.properties.get("project_name") != project_name:
                continue

            node_dict = {
                "id": node.id,
                "name": node.name,
                "type": node.type.value,
                "properties": node.properties,
            }

            # 如果包含指标，添加NetworkX计算的指标
            if include_metrics and "pagerank" in node.properties:
                node_dict["metrics"] = {
                    "pagerank": node.properties.get("pagerank"),
                    "degree_centrality": node.properties.get("degree_centrality"),
                    "betweenness_centrality": node.properties.get("betweenness_centrality"),
                }

            nodes_to_export.append(node_dict)

        # 筛选边
        edges_to_export = []
        node_ids_set = {n["id"] for n in nodes_to_export}

        for edge in self.edges.values():
            # 只导出两端节点都存在的边
            if edge.source not in node_ids_set or edge.target not in node_ids_set:
                continue

            edge_dict = {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": edge.type.value,
                "properties": edge.properties,
            }
            edges_to_export.append(edge_dict)

        return {
            "project_name": project_name or "all",
            "nodes": nodes_to_export,
            "edges": edges_to_export,
            "statistics": {
                "total_nodes": len(nodes_to_export),
                "total_edges": len(edges_to_export),
            },
            "exported_at": datetime.now().isoformat(),
        }

    def export_html_visualization(
        self, output_path: str, project_name: Optional[str] = None
    ) -> None:
        """
        导出HTML可视化文件

        Args:
            output_path: 输出文件路径
            project_name: 项目名称（为空则导出全部）
        """
        graph_data = self.export_graph_data(project_name=project_name, include_metrics=True)

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FieldMind 知识图谱 - {project_name}</title>
    <script src="https://unpkg.com/@antv/g6@4.8.18/dist/g6.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #container {{ width: 100vw; height: 100vh; }}
        .info {{ position: absolute; top: 20px; left: 20px; background: white;
                 padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .info h3 {{ margin: 0 0 10px 0; }}
        .info p {{ margin: 5px 0; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="info">
        <h3>📊 知识图谱统计</h3>
        <p>项目：{project_name}</p>
        <p>节点数：{node_count}</p>
        <p>边数：{edge_count}</p>
        <p>导出时间：{exported_at}</p>
    </div>
    <div id="container"></div>
    <script>
        const data = {graph_data_json};

        // 转换为G6格式
        const graphData = {{
            nodes: data.nodes.map(n => ({{
                id: n.id,
                label: n.name,
                type: n.type,
                style: {{
                    fill: getNodeColor(n.type),
                    lineWidth: 2,
                }}
            }})),
            edges: data.edges.map(e => ({{
                source: e.source,
                target: e.target,
                label: e.type,
            }}))
        }};

        function getNodeColor(type) {{
            const colors = {{
                'PERSON': '#5B8FF9',
                'LOCATION': '#5AD8A6',
                'ORGANIZATION': '#5D7092',
                'EVENT': '#F6BD16',
                'CONCEPT': '#E86452',
                'ARTIFACT': '#6DC8EC',
                'TIMEPOINT': '#945FB9',
                'KEYWORD': '#FF9845',
            }};
            return colors[type] || '#C9C9C9';
        }}

        const graph = new G6.Graph({{
            container: 'container',
            width: window.innerWidth,
            height: window.innerHeight,
            modes: {{
                default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
            }},
            layout: {{
                type: 'force',
                preventOverlap: true,
                nodeStrength: -50,
                edgeStrength: 0.2,
            }},
            defaultNode: {{
                size: 30,
                labelCfg: {{
                    position: 'bottom',
                    style: {{ fontSize: 12 }},
                }},
            }},
            defaultEdge: {{
                type: 'line',
                style: {{ stroke: '#999', lineWidth: 1 }},
                labelCfg: {{ style: {{ fontSize: 10 }} }},
            }},
        }});

        graph.data(graphData);
        graph.render();

        // 响应式
        window.onresize = () => {{
            graph.changeSize(window.innerWidth, window.innerHeight);
        }};
    </script>
</body>
</html>
        """

        import json
        html_content = html_template.format(
            project_name=graph_data["project_name"],
            node_count=graph_data["statistics"]["total_nodes"],
            edge_count=graph_data["statistics"]["total_edges"],
            exported_at=graph_data["exported_at"],
            graph_data_json=json.dumps(graph_data, ensure_ascii=False, indent=2),
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"✅ HTML可视化已导出: {output_path}")

    def export_cypher_statements(self, project_name: Optional[str] = None) -> List[str]:
        """
        导出Neo4j Cypher导入语句

        Args:
            project_name: 项目名称（为空则导出全部）

        Returns:
            Cypher语句列表
        """
        statements = []

        # 创建节点
        for node in self.nodes.values():
            if project_name and node.properties.get("project_name") != project_name:
                continue

            props = ", ".join([
                f"{k}: {repr(v)}" for k, v in node.properties.items()
            ])

            cypher = f"""CREATE (n:Entity {{id: '{node.id}', name: '{node.name}', type: '{node.type.value}', {props}}})"""
            statements.append(cypher)

        # 创建边
        node_ids_set = {
            n.id for n in self.nodes.values()
            if not project_name or n.properties.get("project_name") == project_name
        }

        for edge in self.edges.values():
            if edge.source not in node_ids_set or edge.target not in node_ids_set:
                continue

            props = ", ".join([
                f"{k}: {repr(v)}" for k, v in edge.properties.items()
            ])

            cypher = f"""
MATCH (a:Entity {{id: '{edge.source}'}}), (b:Entity {{id: '{edge.target}'}})
CREATE (a)-[r:{edge.type.value} {{id: '{edge.id}', {props}}}]->(b)
            """.strip()
            statements.append(cypher)

        logger.info(f"✅ Cypher语句已生成: {len(statements)}条")
        return statements


# ========== 工厂函数 ==========

def get_graph_construction_service() -> GraphConstructionService:
    """获取图谱构建服务单例"""
    return GraphConstructionService()
