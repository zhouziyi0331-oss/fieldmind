"""
测试 LRU 缓存实现

验证缓存功能和性能
"""

import pytest
import numpy as np
import time

from app.vector_store.cache import LRUCache, CacheEntry


class TestLRUCacheBasic:
    """测试基本功能"""

    @pytest.fixture
    def cache(self):
        """创建测试缓存"""
        return LRUCache(max_size=10)

    @pytest.fixture
    def sample_query(self):
        """创建示例查询向量"""
        return np.random.rand(128).astype(np.float32)

    @pytest.fixture
    def sample_result(self):
        """创建示例搜索结果"""
        return [{"id": "doc1", "score": 0.95}, {"id": "doc2", "score": 0.85}]

    def test_create_cache(self):
        """测试创建缓存"""
        cache = LRUCache(max_size=100, ttl=300)
        assert cache.max_size == 100
        assert cache.ttl == 300
        assert cache.size() == 0

    def test_set_and_get(self, cache, sample_query, sample_result):
        """测试设置和获取"""
        cache.set(sample_query, sample_result)

        assert cache.size() == 1

        result = cache.get(sample_query)
        assert result == sample_result
        assert cache.hits == 1
        assert cache.misses == 0

    def test_cache_miss(self, cache, sample_query):
        """测试缓存未命中"""
        result = cache.get(sample_query)

        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0

    def test_multiple_queries(self, cache):
        """测试多个查询"""
        queries = [np.random.rand(128).astype(np.float32) for _ in range(5)]
        results = [f"result_{i}" for i in range(5)]

        # 设置
        for q, r in zip(queries, results):
            cache.set(q, r)

        assert cache.size() == 5

        # 获取
        for q, r in zip(queries, results):
            cached = cache.get(q)
            assert cached == r

    def test_lru_eviction(self):
        """测试 LRU 淘汰策略"""
        cache = LRUCache(max_size=3)

        # 添加 3 个条目
        for i in range(3):
            query = np.array([i] * 128, dtype=np.float32)
            cache.set(query, f"result_{i}")

        assert cache.size() == 3
        assert cache.evictions == 0

        # 添加第 4 个，应该淘汰最早的
        query_4 = np.array([4] * 128, dtype=np.float32)
        cache.set(query_4, "result_4")

        assert cache.size() == 3
        assert cache.evictions == 1

        # 第一个应该被淘汰
        query_0 = np.array([0] * 128, dtype=np.float32)
        result = cache.get(query_0)
        assert result is None

    def test_lru_order(self):
        """测试 LRU 顺序"""
        cache = LRUCache(max_size=3)

        # 添加 3 个条目
        queries = []
        for i in range(3):
            query = np.array([i] * 128, dtype=np.float32)
            queries.append(query)
            cache.set(query, f"result_{i}")

        # 访问第一个（应该移到最后）
        cache.get(queries[0])

        # 添加新条目，应该淘汰第二个（queries[1]）
        query_new = np.array([99] * 128, dtype=np.float32)
        cache.set(query_new, "result_new")

        # 验证
        assert cache.get(queries[0]) is not None  # 仍在
        assert cache.get(queries[1]) is None      # 被淘汰
        assert cache.get(queries[2]) is not None  # 仍在

    def test_update_existing(self, cache, sample_query):
        """测试更新已存在的条目"""
        cache.set(sample_query, "result_1")
        cache.set(sample_query, "result_2")

        assert cache.size() == 1
        assert cache.get(sample_query) == "result_2"

    def test_clear(self, cache):
        """测试清空缓存"""
        for i in range(5):
            query = np.random.rand(128).astype(np.float32)
            cache.set(query, f"result_{i}")

        assert cache.size() == 5

        cache.clear()
        assert cache.size() == 0


class TestLRUCacheTTL:
    """测试 TTL 过期功能"""

    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        cache = LRUCache(max_size=10, ttl=0.1)  # 0.1 秒过期

        query = np.random.rand(128).astype(np.float32)
        cache.set(query, "result")

        # 立即获取应该命中
        assert cache.get(query) == "result"

        # 等待过期
        time.sleep(0.15)

        # 应该已过期
        assert cache.get(query) is None

    def test_no_ttl(self):
        """测试无 TTL（永不过期）"""
        cache = LRUCache(max_size=10, ttl=None)

        query = np.random.rand(128).astype(np.float32)
        cache.set(query, "result")

        # 等待一段时间
        time.sleep(0.1)

        # 应该仍然存在
        assert cache.get(query) == "result"

    def test_evict_expired(self):
        """测试主动淘汰过期条目"""
        cache = LRUCache(max_size=10, ttl=0.1)

        # 添加多个条目
        for i in range(5):
            query = np.random.rand(128).astype(np.float32)
            cache.set(query, f"result_{i}")

        assert cache.size() == 5

        # 等待过期
        time.sleep(0.15)

        # 主动淘汰
        evicted = cache.evict_expired()
        assert evicted == 5
        assert cache.size() == 0


