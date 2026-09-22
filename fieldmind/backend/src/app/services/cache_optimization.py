"""
缓存优化服务

为规范化结果、知识图谱查询等提供缓存支持
"""

import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务"""

    def __init__(self, redis_client=None):
        """
        初始化缓存服务

        Args:
            redis_client: Redis客户端（可选，如果不提供则使用内存缓存）
        """
        self.redis = redis_client
        self.memory_cache = {}  # 降级方案：内存缓存

    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        return f"fieldmind:{prefix}:{identifier}"

    def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            prefix: 缓存前缀（如 'normalization', 'kg_query'）
            identifier: 标识符（如 file_id, query_hash）

        Returns:
            缓存的值，如果不存在则返回 None
        """
        cache_key = self._get_cache_key(prefix, identifier)

        try:
            if self.redis:
                # 使用 Redis
                data = self.redis.get(cache_key)
                if data:
                    logger.debug(f"✅ 缓存命中: {cache_key}")
                    return json.loads(data)
            else:
                # 使用内存缓存
                if cache_key in self.memory_cache:
                    logger.debug(f"✅ 内存缓存命中: {cache_key}")
                    return self.memory_cache[cache_key]

        except Exception as e:
            logger.error(f"获取缓存失败: {e}")

        logger.debug(f"❌ 缓存未命中: {cache_key}")
        return None

    def set(
        self,
        prefix: str,
        identifier: str,
        value: Any,
        ttl_seconds: int = 3600
    ):
        """
        设置缓存

        Args:
            prefix: 缓存前缀
            identifier: 标识符
            value: 要缓存的值
            ttl_seconds: 过期时间（秒），默认1小时
        """
        cache_key = self._get_cache_key(prefix, identifier)

        try:
            if self.redis:
                # 使用 Redis
                self.redis.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(value, ensure_ascii=False)
                )
                logger.debug(f"💾 Redis缓存已设置: {cache_key} (TTL: {ttl_seconds}s)")
            else:
                # 使用内存缓存（简化版，无过期）
                self.memory_cache[cache_key] = value
                logger.debug(f"💾 内存缓存已设置: {cache_key}")

        except Exception as e:
            logger.error(f"设置缓存失败: {e}")

    def delete(self, prefix: str, identifier: str):
        """
        删除缓存

        Args:
            prefix: 缓存前缀
            identifier: 标识符
        """
        cache_key = self._get_cache_key(prefix, identifier)

        try:
            if self.redis:
                self.redis.delete(cache_key)
            else:
                self.memory_cache.pop(cache_key, None)

            logger.debug(f"🗑️  缓存已删除: {cache_key}")

        except Exception as e:
            logger.error(f"删除缓存失败: {e}")

    def clear_prefix(self, prefix: str):
        """
        清除指定前缀的所有缓存

        Args:
            prefix: 缓存前缀
        """
        try:
            if self.redis:
                pattern = f"fieldmind:{prefix}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"🗑️  清除了 {len(keys)} 个缓存: {prefix}")
            else:
                # 内存缓存
                prefix_key = f"fieldmind:{prefix}:"
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if k.startswith(prefix_key)
                ]
                for k in keys_to_delete:
                    del self.memory_cache[k]
                logger.info(f"🗑️  清除了 {len(keys_to_delete)} 个内存缓存: {prefix}")

        except Exception as e:
            logger.error(f"清除缓存失败: {e}")


# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def init_cache_service(redis_client=None):
    """初始化缓存服务"""
    global _cache_service
    _cache_service = CacheService(redis_client)
    logger.info("✅ 缓存服务已初始化")


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# =====================================================
# 缓存装饰器
# =====================================================

def cached(prefix: str, ttl_seconds: int = 3600, key_func: Optional[Callable] = None):
    """
    缓存装饰器

    Args:
        prefix: 缓存前缀
        ttl_seconds: 过期时间（秒）
        key_func: 自定义键生成函数

    Example:
        @cached(prefix="normalization", ttl_seconds=3600)
        def normalize_file(file_id: int):
            # 处理逻辑
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认：使用第一个参数作为标识符
                if args:
                    cache_key = str(args[0])
                else:
                    # 使用所有参数的哈希
                    param_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
                    cache_key = hashlib.md5(param_str.encode()).hexdigest()

            cache = get_cache_service()

            # 尝试从缓存获取
            cached_value = cache.get(prefix, cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 保存到缓存
            cache.set(prefix, cache_key, result, ttl_seconds)

            return result

        return wrapper

    return decorator


# =====================================================
# 预定义缓存策略
# =====================================================

class CacheStrategy:
    """缓存策略"""

    # 规范化结果：1小时
    NORMALIZATION = {"prefix": "normalization", "ttl": 3600}

    # 知识图谱查询：30分钟
    KG_QUERY = {"prefix": "kg_query", "ttl": 1800}

    # 缩影生成：2小时
    SUMMARY = {"prefix": "summary", "ttl": 7200}

    # 向量检索：15分钟
    VECTOR_SEARCH = {"prefix": "vector_search", "ttl": 900}

    # API响应：5分钟
    API_RESPONSE = {"prefix": "api_response", "ttl": 300}


def cache_normalization_result(file_id: int, result: Any):
    """缓存规范化结果"""
    cache = get_cache_service()
    cache.set(
        CacheStrategy.NORMALIZATION["prefix"],
        str(file_id),
        result,
        CacheStrategy.NORMALIZATION["ttl"]
    )


def get_cached_normalization_result(file_id: int) -> Optional[Any]:
    """获取缓存的规范化结果"""
    cache = get_cache_service()
    return cache.get(
        CacheStrategy.NORMALIZATION["prefix"],
        str(file_id)
    )


def invalidate_normalization_cache(file_id: int):
    """使规范化缓存失效"""
    cache = get_cache_service()
    cache.delete(
        CacheStrategy.NORMALIZATION["prefix"],
        str(file_id)
    )
