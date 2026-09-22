"""
向量存储抽象接口

提供统一的向量存储抽象层，支持多种后端实现（FAISS、Chroma等）
遵循开闭原则，便于扩展新的向量数据库后端
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import numpy as np


class DistanceMetric(Enum):
    """距离度量方式"""
    COSINE = "cosine"           # 余弦相似度
    EUCLIDEAN = "euclidean"     # 欧几里得距离
    DOT_PRODUCT = "dot_product" # 点积
    L2 = "l2"                   # L2范数


class IndexType(Enum):
    """索引类型"""
    FLAT = "flat"               # 暴力搜索（精确但慢）
    IVF = "ivf"                 # 倒排文件索引
    HNSW = "hnsw"               # 层次化可导航小世界图
    LSH = "lsh"                 # 局部敏感哈希


@dataclass
class Document:
    """文档数据类

    Attributes:
        id: 文档唯一标识符
        content: 文档文本内容
        embedding: 向量表示（numpy数组）
        metadata: 元数据字典（如来源、时间戳等）
    """
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证数据完整性"""
        if not self.id:
            raise ValueError("Document id cannot be empty")
        if not isinstance(self.embedding, np.ndarray):
            raise TypeError("Embedding must be a numpy array")
        if len(self.embedding.shape) != 1:
            raise ValueError("Embedding must be 1-dimensional")


@dataclass
class SearchResult:
    """搜索结果数据类

    Attributes:
        document: 匹配的文档
        score: 相似度分数（越高越相似）
        distance: 距离值（越小越相似）
        rank: 排名位置（从0开始）
    """
    document: Document
    score: float
    distance: float
    rank: int = 0

    def __post_init__(self):
        """验证分数范围"""
        if not 0 <= self.score <= 1:
            # 某些情况下score可能超出[0,1]，这里不强制限制，只警告
            pass


class VectorStore(ABC):
    """向量存储抽象基类

    定义所有向量存储后端必须实现的核心接口
    支持CRUD操作、批量操作、过滤搜索等
    """

    def __init__(
        self,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_type: IndexType = IndexType.FLAT,
        **kwargs
    ):
        """初始化向量存储

        Args:
            dimension: 向量维度
            distance_metric: 距离度量方式
            index_type: 索引类型
            **kwargs: 后端特定配置参数
        """
        self.dimension = dimension
        self.distance_metric = distance_metric
        self.index_type = index_type
        self.config = kwargs

    @abstractmethod
    def add(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储

        Args:
            documents: 要添加的文档列表

        Returns:
            成功添加的文档ID列表

        Raises:
            ValueError: 如果文档格式无效
            RuntimeError: 如果添加操作失败
        """
        pass

    @abstractmethod
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
            filters: 元数据过滤条件（如 {"source": "pdf", "year": 2024}）

        Returns:
            按相似度排序的搜索结果列表

        Raises:
            ValueError: 如果查询向量维度不匹配
            RuntimeError: 如果搜索操作失败
        """
        pass

    @abstractmethod
    def delete(self, doc_ids: List[str]) -> int:
        """删除文档

        Args:
            doc_ids: 要删除的文档ID列表

        Returns:
            成功删除的文档数量

        Raises:
            RuntimeError: 如果删除操作失败
        """
        pass

    @abstractmethod
    def update(self, documents: List[Document]) -> int:
        """更新文档

        Args:
            documents: 要更新的文档列表（根据ID匹配）

        Returns:
            成功更新的文档数量

        Raises:
            ValueError: 如果文档格式无效
            RuntimeError: 如果更新操作失败
        """
        pass

    @abstractmethod
    def get(self, doc_ids: List[str]) -> List[Optional[Document]]:
        """根据ID获取文档

        Args:
            doc_ids: 文档ID列表

        Returns:
            文档列表（不存在的ID返回None）
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """获取存储中的文档总数

        Returns:
            文档总数
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有文档

        警告：此操作不可逆
        """
        pass

    def batch_search(
        self,
        query_embeddings: List[np.ndarray],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[List[SearchResult]]:
        """批量搜索（默认实现为循环调用单次搜索）

        子类可以重写此方法以提供更高效的批量搜索

        Args:
            query_embeddings: 查询向量列表
            top_k: 每个查询返回前K个结果
            filters: 元数据过滤条件

        Returns:
            每个查询的搜索结果列表
        """
        results = []
        for embedding in query_embeddings:
            results.append(self.search(embedding, top_k, filters))
        return results

    def exists(self, doc_id: str) -> bool:
        """检查文档是否存在

        Args:
            doc_id: 文档ID

        Returns:
            True如果文档存在，否则False
        """
        docs = self.get([doc_id])
        return docs[0] is not None

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            统计信息字典（文档数、索引类型、内存占用等）
        """
        return {
            "count": self.count(),
            "dimension": self.dimension,
            "distance_metric": self.distance_metric.value,
            "index_type": self.index_type.value,
        }

    def validate_embedding(self, embedding: np.ndarray) -> None:
        """验证向量维度

        Args:
            embedding: 要验证的向量

        Raises:
            ValueError: 如果维度不匹配
        """
        if embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embedding.shape[0]}"
            )

    def __len__(self) -> int:
        """支持 len() 操作"""
        return self.count()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"dimension={self.dimension}, "
            f"count={self.count()}, "
            f"metric={self.distance_metric.value}, "
            f"index={self.index_type.value})"
        )
