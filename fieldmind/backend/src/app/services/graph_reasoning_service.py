"""
图谱推理服务 (Graph Reasoning Service)

功能：
1. 关系传递推理 (A→B→C，推导A→C)
2. 多跳路径发现 (找到两个节点之间的所有路径)
3. 社区发现 (使用NetworkX发现紧密关联的节点群)
4. 中心性分析 (识别图谱中最重要的节点)
5. 关系强度计算 (基于共现频率和上下文相似度)

设计原则：
- 使用NetworkX进行快速图算法计算
- 支持跨项目统一大图推理
- 所有结果都是中文标注
- 思路清晰，逻辑严谨
"""

import networkx as nx
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import numpy as np
from app.core.logging import logger

from app.models.knowledge_graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    ReasoningResult,
    PathDiscoveryResult,
    CommunityDetectionResult,
    CentralityAnalysisResult
)


class GraphReasoningService:
    """
    图谱推理服务

    核心功能：
    1. 关系传递推理
    2. 多跳路径发现
    3. 社区发现
    4. 中心性分析
    """

    def __init__(self):
        """初始化推理服务"""
        self.graph: nx.DiGraph = nx.DiGraph()

        # 可传递的关系类型（这些关系支持A→B→C推导A→C）
        self.transitive_relations = {
            EdgeType.FAMILY_KINSHIP,          # 家族关系可传递
            EdgeType.ORGANIZATIONAL_SUCCESSION,  # 组织继任可传递
            EdgeType.CULTURAL_INHERITANCE,    # 文化传承可传递
            EdgeType.SKILL_TRANSMISSION,      # 技艺传授可传递
            EdgeType.MENTOR_STUDENT,          # 师徒关系可传递
        }

        # 对称关系类型（A→B等价于B→A）
        self.symmetric_relations = {
            EdgeType.FAMILY_KINSHIP,          # 亲属关系是对称的
            EdgeType.CO_ORGANIZED,            # 共同组织是对称的
            EdgeType.COLLABORATION,           # 合作关系是对称的
        }

        logger.info("图谱推理服务初始化完成")


    def load_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> None:
        """
        加载图谱数据到NetworkX

        Args:
            nodes: 节点列表
            edges: 边列表
        """
        self.graph.clear()

        # 添加节点
        for node in nodes:
            self.graph.add_node(
                node.id,
                name=node.name,
                type=node.type.value,
                importance_score=node.importance_score,
                is_core_keyword=node.is_core_keyword,
                layer=node.layer,
                actions=node.actions,
                context_vector=node.context_vector,
                source_projects=node.source_projects,
            )

        # 添加边
        for edge in edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                type=edge.type.value,
                weight=edge.weight,
                confidence=edge.confidence,
                evidence=edge.evidence,
                temporal_info=edge.temporal_info,
            )

        logger.info(f"图谱加载完成: {len(nodes)}个节点, {len(edges)}条边")


    def transitive_reasoning(
        self,
        max_hops: int = 3,
        min_confidence: float = 0.6
    ) -> List[GraphEdge]:
        """
        关系传递推理

        规则：如果 A→B 和 B→C 都存在，且关系类型可传递，则推导 A→C

        Args:
            max_hops: 最大传递跳数（默认3跳）
            min_confidence: 最小置信度阈值（默认0.6）

        Returns:
            推导出的新边列表
        """
        inferred_edges = []

        # 遍历所有可传递的关系类型
        for relation_type in self.transitive_relations:
            relation_str = relation_type.value

            # 找到所有该类型的边
            edges_of_type = [
                (u, v, data)
                for u, v, data in self.graph.edges(data=True)
                if data.get('type') == relation_str
            ]

            if not edges_of_type:
                continue

            # 构建该关系类型的子图
            subgraph = nx.DiGraph()
            for u, v, data in edges_of_type:
                subgraph.add_edge(u, v, **data)

            # 对每个节点对，尝试找路径
            nodes = list(subgraph.nodes())
            for i, source_node in enumerate(nodes):
                for target_node in nodes[i+1:]:
                    # 检查是否已经有直接边
                    if self.graph.has_edge(source_node, target_node):
                        continue

                    # 查找路径
                    try:
                        paths = list(nx.all_simple_paths(
                            subgraph,
                            source_node,
                            target_node,
                            cutoff=max_hops
                        ))

                        if not paths:
                            continue

                        # 选择最短路径
                        shortest_path = min(paths, key=len)
                        path_length = len(shortest_path) - 1

                        # 计算推理置信度（路径越短，置信度越高）
                        confidence = 1.0 / path_length

                        # 收集路径上的所有置信度
                        path_confidences = []
                        for j in range(len(shortest_path) - 1):
                            edge_data = subgraph.get_edge_data(
                                shortest_path[j],
                                shortest_path[j+1]
                            )
                            path_confidences.append(edge_data.get('confidence', 1.0))

                        # 综合置信度 = 几何平均
                        if path_confidences:
                            confidence *= np.prod(path_confidences) ** (1.0 / len(path_confidences))

                        if confidence < min_confidence:
                            continue

                        # 创建推导边
                        source_name = self.graph.nodes[source_node]['name']
                        target_name = self.graph.nodes[target_node]['name']

                        inferred_edge = GraphEdge(
                            source=source_node,
                            target=target_node,
                            type=relation_type,
                            weight=confidence,
                            confidence=confidence,
                            evidence=[f"推理路径: {' → '.join([self.graph.nodes[n]['name'] for n in shortest_path])}"],
                            is_inferred=True,
                            inference_method="传递推理",
                            inference_path=shortest_path,
                        )

                        inferred_edges.append(inferred_edge)

                        logger.debug(
                            f"推导新关系: {source_name} → {target_name} "
                            f"({relation_str}, 置信度={confidence:.3f})"
                        )

                    except nx.NetworkXNoPath:
                        continue

        logger.info(f"传递推理完成: 推导出{len(inferred_edges)}条新边")
        return inferred_edges


    def find_paths(
        self,
        source_node_id: str,
        target_node_id: str,
        max_depth: int = 5,
        max_paths: int = 10
    ) -> PathDiscoveryResult:
        """
        多跳路径发现

        找到两个节点之间的所有路径（支持前端树状展开）

        Args:
            source_node_id: 起始节点ID
            target_node_id: 目标节点ID
            max_depth: 最大路径深度
            max_paths: 最多返回多少条路径

        Returns:
            路径发现结果
        """
        if source_node_id not in self.graph:
            raise ValueError(f"起始节点不存在: {source_node_id}")

        if target_node_id not in self.graph:
            raise ValueError(f"目标节点不存在: {target_node_id}")

        try:
            # 查找所有简单路径
            all_paths = list(nx.all_simple_paths(
                self.graph,
                source_node_id,
                target_node_id,
                cutoff=max_depth
            ))

            # 限制返回数量
            all_paths = all_paths[:max_paths]

            # 构建详细路径信息
            detailed_paths = []
            for path in all_paths:
                path_info = {
                    "node_ids": path,
                    "node_names": [self.graph.nodes[n]['name'] for n in path],
                    "length": len(path) - 1,
                    "edges": []
                }

                # 收集路径上的边信息
                for i in range(len(path) - 1):
                    edge_data = self.graph.get_edge_data(path[i], path[i+1])
                    path_info["edges"].append({
                        "source": path[i],
                        "target": path[i+1],
                        "type": edge_data.get('type', '未知关系'),
                        "weight": edge_data.get('weight', 0.0),
                    })

                detailed_paths.append(path_info)

            # 按路径长度排序（最短路径优先）
            detailed_paths.sort(key=lambda x: x['length'])

            source_name = self.graph.nodes[source_node_id]['name']
            target_name = self.graph.nodes[target_node_id]['name']

            result = PathDiscoveryResult(
                source_node=source_node_id,
                target_node=target_node_id,
                source_name=source_name,
                target_name=target_name,
                paths=detailed_paths,
                total_paths=len(detailed_paths),
                shortest_distance=detailed_paths[0]['length'] if detailed_paths else float('inf')
            )

            logger.info(
                f"路径发现: {source_name} → {target_name}, "
                f"找到{len(detailed_paths)}条路径, 最短距离={result.shortest_distance}"
            )

            return result

        except nx.NetworkXNoPath:
            logger.warning(f"无路径: {source_node_id} → {target_node_id}")
            return PathDiscoveryResult(
                source_node=source_node_id,
                target_node=target_node_id,
                source_name=self.graph.nodes[source_node_id]['name'],
                target_name=self.graph.nodes[target_node_id]['name'],
                paths=[],
                total_paths=0,
                shortest_distance=float('inf')
            )


    def detect_communities(
        self,
        algorithm: str = "louvain",
        min_community_size: int = 3
    ) -> CommunityDetectionResult:
        """
        社区发现（识别紧密关联的节点群）

        应用场景：
        - 识别家族群体
        - 识别组织派系
        - 识别民俗传承圈

        Args:
            algorithm: 算法选择 ("louvain", "label_propagation", "greedy_modularity")
            min_community_size: 最小社区规模

        Returns:
            社区检测结果
        """
        # 转换为无向图（社区检测通常在无向图上进行）
        undirected_graph = self.graph.to_undirected()

        # 选择算法
        if algorithm == "louvain":
            # Louvain算法（需要python-louvain包）
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(undirected_graph)
            except ImportError:
                logger.warning("python-louvain未安装，回退到label_propagation")
                algorithm = "label_propagation"

        if algorithm == "label_propagation":
            # 标签传播算法
            communities_generator = nx.community.label_propagation_communities(undirected_graph)
            communities = list(communities_generator)
            partition = {}
            for idx, comm in enumerate(communities):
                for node in comm:
                    partition[node] = idx

        elif algorithm == "greedy_modularity":
            # 贪心模块度优化算法
            communities_generator = nx.community.greedy_modularity_communities(undirected_graph)
            communities = list(communities_generator)
            partition = {}
            for idx, comm in enumerate(communities):
                for node in comm:
                    partition[node] = idx

        # 整理社区结果
        communities_dict = defaultdict(list)
        for node_id, community_id in partition.items():
            communities_dict[community_id].append(node_id)

        # 过滤小社区
        filtered_communities = {
            cid: nodes
            for cid, nodes in communities_dict.items()
            if len(nodes) >= min_community_size
        }

        # 构建详细社区信息
        detailed_communities = []
        for community_id, node_ids in filtered_communities.items():
            # 收集节点信息
            nodes_info = []
            for node_id in node_ids:
                nodes_info.append({
                    "id": node_id,
                    "name": self.graph.nodes[node_id]['name'],
                    "type": self.graph.nodes[node_id]['type'],
                    "importance": self.graph.nodes[node_id].get('importance_score', 0.0),
                })

            # 计算社区内部边数
            internal_edges = 0
            for i, node1 in enumerate(node_ids):
                for node2 in node_ids[i+1:]:
                    if undirected_graph.has_edge(node1, node2):
                        internal_edges += 1

            # 社区密度 = 实际边数 / 最大可能边数
            max_edges = len(node_ids) * (len(node_ids) - 1) / 2
            density = internal_edges / max_edges if max_edges > 0 else 0.0

            # 识别社区核心节点（degree最高）
            core_node_id = max(node_ids, key=lambda n: undirected_graph.degree(n))
            core_node_name = self.graph.nodes[core_node_id]['name']

            detailed_communities.append({
                "community_id": community_id,
                "size": len(node_ids),
                "nodes": nodes_info,
                "internal_edges": internal_edges,
                "density": density,
                "core_node_id": core_node_id,
                "core_node_name": core_node_name,
                "label": f"{core_node_name}社区",  # 用核心节点命名社区
            })

        # 按社区规模排序
        detailed_communities.sort(key=lambda x: x['size'], reverse=True)

        result = CommunityDetectionResult(
            algorithm=algorithm,
            total_communities=len(detailed_communities),
            communities=detailed_communities,
        )

        logger.info(
            f"社区发现完成: 使用{algorithm}算法, "
            f"发现{len(detailed_communities)}个社区"
        )

        return result


    def analyze_centrality(
        self,
        top_k: int = 20
    ) -> CentralityAnalysisResult:
        """
        中心性分析（识别图谱中最重要的节点）

        计算4种中心性指标：
        1. 度中心性 (Degree Centrality) - 直接连接数
        2. 接近中心性 (Closeness Centrality) - 到其他节点的平均距离
        3. 介数中心性 (Betweenness Centrality) - 作为桥梁的频率
        4. PageRank - 基于图结构的重要性

        Args:
            top_k: 返回Top K最重要的节点

        Returns:
            中心性分析结果
        """
        # 1. 度中心性
        degree_centrality = nx.degree_centrality(self.graph)

        # 2. 接近中心性（需要强连通图）
        try:
            if nx.is_strongly_connected(self.graph):
                closeness_centrality = nx.closeness_centrality(self.graph)
            else:
                # 如果不是强连通，对每个强连通分量分别计算
                closeness_centrality = {}
                for component in nx.strongly_connected_components(self.graph):
                    subgraph = self.graph.subgraph(component)
                    closeness = nx.closeness_centrality(subgraph)
                    closeness_centrality.update(closeness)
        except:
            logger.warning("接近中心性计算失败，使用度中心性代替")
            closeness_centrality = degree_centrality

        # 3. 介数中心性
        betweenness_centrality = nx.betweenness_centrality(self.graph)

        # 4. PageRank
        pagerank = nx.pagerank(self.graph, alpha=0.85)

        # 综合评分（加权平均）
        combined_scores = {}
        for node_id in self.graph.nodes():
            combined_scores[node_id] = (
                0.25 * degree_centrality.get(node_id, 0.0) +
                0.20 * closeness_centrality.get(node_id, 0.0) +
                0.20 * betweenness_centrality.get(node_id, 0.0) +
                0.35 * pagerank.get(node_id, 0.0)
            )

        # 排序并取Top K
        top_nodes = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # 构建详细结果
        detailed_results = []
        for node_id, combined_score in top_nodes:
            node_data = self.graph.nodes[node_id]
            detailed_results.append({
                "node_id": node_id,
                "name": node_data['name'],
                "type": node_data['type'],
                "combined_score": combined_score,
                "degree_centrality": degree_centrality.get(node_id, 0.0),
                "closeness_centrality": closeness_centrality.get(node_id, 0.0),
                "betweenness_centrality": betweenness_centrality.get(node_id, 0.0),
                "pagerank": pagerank.get(node_id, 0.0),
                "degree": self.graph.degree(node_id),
            })

        result = CentralityAnalysisResult(
            top_k=top_k,
            nodes=detailed_results,
        )

        logger.info(f"中心性分析完成: Top {top_k}节点已识别")

        return result


    def calculate_relationship_strength(
        self,
        node1_id: str,
        node2_id: str
    ) -> float:
        """
        计算两个节点之间的关系强度

        考虑因素：
        1. 直接边的权重
        2. 共同邻居数量
        3. 上下文向量相似度
        4. 共现频率

        Args:
            node1_id: 节点1 ID
            node2_id: 节点2 ID

        Returns:
            关系强度分数 (0.0 - 1.0)
        """
        strength = 0.0

        # 1. 直接边权重（如果存在）
        if self.graph.has_edge(node1_id, node2_id):
            edge_data = self.graph.get_edge_data(node1_id, node2_id)
            strength += 0.4 * edge_data.get('weight', 0.0)

        # 2. 共同邻居（Jaccard系数）
        neighbors1 = set(self.graph.neighbors(node1_id))
        neighbors2 = set(self.graph.neighbors(node2_id))

        if neighbors1 or neighbors2:
            jaccard = len(neighbors1 & neighbors2) / len(neighbors1 | neighbors2)
            strength += 0.3 * jaccard

        # 3. 上下文向量相似度
        node1_data = self.graph.nodes[node1_id]
        node2_data = self.graph.nodes[node2_id]

        vec1 = node1_data.get('context_vector')
        vec2 = node2_data.get('context_vector')

        if vec1 and vec2:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            strength += 0.3 * max(0.0, cosine_sim)

        return min(1.0, strength)


    def get_node_neighborhood(
        self,
        node_id: str,
        radius: int = 2,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """
        获取节点的邻域子图（用于前端树状展开）

        Args:
            node_id: 中心节点ID
            radius: 邻域半径（跳数）
            max_nodes: 最多返回多少个节点

        Returns:
            邻域子图（节点+边）
        """
        if node_id not in self.graph:
            raise ValueError(f"节点不存在: {node_id}")

        # BFS获取邻域节点
        neighborhood_nodes = set([node_id])
        current_layer = {node_id}

        for _ in range(radius):
            next_layer = set()
            for node in current_layer:
                # 出边邻居
                next_layer.update(self.graph.successors(node))
                # 入边邻居
                next_layer.update(self.graph.predecessors(node))

            neighborhood_nodes.update(next_layer)
            current_layer = next_layer

            if len(neighborhood_nodes) >= max_nodes:
                break

        # 限制节点数
        if len(neighborhood_nodes) > max_nodes:
            # 按重要性排序，保留Top K
            node_scores = {
                n: self.graph.nodes[n].get('importance_score', 0.0)
                for n in neighborhood_nodes
            }
            top_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            neighborhood_nodes = {n for n, _ in top_nodes}
            neighborhood_nodes.add(node_id)  # 确保中心节点在内

        # 提取子图
        subgraph = self.graph.subgraph(neighborhood_nodes)

        # 构建返回结果
        nodes_data = []
        for n in subgraph.nodes():
            node_data = self.graph.nodes[n]
            nodes_data.append({
                "id": n,
                "name": node_data['name'],
                "type": node_data['type'],
                "importance_score": node_data.get('importance_score', 0.0),
                "is_core_keyword": node_data.get('is_core_keyword', False),
                "layer": node_data.get('layer', 3),
            })

        edges_data = []
        for u, v in subgraph.edges():
            edge_data = self.graph.get_edge_data(u, v)
            edges_data.append({
                "source": u,
                "target": v,
                "type": edge_data.get('type', '未知关系'),
                "weight": edge_data.get('weight', 0.0),
            })

        result = {
            "center_node": node_id,
            "center_name": self.graph.nodes[node_id]['name'],
            "radius": radius,
            "total_nodes": len(nodes_data),
            "total_edges": len(edges_data),
            "nodes": nodes_data,
            "edges": edges_data,
        }

        logger.info(
            f"获取邻域子图: {result['center_name']}, "
            f"半径={radius}, {len(nodes_data)}个节点"
        )

        return result


# 单例实例
_graph_reasoning_service = None

def get_graph_reasoning_service() -> GraphReasoningService:
    """获取图谱推理服务单例"""
    global _graph_reasoning_service
    if _graph_reasoning_service is None:
        _graph_reasoning_service = GraphReasoningService()
    return _graph_reasoning_service
