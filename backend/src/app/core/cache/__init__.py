"""
缓存系统 - 统一缓存接口
支持 MemoryCache 和 RedisCache 切换
"""
from .memory_cache import (
    CacheBackend,
    MemoryCache,
    cache,
    cache_async,
    generate_cache_key,
    CacheManager,
)

__all__ = [
    "CacheBackend",
    "MemoryCache",
    "cache",
    "cache_async",
    "generate_cache_key",
    "CacheManager",
    "get_cache_backend",
    "set_cache_backend",
    "cache_manager",
]

# 全局缓存实例（默认使用 MemoryCache）
_cache_backend: CacheBackend = MemoryCache()


def get_cache_backend() -> CacheBackend:
    """获取当前缓存后端"""
    return _cache_backend


def set_cache_backend(backend: CacheBackend):
    """设置缓存后端（支持运行时切换）"""
    global _cache_backend
    _cache_backend = backend


# 全局缓存管理器
cache_manager = CacheManager()


def init_cache_backend(use_redis: bool = False, redis_url: str = None) -> CacheBackend:
    """
    初始化缓存后端

    Args:
        use_redis: 是否使用 Redis 缓存
        redis_url: Redis 连接 URL

    Returns:
        CacheBackend 实例
    """
    global _cache_backend

    if use_redis:
        try:
            from .redis_cache import RedisCache
            _cache_backend = RedisCache(url=redis_url)
            print(f"✅ 使用 Redis 缓存: {redis_url}")
        except Exception as e:
            print(f"⚠️ Redis 连接失败，回退到内存缓存: {e}")
            _cache_backend = MemoryCache()
    else:
        _cache_backend = MemoryCache()
        print("✅ 使用内存缓存")

    return _cache_backend
