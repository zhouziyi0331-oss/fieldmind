"""
交互式知识图谱服务

提供可视化的知识图谱构建、查询和交互功能
"""
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """节点类型"""
    CONCEPT = "concept"          # 概念
    ENTITY = "entity"            # 实体
    DOCUMENT = "document"        # 文档
    USER = "user"                # 用户
    PROJECT = "project"          # 项目
    KEYWORD = "keyword"          # 关键词
    TOPIC = "topic"              # 主题


class RelationType(str, Enum):
    """关系类型"""
    RELATED_TO = "related_to"        # 相关
    PART_OF = "part_of"              # 部分
    DEPENDS_ON = "depends_on"        # 依赖
    DERIVES_FROM = "derives_from"    # 派生
    REFERENCES = "references"        # 引用
    CREATED_BY = "created_by"        # 创建者
    BELONGS_TO = "belongs_to"        # 属于
    SIMILAR_TO = "similar_to"        # 相似
    LEADS_TO = "leads_to"            # 导向


@dataclass
class GraphNode:
    """图节点"""
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "properties": self.properties,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class GraphEdge:
    """图边"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


class InteractiveKnowledgeGraph:
    """
    交互式知识图谱

    提供知识图谱的构建、查询、更新和可视化功能
    """

    def __init__(self):
        """初始化知识图谱"""
        # 节点存储: node_id -> GraphNode
        self.nodes: Dict[str, GraphNode] = {}

        # 边存储: edge_id -> GraphEdge
        self.edges: Dict[str, GraphEdge] = {}

        # 索引: source_id -> List[edge_id]
        self.outgoing_edges: Dict[str, List[str]] = {}

        # 索引: target_id -> List[edge_id]
        self.incoming_edges: Dict[str, List[str]] = {}

        # 类型索引: node_type -> Set[node_id]
        self.nodes_by_type: Dict[NodeType, Set[str]] = {t: set() for t in NodeType}

        # 关系索引: relation_type -> Set[edge_id]
        self.edges_by_type: Dict[RelationType, Set[str]] = {t: set() for t in RelationType}

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: NodeType,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        """
        添加节点

        Args:
            node_id: 节点 ID
            label: 节点标签
            node_type: 节点类型
            properties: 节点属性
            metadata: 元数据

        Returns:
            创建的节点
        """
        if node_id in self.nodes:
            logger.warning(f"Node {node_id} already exists, updating")
            return self.update_node(node_id, label, properties, metadata)

        node = GraphNode(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=properties or {},
            metadata=metadata or {}
        )

        self.nodes[node_id] = node
        self.nodes_by_type[node_type].add(node_id)
        self.outgoing_edges[node_id] = []
        self.incoming_edges[node_id] = []

        logger.info(f"Added node {node_id} of type {node_type}")
        return node

    def update_node(
        self,
        node_id: str,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[GraphNode]:
        """
        更新节点

        Args:
            node_id: 节点 ID
            label: 新标签
            properties: 新属性
            metadata: 新元数据

        Returns:
            更新后的节点
        """
        if node_id not in self.nodes:
            logger.error(f"Node {node_id} not found")
            return None

        node = self.nodes[node_id]

        if label:
            node.label = label

        if properties:
            node.properties.update(properties)

        if metadata:
            node.metadata.update(metadata)

        node.updated_at = datetime.now()

        logger.info(f"Updated node {node_id}")
        return node

    def remove_node(self, node_id: str) -> bool:
        """
        删除节点

        Args:
            node_id: 节点 ID

        Returns:
            是否成功
        """
        if node_id not in self.nodes:
            logger.error(f"Node {node_id} not found")
            return False

        node = self.nodes[node_id]

        # 删除相关的边
        edges_to_remove = (
            self.outgoing_edges.get(node_id, []).copy() +
            self.incoming_edges.get(node_id, []).copy()
        )

        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # 从类型索引中移除
        self.nodes_by_type[node.node_type].discard(node_id)

        # 删除节点
        del self.nodes[node_id]
        del self.outgoing_edges[node_id]
        del self.incoming_edges[node_id]

        logger.info(f"Removed node {node_id}")
        return True

    def add_edge(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ) -> Optional[GraphEdge]:
        """
        添加边

        Args:
            edge_id: 边 ID
            source_id: 源节点 ID
            target_id: 目标节点 ID
            relation_type: 关系类型
            weight: 权重
            properties: 属性

        Returns:
            创建的边
        """
        # 验证节点存在
        if source_id not in self.nodes:
            logger.error(f"Source node {source_id} not found")
            return None

        if target_id not in self.nodes:
            logger.error(f"Target node {target_id} not found")
            return None

        if edge_id in self.edges:
            logger.warning(f"Edge {edge_id} already exists")
            return self.edges[edge_id]

        edge = GraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {}
        )

        self.edges[edge_id] = edge
        self.outgoing_edges[source_id].append(edge_id)
        self.incoming_edges[target_id].append(edge_id)
        self.edges_by_type[relation_type].add(edge_id)

        logger.info(f"Added edge {edge_id}: {source_id} -> {target_id} ({relation_type})")
        return edge

    def remove_edge(self, edge_id: str) -> bool:
        """
        删除边

        Args:
            edge_id: 边 ID

        Returns:
            是否成功
        """
        if edge_id not in self.edges:
            logger.error(f"Edge {edge_id} not found")
            return False

        edge = self.edges[edge_id]

        # 从索引中移除
        self.outgoing_edges[edge.source_id].remove(edge_id)
        self.incoming_edges[edge.target_id].remove(edge_id)
        self.edges_by_type[edge.relation_type].discard(edge_id)

        # 删除边
        del self.edges[edge_id]

        logger.info(f"Removed edge {edge_id}")
        return True

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """获取边"""
        return self.edges.get(edge_id)

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        relation_type: Optional[RelationType] = None
    ) -> List[GraphNode]:
        """
        获取邻居节点

        Args:
            node_id: 节点 ID
            direction: 方向 (outgoing/incoming/both)
            relation_type: 关系类型过滤

        Returns:
            邻居节点列表
        """
        if node_id not in self.nodes:
            return []

        neighbor_ids = set()

        if direction in ["outgoing", "both"]:
            for edge_id in self.outgoing_edges.get(node_id, []):
                edge = self.edges[edge_id]
                if relation_type is None or edge.relation_type == relation_type:
                    neighbor_ids.add(edge.target_id)

        if direction in ["incoming", "both"]:
            for edge_id in self.incoming_edges.get(node_id, []):
                edge = self.edges[edge_id]
                if relation_type is None or edge.relation_type == relation_type:
                    neighbor_ids.add(edge.source_id)

        return [self.nodes[nid] for nid in neighbor_ids]

    def get_subgraph(
        self,
        center_node_id: str,
        depth: int = 1,
        max_nodes: int = 100
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        获取子图

        Args:
            center_node_id: 中心节点 ID
            depth: 深度
            max_nodes: 最大节点数

        Returns:
            (节点列表, 边列表)
        """
        if center_node_id not in self.nodes:
            return [], []

        visited_nodes = {center_node_id}
        current_layer = {center_node_id}

        for _ in range(depth):
            if len(visited_nodes) >= max_nodes:
                break

            next_layer = set()
            for node_id in current_layer:
                neighbors = self.get_neighbors(node_id)
                for neighbor in neighbors:
                    if neighbor.id not in visited_nodes:
                        next_layer.add(neighbor.id)
                        visited_nodes.add(neighbor.id)

                        if len(visited_nodes) >= max_nodes:
                            break

                if len(visited_nodes) >= max_nodes:
                    break

            current_layer = next_layer

        # 获取节点
        nodes = [self.nodes[nid] for nid in visited_nodes]

        # 获取边
        edges = []
        for edge_id, edge in self.edges.items():
            if edge.source_id in visited_nodes and edge.target_id in visited_nodes:
                edges.append(edge)

        return nodes, edges

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """
        寻找两个节点之间的路径 (BFS)

        Args:
            start_id: 起始节点 ID
            end_id: 目标节点 ID
            max_depth: 最大深度

        Returns:
            路径节点 ID 列表
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        if start_id == end_id:
            return [start_id]

        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            neighbors = self.get_neighbors(current_id, direction="outgoing")

            for neighbor in neighbors:
                if neighbor.id == end_id:
                    return path + [neighbor.id]

                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append((neighbor.id, path + [neighbor.id]))

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": {
                t.value: len(nodes) for t, nodes in self.nodes_by_type.items()
            },
            "edges_by_type": {
                t.value: len(edges) for t, edges in self.edges_by_type.items()
            },
            "avg_degree": (
                sum(len(edges) for edges in self.outgoing_edges.values()) / len(self.nodes)
                if self.nodes else 0
            )
        }

    def export_graph(self) -> Dict[str, Any]:
        """
        导出整个图

        Returns:
            图数据
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "statistics": self.get_statistics()
        }

    def import_graph(self, graph_data: Dict[str, Any]) -> bool:
        """
        导入图数据

        Args:
            graph_data: 图数据

        Returns:
            是否成功
        """
        try:
            # 清空当前图
            self.nodes.clear()
            self.edges.clear()
            self.outgoing_edges.clear()
            self.incoming_edges.clear()
            for node_type in NodeType:
                self.nodes_by_type[node_type].clear()
            for relation_type in RelationType:
                self.edges_by_type[relation_type].clear()

            # 导入节点
            for node_data in graph_data.get("nodes", []):
                self.add_node(
                    node_id=node_data["id"],
                    label=node_data["label"],
                    node_type=NodeType(node_data["type"]),
                    properties=node_data.get("properties"),
                    metadata=node_data.get("metadata")
                )

            # 导入边
            for edge_data in graph_data.get("edges", []):
                self.add_edge(
                    edge_id=edge_data["id"],
                    source_id=edge_data["source"],
                    target_id=edge_data["target"],
                    relation_type=RelationType(edge_data["type"]),
                    weight=edge_data.get("weight", 1.0),
                    properties=edge_data.get("properties")
                )

            logger.info("Graph imported successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to import graph: {e}")
            return False
