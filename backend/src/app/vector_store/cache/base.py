"""
向量搜索缓存抽象接口

提供查询缓存和语义缓存功能
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Tuple
from dataclasses import dataclass
import time
import numpy as np


@dataclass
class CacheEntry:
    """缓存条目

    Attributes:
        key: 缓存键（查询向量的哈希或ID）
        value: 缓存值（搜索结果）
        timestamp: 缓存时间戳
        hits: 命中次数
        query_embedding: 查询向量（用于语义缓存）
    """
    key: str
    value: Any
    timestamp: float
    hits: int = 0
    query_embedding: Optional[np.ndarray] = None


class VectorCache(ABC):
    """向量搜索缓存抽象基类

    提供两种缓存策略：
    1. 精确匹配缓存：查询向量完全相同
    2. 语义缓存：查询向量相似（余弦相似度 > 阈值）
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        enable_semantic: bool = False,
        semantic_threshold: float = 0.95
    ):
        """初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间（秒），None 表示永不过期
            enable_semantic: 是否启用语义缓存
            semantic_threshold: 语义相似度阈值
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enable_semantic = enable_semantic
        self.semantic_threshold = semantic_threshold

        # 统计信息
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @abstractmethod
    def get(self, query_embedding: np.ndarray, **kwargs) -> Optional[Any]:
        """获取缓存值

        Args:
            query_embedding: 查询向量
            **kwargs: 额外的查询参数（如 top_k, filters）

        Returns:
            缓存的搜索结果，如果未命中返回 None
        """
        pass

    @abstractmethod
    def set(self, query_embedding: np.ndarray, value: Any, **kwargs) -> None:
        """设置缓存值

        Args:
            query_embedding: 查询向量
            value: 搜索结果
            **kwargs: 额外的查询参数
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有缓存"""
        pass

    @abstractmethod
    def size(self) -> int:
        """获取当前缓存条目数

        Returns:
            缓存条目数量
        """
        pass

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否过期

        Args:
            entry: 缓存条目

        Returns:
            True 如果已过期
        """
        if self.ttl is None:
            return False
        return (time.time() - entry.timestamp) > self.ttl

    def _generate_key(self, query_embedding: np.ndarray, **kwargs) -> str:
        """生成缓存键

        Args:
            query_embedding: 查询向量
            **kwargs: 额外参数

        Returns:
            缓存键字符串
        """
        # 使用向量的哈希 + 参数的哈希
        vector_hash = hash(query_embedding.tobytes())

        # 处理嵌套字典的哈希
        if kwargs:
            # 将字典转换为可哈希的格式
            kwargs_items = []
            for k, v in kwargs.items():
                if isinstance(v, dict):
                    # 递归处理嵌套字典
                    v = frozenset(v.items())
                elif isinstance(v, (list, tuple)):
                    v = tuple(v)
                kwargs_items.append((k, v))
            kwargs_hash = hash(frozenset(kwargs_items))
        else:
            kwargs_hash = 0

        return f"{vector_hash}_{kwargs_hash}"

    def _compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            余弦相似度 [0, 1]
        """
        # 归一化
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

        # 余弦相似度
        similarity = np.dot(vec1_norm, vec2_norm)
        return float(similarity)

    def get_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "size": self.size(),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "ttl": self.ttl,
            "enable_semantic": self.enable_semantic,
            "semantic_threshold": self.semantic_threshold,
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def __len__(self) -> int:
        """支持 len() 操作"""
        return self.size()

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (
            f"{self.__class__.__name__}("
            f"size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.2%})"
        )
