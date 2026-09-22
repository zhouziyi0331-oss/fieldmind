"""
知识图谱查询服务
Knowledge Graph Query Service

功能：
1. 节点查询（按类型、属性、ID）
2. 边查询（按关系类型、源/目标节点）
3. 路径查询（最短路径、所有路径）
4. 邻居查询（N 跳邻居）
5. 子图查询（提取子图）
6. 全文搜索（节点标签搜索）
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import json

from app.models.unified_models import KnowledgeGraphNode, KnowledgeGraphEdge

logger = logging.getLogger(__name__)


class KnowledgeGraphQueryService:
    """知识图谱查询服务"""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # 节点查询
    # ============================================================

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        根据 ID 获取节点

        Args:
            node_id: 节点 ID

        Returns:
            节点信息
        """
        node = self.db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.node_id == node_id
        ).first()

        if not node:
            return None

        return self._node_to_dict(node)

    def get_nodes_by_type(
        self,
        node_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        根据类型获取节点

        Args:
            node_type: 节点类型（entity/event/concept/document/knowledge_unit）
            limit: 返回数量
            offset: 偏移量

        Returns:
            节点列表
        """
        nodes = self.db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.node_type == node_type
        ).order_by(
            KnowledgeGraphNode.importance_score.desc()
        ).limit(limit).offset(offset).all()

        return [self._node_to_dict(node) for node in nodes]

    def search_nodes(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        搜索节点（全文搜索）

        Args:
            query: 搜索关键词
            node_type: 节点类型（可选）
            limit: 返回数量

        Returns:
            节点列表
        """
        q = self.db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.label.like(f'%{query}%')
        )

        if node_type:
            q = q.filter(KnowledgeGraphNode.node_type == node_type)

        nodes = q.order_by(
            KnowledgeGraphNode.importance_score.desc()
        ).limit(limit).all()

        return [self._node_to_dict(node) for node in nodes]

    def get_nodes_by_source(
        self,
        source_table: str,
        source_id: str
    ) -> List[Dict]:
        """
        根据来源表和 ID 获取节点

        Args:
            source_table: 来源表名
            source_id: 来源表的 ID

        Returns:
            节点列表
        """
        nodes = self.db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.source_table == source_table,
            KnowledgeGraphNode.source_id == source_id
        ).all()

        return [self._node_to_dict(node) for node in nodes]

    # ============================================================
    # 边查询
    # ============================================================

    def get_edge_by_id(self, edge_id: str) -> Optional[Dict]:
        """
        根据 ID 获取边

        Args:
            edge_id: 边 ID

        Returns:
            边信息
        """
        edge = self.db.query(KnowledgeGraphEdge).filter(
            KnowledgeGraphEdge.edge_id == edge_id
        ).first()

        if not edge:
            return None

        return self._edge_to_dict(edge)

    def get_edges_by_type(
        self,
        edge_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        根据类型获取边

        Args:
            edge_type: 边类型（关系类型）
            limit: 返回数量
            offset: 偏移量

        Returns:
            边列表
        """
        edges = self.db.query(KnowledgeGraphEdge).filter(
            KnowledgeGraphEdge.edge_type == edge_type
        ).limit(limit).offset(offset).all()

        return [self._edge_to_dict(edge) for edge in edges]

    def get_node_edges(
        self,
        node_id: str,
        direction: str = 'both'
    ) -> Dict[str, List[Dict]]:
        """
        获取节点的所有边

        Args:
            node_id: 节点 ID
            direction: 方向（'in'/'out'/'both'）

        Returns:
            边列表（分入边和出边）
        """
        result = {
            'in_edges': [],
            'out_edges': []
        }

        if direction in ['in', 'both']:
            in_edges = self.db.query(KnowledgeGraphEdge).filter(
                KnowledgeGraphEdge.target_node_id == node_id
            ).all()
            result['in_edges'] = [self._edge_to_dict(edge) for edge in in_edges]

        if direction in ['out', 'both']:
            out_edges = self.db.query(KnowledgeGraphEdge).filter(
                KnowledgeGraphEdge.source_node_id == node_id
            ).all()
            result['out_edges'] = [self._edge_to_dict(edge) for edge in out_edges]

        return result

    # ============================================================
    # 邻居查询
    # ============================================================

    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1,
        direction: str = 'both',
        edge_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取节点的邻居

        Args:
            node_id: 节点 ID
            depth: 跳数（1-3）
            direction: 方向（'in'/'out'/'both'）
            edge_types: 边类型过滤

        Returns:
            邻居节点和边
        """
        if depth > 3:
            depth = 3  # 限制最大跳数

        visited_nodes = set()
        visited_edges = set()
        neighbors = []
        edges = []

        # 初始节点
        current_level = {node_id}
        visited_nodes.add(node_id)

        for _ in range(depth):
            next_level = set()

            for current_node_id in current_level:
                # 获取邻居
                node_edges = self.get_node_edges(current_node_id, direction)

                for edge_dict in node_edges['out_edges'] + node_edges['in_edges']:
                    edge_id = edge_dict['edge_id']

                    # 过滤边类型
                    if edge_types and edge_dict['edge_type'] not in edge_types:
                        continue

                    # 避免重复
                    if edge_id in visited_edges:
                        continue

                    visited_edges.add(edge_id)
                    edges.append(edge_dict)

                    # 获取邻居节点
                    neighbor_id = (
                        edge_dict['target_node_id']
                        if edge_dict['source_node_id'] == current_node_id
                        else edge_dict['source_node_id']
                    )

                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        next_level.add(neighbor_id)

                        neighbor_node = self.get_node_by_id(neighbor_id)
                        if neighbor_node:
                            neighbors.append(neighbor_node)

            current_level = next_level

            if not current_level:
                break

        return {
            'center_node_id': node_id,
            'depth': depth,
            'neighbors': neighbors,
            'edges': edges,
            'total_neighbors': len(neighbors),
            'total_edges': len(edges)
        }

    def get_direct_neighbors(self, node_id: str) -> Dict[str, Any]:
        """
        获取直接邻居（1 跳）

        Args:
            node_id: 节点 ID

        Returns:
            直接邻居信息
        """
        return self.get_neighbors(node_id, depth=1)

    # ============================================================
    # 路径查询
    # ============================================================

    def find_shortest_path(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 5
    ) -> Optional[Dict]:
        """
        查找最短路径（BFS）

        Args:
            start_node_id: 起始节点 ID
            end_node_id: 目标节点 ID
            max_depth: 最大深度

        Returns:
            路径信息
        """
        if start_node_id == end_node_id:
            return {
                'found': True,
                'path_length': 0,
                'nodes': [self.get_node_by_id(start_node_id)],
                'edges': []
            }

        # BFS 搜索
        queue = [(start_node_id, [start_node_id], [])]
        visited = {start_node_id}

        while queue:
            current_node_id, path_nodes, path_edges = queue.pop(0)

            # 深度限制
            if len(path_nodes) > max_depth:
                continue

            # 获取邻居
            neighbors_data = self.get_neighbors(current_node_id, depth=1)

            for edge in neighbors_data['edges']:
                # 确定下一个节点
                next_node_id = (
                    edge['target_node_id']
                    if edge['source_node_id'] == current_node_id
                    else edge['source_node_id']
                )

                # 找到目标
                if next_node_id == end_node_id:
                    final_path_nodes = path_nodes + [next_node_id]
                    final_path_edges = path_edges + [edge]

                    return {
                        'found': True,
                        'path_length': len(final_path_nodes) - 1,
                        'nodes': [self.get_node_by_id(nid) for nid in final_path_nodes],
                        'edges': final_path_edges
                    }

                # 继续搜索
                if next_node_id not in visited:
                    visited.add(next_node_id)
                    queue.append((
                        next_node_id,
                        path_nodes + [next_node_id],
                        path_edges + [edge]
                    ))

        # 未找到路径
        return {
            'found': False,
            'message': f'No path found between {start_node_id} and {end_node_id}'
        }

    # ============================================================
    # 子图查询
    # ============================================================

    def get_subgraph(
        self,
        node_ids: List[str],
        include_edges: bool = True
    ) -> Dict[str, Any]:
        """
        提取子图

        Args:
            node_ids: 节点 ID 列表
            include_edges: 是否包含边

        Returns:
            子图数据
        """
        # 获取节点
        nodes = []
        for node_id in node_ids:
            node = self.get_node_by_id(node_id)
            if node:
                nodes.append(node)

        if not include_edges:
            return {
                'nodes': nodes,
                'edges': []
            }

        # 获取节点间的边
        node_id_set = set(node_ids)
        edges = []

        for node_id in node_ids:
            node_edges = self.get_node_edges(node_id, direction='out')

            for edge in node_edges['out_edges']:
                # 只包含两端都在子图中的边
                if edge['target_node_id'] in node_id_set:
                    edges.append(edge)

        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges)
        }

    # ============================================================
    # 统计查询
    # ============================================================

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息

        Returns:
            统计数据
        """
        # 节点统计
        total_nodes = self.db.query(func.count(KnowledgeGraphNode.id)).scalar()

        node_type_counts = self.db.execute(text("""
            SELECT node_type, COUNT(*) as count
            FROM knowledge_graph_nodes
            GROUP BY node_type
        """)).fetchall()

        # 边统计
        total_edges = self.db.query(func.count(KnowledgeGraphEdge.id)).scalar()

        edge_type_counts = self.db.execute(text("""
            SELECT edge_type, COUNT(*) as count
            FROM knowledge_graph_edges
            GROUP BY edge_type
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()

        # 度数统计
        degree_stats = self.db.execute(text("""
            SELECT
                AVG(degree) as avg_degree,
                MAX(degree) as max_degree,
                MIN(degree) as min_degree
            FROM knowledge_graph_nodes
        """)).fetchone()

        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'node_types': {row[0]: row[1] for row in node_type_counts},
            'edge_types': {row[0]: row[1] for row in edge_type_counts},
            'degree_stats': {
                'avg': round(float(degree_stats[0]), 2) if degree_stats[0] else 0,
                'max': degree_stats[1] or 0,
                'min': degree_stats[2] or 0
            }
        }

    def get_top_nodes(
        self,
        by: str = 'degree',
        limit: int = 10
    ) -> List[Dict]:
        """
        获取 Top 节点

        Args:
            by: 排序依据（'degree'/'importance'/'centrality'/'pagerank'）
            limit: 返回数量

        Returns:
            Top 节点列表
        """
        order_column = {
            'degree': KnowledgeGraphNode.degree,
            'importance': KnowledgeGraphNode.importance_score,
            'centrality': KnowledgeGraphNode.centrality_score,
            'pagerank': KnowledgeGraphNode.pagerank_score
        }.get(by, KnowledgeGraphNode.degree)

        nodes = self.db.query(KnowledgeGraphNode).order_by(
            order_column.desc()
        ).limit(limit).all()

        return [self._node_to_dict(node) for node in nodes]

    # ============================================================
    # 辅助方法
    # ============================================================

    def _node_to_dict(self, node: KnowledgeGraphNode) -> Dict:
        """将节点对象转换为字典"""
        return {
            'node_id': node.node_id,
            'node_type': node.node_type,
            'label': node.label,
            'display_name': node.display_name,
            'description': node.description,
            'properties': json.loads(node.properties) if node.properties else {},
            'degree': node.degree,
            'in_degree': node.in_degree,
            'out_degree': node.out_degree,
            'importance_score': node.importance_score,
            'centrality_score': node.centrality_score,
            'pagerank_score': node.pagerank_score,
            'tags': json.loads(node.tags) if node.tags else [],
            'source_table': node.source_table,
            'source_id': node.source_id,
            'created_at': node.created_at.isoformat() if node.created_at else None
        }

    def _edge_to_dict(self, edge: KnowledgeGraphEdge) -> Dict:
        """将边对象转换为字典"""
        return {
            'edge_id': edge.edge_id,
            'source_node_id': edge.source_node_id,
            'target_node_id': edge.target_node_id,
            'edge_type': edge.edge_type,
            'edge_label': edge.edge_label,
            'properties': json.loads(edge.properties) if edge.properties else {},
            'weight': edge.weight,
            'confidence': edge.confidence,
            'is_directed': edge.is_directed,
            'source_table': edge.source_table,
            'source_id': edge.source_id,
            'created_at': edge.created_at.isoformat() if edge.created_at else None
        }


# ============================================================
# 便捷函数
# ============================================================

def query_kg(db: Session) -> KnowledgeGraphQueryService:
    """
    获取知识图谱查询服务实例

    Args:
        db: 数据库会话

    Returns:
        查询服务实例
    """
    return KnowledgeGraphQueryService(db)
