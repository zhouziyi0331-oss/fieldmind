"""
核心关键词提取服务
从知识图谱中提取5-6个最核心的关键词

原则：
1. 从真正有用的点生发，不是无用的点
2. 核心关键词必须是最重要的5-6个
3. 其他节点必须从核心关键词衍生
4. 支持两种发散模式：关系发散、民俗发散
"""
from typing import List, Dict, Any, Tuple
import networkx as nx
from collections import defaultdict
from app.models.knowledge_graph import (
    GraphNode,
    GraphEdge,
    CoreKeyword,
    NodeType
)


class CoreKeywordExtractor:
    """核心关键词提取器"""
    def __init__(self, use_workflow_engine: bool = True):

        # 核心关键词数量
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.core_keyword_count = 6  # 5-6个

        # 节点类型权重（哪些类型更可能是核心）
        self.node_type_weights = {
            NodeType.CORE_KEYWORD: 10.0,  # 已标记的核心关键词
            NodeType.INTANGIBLE_HERITAGE: 5.0,  # 非遗
            NodeType.CUSTOM: 4.5,  # 习俗
            NodeType.RITUAL: 4.5,  # 仪式
            NodeType.FESTIVAL: 4.0,  # 节日
            NodeType.CLAN: 3.5,  # 宗族
            NodeType.ANCESTRAL_HALL: 3.5,  # 祠堂
            NodeType.ORGANIZATION: 3.0,  # 组织
            NodeType.SKILL: 3.0,  # 技艺
            NodeType.PERSON: 2.0,  # 人物（重要人物）
            NodeType.LOCATION: 1.5,  # 地点
            NodeType.DIALECT_TERM: 1.0,  # 方言（通常不是核心）
        }

    def extract_core_keywords(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        mode: str = "auto"  # "auto", "relationship", "folklore"
    ) -> List[CoreKeyword]:
        """
        提取核心关键词

        Args:
            nodes: 所有节点
            edges: 所有边
            mode: 发散模式
                - "auto": 自动选择最重要的
                - "relationship": 关系发散（人物、组织关系网）
                - "folklore": 民俗发散（习俗、仪式、非遗）

        Returns:
            List[CoreKeyword]: 核心关键词列表（5-6个）
        """
        # 1. 构建NetworkX图（用于计算图算法指标）
        G = self._build_networkx_graph(nodes, edges)

        # 2. 计算多维度重要性指标
        importance_scores = self._calculate_importance_scores(nodes, edges, G, mode)

        # 3. 根据模式过滤候选节点
        candidates = self._filter_candidates_by_mode(nodes, mode)

        # 4. 排序并选择Top 5-6
        sorted_candidates = sorted(
            candidates,
            key=lambda n: importance_scores.get(n.id, 0.0),
            reverse=True
        )

        top_keywords = sorted_candidates[:self.core_keyword_count]

        # 5. 为每个核心关键词构建发散路径
        core_keywords = []
        for node in top_keywords:
            keyword = CoreKeyword(
                keyword=node.name,
                node_id=node.id,
                importance=importance_scores.get(node.id, 0.0),
                category=self._get_category(node, mode),
                derived_keywords=[],
                radiation_paths=[]
            )

            # 计算发散路径
            keyword.derived_keywords = self._find_derived_keywords(node, G, nodes)
            keyword.radiation_paths = self._build_radiation_paths(node, G, nodes)

            core_keywords.append(keyword)

        return core_keywords

    def _build_networkx_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ) -> nx.DiGraph:
        """构建NetworkX有向图"""
        G = nx.DiGraph()

        # 添加节点
        for node in nodes:
            G.add_node(
                node.id,
                name=node.name,
                type=node.type,
                importance=node.importance_score
            )

        # 添加边
        for edge in edges:
            G.add_edge(
                edge.source,
                edge.target,
                type=edge.type,
                weight=edge.weight
            )

        return G

    def _calculate_importance_scores(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        G: nx.DiGraph,
        mode: str
    ) -> Dict[str, float]:
        """
        计算节点重要性（多维度综合）

        指标：
        1. PageRank（图结构重要性）⭐
        2. 度中心性（连接数量）
        3. 介数中心性（桥接作用）
        4. 节点类型权重
        5. 用户标记的importance_score
        """
        importance = {}

        # 1. PageRank（最重要）
        try:
            pagerank = nx.pagerank(G, alpha=0.85)
        except:
            pagerank = {node.id: 1.0 / len(nodes) for node in nodes}

        # 2. 度中心性
        try:
            degree_centrality = nx.degree_centrality(G)
        except:
            degree_centrality = {node.id: 0.0 for node in nodes}

        # 3. 介数中心性
        try:
            betweenness = nx.betweenness_centrality(G)
        except:
            betweenness = {node.id: 0.0 for node in nodes}

        # 4. 综合计算
        for node in nodes:
            score = 0.0

            # PageRank (40%)
            score += pagerank.get(node.id, 0.0) * 0.40

            # 度中心性 (20%)
            score += degree_centrality.get(node.id, 0.0) * 0.20

            # 介数中心性 (15%)
            score += betweenness.get(node.id, 0.0) * 0.15

            # 节点类型权重 (15%)
            type_weight = self.node_type_weights.get(node.type, 1.0)
            normalized_type_weight = type_weight / 10.0  # 归一化到0-1
            score += normalized_type_weight * 0.15

            # 用户标记的importance_score (10%)
            score += node.importance_score * 0.10

            importance[node.id] = score

        return importance

    def _filter_candidates_by_mode(
        self,
        nodes: List[GraphNode],
        mode: str
    ) -> List[GraphNode]:
        """
        根据模式过滤候选节点

        - "relationship": 优先选择人物、组织、宗族
        - "folklore": 优先选择习俗、仪式、非遗、节日
        - "auto": 不过滤
        """
        if mode == "auto":
            return nodes

        if mode == "relationship":
            # 关系发散：人物、组织、宗族为核心
            relationship_types = {
                NodeType.PERSON,
                NodeType.ORGANIZATION,
                NodeType.CLAN,
                NodeType.FAMILY,
                NodeType.VILLAGE_COMMITTEE,
                NodeType.ASSOCIATION,
            }
            return [n for n in nodes if n.type in relationship_types]

        if mode == "folklore":
            # 民俗发散：习俗、仪式、非遗、节日为核心
            folklore_types = {
                NodeType.INTANGIBLE_HERITAGE,
                NodeType.CUSTOM,
                NodeType.RITUAL,
                NodeType.FESTIVAL,
                NodeType.CEREMONY,
                NodeType.SKILL,
                NodeType.CRAFT,
            }
            return [n for n in nodes if n.type in folklore_types]

        return nodes

    def _get_category(self, node: GraphNode, mode: str) -> str:
        """获取核心关键词的类别"""
        if mode == "relationship":
            return "关系"
        elif mode == "folklore":
            return "民俗"
        else:
            # 根据节点类型判断
            folklore_types = {
                NodeType.INTANGIBLE_HERITAGE,
                NodeType.CUSTOM,
                NodeType.RITUAL,
                NodeType.FESTIVAL,
            }
            if node.type in folklore_types:
                return "民俗"
            else:
                return "关系"

    def _find_derived_keywords(
        self,
        core_node: GraphNode,
        G: nx.DiGraph,
        all_nodes: List[GraphNode]
    ) -> List[str]:
        """
        找出从核心关键词衍生的次要关键词

        策略：
        1. 直接邻居（1跳）
        2. 2跳邻居中的重要节点
        """
        derived = []
        node_map = {n.id: n for n in all_nodes}

        # 1. 直接邻居（1跳）
        if core_node.id in G:
            neighbors = list(G.neighbors(core_node.id))
            for neighbor_id in neighbors:
                if neighbor_id in node_map:
                    derived.append(node_map[neighbor_id].name)

        # 2. 2跳邻居（重要的）
        try:
            two_hop = nx.single_source_shortest_path_length(G, core_node.id, cutoff=2)
            for node_id, distance in two_hop.items():
                if distance == 2 and node_id in node_map:
                    node = node_map[node_id]
                    # 只添加重要节点
                    if node.importance_score >= 0.5:
                        derived.append(node.name)
        except:
            pass

        return derived[:20]  # 最多20个衍生关键词

    def _build_radiation_paths(
        self,
        core_node: GraphNode,
        G: nx.DiGraph,
        all_nodes: List[GraphNode]
    ) -> List[List[str]]:
        """
        构建发散路径：核心 → 次要 → 细节

        例如：
        ["布依族蜡染", "蜡染技艺", "蜡刀工具"]
        ["村支书", "村委会", "村务管理"]
        """
        paths = []
        node_map = {n.id: n for n in all_nodes}

        # 使用BFS找出多条发散路径
        if core_node.id not in G:
            return paths

        # 找出最多10条路径
        visited = set([core_node.id])
        queue = [(core_node.id, [core_node.name])]

        while queue and len(paths) < 10:
            current_id, path = queue.pop(0)

            # 路径长度限制为3（核心 → 次要 → 细节）
            if len(path) >= 3:
                paths.append(path)
                continue

            # 扩展路径
            if current_id in G:
                neighbors = list(G.neighbors(current_id))
                for neighbor_id in neighbors:
                    if neighbor_id not in visited and neighbor_id in node_map:
                        visited.add(neighbor_id)
                        neighbor_name = node_map[neighbor_id].name
                        queue.append((neighbor_id, path + [neighbor_name]))

        return paths

    def validate_core_keywords(
        self,
        core_keywords: List[CoreKeyword]
    ) -> Dict[str, Any]:
        """
        验证核心关键词质量

        检查：
        1. 数量是否为5-6个 ✓
        2. 每个核心关键词是否有衍生关键词 ✓
        3. 是否覆盖关系和民俗两个维度 ✓
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 1. 数量检查
        if len(core_keywords) < 5:
            validation["errors"].append(f"核心关键词数量不足：{len(core_keywords)} < 5")
            validation["valid"] = False
        elif len(core_keywords) > 6:
            validation["warnings"].append(f"核心关键词数量过多：{len(core_keywords)} > 6")

        # 2. 衍生关键词检查
        for kw in core_keywords:
            if len(kw.derived_keywords) == 0:
                validation["warnings"].append(
                    f"核心关键词 '{kw.keyword}' 没有衍生关键词"
                )

        # 3. 类别覆盖检查
        categories = set(kw.category for kw in core_keywords)
        if len(categories) < 2:
            validation["warnings"].append(
                f"核心关键词类别单一，建议同时覆盖关系和民俗：{categories}"
            )

        return validation
