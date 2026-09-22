"""
Redis 缓存管理器
提供统一的缓存接口，支持查询结果缓存、文档元数据缓存、向量检索结果缓存
"""
import redis
from functools import wraps
import json
import hashlib
import pickle
from typing import Any, Optional, Callable, Union
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis 缓存管理器"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,
        max_connections: int = 50
    ):
        """
        初始化缓存管理器

        Args:
            redis_url: Redis 连接 URL
            default_ttl: 默认 TTL（秒）
            max_connections: 最大连接数
        """
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # 支持存储 pickle 数据
                max_connections=max_connections,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"✅ Redis 缓存已启用: {redis_url}")

        except Exception as e:
            self.redis_client = None
            self.enabled = False
            logger.warning(f"⚠️ Redis 连接失败，缓存已禁用: {e}")

        self.default_ttl = default_ttl

    def _generate_cache_key(
        self,
        prefix: str,
        func: Callable,
        args: tuple,
        kwargs: dict
    ) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            func: 函数对象
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            缓存键
        """
        # 构建键的组成部分
        func_name = f"{func.__module__}.{func.__name__}"

        # 序列化参数
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))

        # 生成哈希
        key_data = f"{func_name}:{args_str}:{kwargs_str}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()

        return f"{prefix}:{func_name}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回 None
        """
        if not self.enabled:
            return None

        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            ttl = ttl or self.default_ttl
            data = pickle.dumps(value)
            self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"缓存删除失败: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存

        Args:
            pattern: 键模式（支持 * 通配符）

        Returns:
            删除的键数量
        """
        if not self.enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"批量删除缓存失败: {e}")
            return 0

    def cache_result(
        self,
        ttl: Optional[int] = None,
        prefix: str = "cache",
        key_builder: Optional[Callable] = None
    ):
        """
        缓存装饰器

        Args:
            ttl: 缓存过期时间（秒）
            prefix: 缓存键前缀
            key_builder: 自定义键生成函数

        Example:
            @cache_manager.cache_result(ttl=600, prefix="projects")
            def get_project(project_id: int):
                return db.query(Project).get(project_id)
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # 生成缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(prefix, func, args, kwargs)

                # 尝试从缓存获取
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached

                # 执行函数
                result = func(*args, **kwargs)

                # 存入缓存
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存已更新: {cache_key}")

                return result

            # 添加缓存控制方法
            wrapper.invalidate = lambda *args, **kwargs: self.delete(
                key_builder(*args, **kwargs) if key_builder
                else self._generate_cache_key(prefix, func, args, kwargs)
            )

            wrapper.invalidate_all = lambda: self.delete_pattern(f"{prefix}:*")

            return wrapper
        return decorator

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Redis not available"
            }

        try:
            info = self.redis_client.info("stats")
            keyspace = self.redis_client.info("keyspace")

            return {
                "enabled": True,
                "total_keys": sum(
                    int(db_info.get('keys', 0))
                    for db_info in keyspace.values()
                ),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                )
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"enabled": True, "error": str(e)}


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    获取全局缓存管理器实例

    Returns:
        CacheManager 实例
    """
    global _cache_manager

    if _cache_manager is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_manager = CacheManager(redis_url=redis_url)

    return _cache_manager


# 便捷的装饰器
def cached(ttl: int = 300, prefix: str = "cache"):
    """
    便捷的缓存装饰器

    Example:
        @cached(ttl=600, prefix="documents")
        def get_document(doc_id: int):
            return db.query(Document).get(doc_id)
    """
    cache_manager = get_cache_manager()
    return cache_manager.cache_result(ttl=ttl, prefix=prefix)
