"""
混合检索实现

结合密集向量检索和稀疏关键词检索
"""

from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import numpy as np

from ..base import VectorStore, SearchResult, Document
from .bm25 import BM25Retriever


class FusionMethod(Enum):
    """融合方法"""
    RRF = "rrf"  # Reciprocal Rank Fusion
    LINEAR = "linear"  # 线性加权
    MAX = "max"  # 取最大值


class HybridRetriever:
    """混合检索器

    结合密集向量检索（语义）和稀疏关键词检索（精确匹配）

    特性：
    - 双路召回：向量 + BM25
    - 多种融合策略：RRF、线性加权、最大值
    - 可配置权重
    - 自动去重

    示例：
        retriever = HybridRetriever(
            vector_store=faiss_store,
            fusion_method=FusionMethod.RRF,
            dense_weight=0.7,
            sparse_weight=0.3
        )

        results = retriever.search(
            query_text="机器学习算法",
            query_embedding=embedding,
            top_k=10
        )
    """

    def __init__(
        self,
        vector_store: VectorStore,
        fusion_method: FusionMethod = FusionMethod.RRF,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        language: str = "zh"
    ):
        """初始化混合检索器

        Args:
            vector_store: 向量存储后端
            fusion_method: 融合方法
            dense_weight: 密集检索权重
            sparse_weight: 稀疏检索权重
            bm25_k1: BM25 k1 参数
            bm25_b: BM25 b 参数
            language: 语言类型
        """
        self.vector_store = vector_store
        self.fusion_method = fusion_method
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight

        # 归一化权重
        total = dense_weight + sparse_weight
        if total > 0:
            self.dense_weight = dense_weight / total
            self.sparse_weight = sparse_weight / total

        # BM25 检索器
        self.bm25 = BM25Retriever(k1=bm25_k1, b=bm25_b, language=language)

    def add_documents(self, documents: List[Document]) -> None:
        """添加文档到索引

        Args:
            documents: 文档列表（需包含 embedding 和 content）
        """
        # 添加到向量存储
        self.vector_store.add(documents)

        # 添加到 BM25
        contents = [doc.content for doc in documents]
        doc_ids = [doc.id for doc in documents]
        self.bm25.add_documents(contents, doc_ids)

    def search(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        dense_top_k: Optional[int] = None,
        sparse_top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """混合搜索

        Args:
            query_text: 查询文本
            query_embedding: 查询向量
            top_k: 最终返回的结果数
            dense_top_k: 密集检索召回数（默认为 top_k * 2）
            sparse_top_k: 稀疏检索召回数（默认为 top_k * 2）
            filters: 元数据过滤

        Returns:
            融合后的搜索结果列表
        """
        # 默认召回数为最终结果的2倍
        dense_top_k = dense_top_k or (top_k * 2)
        sparse_top_k = sparse_top_k or (top_k * 2)

        # 1. 密集检索（向量）
        dense_results = self.vector_store.search(
            query_embedding,
            top_k=dense_top_k,
            filters=filters
        )

        # 2. 稀疏检索（BM25）
        sparse_results = self.bm25.search(query_text, top_k=sparse_top_k)

        # 3. 融合结果
        fused_results = self._fuse_results(dense_results, sparse_results, top_k)

        return fused_results

    def _fuse_results(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[Tuple[str, float]],
        top_k: int
    ) -> List[SearchResult]:
        """融合密集和稀疏检索结果

        Args:
            dense_results: 密集检索结果
            sparse_results: 稀疏检索结果 (doc_id, score)
            top_k: 返回数量

        Returns:
            融合后的结果列表
        """
        if self.fusion_method == FusionMethod.RRF:
            return self._rrf_fusion(dense_results, sparse_results, top_k)
        elif self.fusion_method == FusionMethod.LINEAR:
            return self._linear_fusion(dense_results, sparse_results, top_k)
        elif self.fusion_method == FusionMethod.MAX:
            return self._max_fusion(dense_results, sparse_results, top_k)
        else:
            return dense_results[:top_k]

    def _rrf_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[Tuple[str, float]],
        top_k: int,
        k: int = 60
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion

        RRF(d) = Σ 1 / (k + rank(d))

        Args:
            dense_results: 密集结果
            sparse_results: 稀疏结果
            top_k: 返回数量
            k: RRF 参数（默认 60）

        Returns:
            融合结果
        """
        # 计算 RRF 分数
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, SearchResult] = {}

        # 密集结果
        for rank, result in enumerate(dense_results):
            doc_id = result.document.id
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + self.dense_weight / (k + rank + 1)
            doc_map[doc_id] = result

        # 稀疏结果
        for rank, (doc_id, score) in enumerate(sparse_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + self.sparse_weight / (k + rank + 1)

            # 如果密集结果中没有，需要从向量存储获取
            if doc_id not in doc_map:
                docs = self.vector_store.get([doc_id])
                if docs[0] is not None:
                    doc_map[doc_id] = SearchResult(
                        document=docs[0],
                        score=0.0,
                        distance=0.0,
                        rank=0
                    )

        # 排序
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建结果
        results = []
        for rank, (doc_id, score) in enumerate(sorted_ids[:top_k]):
            if doc_id in doc_map:
                result = doc_map[doc_id]
                result.score = score
                result.rank = rank
                results.append(result)

        return results

    def _linear_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[Tuple[str, float]],
        top_k: int
    ) -> List[SearchResult]:
        """线性加权融合

        Score(d) = w1 * dense_score(d) + w2 * sparse_score(d)

        Args:
            dense_results: 密集结果
            sparse_results: 稀疏结果
            top_k: 返回数量

        Returns:
            融合结果
        """
        # 归一化分数
        dense_scores = self._normalize_scores(
            {r.document.id: r.score for r in dense_results}
        )
        sparse_scores = self._normalize_scores(
            {doc_id: score for doc_id, score in sparse_results}
        )

        # 线性组合
        combined_scores: Dict[str, float] = {}
        doc_map: Dict[str, SearchResult] = {}

        # 密集分数
        for result in dense_results:
            doc_id = result.document.id
            combined_scores[doc_id] = self.dense_weight * dense_scores.get(doc_id, 0)
            doc_map[doc_id] = result

        # 稀疏分数
        for doc_id, _ in sparse_results:
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + \
                                      self.sparse_weight * sparse_scores.get(doc_id, 0)

            # 获取文档
            if doc_id not in doc_map:
                docs = self.vector_store.get([doc_id])
                if docs[0] is not None:
                    doc_map[doc_id] = SearchResult(
                        document=docs[0],
                        score=0.0,
                        distance=0.0,
                        rank=0
                    )

        # 排序
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建结果
        results = []
        for rank, (doc_id, score) in enumerate(sorted_ids[:top_k]):
            if doc_id in doc_map:
                result = doc_map[doc_id]
                result.score = score
                result.rank = rank
                results.append(result)

        return results

    def _max_fusion(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[Tuple[str, float]],
        top_k: int
    ) -> List[SearchResult]:
        """最大值融合

        Score(d) = max(dense_score(d), sparse_score(d))

        Args:
            dense_results: 密集结果
            sparse_results: 稀疏结果
            top_k: 返回数量

        Returns:
            融合结果
        """
        # 归一化分数
        dense_scores = self._normalize_scores(
            {r.document.id: r.score for r in dense_results}
        )
        sparse_scores = self._normalize_scores(
            {doc_id: score for doc_id, score in sparse_results}
        )

        # 取最大值
        max_scores: Dict[str, float] = {}
        doc_map: Dict[str, SearchResult] = {}

        # 密集结果
        for result in dense_results:
            doc_id = result.document.id
            max_scores[doc_id] = dense_scores.get(doc_id, 0)
            doc_map[doc_id] = result

        # 稀疏结果
        for doc_id, _ in sparse_results:
            sparse_score = sparse_scores.get(doc_id, 0)
            max_scores[doc_id] = max(max_scores.get(doc_id, 0), sparse_score)

            # 获取文档
            if doc_id not in doc_map:
                docs = self.vector_store.get([doc_id])
                if docs[0] is not None:
                    doc_map[doc_id] = SearchResult(
                        document=docs[0],
                        score=0.0,
                        distance=0.0,
                        rank=0
                    )

        # 排序
        sorted_ids = sorted(max_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建结果
        results = []
        for rank, (doc_id, score) in enumerate(sorted_ids[:top_k]):
            if doc_id in doc_map:
                result = doc_map[doc_id]
                result.score = score
                result.rank = rank
                results.append(result)

        return results

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """归一化分数到 [0, 1]

        使用 Min-Max 归一化

        Args:
            scores: 分数字典

        Returns:
            归一化后的分数
        """
        if not scores:
            return {}

        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            return {k: 1.0 for k in scores.keys()}

        return {
            k: (v - min_val) / (max_val - min_val)
            for k, v in scores.items()
        }

    def clear(self) -> None:
        """清空所有数据"""
        self.vector_store.clear()
        self.bm25.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "vector_store": self.vector_store.get_stats(),
            "bm25_docs": len(self.bm25),
            "bm25_vocab": len(self.bm25.vocab),
            "fusion_method": self.fusion_method.value,
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"HybridRetriever("
            f"method={self.fusion_method.value}, "
            f"dense={self.dense_weight:.2f}, "
            f"sparse={self.sparse_weight:.2f})"
        )
