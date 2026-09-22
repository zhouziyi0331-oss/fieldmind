"""
向量检索增强服务
基于 PageIndex 的核心思想
使用 FAISS 实现高性能向量搜索
"""
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

# 尝试导入 FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("FAISS 未安装，使用备用方案")
    FAISS_AVAILABLE = False


class VectorIndexService:
    """
    向量索引服务

    功能：
    1. 文档向量化
    2. 向量索引构建（FAISS）
    3. 语义搜索
    4. 混合检索（关键词 + 向量）
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = None
        self.documents = []
        self.doc_ids = []

        if FAISS_AVAILABLE:
            self._init_faiss_index()
        else:
            self._init_fallback_index()

    def _init_faiss_index(self):
        """初始化 FAISS 索引"""
        # 使用 IVF (Inverted File Index) + PQ (Product Quantization)
        quantizer = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIVFPQ(
            quantizer,
            self.dimension,
            100,  # nlist: 聚类中心数
            8,    # M: 子向量数
            8     # nbits: 每个子向量的比特数
        )
        logger.info("FAISS 索引初始化成功")

    def _init_fallback_index(self):
        """初始化备用索引（简单的向量列表）"""
        self.vectors = []
        logger.info("使用备用索引")

    def add_documents(
        self,
        documents: List[str],
        vectors: np.ndarray,
        doc_ids: List[int]
    ):
        """
        添加文档到索引

        Args:
            documents: 文档内容列表
            vectors: 文档向量矩阵 (n, dimension)
            doc_ids: 文档 ID 列表
        """
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"向量维度不匹配: {vectors.shape[1]} != {self.dimension}")

        self.documents.extend(documents)
        self.doc_ids.extend(doc_ids)

        if FAISS_AVAILABLE:
            # 训练索引（如果尚未训练）
            if not self.index.is_trained:
                self.index.train(vectors)

            # 添加向量
            self.index.add(vectors)
            logger.info(f"添加了 {len(documents)} 个文档到 FAISS 索引")
        else:
            # 备用方案：直接存储向量
            if not hasattr(self, 'vectors'):
                self.vectors = []
            self.vectors.extend(vectors.tolist())
            logger.info(f"添加了 {len(documents)} 个文档到备用索引")

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        向量搜索

        Args:
            query_vector: 查询向量 (dimension,)
            top_k: 返回结果数
            return_scores: 是否返回相似度分数

        Returns:
            [
                {
                    "doc_id": int,
                    "content": str,
                    "score": float,
                    "rank": int
                }
            ]
        """
        if len(self.documents) == 0:
            return []

        query_vector = query_vector.reshape(1, -1).astype('float32')

        if FAISS_AVAILABLE:
            return self._faiss_search(query_vector, top_k, return_scores)
        else:
            return self._fallback_search(query_vector, top_k, return_scores)

    def _faiss_search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        return_scores: bool
    ) -> List[Dict]:
        """FAISS 搜索"""
        # 搜索
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:  # FAISS 返回 -1 表示无结果
                continue

            result = {
                "doc_id": self.doc_ids[idx],
                "content": self.documents[idx],
                "rank": rank + 1,
            }

            if return_scores:
                # 转换距离为相似度（越小越相似）
                result["score"] = 1.0 / (1.0 + dist)

            results.append(result)

        return results

    def _fallback_search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        return_scores: bool
    ) -> List[Dict]:
        """备用搜索（余弦相似度）"""
        from sklearn.metrics.pairwise import cosine_similarity

        vectors = np.array(self.vectors)
        similarities = cosine_similarity(query_vector, vectors)[0]

        # 排序
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            result = {
                "doc_id": self.doc_ids[idx],
                "content": self.documents[idx],
                "rank": rank + 1,
            }

            if return_scores:
                result["score"] = float(similarities[idx])

            results.append(result)

        return results

    def hybrid_search(
        self,
        query_text: str,
        query_vector: np.ndarray,
        top_k: int = 5,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        混合检索（关键词 + 向量）

        Args:
            query_text: 查询文本（用于关键词匹配）
            query_vector: 查询向量（用于语义搜索）
            top_k: 返回结果数
            vector_weight: 向量搜索权重（0-1）

        Returns:
            混合排序的结果
        """
        # 1. 向量搜索
        vector_results = self.search(query_vector, top_k * 2, return_scores=True)

        # 2. 关键词搜索
        keyword_results = self._keyword_search(query_text, top_k * 2)

        # 3. 混合排序
        doc_scores = {}

        for result in vector_results:
            doc_id = result["doc_id"]
            doc_scores[doc_id] = result["score"] * vector_weight

        for result in keyword_results:
            doc_id = result["doc_id"]
            keyword_score = result["score"] * (1 - vector_weight)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + keyword_score

        # 排序
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # 构建结果
        results = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            idx = self.doc_ids.index(doc_id)
            results.append({
                "doc_id": doc_id,
                "content": self.documents[idx],
                "score": score,
                "rank": rank,
            })

        return results

    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """关键词搜索（BM25）"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        if len(self.documents) == 0:
            return []

        # TF-IDF 向量化
        vectorizer = TfidfVectorizer()
        doc_vectors = vectorizer.fit_transform(self.documents)
        query_vector = vectorizer.transform([query])

        # 计算相似度
        similarities = cosine_similarity(query_vector, doc_vectors)[0]

        # 排序
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # 只返回有匹配的
                results.append({
                    "doc_id": self.doc_ids[idx],
                    "content": self.documents[idx],
                    "score": float(similarities[idx]),
                })

        return results

    def save_index(self, path: str):
        """保存索引到磁盘"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # 保存元数据
        metadata = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "dimension": self.dimension,
        }

        with open(path / "metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

        # 保存索引
        if FAISS_AVAILABLE:
            faiss.write_index(self.index, str(path / "index.faiss"))
        else:
            with open(path / "vectors.pkl", "wb") as f:
                pickle.dump(self.vectors, f)

        logger.info(f"索引已保存到 {path}")

    def load_index(self, path: str):
        """从磁盘加载索引"""
        path = Path(path)

        # 加载元数据
        with open(path / "metadata.pkl", "rb") as f:
            metadata = pickle.load(f)

        self.documents = metadata["documents"]
        self.doc_ids = metadata["doc_ids"]
        self.dimension = metadata["dimension"]

        # 加载索引
        if FAISS_AVAILABLE:
            self.index = faiss.read_index(str(path / "index.faiss"))
        else:
            with open(path / "vectors.pkl", "rb") as f:
                self.vectors = pickle.load(f)

        logger.info(f"索引已从 {path} 加载")

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        stats = {
            "num_documents": len(self.documents),
            "dimension": self.dimension,
            "backend": "FAISS" if FAISS_AVAILABLE else "Fallback",
        }

        if FAISS_AVAILABLE:
            stats["index_trained"] = self.index.is_trained
            stats["index_total"] = self.index.ntotal

        return stats


# 全局实例
vector_index_service = VectorIndexService()
