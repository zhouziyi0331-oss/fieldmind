"""
关键词网络构建服务
基于 KeywordRelationBuilder，增加主关键词识别、社区检测、网络可视化
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from collections import defaultdict
import json

from app.models.keyword import Keyword, KeywordRelation
from app.services.keyword_relation_builder import KeywordRelationBuilder

logger = logging.getLogger(__name__)


class KeywordNetworkBuilder:
    """关键词网络构建器"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.relation_builder = KeywordRelationBuilder(db)

    def build_keyword_network(
        self,
        project_id: int,
        min_strength: float = 0.1,
        include_communities: bool = True
    ) -> Dict[str, Any]:
        """
        构建关键词网络

        Args:
            project_id: 项目ID
            min_strength: 最小关系强度阈值
            include_communities: 是否进行社区检测

        Returns:
            网络数据 {nodes, edges, communities, statistics}
        """
        logger.info(f"开始构建关键词网络: project_id={project_id}")

        # 获取所有关键词
        keywords = self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).all()

        if not keywords:
            logger.warning(f"项目 {project_id} 没有关键词")
            return {"nodes": [], "edges": [], "communities": [], "statistics": {}}

        # 获取所有关系
        relations = self.db.query(KeywordRelation).filter(
            and_(
                KeywordRelation.project_id == project_id,
                KeywordRelation.strength >= min_strength
            )
        ).all()

        logger.info(f"找到 {len(keywords)} 个关键词，{len(relations)} 条关系")

        # 构建图数据结构
        import networkx as nx
        G = nx.Graph()

        # 添加节点
        for kw in keywords:
            G.add_node(kw.id,
                      text=kw.text,
                      category=kw.category,
                      frequency=kw.frequency,
                      weight=kw.weight,
                      importance=kw.importance)

        # 添加边
        for rel in relations:
            G.add_edge(rel.keyword1_id, rel.keyword2_id,
                      strength=rel.strength,
                      co_occurrence=rel.co_occurrence,
                      correlation=rel.correlation)

        # 计算中心性指标
        centrality_metrics = self._calculate_centrality(G)

        # 识别主关键词（使用 PageRank）
        main_keywords = self._identify_main_keywords(G, centrality_metrics, top_n=20)

        # 社区检测
        communities = []
        if include_communities:
            communities = self._detect_communities(G)

        # 构建节点数据
        nodes = self._build_nodes_data(keywords, centrality_metrics, main_keywords, communities)

        # 构建边数据
        edges = self._build_edges_data(relations)

        # 统计信息
        statistics = {
            "total_keywords": len(keywords),
            "total_relations": len(relations),
            "network_density": nx.density(G) if len(G.nodes) > 1 else 0,
            "connected_components": nx.number_connected_components(G),
            "average_degree": sum(dict(G.degree()).values()) / len(G.nodes) if len(G.nodes) > 0 else 0,
            "main_keywords_count": len(main_keywords),
            "communities_count": len(communities)
        }

        logger.info(f"关键词网络构建完成: {statistics}")

        return {
            "nodes": nodes,
            "edges": edges,
            "communities": communities,
            "statistics": statistics
        }

    def _calculate_centrality(self, G) -> Dict[str, Dict[int, float]]:
        """
        计算多种中心性指标

        Returns:
            {
                'degree': {node_id: score},
                'betweenness': {node_id: score},
                'closeness': {node_id: score},
                'pagerank': {node_id: score}
            }
        """
        import networkx as nx

        logger.info("计算中心性指标...")

        centrality = {}

        # 度中心性
        centrality['degree'] = nx.degree_centrality(G)

        # 介数中心性（关键桥接节点）
        if len(G.nodes) > 2:
            centrality['betweenness'] = nx.betweenness_centrality(G)
        else:
            centrality['betweenness'] = {node: 0.0 for node in G.nodes}

        # 接近中心性
        if nx.is_connected(G):
            centrality['closeness'] = nx.closeness_centrality(G)
        else:
            # 对非连通图，计算每个连通分量的接近中心性
            closeness = {}
            for component in nx.connected_components(G):
                subgraph = G.subgraph(component)
                component_closeness = nx.closeness_centrality(subgraph)
                closeness.update(component_closeness)
            centrality['closeness'] = closeness

        # PageRank（主关键词识别的核心指标）
        centrality['pagerank'] = nx.pagerank(G, weight='strength')

        logger.info("中心性指标计算完成")

        return centrality

    def _identify_main_keywords(
        self,
        G,
        centrality_metrics: Dict[str, Dict[int, float]],
        top_n: int = 20
    ) -> List[int]:
        """
        识别主关键词

        策略：综合 PageRank、度中心性、频率

        Returns:
            主关键词的 keyword_id 列表
        """
        logger.info(f"识别前 {top_n} 个主关键词...")

        pagerank = centrality_metrics['pagerank']
        degree = centrality_metrics['degree']

        # 综合评分 = 0.5 * pagerank + 0.3 * degree + 0.2 * normalized_frequency
        scores = {}

        # 获取所有节点的频率
        frequencies = {node: G.nodes[node].get('frequency', 1) for node in G.nodes}
        max_freq = max(frequencies.values()) if frequencies else 1

        for node in G.nodes:
            normalized_freq = frequencies[node] / max_freq

            score = (
                0.5 * pagerank.get(node, 0) +
                0.3 * degree.get(node, 0) +
                0.2 * normalized_freq
            )
            scores[node] = score

        # 排序并取前 N 个
        sorted_keywords = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        main_keywords = [kw_id for kw_id, score in sorted_keywords[:top_n]]

        logger.info(f"识别出 {len(main_keywords)} 个主关键词")

        return main_keywords

    def _detect_communities(self, G) -> List[Dict[str, Any]]:
        """
        社区检测（使用 Louvain 算法）

        Returns:
            [
                {
                    "id": 0,
                    "keywords": [kw_id1, kw_id2, ...],
                    "size": 10,
                    "main_keyword": kw_id,  # 社区中心
                    "label": "社区标签"
                }
            ]
        """
        logger.info("开始社区检测...")

        try:
            import community.community_louvain as community_louvain
        except ImportError:
            logger.warning("python-louvain 未安装，跳过社区检测。安装: pip install python-louvain")
            return []

        # Louvain 算法
        partition = community_louvain.best_partition(G, weight='strength')

        # 组织社区数据
        communities_dict = defaultdict(list)
        for node, comm_id in partition.items():
            communities_dict[comm_id].append(node)

        communities = []
        for comm_id, keyword_ids in communities_dict.items():
            # 找到社区中心（度最高的节点）
            subgraph = G.subgraph(keyword_ids)
            degrees = dict(subgraph.degree())
            center_node = max(degrees, key=degrees.get) if degrees else keyword_ids[0]

            # 获取中心关键词文本作为标签
            center_kw = self.db.query(Keyword).filter(Keyword.id == center_node).first()
            label = center_kw.text if center_kw else f"社区 {comm_id}"

            communities.append({
                "id": comm_id,
                "keywords": keyword_ids,
                "size": len(keyword_ids),
                "main_keyword": center_node,
                "label": label
            })

        logger.info(f"检测到 {len(communities)} 个社区")

        return communities

    def _build_nodes_data(
        self,
        keywords: List[Keyword],
        centrality_metrics: Dict[str, Dict[int, float]],
        main_keywords: List[int],
        communities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """构建节点数据（用于前端可视化）"""

        # 构建社区映射
        keyword_to_community = {}
        for comm in communities:
            for kw_id in comm['keywords']:
                keyword_to_community[kw_id] = comm['id']

        nodes = []
        for kw in keywords:
            node = {
                "id": kw.id,
                "text": kw.text,
                "category": kw.category,
                "frequency": kw.frequency,
                "weight": kw.weight,
                "importance": kw.importance,

                # 中心性指标
                "degree_centrality": round(centrality_metrics['degree'].get(kw.id, 0), 4),
                "betweenness_centrality": round(centrality_metrics['betweenness'].get(kw.id, 0), 4),
                "closeness_centrality": round(centrality_metrics['closeness'].get(kw.id, 0), 4),
                "pagerank": round(centrality_metrics['pagerank'].get(kw.id, 0), 4),

                # 主关键词标识
                "is_main_keyword": kw.id in main_keywords,

                # 社区归属
                "community_id": keyword_to_community.get(kw.id)
            }
            nodes.append(node)

        return nodes

    def _build_edges_data(self, relations: List[KeywordRelation]) -> List[Dict[str, Any]]:
        """构建边数据（用于前端可视化）"""

        edges = []
        for rel in relations:
            edge = {
                "source": rel.keyword1_id,
                "target": rel.keyword2_id,
                "strength": rel.strength,
                "co_occurrence": rel.co_occurrence,
                "correlation": rel.correlation,
                "relation_type": rel.relation_type
            }
            edges.append(edge)

        return edges

    def get_keyword_neighborhood(
        self,
        keyword_id: int,
        project_id: int,
        depth: int = 1,
        min_strength: float = 0.1
    ) -> Dict[str, Any]:
        """
        获取关键词的邻域网络

        Args:
            keyword_id: 关键词ID
            project_id: 项目ID
            depth: 邻域深度（1=直接邻居，2=二度邻居）
            min_strength: 最小关系强度

        Returns:
            局部网络数据
        """
        logger.info(f"获取关键词 {keyword_id} 的 {depth} 度邻域网络")

        # 获取中心关键词
        center_kw = self.db.query(Keyword).filter(
            and_(Keyword.id == keyword_id, Keyword.project_id == project_id)
        ).first()

        if not center_kw:
            return {"nodes": [], "edges": []}

        # 递归获取邻居
        visited_keywords = set()
        visited_relations = set()

        self._expand_neighborhood(
            keyword_id, project_id, depth, min_strength,
            visited_keywords, visited_relations
        )

        # 获取节点和边数据
        keywords = self.db.query(Keyword).filter(
            Keyword.id.in_(visited_keywords)
        ).all()

        relations = self.db.query(KeywordRelation).filter(
            and_(
                KeywordRelation.id.in_(visited_relations),
                KeywordRelation.strength >= min_strength
            )
        ).all()

        # 构建简化的网络
        import networkx as nx
        G = nx.Graph()

        for kw in keywords:
            G.add_node(kw.id, text=kw.text, frequency=kw.frequency)

        for rel in relations:
            G.add_edge(rel.keyword1_id, rel.keyword2_id, strength=rel.strength)

        # 计算局部中心性
        centrality_metrics = self._calculate_centrality(G)

        # 构建数据
        nodes = []
        for kw in keywords:
            nodes.append({
                "id": kw.id,
                "text": kw.text,
                "category": kw.category,
                "frequency": kw.frequency,
                "pagerank": round(centrality_metrics['pagerank'].get(kw.id, 0), 4),
                "is_center": kw.id == keyword_id
            })

        edges = self._build_edges_data(relations)

        return {
            "center_keyword": center_kw.text,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "depth": depth
            }
        }

    def _expand_neighborhood(
        self,
        keyword_id: int,
        project_id: int,
        depth: int,
        min_strength: float,
        visited_keywords: set,
        visited_relations: set,
        current_depth: int = 0
    ):
        """递归扩展邻域"""

        if current_depth >= depth:
            return

        visited_keywords.add(keyword_id)

        # 获取直接邻居
        relations = self.db.query(KeywordRelation).filter(
            and_(
                KeywordRelation.project_id == project_id,
                KeywordRelation.strength >= min_strength,
                or_(
                    KeywordRelation.keyword1_id == keyword_id,
                    KeywordRelation.keyword2_id == keyword_id
                )
            )
        ).all()

        for rel in relations:
            visited_relations.add(rel.id)

            # 找到邻居节点
            neighbor_id = rel.keyword2_id if rel.keyword1_id == keyword_id else rel.keyword1_id

            if neighbor_id not in visited_keywords:
                self._expand_neighborhood(
                    neighbor_id, project_id, depth, min_strength,
                    visited_keywords, visited_relations, current_depth + 1
                )

    def get_main_keywords(
        self,
        project_id: int,
        top_n: int = 20,
        method: str = "comprehensive"
    ) -> List[Dict[str, Any]]:
        """
        获取主关键词列表

        Args:
            project_id: 项目ID
            top_n: 返回数量
            method: 排序方法
                - "comprehensive": 综合评分（PageRank + 度中心性 + 频率）
                - "pagerank": 仅 PageRank
                - "frequency": 仅频率
                - "degree": 仅度中心性

        Returns:
            主关键词列表
        """
        logger.info(f"获取主关键词: method={method}, top_n={top_n}")

        # 构建网络
        network = self.build_keyword_network(project_id, min_strength=0.1, include_communities=False)

        nodes = network['nodes']

        # 根据方法排序
        if method == "pagerank":
            nodes.sort(key=lambda x: x['pagerank'], reverse=True)
        elif method == "frequency":
            nodes.sort(key=lambda x: x['frequency'], reverse=True)
        elif method == "degree":
            nodes.sort(key=lambda x: x['degree_centrality'], reverse=True)
        else:  # comprehensive
            # 综合评分
            for node in nodes:
                node['comprehensive_score'] = (
                    0.5 * node['pagerank'] +
                    0.3 * node['degree_centrality'] +
                    0.2 * (node['frequency'] / max(n['frequency'] for n in nodes))
                )
            nodes.sort(key=lambda x: x['comprehensive_score'], reverse=True)

        return nodes[:top_n]
