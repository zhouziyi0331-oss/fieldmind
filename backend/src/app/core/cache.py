"""
缓存系统 - 提升系统性能
"""
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import json
import pickle
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheBackend:
    """缓存后端接口"""

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        raise NotImplementedError

    def delete(self, key: str):
        """删除缓存"""
        raise NotImplementedError

    def clear(self):
        """清空缓存"""
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """内存缓存实现"""

    def __init__(self):
        self._cache = {}
        self._expire_times = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 检查是否过期
        if key in self._expire_times:
            if datetime.now() > self._expire_times[key]:
                self.delete(key)
                return None

        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存，ttl单位为秒"""
        self._cache[key] = value
        self._expire_times[key] = datetime.now() + timedelta(seconds=ttl)

        # 清理过期缓存
        self._cleanup_expired()

    def delete(self, key: str):
        """删除缓存"""
        self._cache.pop(key, None)
        self._expire_times.pop(key, None)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expire_times.clear()

    def _cleanup_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, expire_time in self._expire_times.items()
            if now > expire_time
        ]

        for key in expired_keys:
            self.delete(key)

    def stats(self):
        """缓存统计"""
        self._cleanup_expired()
        return {
            "total_keys": len(self._cache),
            "memory_usage_estimate": sum(
                len(pickle.dumps(v)) for v in self._cache.values()
            )
        }


# 全局缓存实例
_cache_backend: CacheBackend = MemoryCache()


def get_cache_backend() -> CacheBackend:
    """获取缓存后端"""
    return _cache_backend


def set_cache_backend(backend: CacheBackend):
    """设置缓存后端"""
    global _cache_backend
    _cache_backend = backend


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    # 将参数序列化为字符串
    key_data = {
        "args": args,
        "kwargs": kwargs
    }

    # 使用MD5生成短key
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    用法:
    @cache(ttl=600, key_prefix="user")
    def get_user(user_id: int):
        return db.query(User).get(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # 尝试从缓存获取
            cached_value = _cache_backend.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 保存到缓存
            _cache_backend.set(cache_key, result, ttl)
            logger.debug(f"缓存保存: {cache_key}")

            return result

        # 添加清除缓存方法
        def clear_cache(*args, **kwargs):
            """清除特定参数的缓存"""
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            _cache_backend.delete(cache_key)

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator


def cache_async(ttl: int = 300, key_prefix: str = ""):
    """
    异步缓存装饰器

    用法:
    @cache_async(ttl=600, key_prefix="analysis")
    async def get_analysis(analysis_id: int):
        return await db.query(Analysis).get(analysis_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # 尝试从缓存获取
            cached_value = _cache_backend.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 保存到缓存
            _cache_backend.set(cache_key, result, ttl)
            logger.debug(f"缓存保存: {cache_key}")

            return result

        # 添加清除缓存方法
        def clear_cache(*args, **kwargs):
            """清除特定参数的缓存"""
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            _cache_backend.delete(cache_key)

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator


class CacheManager:
    """缓存管理器"""

    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or get_cache_backend()

    def invalidate_pattern(self, pattern: str):
        """
        根据模式失效缓存

        注意: MemoryCache不支持模式匹配，需要Redis等支持
        """
        # 简单实现：清空所有缓存
        logger.warning("MemoryCache不支持模式匹配，清空所有缓存")
        self.backend.clear()

    def invalidate_project(self, project_id: int):
        """失效项目相关的所有缓存"""
        self.invalidate_pattern(f"*:project_id:{project_id}:*")

    def invalidate_user(self, user_id: str):
        """失效用户相关的所有缓存"""
        self.invalidate_pattern(f"*:user_id:{user_id}:*")

    def get_stats(self):
        """获取缓存统计"""
        if hasattr(self.backend, 'stats'):
            return self.backend.stats()
        return {}


# 全局缓存管理器
cache_manager = CacheManager()
