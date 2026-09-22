"""
LRU 缓存实现

基于最近最少使用（Least Recently Used）策略
"""

from typing import Optional, Any, OrderedDict
from collections import OrderedDict as OrderedDictType
import time
import numpy as np

from .base import VectorCache, CacheEntry


class LRUCache(VectorCache):
    """LRU 缓存实现

    使用 OrderedDict 实现 O(1) 的访问和更新
    支持精确匹配和语义缓存两种模式

    特性：
    - O(1) 查询和插入
    - 自动淘汰最久未使用的条目
    - 支持 TTL 过期
    - 可选语义缓存（相似查询命中）

    示例：
        # 精确匹配缓存
        cache = LRUCache(max_size=100, ttl=300)

        # 语义缓存
        cache = LRUCache(
            max_size=100,
            enable_semantic=True,
            semantic_threshold=0.95
        )
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        enable_semantic: bool = False,
        semantic_threshold: float = 0.95
    ):
        """初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间（秒）
            enable_semantic: 是否启用语义缓存
            semantic_threshold: 语义相似度阈值
        """
        super().__init__(max_size, ttl, enable_semantic, semantic_threshold)

        # 使用 OrderedDict 实现 LRU
        self._cache: OrderedDictType[str, CacheEntry] = OrderedDict()

    def get(self, query_embedding: np.ndarray, **kwargs) -> Optional[Any]:
        """获取缓存值

        Args:
            query_embedding: 查询向量
            **kwargs: 额外的查询参数

        Returns:
            缓存的搜索结果，如果未命中返回 None
        """
        # 1. 尝试精确匹配
        key = self._generate_key(query_embedding, **kwargs)

        if key in self._cache:
            entry = self._cache[key]

            # 检查是否过期
            if self._is_expired(entry):
                del self._cache[key]
                self.misses += 1
                return None

            # 命中：移到末尾（表示最近使用）
            self._cache.move_to_end(key)
            entry.hits += 1
            self.hits += 1
            return entry.value

        # 2. 如果启用语义缓存，尝试相似查询
        if self.enable_semantic:
            similar_entry = self._find_similar(query_embedding, **kwargs)
            if similar_entry is not None:
                # 语义缓存命中
                similar_entry.hits += 1
                self.hits += 1
                return similar_entry.value

        # 3. 未命中
        self.misses += 1
        return None

    def set(self, query_embedding: np.ndarray, value: Any, **kwargs) -> None:
        """设置缓存值

        Args:
            query_embedding: 查询向量
            value: 搜索结果
            **kwargs: 额外的查询参数
        """
        # 如果 max_size 为 0，不缓存
        if self.max_size == 0:
            return

        key = self._generate_key(query_embedding, **kwargs)

        # 如果已存在，更新
        if key in self._cache:
            self._cache[key].value = value
            self._cache[key].timestamp = time.time()
            self._cache.move_to_end(key)
            return

        # 检查是否需要淘汰
        if len(self._cache) >= self.max_size:
            # 淘汰最久未使用的条目（第一个）
            self._cache.popitem(last=False)
            self.evictions += 1

        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            hits=0,
            query_embedding=query_embedding.copy() if self.enable_semantic else None
        )
        self._cache[key] = entry

    def _find_similar(self, query_embedding: np.ndarray, **kwargs) -> Optional[CacheEntry]:
        """查找相似的缓存条目（语义缓存）

        Args:
            query_embedding: 查询向量
            **kwargs: 查询参数（必须完全匹配）

        Returns:
            相似的缓存条目，如果未找到返回 None
        """
        # 生成当前查询的参数哈希（用于匹配）
        current_key = self._generate_key(query_embedding, **kwargs)
        current_params_hash = current_key.split('_')[1] if '_' in current_key else '0'

        for entry in self._cache.values():
            # 检查是否过期
            if self._is_expired(entry):
                continue

            # 检查参数是否匹配
            entry_params_hash = entry.key.split('_')[1] if '_' in entry.key else '0'
            if entry_params_hash != current_params_hash:
                continue

            # 检查向量相似度
            if entry.query_embedding is not None:
                similarity = self._compute_similarity(
                    query_embedding,
                    entry.query_embedding
                )

                if similarity >= self.semantic_threshold:
                    return entry

        return None

    def _params_match(self, entry_key: str, kwargs: dict) -> bool:
        """检查缓存条目的参数是否匹配

        Args:
            entry_key: 缓存条目的键
            kwargs: 当前查询参数

        Returns:
            True 如果参数匹配
        """
        # 从 key 中提取参数哈希
        parts = entry_key.split('_')
        if len(parts) != 2:
            return False

        entry_kwargs_hash = int(parts[1])
        query_kwargs_hash = hash(frozenset(kwargs.items()) if kwargs else 0)

        return entry_kwargs_hash == query_kwargs_hash

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def size(self) -> int:
        """获取当前缓存条目数

        Returns:
            缓存条目数量
        """
        return len(self._cache)

    def evict_expired(self) -> int:
        """主动淘汰过期条目

        Returns:
            淘汰的条目数量
        """
        if self.ttl is None:
            return 0

        expired_keys = []
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_top_entries(self, n: int = 10) -> list:
        """获取命中次数最多的前 N 个条目

        Args:
            n: 返回的条目数量

        Returns:
            条目列表，按命中次数排序
        """
        entries = list(self._cache.values())
        entries.sort(key=lambda e: e.hits, reverse=True)
        return entries[:n]

    def get_oldest_entries(self, n: int = 10) -> list:
        """获取最久未使用的前 N 个条目

        Args:
            n: 返回的条目数量

        Returns:
            条目列表，按时间戳排序
        """
        entries = list(self._cache.values())
        entries.sort(key=lambda e: e.timestamp)
        return entries[:n]
