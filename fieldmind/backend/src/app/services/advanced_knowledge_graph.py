"""
高级知识图谱构建器
基于 rahulnyk/knowledge_graph 的核心思想
使用 NetworkX + spaCy 构建知识图谱
"""
import spacy
import networkx as nx
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class AdvancedKnowledgeGraphBuilder:
    """
    高级知识图谱构建器

    核心功能：
    1. 实体识别（使用 spaCy NER）
    2. 关系抽取（基于依存句法分析）
    3. 图谱构建（NetworkX）
    4. 社区发现（Louvain 算法）
    5. 中心性分析（PageRank）
    """

    def __init__(self):
        # 加载 spaCy 模型
        try:
            self.nlp = spacy.load("zh_core_web_sm")
        except:
            logger.warning("中文模型未安装，使用英文模型")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                logger.error("spaCy 模型未安装，功能受限")
                self.nlp = None

        self.graph = nx.Graph()
        self.entities = []
        self.relations = []

    def build_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本构建知识图谱

        Args:
            text: 输入文本

        Returns:
            {
                "entities": [...],
                "relations": [...],
                "graph_metrics": {...},
                "communities": [...],
                "central_nodes": [...]
            }
        """
        if not self.nlp:
            return self._fallback_extraction(text)

        # 1. 实体识别
        doc = self.nlp(text)
        self.entities = self._extract_entities(doc)

        # 2. 关系抽取
        self.relations = self._extract_relations(doc)

        # 3. 构建图谱
        self._build_graph()

        # 4. 图分析
        metrics = self._analyze_graph()

        # 5. 社区发现
        communities = self._detect_communities()

        # 6. 中心性分析
        central_nodes = self._find_central_nodes()

        return {
            "entities": self.entities,
            "relations": self.relations,
            "graph_metrics": metrics,
            "communities": communities,
            "central_nodes": central_nodes,
        }

    def _extract_entities(self, doc) -> List[Dict]:
        """提取命名实体"""
        entities = []
        seen = set()

        for ent in doc.ents:
            if ent.text not in seen:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
                seen.add(ent.text)

        logger.info(f"提取了 {len(entities)} 个实体")
        return entities

    def _extract_relations(self, doc) -> List[Dict]:
        """
        基于依存句法分析提取关系

        参考 rahulnyk/knowledge_graph 的关系提取方法
        """
        relations = []

        for token in doc:
            # 主语-谓语-宾语模式
            if token.dep_ in ["nsubj", "nsubjpass"]:
                subject = token.text
                verb = token.head.text

                # 查找宾语
                for child in token.head.children:
                    if child.dep_ in ["dobj", "pobj"]:
                        obj = child.text

                        relations.append({
                            "subject": subject,
                            "relation": verb,
                            "object": obj,
                            "confidence": 0.8,
                        })

            # 名词修饰关系
            elif token.dep_ == "compound":
                relations.append({
                    "subject": token.text,
                    "relation": "修饰",
                    "object": token.head.text,
                    "confidence": 0.6,
                })

        logger.info(f"提取了 {len(relations)} 个关系")
        return relations

    def _build_graph(self):
        """构建 NetworkX 图"""
        self.graph.clear()

        # 添加实体节点
        for entity in self.entities:
            self.graph.add_node(
                entity["text"],
                type=entity["type"],
            )

        # 添加关系边
        for relation in self.relations:
            self.graph.add_edge(
                relation["subject"],
                relation["object"],
                relation=relation["relation"],
                weight=relation["confidence"],
            )

        logger.info(
            f"构建图谱: {self.graph.number_of_nodes()} 节点, "
            f"{self.graph.number_of_edges()} 边"
        )

    def _analyze_graph(self) -> Dict:
        """图谱分析"""
        if self.graph.number_of_nodes() == 0:
            return {}

        metrics = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
        }

        # 连通性
        if nx.is_connected(self.graph):
            metrics["diameter"] = nx.diameter(self.graph)
            metrics["avg_shortest_path"] = nx.average_shortest_path_length(self.graph)

        return metrics

    def _detect_communities(self) -> List[List[str]]:
        """
        社区发现
        使用 Louvain 算法（参考 rahulnyk/knowledge_graph）
        """
        if self.graph.number_of_nodes() == 0:
            return []

        try:
            from networkx.algorithms import community

            # Louvain 社区发现
            communities = community.louvain_communities(self.graph)

            result = [list(comm) for comm in communities]
            logger.info(f"发现 {len(result)} 个社区")

            return result
        except Exception as e:
            logger.error(f"社区发现失败: {e}")
            return []

    def _find_central_nodes(self, top_k: int = 10) -> List[Dict]:
        """
        找出中心节点
        使用 PageRank 算法
        """
        if self.graph.number_of_nodes() == 0:
            return []

        try:
            # PageRank
            pagerank = nx.pagerank(self.graph)

            # 排序
            sorted_nodes = sorted(
                pagerank.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]

            result = [
                {
                    "node": node,
                    "score": score,
                    "degree": self.graph.degree(node),
                }
                for node, score in sorted_nodes
            ]

            logger.info(f"找到 {len(result)} 个中心节点")
            return result

        except Exception as e:
            logger.error(f"中心性分析失败: {e}")
            return []

    def _fallback_extraction(self, text: str) -> Dict:
        """备用提取方法（spaCy 不可用时）"""
        logger.warning("使用备用提取方法")

        # 使用简单的关键词提取
        from app.services.knowledge_graph_enhanced import knowledge_graph_enhancer

        result = knowledge_graph_enhancer.enhance_document(text)

        return {
            "entities": result["entities"],
            "relations": result["relations"],
            "graph_metrics": {},
            "communities": [],
            "central_nodes": [],
        }

    def export_to_json(self) -> Dict:
        """导出为 JSON 格式"""
        return {
            "nodes": [
                {
                    "id": node,
                    "type": self.graph.nodes[node].get("type", "unknown"),
                }
                for node in self.graph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "relation": data.get("relation", "related"),
                    "weight": data.get("weight", 1.0),
                }
                for u, v, data in self.graph.edges(data=True)
            ],
        }

    def get_subgraph(self, entity: str, depth: int = 1) -> nx.Graph:
        """获取实体的子图"""
        if entity not in self.graph:
            return nx.Graph()

        # BFS 获取指定深度的邻居
        nodes = set([entity])
        current_level = set([entity])

        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.neighbors(node))
            nodes.update(next_level)
            current_level = next_level

        return self.graph.subgraph(nodes)


class SemanticSimilarityAnalyzer:
    """
    语义相似度分析器
    基于 TF-IDF 和余弦相似度
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.documents = []
        self.vectors = None

    def add_documents(self, documents: List[str]):
        """添加文档"""
        self.documents = documents
        self.vectors = self.vectorizer.fit_transform(documents)

    def find_similar(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """找出最相似的文档"""
        if self.vectors is None:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors)[0]

        # 排序
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(idx, similarities[idx]) for idx in top_indices]


# 全局实例
kg_builder = AdvancedKnowledgeGraphBuilder()
similarity_analyzer = SemanticSimilarityAnalyzer()
