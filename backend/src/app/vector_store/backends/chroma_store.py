"""
ChromaDB 向量存储后端实现

基于 ChromaDB 向量数据库
特点：内置持久化、丰富的元数据过滤、简单易用
"""

import warnings
# 忽略 requests 依赖警告
warnings.filterwarnings("ignore", category=Warning, module="requests")

import uuid
from typing import List, Optional, Dict, Any
import numpy as np
import chromadb
from chromadb.config import Settings

from ..base import (
    VectorStore,
    Document,
    SearchResult,
    DistanceMetric,
    IndexType,
)


class ChromaVectorStore(VectorStore):
    """ChromaDB 向量存储实现

    特性：
    - 自动持久化
    - 强大的元数据过滤（支持 $eq, $ne, $gt, $lt, $in 等）
    - 内置向量归一化
    - 简单的集合管理

    示例：
        # 创建持久化存储
        store = ChromaVectorStore(
            dimension=768,
            collection_name="my_collection",
            persist_directory="./chroma_db"
        )

        # 添加文档
        store.add(documents)

        # 搜索（支持复杂过滤）
        results = store.search(
            query_embedding,
            top_k=10,
            filters={"category": "tech", "year": {"$gte": 2020}}
        )
    """

    def __init__(
        self,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_type: IndexType = IndexType.HNSW,
        collection_name: str = "default_collection",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """初始化 ChromaDB 向量存储

        Args:
            dimension: 向量维度
            distance_metric: 距离度量方式
            index_type: 索引类型（Chroma 主要使用 HNSW）
            collection_name: 集合名称
            persist_directory: 持久化目录（None 则使用内存）
        """
        super().__init__(dimension, distance_metric, index_type, **kwargs)

        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 转换距离度量
        self._chroma_distance = self._convert_distance_metric(distance_metric)

        # 创建 Chroma 客户端
        if persist_directory:
            self._client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        else:
            self._client = chromadb.EphemeralClient(
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

        # 获取或创建集合
        try:
            self._collection = self._client.get_collection(
                name=collection_name,
                metadata={"hnsw:space": self._chroma_distance}
            )
        except Exception:
            # 集合不存在，创建新的
            self._collection = self._client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": self._chroma_distance}
            )

    def _convert_distance_metric(self, metric: DistanceMetric) -> str:
        """转换距离度量为 Chroma 格式

        Args:
            metric: 距离度量枚举

        Returns:
            Chroma 距离度量字符串
        """
        mapping = {
            DistanceMetric.COSINE: "cosine",
            DistanceMetric.L2: "l2",
            DistanceMetric.DOT_PRODUCT: "ip",  # inner product
            DistanceMetric.EUCLIDEAN: "l2",
        }
        return mapping.get(metric, "cosine")

    def add(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储

        Args:
            documents: 要添加的文档列表

        Returns:
            成功添加的文档ID列表
        """
        if not documents:
            return []

        # 准备数据
        ids = []
        embeddings = []
        metadatas = []
        contents = []

        for doc in documents:
            # 验证维度
            self.validate_embedding(doc.embedding)

            ids.append(doc.id)
            embeddings.append(doc.embedding.tolist())

            # Chroma 要求元数据值是基本类型
            metadata = self._sanitize_metadata(doc.metadata)
            metadatas.append(metadata)

            contents.append(doc.content)

        # 添加到集合
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=contents
        )

        return ids

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """清理元数据，确保兼容 Chroma

        Chroma 只支持：str, int, float, bool

        Args:
            metadata: 原始元数据

        Returns:
            清理后的元数据
        """
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                # 转换为逗号分隔的字符串
                sanitized[key] = ",".join(str(v) for v in value)
            else:
                # 其他类型转换为字符串
                sanitized[key] = str(value)
        return sanitized

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索最相似的文档

        Args:
            query_embedding: 查询向量
            top_k: 返回前K个结果
            filters: 元数据过滤条件
                支持 Chroma 的 where 语法：
                - {"key": "value"} - 等于
                - {"key": {"$ne": "value"}} - 不等于
                - {"key": {"$gt": 10}} - 大于
                - {"key": {"$gte": 10}} - 大于等于
                - {"key": {"$lt": 10}} - 小于
                - {"key": {"$lte": 10}} - 小于等于
                - {"key": {"$in": ["a", "b"]}} - 在列表中
                - {"$and": [...]} - 逻辑与
                - {"$or": [...]} - 逻辑或

        Returns:
            按相似度排序的搜索结果列表
        """
        # 验证维度
        self.validate_embedding(query_embedding)

        # 如果没有文档，返回空
        if self.count() == 0:
            return []

        # 查询
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(top_k, self.count()),
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            # 处理查询错误（如过滤器格式错误）
            raise RuntimeError(f"Search failed: {str(e)}")

        # 转换结果
        search_results = []

        if not results["ids"] or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        distances = results["distances"][0]
        documents_text = results["documents"][0]
        metadatas = results["metadatas"][0]

        for rank, (doc_id, distance, content, metadata) in enumerate(
            zip(ids, distances, documents_text, metadatas)
        ):
            # 计算相似度分数
            score = self._distance_to_score(distance)

            # 重建 Document 对象
            # 注意：我们需要从 Chroma 重新获取 embedding
            # 为了性能，这里不获取 embedding
            # 如果需要，可以添加 include=["embeddings"] 选项
            doc = Document(
                id=doc_id,
                content=content,
                embedding=np.zeros(self.dimension),  # 占位符
                metadata=metadata or {}
            )

            search_results.append(SearchResult(
                document=doc,
                score=score,
                distance=float(distance),
                rank=rank
            ))

        return search_results

    def _distance_to_score(self, distance: float) -> float:
        """将距离转换为相似度分数 [0, 1]

        Args:
            distance: 距离值

        Returns:
            相似度分数
        """
        if self.distance_metric == DistanceMetric.COSINE:
            # Chroma 的余弦距离已经归一化到 [0, 2]
            # 转换为相似度 [0, 1]
            return float(1 - distance / 2)
        elif self.distance_metric == DistanceMetric.L2:
            # L2 距离转换为相似度
            return float(1 / (1 + distance))
        elif self.distance_metric == DistanceMetric.DOT_PRODUCT:
            # 内积：值越大越相似
            # Chroma 返回的是负的内积
            return float(1 / (1 + abs(distance)))
        else:
            return float(1 / (1 + distance))

    def delete(self, doc_ids: List[str]) -> int:
        """删除文档

        Args:
            doc_ids: 要删除的文档ID列表

        Returns:
            成功删除的文档数量
        """
        if not doc_ids:
            return 0

        try:
            # 检查哪些ID存在
            existing_ids = []
            for doc_id in doc_ids:
                try:
                    result = self._collection.get(ids=[doc_id])
                    if result["ids"]:
                        existing_ids.append(doc_id)
                except Exception:
                    continue

            # 删除存在的ID
            if existing_ids:
                self._collection.delete(ids=existing_ids)

            return len(existing_ids)
        except Exception as e:
            raise RuntimeError(f"Delete failed: {str(e)}")

    def update(self, documents: List[Document]) -> int:
        """更新文档

        Args:
            documents: 要更新的文档列表

        Returns:
            成功更新的文档数量
        """
        if not documents:
            return 0

        # 准备数据
        ids = []
        embeddings = []
        metadatas = []
        contents = []

        for doc in documents:
            # 验证维度
            self.validate_embedding(doc.embedding)

            # 检查文档是否存在
            try:
                result = self._collection.get(ids=[doc.id])
                if not result["ids"]:
                    continue  # 跳过不存在的文档
            except Exception:
                continue

            ids.append(doc.id)
            embeddings.append(doc.embedding.tolist())
            metadatas.append(self._sanitize_metadata(doc.metadata))
            contents.append(doc.content)

        # 更新
        if ids:
            try:
                self._collection.update(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=contents
                )
            except Exception as e:
                raise RuntimeError(f"Update failed: {str(e)}")

        return len(ids)

    def get(self, doc_ids: List[str]) -> List[Optional[Document]]:
        """根据ID获取文档

        Args:
            doc_ids: 文档ID列表

        Returns:
            文档列表（不存在的ID返回None）
        """
        results = []

        for doc_id in doc_ids:
            try:
                result = self._collection.get(
                    ids=[doc_id],
                    include=["documents", "metadatas", "embeddings"]
                )

                if result["ids"] and result["ids"][0]:
                    doc = Document(
                        id=result["ids"][0],
                        content=result["documents"][0],
                        embedding=np.array(result["embeddings"][0], dtype=np.float32),
                        metadata=result["metadatas"][0] or {}
                    )
                    results.append(doc)
                else:
                    results.append(None)
            except Exception:
                results.append(None)

        return results

    def count(self) -> int:
        """获取存储中的文档总数

        Returns:
            文档总数
        """
        try:
            return self._collection.count()
        except Exception:
            return 0

    def clear(self) -> None:
        """清空所有文档"""
        try:
            # Chroma 没有 clear 方法，需要删除并重建集合
            self._client.delete_collection(name=self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self._chroma_distance}
            )
        except Exception as e:
            raise RuntimeError(f"Clear failed: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            统计信息字典
        """
        base_stats = super().get_stats()
        base_stats.update({
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "chroma_distance": self._chroma_distance,
        })
        return base_stats

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """预览集合中的文档

        Args:
            limit: 返回的文档数量

        Returns:
            包含文档信息的字典
        """
        try:
            return self._collection.peek(limit=limit)
        except Exception as e:
            raise RuntimeError(f"Peek failed: {str(e)}")

    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        dimension: int,
        collection_name: str = "default_collection",
        persist_directory: Optional[str] = None,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        **kwargs
    ) -> "ChromaVectorStore":
        """从文档列表创建向量存储（便捷方法）

        Args:
            documents: 文档列表
            dimension: 向量维度
            collection_name: 集合名称
            persist_directory: 持久化目录
            distance_metric: 距离度量

        Returns:
            ChromaVectorStore 实例
        """
        store = cls(
            dimension=dimension,
            collection_name=collection_name,
            persist_directory=persist_directory,
            distance_metric=distance_metric,
            **kwargs
        )
        store.add(documents)
        return store
