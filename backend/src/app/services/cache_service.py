"""
Redis 缓存服务
提供统一的缓存接口，支持优雅降级
"""

import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务（支持 Redis 或内存缓存）"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.redis_client = None
        self.memory_cache = {}  # 降级方案：内存缓存
        self.enabled = False
        self._init_redis()

    def _init_redis(self):
        """初始化 Redis 连接"""
        try:
            from app.config import settings

            if not settings.REDIS_ENABLED:
                logger.info("Redis 未启用，使用内存缓存降级")
                return

            import redis
            from redis.connection import ConnectionPool

            pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                max_connections=50,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            self.redis_client = redis.Redis(connection_pool=pool)

            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis 连接成功")

        except Exception as e:
            logger.warning(f"⚠️  Redis 连接失败，使用内存缓存降级: {e}")
            self.redis_client = None
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # 降级到内存缓存
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"缓存读取失败 {key}: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存值"""
        try:
            serialized = json.dumps(value, ensure_ascii=False)

            if self.redis_client:
                self.redis_client.setex(key, ttl, serialized)
            else:
                # 降级到内存缓存（简单实现，不支持过期）
                self.memory_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"缓存写入失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # 内存缓存简单实现
                count = 0
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    self.memory_cache.pop(key, None)
                    count += 1
                return count
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败 {pattern}: {e}")
            return 0

    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            logger.info("✅ 缓存已清空")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            if self.redis_client:
                info = self.redis_client.info('stats')
                return {
                    "enabled": True,
                    "backend": "redis",
                    "keyspace_hits": info.get('keyspace_hits', 0),
                    "keyspace_misses": info.get('keyspace_misses', 0),
                    "hit_rate": self._calculate_hit_rate(
                        info.get('keyspace_hits', 0),
                        info.get('keyspace_misses', 0)
                    ),
                    "used_memory_human": self.redis_client.info('memory').get('used_memory_human', 'N/A'),
                }
            else:
                return {
                    "enabled": False,
                    "backend": "memory",
                    "keys_count": len(self.memory_cache),
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"enabled": False, "error": str(e)}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total * 100, 2)

    def health_check(self) -> dict:
        """健康检查"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return {"status": "healthy", "backend": "redis"}
            else:
                return {"status": "healthy", "backend": "memory"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# 全局缓存实例
cache = CacheService()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀

    Example:
        @cached(ttl=600, key_prefix="projects")
        def get_project_list(user_id: int):
            # 业务逻辑
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 写入缓存
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存写入: {cache_key}")

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    缓存失效装饰器

    Args:
        pattern: 缓存键模式（支持通配符）

    Example:
        @invalidate_cache("projects:*")
        def create_project(name: str):
            # 创建项目后自动失效相关缓存
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache.delete_pattern(pattern)
            logger.debug(f"缓存失效: {pattern}")
            return result
        return wrapper
    return decorator


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    # 组合参数
    key_parts = [prefix, func_name]

    # 添加位置参数
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))

    # 添加关键字参数（排序保证一致性）
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")

    # 生成哈希（避免键过长）
    key_str = ":".join(key_parts)
    if len(key_str) > 100:
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"

    return key_str


# 预定义缓存键前缀
class CacheKeys:
    """缓存键前缀常量"""

    # 项目相关
    PROJECT_LIST = "projects:list"
    PROJECT_DETAIL = "projects:detail"
    PROJECT_STATS = "projects:stats"

    # 数据质量
    DATA_QUALITY = "quality"
    DATA_QUALITY_GAPS = "quality:gaps"

    # 知识图谱
    KNOWLEDGE_GRAPH = "knowledge:graph"
    KNOWLEDGE_ENTITIES = "knowledge:entities"

    # 用户权限
    USER_PERMISSIONS = "users:permissions"
    USER_PROJECTS = "users:projects"

    # 文档相关
    DOCUMENT_LIST = "documents:list"
    DOCUMENT_CHUNKS = "documents:chunks"