class TestLRUCacheSemantic:
    """测试语义缓存功能"""

    def test_semantic_cache_enabled(self):
        """测试启用语义缓存"""
        cache = LRUCache(
            max_size=10,
            enable_semantic=True,
            semantic_threshold=0.95
        )

        # 添加一个查询
        query1 = np.array([1.0] * 128, dtype=np.float32)
        cache.set(query1, "result_1")

        # 创建非常相似的查询（几乎相同）
        query2 = query1 + np.random.rand(128).astype(np.float32) * 0.01

        # 应该命中语义缓存
        result = cache.get(query2)
        assert result == "result_1"
        assert cache.hits == 1

    def test_semantic_cache_threshold(self):
        """测试语义缓存阈值"""
        cache = LRUCache(
            max_size=10,
            enable_semantic=True,
            semantic_threshold=0.99  # 高阈值
        )

        # 添加查询
        query1 = np.random.rand(128).astype(np.float32)
        cache.set(query1, "result_1")

        # 创建不太相似的查询
        query2 = np.random.rand(128).astype(np.float32)

        # 应该未命中
        result = cache.get(query2)
        assert result is None
        assert cache.misses == 1

    def test_semantic_cache_disabled(self):
        """测试禁用语义缓存"""
        cache = LRUCache(
            max_size=10,
            enable_semantic=False
        )

        # 添加查询
        query1 = np.array([1.0] * 128, dtype=np.float32)
        cache.set(query1, "result_1")

        # 创建相似但不完全相同的查询
        query2 = query1 + 0.001

        # 不应该命中（需要精确匹配）
        result = cache.get(query2)
        assert result is None

    def test_semantic_with_params(self):
        """测试语义缓存与参数匹配"""
        cache = LRUCache(
            max_size=10,
            enable_semantic=True,
            semantic_threshold=0.95
        )

        query = np.array([1.0] * 128, dtype=np.float32)

        # 设置带参数的缓存
        cache.set(query, "result_1", top_k=5, filters={"category": "A"})

        # 相似查询，相同参数 - 应该命中
        similar_query = query + 0.01
        result = cache.get(similar_query, top_k=5, filters={"category": "A"})
        assert result == "result_1"

        # 相似查询，不同参数 - 不应该命中
        result = cache.get(similar_query, top_k=10)
        assert result is None


class TestLRUCacheStats:
    """测试统计信息功能"""

    def test_get_stats(self):
        """测试获取统计信息"""
        cache = LRUCache(max_size=100, ttl=300)

        # 添加一些数据
        for i in range(5):
            query = np.random.rand(128).astype(np.float32)
            cache.set(query, f"result_{i}")

        # 触发一些命中和未命中
        query = np.random.rand(128).astype(np.float32)
        cache.set(query, "result")
        cache.get(query)  # 命中
        cache.get(np.random.rand(128).astype(np.float32))  # 未命中

        stats = cache.get_stats()

        assert stats["size"] == 6
        assert stats["max_size"] == 100
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["ttl"] == 300

    def test_reset_stats(self):
        """测试重置统计信息"""
        cache = LRUCache(max_size=10)

        query = np.random.rand(128).astype(np.float32)
        cache.set(query, "result")
        cache.get(query)

        assert cache.hits == 1

        cache.reset_stats()

        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.evictions == 0

    def test_get_top_entries(self):
        """测试获取最热门条目"""
        cache = LRUCache(max_size=10)

        # 添加条目并访问不同次数
        queries = []
        for i in range(5):
            query = np.random.rand(128).astype(np.float32)
            queries.append(query)
            cache.set(query, f"result_{i}")

        # 访问不同次数
        cache.get(queries[0])
        cache.get(queries[0])
        cache.get(queries[0])  # 3 次
        cache.get(queries[1])
        cache.get(queries[1])  # 2 次
        cache.get(queries[2])  # 1 次

        top = cache.get_top_entries(n=3)

        assert len(top) == 3
        assert top[0].hits == 3
        assert top[1].hits == 2
        assert top[2].hits == 1

    def test_get_oldest_entries(self):
        """测试获取最旧条目"""
        cache = LRUCache(max_size=10)

        # 依次添加条目
        for i in range(5):
            query = np.random.rand(128).astype(np.float32)
            cache.set(query, f"result_{i}")
            time.sleep(0.01)  # 确保时间戳不同

        oldest = cache.get_oldest_entries(n=2)

        assert len(oldest) == 2
        # 第一个应该是最旧的
        assert oldest[0].timestamp < oldest[1].timestamp


class TestLRUCacheEdgeCases:
    """测试边界情况"""

    def test_max_size_zero(self):
        """测试最大大小为 0"""
        cache = LRUCache(max_size=0)

        query = np.random.rand(128).astype(np.float32)
        cache.set(query, "result")

        # 应该立即被淘汰
        assert cache.size() == 0

    def test_max_size_one(self):
        """测试最大大小为 1"""
        cache = LRUCache(max_size=1)

        query1 = np.random.rand(128).astype(np.float32)
        query2 = np.random.rand(128).astype(np.float32)

        cache.set(query1, "result_1")
        assert cache.size() == 1

        cache.set(query2, "result_2")
        assert cache.size() == 1
        assert cache.evictions == 1

    def test_empty_params(self):
        """测试空参数"""
        cache = LRUCache(max_size=10)

        query = np.random.rand(128).astype(np.float32)

        # 无参数
        cache.set(query, "result_1")
        result = cache.get(query)
        assert result == "result_1"

        # 空字典参数
        cache.set(query, "result_2", **{})
        result = cache.get(query, **{})
        assert result == "result_2"

    def test_len_and_repr(self):
        """测试 len() 和 repr()"""
        cache = LRUCache(max_size=10)

        for i in range(3):
            query = np.random.rand(128).astype(np.float32)
            cache.set(query, f"result_{i}")

        assert len(cache) == 3

        repr_str = repr(cache)
        assert "LRUCache" in repr_str
        assert "3/10" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
