"""
知识图谱可视化服务

提供图谱的可视化布局和渲染支持
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import math
import logging

from app.services.knowledge_graph.interactive_graph import (
    InteractiveKnowledgeGraph,
    GraphNode,
    GraphEdge
)

logger = logging.getLogger(__name__)


@dataclass
class NodePosition:
    """节点位置"""
    x: float
    y: float
    z: float = 0.0


class GraphLayoutEngine:
    """
    图布局引擎

    实现多种图布局算法
    """

    @staticmethod
    def force_directed_layout(
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        iterations: int = 50,
        area: float = 1000.0
    ) -> Dict[str, NodePosition]:
        """
        力导向布局算法

        Args:
            nodes: 节点列表
            edges: 边列表
            iterations: 迭代次数
            area: 布局区域大小

        Returns:
            节点位置字典
        """
        if not nodes:
            return {}

        # 初始化随机位置
        import random
        positions = {}
        for node in nodes:
            positions[node.id] = NodePosition(
                x=random.uniform(-area/2, area/2),
                y=random.uniform(-area/2, area/2)
            )

        # 计算理想距离
        k = math.sqrt(area / len(nodes))

        # 力导向迭代
        for iteration in range(iterations):
            # 计算排斥力
            forces = {node.id: {'x': 0.0, 'y': 0.0} for node in nodes}

            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    pos1 = positions[node1.id]
                    pos2 = positions[node2.id]

                    dx = pos2.x - pos1.x
                    dy = pos2.y - pos1.y
                    distance = math.sqrt(dx*dx + dy*dy) or 0.01

                    # 排斥力
                    repulsion = k * k / distance
                    fx = (dx / distance) * repulsion
                    fy = (dy / distance) * repulsion

                    forces[node1.id]['x'] -= fx
                    forces[node1.id]['y'] -= fy
                    forces[node2.id]['x'] += fx
                    forces[node2.id]['y'] += fy

            # 计算吸引力
            for edge in edges:
                source_pos = positions.get(edge.source_id)
                target_pos = positions.get(edge.target_id)

                if not source_pos or not target_pos:
                    continue

                dx = target_pos.x - source_pos.x
                dy = target_pos.y - source_pos.y
                distance = math.sqrt(dx*dx + dy*dy) or 0.01

                # 吸引力
                attraction = distance * distance / k
                fx = (dx / distance) * attraction
                fy = (dy / distance) * attraction

                forces[edge.source_id]['x'] += fx
                forces[edge.source_id]['y'] += fy
                forces[edge.target_id]['x'] -= fx
                forces[edge.target_id]['y'] -= fy

            # 应用力并限制移动
            temperature = 1.0 - (iteration / iterations)
            max_displacement = area * temperature * 0.1

            for node in nodes:
                force = forces[node.id]
                displacement = math.sqrt(force['x']**2 + force['y']**2) or 0.01

                if displacement > max_displacement:
                    force['x'] = (force['x'] / displacement) * max_displacement
                    force['y'] = (force['y'] / displacement) * max_displacement

                positions[node.id].x += force['x']
                positions[node.id].y += force['y']

        return positions

    @staticmethod
    def circular_layout(
        nodes: List[GraphNode],
        radius: float = 500.0
    ) -> Dict[str, NodePosition]:
        """
        圆形布局

        Args:
            nodes: 节点列表
            radius: 半径

        Returns:
            节点位置字典
        """
        positions = {}
        n = len(nodes)

        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            positions[node.id] = NodePosition(
                x=radius * math.cos(angle),
                y=radius * math.sin(angle)
            )

        return positions

    @staticmethod
    def hierarchical_layout(
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        level_height: float = 200.0,
        node_spacing: float = 100.0
    ) -> Dict[str, NodePosition]:
        """
        层次布局

        Args:
            nodes: 节点列表
            edges: 边列表
            level_height: 层高
            node_spacing: 节点间距

        Returns:
            节点位置字典
        """
        # 构建邻接表
        adjacency = {node.id: [] for node in nodes}
        for edge in edges:
            if edge.source_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)

        # 找根节点（入度为0）
        in_degree = {node.id: 0 for node in nodes}
        for edge in edges:
            if edge.target_id in in_degree:
                in_degree[edge.target_id] += 1

        roots = [node_id for node_id, degree in in_degree.items() if degree == 0]
        if not roots and nodes:
            roots = [nodes[0].id]

        # BFS 分配层级
        levels = {}
        queue = [(root, 0) for root in roots]
        visited = set()

        while queue:
            node_id, level = queue.pop(0)
            if node_id in visited:
                continue

            visited.add(node_id)
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)

            for neighbor_id in adjacency.get(node_id, []):
                if neighbor_id not in visited:
                    queue.append((neighbor_id, level + 1))

        # 分配位置
        positions = {}
        for level, node_ids in levels.items():
            width = len(node_ids) * node_spacing
            for i, node_id in enumerate(node_ids):
                positions[node_id] = NodePosition(
                    x=i * node_spacing - width / 2,
                    y=level * level_height
                )

        # 未访问的节点放在底部
        unvisited = [node.id for node in nodes if node.id not in visited]
        if unvisited:
            max_level = max(levels.keys()) if levels else 0
            width = len(unvisited) * node_spacing
            for i, node_id in enumerate(unvisited):
                positions[node_id] = NodePosition(
                    x=i * node_spacing - width / 2,
                    y=(max_level + 1) * level_height
                )

        return positions


class GraphVisualizationService:
    """
    图可视化服务

    提供图谱的可视化数据生成
    """

    def __init__(self, graph: InteractiveKnowledgeGraph):
        """初始化服务"""
        self.graph = graph
        self.layout_engine = GraphLayoutEngine()

    def generate_visualization_data(
        self,
        center_node_id: Optional[str] = None,
        depth: int = 2,
        max_nodes: int = 100,
        layout: str = "force"
    ) -> Dict[str, Any]:
        """
        生成可视化数据

        Args:
            center_node_id: 中心节点 ID（None 则显示全图）
            depth: 深度
            max_nodes: 最大节点数
            layout: 布局算法 (force/circular/hierarchical)

        Returns:
            可视化数据
        """
        # 获取子图
        if center_node_id:
            nodes, edges = self.graph.get_subgraph(center_node_id, depth, max_nodes)
        else:
            nodes = list(self.graph.nodes.values())[:max_nodes]
            edges = [
                edge for edge in self.graph.edges.values()
                if edge.source_id in [n.id for n in nodes] and
                   edge.target_id in [n.id for n in nodes]
            ]

        # 计算布局
        if layout == "circular":
            positions = self.layout_engine.circular_layout(nodes)
        elif layout == "hierarchical":
            positions = self.layout_engine.hierarchical_layout(nodes, edges)
        else:  # force
            positions = self.layout_engine.force_directed_layout(nodes, edges)

        # 生成节点数据
        nodes_data = []
        for node in nodes:
            pos = positions.get(node.id, NodePosition(0, 0))
            nodes_data.append({
                "id": node.id,
                "label": node.label,
                "type": node.node_type.value,
                "x": pos.x,
                "y": pos.y,
                "z": pos.z,
                "properties": node.properties,
                "size": self._calculate_node_size(node),
                "color": self._get_node_color(node)
            })

        # 生成边数据
        edges_data = []
        for edge in edges:
            edges_data.append({
                "id": edge.id,
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.relation_type.value,
                "weight": edge.weight,
                "label": edge.relation_type.value.replace("_", " ").title(),
                "color": self._get_edge_color(edge)
            })

        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "layout": layout,
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }

    def _calculate_node_size(self, node: GraphNode) -> float:
        """计算节点大小"""
        # 基于节点的度数计算大小
        degree = (
            len(self.graph.outgoing_edges.get(node.id, [])) +
            len(self.graph.incoming_edges.get(node.id, []))
        )
        return 10 + min(degree * 2, 50)

    def _get_node_color(self, node: GraphNode) -> str:
        """获取节点颜色"""
        color_map = {
            "concept": "#3b82f6",      # 蓝色
            "entity": "#10b981",       # 绿色
            "document": "#f59e0b",     # 橙色
            "user": "#ef4444",         # 红色
            "project": "#8b5cf6",      # 紫色
            "keyword": "#06b6d4",      # 青色
            "topic": "#ec4899"         # 粉色
        }
        return color_map.get(node.node_type.value, "#6b7280")

    def _get_edge_color(self, edge: GraphEdge) -> str:
        """获取边颜色"""
        # 基于权重调整透明度
        alpha = min(edge.weight, 1.0)
        return f"rgba(156, 163, 175, {alpha})"

    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取节点详细信息

        Args:
            node_id: 节点 ID

        Returns:
            节点详细信息
        """
        node = self.graph.get_node(node_id)
        if not node:
            return None

        # 获取邻居
        neighbors = self.graph.get_neighbors(node_id)

        # 获取连接的边
        outgoing_edges = [
            self.graph.edges[edge_id]
            for edge_id in self.graph.outgoing_edges.get(node_id, [])
        ]
        incoming_edges = [
            self.graph.edges[edge_id]
            for edge_id in self.graph.incoming_edges.get(node_id, [])
        ]

        return {
            "node": node.to_dict(),
            "neighbors": [n.to_dict() for n in neighbors],
            "outgoing_edges": [e.to_dict() for e in outgoing_edges],
            "incoming_edges": [e.to_dict() for e in incoming_edges],
            "statistics": {
                "degree": len(neighbors),
                "in_degree": len(incoming_edges),
                "out_degree": len(outgoing_edges)
            }
        }

    def search_nodes(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索节点

        Args:
            query: 搜索查询
            node_type: 节点类型过滤
            limit: 返回数量

        Returns:
            匹配的节点列表
        """
        results = []
        query_lower = query.lower()

        for node in self.graph.nodes.values():
            # 类型过滤
            if node_type and node.node_type.value != node_type:
                continue

            # 标签匹配
            if query_lower in node.label.lower():
                score = 1.0
                if node.label.lower() == query_lower:
                    score = 2.0
                elif node.label.lower().startswith(query_lower):
                    score = 1.5

                results.append({
                    "node": node.to_dict(),
                    "score": score
                })

            # 属性匹配
            elif any(query_lower in str(v).lower() for v in node.properties.values()):
                results.append({
                    "node": node.to_dict(),
                    "score": 0.5
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:limit]

    def get_shortest_path(
        self,
        start_id: str,
        end_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取最短路径

        Args:
            start_id: 起始节点 ID
            end_id: 目标节点 ID

        Returns:
            路径信息
        """
        path_ids = self.graph.find_path(start_id, end_id)
        if not path_ids:
            return None

        # 获取路径节点
        nodes = [self.graph.nodes[node_id] for node_id in path_ids]

        # 获取路径边
        edges = []
        for i in range(len(path_ids) - 1):
            source_id = path_ids[i]
            target_id = path_ids[i + 1]

            # 查找连接边
            for edge_id in self.graph.outgoing_edges.get(source_id, []):
                edge = self.graph.edges[edge_id]
                if edge.target_id == target_id:
                    edges.append(edge)
                    break

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "length": len(path_ids) - 1
        }
