"""
FAISS 向量存储后端实现

基于 Facebook AI Similarity Search (FAISS) 库
支持多种索引类型：Flat、IVF、HNSW
提供高性能的向量检索能力
"""

import os
import pickle
from typing import List, Optional, Dict, Any
from pathlib import Path
import numpy as np
import faiss

from ..base import (
    VectorStore,
    Document,
    SearchResult,
    DistanceMetric,
    IndexType,
)


class FaissVectorStore(VectorStore):
    """FAISS 向量存储实现

    特性：
    - 支持多种索引类型（Flat, IVF, HNSW）
    - 高性能搜索（可GPU加速）
    - 支持持久化保存/加载
    - 内存高效

    示例：
        # 创建 HNSW 索引
        store = FaissVectorStore(
            dimension=768,
            index_type=IndexType.HNSW,
            hnsw_m=32,
            hnsw_ef_construction=200
        )

        # 添加文档
        store.add(documents)

        # 搜索
        results = store.search(query_embedding, top_k=10)
    """

    def __init__(
        self,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_type: IndexType = IndexType.FLAT,
        # IVF 参数
        ivf_nlist: int = 100,
        ivf_nprobe: int = 10,
        # HNSW 参数
        hnsw_m: int = 32,
        hnsw_ef_construction: int = 200,
        hnsw_ef_search: int = 128,
        # 通用参数
        use_gpu: bool = False,
        persist_dir: Optional[str] = None,
        **kwargs
    ):
        """初始化 FAISS 向量存储

        Args:
            dimension: 向量维度
            distance_metric: 距离度量方式
            index_type: 索引类型
            ivf_nlist: IVF 聚类中心数量
            ivf_nprobe: IVF 搜索时探测的聚类数量
            hnsw_m: HNSW 每个节点的连接数
            hnsw_ef_construction: HNSW 构建时的搜索范围
            hnsw_ef_search: HNSW 搜索时的搜索范围
            use_gpu: 是否使用 GPU 加速
            persist_dir: 持久化保存目录
        """
        super().__init__(dimension, distance_metric, index_type, **kwargs)

        # 保存参数
        self.ivf_nlist = ivf_nlist
        self.ivf_nprobe = ivf_nprobe
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construction = hnsw_ef_construction
        self.hnsw_ef_search = hnsw_ef_search
        self.use_gpu = use_gpu
        self.persist_dir = persist_dir

        # 初始化存储
        self._documents: Dict[str, Document] = {}  # id -> Document 映射
        self._id_to_idx: Dict[str, int] = {}       # id -> faiss index 映射
        self._idx_to_id: Dict[int, str] = {}       # faiss index -> id 映射
        self._next_idx = 0

        # 创建 FAISS 索引
        self._index = self._create_index()

        # GPU 支持（如果启用）
        if self.use_gpu and faiss.get_num_gpus() > 0:
            self._index = faiss.index_cpu_to_all_gpus(self._index)

    def _create_index(self) -> faiss.Index:
        """创建 FAISS 索引

        Returns:
            FAISS 索引对象

        Raises:
            ValueError: 如果配置无效
        """
        # 根据距离度量选择索引类型
        if self.distance_metric == DistanceMetric.COSINE:
            # 余弦相似度：先归一化，再用内积
            quantizer = self._create_base_index()
            # 注意：归一化在添加时处理
            return quantizer

        elif self.distance_metric == DistanceMetric.L2:
            return self._create_base_index()

        elif self.distance_metric == DistanceMetric.DOT_PRODUCT:
            # 内积：使用 IndexFlatIP
            if self.index_type == IndexType.FLAT:
                return faiss.IndexFlatIP(self.dimension)
            else:
                quantizer = faiss.IndexFlatIP(self.dimension)
                return self._wrap_with_index_type(quantizer)

        else:
            # 默认使用 L2
            return self._create_base_index()

    def _create_base_index(self) -> faiss.Index:
        """创建基础索引（根据 index_type）

        Returns:
            FAISS 索引对象
        """
        if self.index_type == IndexType.FLAT:
            # 暴力搜索（精确）
            return faiss.IndexFlatL2(self.dimension)

        elif self.index_type == IndexType.IVF:
            # IVF 索引
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(
                quantizer,
                self.dimension,
                self.ivf_nlist,
                faiss.METRIC_L2
            )
            index.nprobe = self.ivf_nprobe
            return index

        elif self.index_type == IndexType.HNSW:
            # HNSW 索引
            index = faiss.IndexHNSWFlat(self.dimension, self.hnsw_m)
            index.hnsw.efConstruction = self.hnsw_ef_construction
            index.hnsw.efSearch = self.hnsw_ef_search
            return index

        else:
            # 默认使用 Flat
            return faiss.IndexFlatL2(self.dimension)

    def _wrap_with_index_type(self, quantizer: faiss.Index) -> faiss.Index:
        """将量化器包装为指定的索引类型

        Args:
            quantizer: 基础量化器

        Returns:
            包装后的索引
        """
        if self.index_type == IndexType.IVF:
            index = faiss.IndexIVFFlat(
                quantizer,
                self.dimension,
                self.ivf_nlist,
                faiss.METRIC_INNER_PRODUCT
            )
            index.nprobe = self.ivf_nprobe
            return index
        else:
            return quantizer

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """归一化向量（用于余弦相似度）

        Args:
            vector: 输入向量

        Returns:
            归一化后的向量
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def add(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储

        Args:
            documents: 要添加的文档列表

        Returns:
            成功添加的文档ID列表
        """
        if not documents:
            return []

        # 验证并准备向量
        embeddings = []
        doc_ids = []

        for doc in documents:
            # 验证维度
            self.validate_embedding(doc.embedding)

            # 归一化（如果使用余弦相似度）
            if self.distance_metric == DistanceMetric.COSINE:
                embedding = self._normalize_vector(doc.embedding.copy())
            else:
                embedding = doc.embedding.copy()

            # 确保是 float32
            embedding = embedding.astype(np.float32)

            embeddings.append(embedding)
            doc_ids.append(doc.id)

            # 保存文档
            self._documents[doc.id] = doc

            # 映射关系
            idx = self._next_idx
            self._id_to_idx[doc.id] = idx
            self._idx_to_id[idx] = doc.id
            self._next_idx += 1

        # 转换为 numpy 数组
        embeddings_array = np.vstack(embeddings)

        # 训练索引（IVF 需要）
        if self.index_type == IndexType.IVF and not self._index.is_trained:
            # IVF 需要训练
            if len(embeddings_array) >= self.ivf_nlist:
                self._index.train(embeddings_array)
            # 如果数据量不足，先累积，稍后训练

        # 添加到 FAISS 索引
        if self._index.is_trained or self.index_type != IndexType.IVF:
            self._index.add(embeddings_array)

        return doc_ids

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

        Returns:
            按相似度排序的搜索结果列表
        """
        # 验证维度
        self.validate_embedding(query_embedding)

        # 如果没有文档，返回空
        if self.count() == 0:
            return []

        # 归一化（如果使用余弦相似度）
        if self.distance_metric == DistanceMetric.COSINE:
            query = self._normalize_vector(query_embedding.copy())
        else:
            query = query_embedding.copy()

        # 确保是 float32 和正确形状
        query = query.astype(np.float32).reshape(1, -1)

        # 搜索
        distances, indices = self._index.search(query, min(top_k, self.count()))

        # 转换结果
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            # 跳过无效索引
            if idx == -1:
                continue

            # 获取文档ID
            doc_id = self._idx_to_id.get(idx)
            if doc_id is None:
                continue

            # 获取文档
            doc = self._documents.get(doc_id)
            if doc is None:
                continue

            # 应用过滤器
            if filters:
                match = all(
                    doc.metadata.get(key) == value
                    for key, value in filters.items()
                )
                if not match:
                    continue

            # 计算相似度分数
            if self.distance_metric == DistanceMetric.COSINE:
                # 余弦相似度：[-1, 1] -> [0, 1]
                score = float((dist + 1) / 2)
            elif self.distance_metric == DistanceMetric.DOT_PRODUCT:
                # 内积：转换为 [0, 1]
                score = float(1 / (1 + np.exp(-dist)))  # sigmoid
            else:
                # L2 距离：转换为相似度
                score = float(1 / (1 + dist))

            results.append(SearchResult(
                document=doc,
                score=score,
                distance=float(dist),
                rank=rank
            ))

        return results[:top_k]

    def delete(self, doc_ids: List[str]) -> int:
        """删除文档

        注意：FAISS 不支持直接删除，这里采用标记删除
        实际索引在下次重建时更新

        Args:
            doc_ids: 要删除的文档ID列表

        Returns:
            成功删除的文档数量
        """
        count = 0
        for doc_id in doc_ids:
            if doc_id in self._documents:
                # 删除文档
                del self._documents[doc_id]

                # 删除映射
                if doc_id in self._id_to_idx:
                    idx = self._id_to_idx[doc_id]
                    del self._id_to_idx[doc_id]
                    del self._idx_to_id[idx]

                count += 1

        return count

    def update(self, documents: List[Document]) -> int:
        """更新文档

        实现方式：删除旧文档，添加新文档

        Args:
            documents: 要更新的文档列表

        Returns:
            成功更新的文档数量
        """
        count = 0
        docs_to_add = []

        for doc in documents:
            if doc.id in self._documents:
                # 删除旧文档
                self.delete([doc.id])
                docs_to_add.append(doc)
                count += 1

        # 添加新文档
        if docs_to_add:
            self.add(docs_to_add)

        return count

    def get(self, doc_ids: List[str]) -> List[Optional[Document]]:
        """根据ID获取文档

        Args:
            doc_ids: 文档ID列表

        Returns:
            文档列表（不存在的ID返回None）
        """
        return [self._documents.get(doc_id) for doc_id in doc_ids]

    def count(self) -> int:
        """获取存储中的文档总数

        Returns:
            文档总数
        """
        return len(self._documents)

    def clear(self) -> None:
        """清空所有文档"""
        self._documents.clear()
        self._id_to_idx.clear()
        self._idx_to_id.clear()
        self._next_idx = 0

        # 重建索引
        self._index = self._create_index()

    def rebuild_index(self) -> None:
        """重建索引

        用于删除操作后压缩索引，或更改索引配置
        """
        if not self._documents:
            self.clear()
            return

        # 保存所有文档
        docs = list(self._documents.values())

        # 清空
        self.clear()

        # 重新添加
        self.add(docs)

    def save(self, path: Optional[str] = None) -> str:
        """保存索引到磁盘

        Args:
            path: 保存路径（如果为None，使用 persist_dir）

        Returns:
            实际保存路径

        Raises:
            ValueError: 如果路径无效
        """
        if path is None:
            if self.persist_dir is None:
                raise ValueError("No persist_dir specified")
            path = self.persist_dir

        # 创建目录
        Path(path).mkdir(parents=True, exist_ok=True)

        # 保存 FAISS 索引
        index_path = os.path.join(path, "index.faiss")
        faiss.write_index(self._index, index_path)

        # 保存元数据
        metadata = {
            "documents": self._documents,
            "id_to_idx": self._id_to_idx,
            "idx_to_id": self._idx_to_id,
            "next_idx": self._next_idx,
            "config": {
                "dimension": self.dimension,
                "distance_metric": self.distance_metric.value,
                "index_type": self.index_type.value,
                "ivf_nlist": self.ivf_nlist,
                "ivf_nprobe": self.ivf_nprobe,
                "hnsw_m": self.hnsw_m,
                "hnsw_ef_construction": self.hnsw_ef_construction,
                "hnsw_ef_search": self.hnsw_ef_search,
            }
        }

        metadata_path = os.path.join(path, "metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)

        return path

    @classmethod
    def load(cls, path: str) -> "FaissVectorStore":
        """从磁盘加载索引

        Args:
            path: 加载路径

        Returns:
            FaissVectorStore 实例

        Raises:
            FileNotFoundError: 如果文件不存在
        """
        # 加载元数据
        metadata_path = os.path.join(path, "metadata.pkl")
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)

        config = metadata["config"]

        # 创建实例
        store = cls(
            dimension=config["dimension"],
            distance_metric=DistanceMetric(config["distance_metric"]),
            index_type=IndexType(config["index_type"]),
            ivf_nlist=config["ivf_nlist"],
            ivf_nprobe=config["ivf_nprobe"],
            hnsw_m=config["hnsw_m"],
            hnsw_ef_construction=config["hnsw_ef_construction"],
            hnsw_ef_search=config["hnsw_ef_search"],
            persist_dir=path,
        )

        # 加载 FAISS 索引
        index_path = os.path.join(path, "index.faiss")
        store._index = faiss.read_index(index_path)

        # 恢复元数据
        store._documents = metadata["documents"]
        store._id_to_idx = metadata["id_to_idx"]
        store._idx_to_id = metadata["idx_to_id"]
        store._next_idx = metadata["next_idx"]

        return store

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            统计信息字典
        """
        base_stats = super().get_stats()
        base_stats.update({
            "index_type": self.index_type.value,
            "is_trained": self._index.is_trained,
            "ntotal": self._index.ntotal,
        })

        # 添加索引特定信息
        if self.index_type == IndexType.IVF:
            base_stats["ivf_nlist"] = self.ivf_nlist
            base_stats["ivf_nprobe"] = self.ivf_nprobe

        elif self.index_type == IndexType.HNSW:
            base_stats["hnsw_m"] = self.hnsw_m
            base_stats["hnsw_ef_search"] = self.hnsw_ef_search

        return base_stats
