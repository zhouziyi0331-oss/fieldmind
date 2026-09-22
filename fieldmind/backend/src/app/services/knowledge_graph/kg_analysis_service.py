"""
知识图谱分析服务
Knowledge Graph Analysis Service

功能：
1. 中心性分析（度中心性、接近中心性、介数中心性）
2. 社区检测（聚类分析）
3. 重要节点识别
4. 路径分析
5. 子图发现
6. 图统计分析
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import json
from collections import defaultdict, deque
import math

from app.models.unified_models import KnowledgeGraphNode, KnowledgeGraphEdge
from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService

logger = logging.getLogger(__name__)


class KnowledgeGraphAnalysisService:
    """知识图谱分析服务"""

    def __init__(self, db: Session):
        self.db = db
        self.kg_query = KnowledgeGraphQueryService(db)

    # ============================================================
    # 中心性分析
    # ============================================================

    def calculate_centrality(
        self,
        node_ids: Optional[List[str]] = None,
        centrality_type: str = 'degree',
        limit: int = 20
    ) -> List[Dict]:
        """
        计算节点中心性

        Args:
            node_ids: 节点 ID 列表（如果为空，计算所有节点）
            centrality_type: 中心性类型（degree/closeness/betweenness）
            limit: 返回 Top N

        Returns:
            中心性排名列表
        """
        if centrality_type == 'degree':
            return self._calculate_degree_centrality(node_ids, limit)
        elif centrality_type == 'closeness':
            return self._calculate_closeness_centrality(node_ids, limit)
        elif centrality_type == 'betweenness':
            return self._calculate_betweenness_centrality(node_ids, limit)
        else:
            return []

    def _calculate_degree_centrality(
        self,
        node_ids: Optional[List[str]],
        limit: int
    ) -> List[Dict]:
        """
        度中心性（已存储在数据库中）

        度中心性 = 节点的度数 / (总节点数 - 1)
        """
        query = self.db.query(KnowledgeGraphNode)

        if node_ids:
            query = query.filter(KnowledgeGraphNode.node_id.in_(node_ids))

        nodes = query.order_by(
            KnowledgeGraphNode.degree.desc()
        ).limit(limit).all()

        total_nodes = self.db.query(func.count(KnowledgeGraphNode.id)).scalar()

        results = []
        for node in nodes:
            # 归一化度中心性
            normalized_degree = node.degree / (total_nodes - 1) if total_nodes > 1 else 0

            results.append({
                'node_id': node.node_id,
                'label': node.label,
                'type': node.node_type,
                'degree': node.degree,
                'in_degree': node.in_degree,
                'out_degree': node.out_degree,
                'degree_centrality': round(normalized_degree, 4)
            })

        return results

    def _calculate_closeness_centrality(
        self,
        node_ids: Optional[List[str]],
        limit: int
    ) -> List[Dict]:
        """
        接近中心性（简化版本）

        接近中心性 = (n-1) / Σ(d(v,u))
        其中 d(v,u) 是节点 v 到节点 u 的最短路径长度
        """
        # 简化实现：使用 BFS 计算到其他节点的平均距离
        if not node_ids:
            # 获取重要节点
            top_nodes = self.kg_query.get_top_nodes(by='degree', limit=50)
            node_ids = [n['node_id'] for n in top_nodes]

        results = []
        for node_id in node_ids[:limit]:
            avg_distance = self._calculate_average_distance(node_id)

            if avg_distance > 0:
                closeness = 1.0 / avg_distance
            else:
                closeness = 0

            node = self.kg_query.get_node_by_id(node_id)
            if node:
                results.append({
                    'node_id': node_id,
                    'label': node['label'],
                    'type': node['node_type'],
                    'closeness_centrality': round(closeness, 4),
                    'avg_distance': round(avg_distance, 2)
                })

        # 按接近中心性排序
        results.sort(key=lambda x: x['closeness_centrality'], reverse=True)

        return results[:limit]

    def _calculate_average_distance(self, node_id: str, max_depth: int = 5) -> float:
        """计算到其他节点的平均距离（BFS）"""
        visited = {node_id: 0}
        queue = deque([(node_id, 0)])
        total_distance = 0
        node_count = 0

        while queue and len(visited) < 100:  # 限制搜索范围
            current_id, distance = queue.popleft()

            if distance >= max_depth:
                continue

            neighbors_data = self.kg_query.get_neighbors(current_id, depth=1)

            for edge in neighbors_data['edges']:
                next_id = (
                    edge['target_node_id']
                    if edge['source_node_id'] == current_id
                    else edge['source_node_id']
                )

                if next_id not in visited:
                    visited[next_id] = distance + 1
                    queue.append((next_id, distance + 1))
                    total_distance += distance + 1
                    node_count += 1

        return total_distance / node_count if node_count > 0 else 0

    def _calculate_betweenness_centrality(
        self,
        node_ids: Optional[List[str]],
        limit: int
    ) -> List[Dict]:
        """
        介数中心性（简化版本）

        介数中心性 = 经过该节点的最短路径数 / 所有最短路径数
        """
        # 简化实现：计算作为桥梁的程度
        # 这里使用节点的邻居数量和连接强度作为近似
        logger.warning("介数中心性计算是简化版本")

        results = []
        if not node_ids:
            top_nodes = self.kg_query.get_top_nodes(by='degree', limit=limit)
            node_ids = [n['node_id'] for n in top_nodes]

        for node_id in node_ids[:limit]:
            node = self.kg_query.get_node_by_id(node_id)
            if not node:
                continue

            # 获取邻居
            neighbors = self.kg_query.get_neighbors(node_id, depth=1)

            # 简化计算：度数 * 连接多样性
            betweenness = node['degree'] * len(neighbors['neighbors']) / 100.0

            results.append({
                'node_id': node_id,
                'label': node['label'],
                'type': node['node_type'],
                'betweenness_centrality': round(betweenness, 4)
            })

        results.sort(key=lambda x: x['betweenness_centrality'], reverse=True)

        return results[:limit]

    # ============================================================
    # 社区检测
    # ============================================================

    def detect_communities(
        self,
        algorithm: str = 'simple',
        min_community_size: int = 3
    ) -> Dict[str, Any]:
        """
        社区检测（聚类分析）

        Args:
            algorithm: 算法类型（simple/modularity）
            min_community_size: 最小社区大小

        Returns:
            社区列表
        """
        if algorithm == 'simple':
            return self._simple_community_detection(min_community_size)
        else:
            return {'error': f'Unknown algorithm: {algorithm}'}

    def _simple_community_detection(self, min_size: int) -> Dict[str, Any]:
        """
        简单社区检测（基于连通性）

        使用 DFS 查找连通分量
        """
        # 获取所有节点
        all_nodes = self.db.query(KnowledgeGraphNode).all()
        node_ids = {node.node_id for node in all_nodes}

        visited = set()
        communities = []

        for node_id in node_ids:
            if node_id in visited:
                continue

            # DFS 查找连通分量
            community = self._find_connected_component(node_id, node_ids, visited)

            if len(community) >= min_size:
                # 获取社区节点信息
                community_nodes = []
                for nid in community:
                    node = self.kg_query.get_node_by_id(nid)
                    if node:
                        community_nodes.append({
                            'node_id': nid,
                            'label': node['label'],
                            'type': node['node_type']
                        })

                communities.append({
                    'community_id': len(communities) + 1,
                    'size': len(community),
                    'nodes': community_nodes
                })

        return {
            'total_communities': len(communities),
            'communities': communities,
            'algorithm': 'simple'
        }

    def _find_connected_component(
        self,
        start_id: str,
        all_node_ids: Set[str],
        visited: Set[str]
    ) -> Set[str]:
        """DFS 查找连通分量"""
        component = set()
        stack = [start_id]

        while stack:
            node_id = stack.pop()

            if node_id in visited:
                continue

            visited.add(node_id)
            component.add(node_id)

            # 获取邻居
            neighbors_data = self.kg_query.get_neighbors(node_id, depth=1)

            for neighbor in neighbors_data['neighbors']:
                neighbor_id = neighbor['node_id']
                if neighbor_id in all_node_ids and neighbor_id not in visited:
                    stack.append(neighbor_id)

        return component

    # ============================================================
    # 重要节点识别
    # ============================================================

    def identify_key_nodes(
        self,
        metrics: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        识别关键节点（综合多个指标）

        Args:
            metrics: 指标列表（degree/importance/centrality/pagerank）
            limit: 返回数量

        Returns:
            关键节点列表
        """
        if not metrics:
            metrics = ['degree', 'importance']

        # 计算每个指标的 Top 节点
        metric_results = {}
        for metric in metrics:
            metric_results[metric] = self.kg_query.get_top_nodes(by=metric, limit=limit)

        # 综合评分
        node_scores = defaultdict(float)
        node_data = {}

        for metric, nodes in metric_results.items():
            weight = 1.0 / len(metrics)  # 均等权重

            for i, node in enumerate(nodes):
                node_id = node['node_id']
                score = (limit - i) * weight  # 排名越高，得分越高
                node_scores[node_id] += score
                node_data[node_id] = node

        # 排序
        sorted_nodes = sorted(
            node_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        key_nodes = []
        for node_id, score in sorted_nodes:
            node = node_data.get(node_id)
            if node:
                node['composite_score'] = round(score, 2)
                key_nodes.append(node)

        return {
            'key_nodes': key_nodes,
            'metrics_used': metrics,
            'total_nodes': len(key_nodes)
        }

    # ============================================================
    # 路径分析
    # ============================================================

    def analyze_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_paths: int = 5
    ) -> Dict[str, Any]:
        """
        路径分析（查找多条路径）

        Args:
            start_node_id: 起始节点
            end_node_id: 目标节点
            max_paths: 最大路径数

        Returns:
            路径分析结果
        """
        # 查找最短路径
        shortest_path = self.kg_query.find_shortest_path(start_node_id, end_node_id)

        return {
            'start_node': self.kg_query.get_node_by_id(start_node_id),
            'end_node': self.kg_query.get_node_by_id(end_node_id),
            'shortest_path': shortest_path,
            'path_exists': shortest_path.get('found', False)
        }

    # ============================================================
    # 子图发现
    # ============================================================

    def discover_subgraphs(
        self,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        子图发现（基于特定条件）

        Args:
            criteria: 条件（如 node_type, min_degree）

        Returns:
            子图列表
        """
        # 查找满足条件的节点
        query = self.db.query(KnowledgeGraphNode)

        if 'node_type' in criteria:
            query = query.filter(KnowledgeGraphNode.node_type == criteria['node_type'])

        if 'min_degree' in criteria:
            query = query.filter(KnowledgeGraphNode.degree >= criteria['min_degree'])

        nodes = query.all()
        node_ids = [n.node_id for n in nodes]

        # 提取子图
        subgraph = self.kg_query.get_subgraph(node_ids, include_edges=True)

        return {
            'criteria': criteria,
            'subgraph': subgraph
        }

    # ============================================================
    # 图统计分析
    # ============================================================

    def analyze_graph_structure(self) -> Dict[str, Any]:
        """
        图结构分析

        Returns:
            图结构统计
        """
        # 基本统计
        stats = self.kg_query.get_graph_statistics()

        # 度分布
        degree_distribution = self._calculate_degree_distribution()

        # 连通性分析
        connectivity = self._analyze_connectivity()

        return {
            'basic_statistics': stats,
            'degree_distribution': degree_distribution,
            'connectivity': connectivity
        }

    def _calculate_degree_distribution(self) -> Dict[str, Any]:
        """计算度分布"""
        result = self.db.execute(text("""
            SELECT degree, COUNT(*) as count
            FROM knowledge_graph_nodes
            GROUP BY degree
            ORDER BY degree
        """)).fetchall()

        distribution = [{'degree': row[0], 'count': row[1]} for row in result]

        return {
            'distribution': distribution,
            'total_nodes': sum(d['count'] for d in distribution)
        }

    def _analyze_connectivity(self) -> Dict[str, Any]:
        """分析连通性"""
        total_nodes = self.db.query(func.count(KnowledgeGraphNode.id)).scalar()
        total_edges = self.db.query(func.count(KnowledgeGraphEdge.id)).scalar()

        # 简单连通性指标
        if total_nodes > 0:
            density = (2 * total_edges) / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        else:
            density = 0

        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'density': round(density, 4),
            'avg_degree': round(2 * total_edges / total_nodes, 2) if total_nodes > 0 else 0
        }


# ============================================================
# 便捷函数
# ============================================================

def kg_analysis(db: Session) -> KnowledgeGraphAnalysisService:
    """
    获取知识图谱分析服务实例

    Args:
        db: 数据库会话

    Returns:
        分析服务实例
    """
    return KnowledgeGraphAnalysisService(db)
