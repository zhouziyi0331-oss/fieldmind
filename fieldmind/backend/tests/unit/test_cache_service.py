"""
缓存服务单元测试
"""

import pytest
from app.services.cache_service import CacheService, cached, invalidate_cache, CacheKeys


@pytest.mark.unit
class TestCacheService:
    """缓存服务测试"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        cache = CacheService()
        assert cache is not None
        assert cache.memory_cache is not None

    def test_cache_get_nonexistent_key(self):
        """测试获取不存在的键"""
        cache = CacheService()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_set_and_get(self):
        """测试设置和获取缓存"""
        cache = CacheService()
        cache.set("test_key", {"data": "test_value"}, ttl=300)
        result = cache.get("test_key")
        assert result == {"data": "test_value"}

    def test_cache_set_with_complex_value(self):
        """测试设置复杂数据结构"""
        cache = CacheService()
        complex_value = {
            "id": 1,
            "name": "Test",
            "nested": {
                "items": [1, 2, 3],
                "metadata": {"created": "2024-01-01"}
            }
        }
        cache.set("complex_key", complex_value)
        result = cache.get("complex_key")
        assert result == complex_value

    def test_cache_delete(self):
        """测试删除缓存"""
        cache = CacheService()
        cache.set("delete_key", "value")
        assert cache.get("delete_key") == "value"

        cache.delete("delete_key")
        assert cache.get("delete_key") is None

    def test_cache_delete_pattern(self):
        """测试模式匹配删除"""
        cache = CacheService()
        cache.set("projects:1", "data1")
        cache.set("projects:2", "data2")
        cache.set("users:1", "data3")

        deleted_count = cache.delete_pattern("projects:*")
        assert deleted_count == 2
        assert cache.get("projects:1") is None
        assert cache.get("projects:2") is None
        assert cache.get("users:1") == "data3"

    def test_cache_clear_all(self):
        """测试清空所有缓存"""
        cache = CacheService()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear_all()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """测试获取缓存统计"""
        cache = CacheService()
        stats = cache.get_stats()
        assert "enabled" in stats
        assert "backend" in stats

    def test_cache_health_check(self):
        """测试健康检查"""
        cache = CacheService()
        health = cache.health_check()
        assert "status" in health
        assert health["status"] == "healthy"


@pytest.mark.unit
class TestCacheDecorators:
    """缓存装饰器测试"""

    def test_cached_decorator(self):
        """测试缓存装饰器"""
        call_count = 0

        @cached(ttl=300, key_prefix="test")
        def expensive_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            return arg1 + arg2

        # 第一次调用，应该执行函数
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # 第二次调用相同参数，应该从缓存获取
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 没有增加

        # 不同参数，应该重新执行
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    def test_invalidate_cache_decorator(self):
        """测试缓存失效装饰器"""
        cache = CacheService()
        cache.set("test:data", "original_value")

        @invalidate_cache("test:*")
        def update_data():
            return "updated"

        assert cache.get("test:data") == "original_value"

        # 调用函数应该失效缓存
        update_data()
        assert cache.get("test:data") is None


@pytest.mark.unit
class TestCacheKeys:
    """缓存键常量测试"""

    def test_cache_keys_defined(self):
        """测试缓存键常量是否定义"""
        assert hasattr(CacheKeys, 'PROJECT_LIST')
        assert hasattr(CacheKeys, 'DATA_QUALITY')
        assert hasattr(CacheKeys, 'KNOWLEDGE_GRAPH')
        assert hasattr(CacheKeys, 'USER_PERMISSIONS')

    def test_cache_keys_are_strings(self):
        """测试缓存键常量是否为字符串"""
        assert isinstance(CacheKeys.PROJECT_LIST, str)
        assert isinstance(CacheKeys.DATA_QUALITY, str)
        assert isinstance(CacheKeys.KNOWLEDGE_GRAPH, str)
