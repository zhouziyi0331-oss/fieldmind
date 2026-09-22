"""
Redis 缓存后端实现
支持分布式部署和持久化缓存
"""
import redis
import pickle
import logging
from typing import Any, Optional
from app.core.cache import CacheBackend

logger = logging.getLogger(__name__)


class RedisCache(CacheBackend):
    """Redis 缓存实现"""

    def __init__(self, url: str = None, **kwargs):
        """
        初始化 Redis 缓存

        Args:
            url: Redis 连接 URL (redis://localhost:6379/0)
            **kwargs: 其他 redis.from_url 参数
        """
        try:
            self.redis = redis.from_url(
                url or "redis://localhost:6379/0",
                decode_responses=False,  # 存储二进制数据（pickle）
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 60,  # TCP_KEEPIDLE
                    2: 10,  # TCP_KEEPINTVL
                    3: 3,   # TCP_KEEPCNT
                },
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=50,
                **kwargs
            )

            # 测试连接
            self.redis.ping()
            logger.info(f"Redis 缓存已连接: {url}")

        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis 连接失败: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            data = self.redis.get(key)
            if data is None:
                return None

            # 反序列化
            return pickle.loads(data)

        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Redis 获取缓存失败 {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存，ttl单位为秒"""
        try:
            # 序列化数据
            data = pickle.dumps(value)

            # 保存到 Redis（带过期时间）
            self.redis.setex(key, ttl, data)

        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Redis 设置缓存失败 {key}: {e}")

    def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis.delete(key)
        except redis.RedisError as e:
            logger.error(f"Redis 删除缓存失败 {key}: {e}")

    def clear(self):
        """清空当前数据库的所有缓存"""
        try:
            self.redis.flushdb()
            logger.warning("Redis 缓存已清空")
        except redis.RedisError as e:
            logger.error(f"Redis 清空缓存失败: {e}")

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"Redis 检查键存在失败 {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间（秒）"""
        try:
            return self.redis.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Redis 获取 TTL 失败 {key}: {e}")
            return -1

    def delete_pattern(self, pattern: str):
        """
        根据模式删除缓存

        Args:
            pattern: Redis 键模式（支持通配符 *）
                    例如: "user:*", "project:123:*"
        """
        try:
            cursor = 0
            deleted_count = 0

            # 使用 SCAN 遍历键（避免 KEYS 阻塞）
            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)

                if keys:
                    self.redis.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Redis 删除模式 {pattern}: {deleted_count} 个键")
            return deleted_count

        except redis.RedisError as e:
            logger.error(f"Redis 删除模式失败 {pattern}: {e}")
            return 0

    def stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            info = self.redis.info("stats")
            memory_info = self.redis.info("memory")

            return {
                "total_keys": self.redis.dbsize(),
                "memory_usage_bytes": memory_info.get("used_memory", 0),
                "memory_usage_human": memory_info.get("used_memory_human", "N/A"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "connected_clients": self.redis.info("clients").get("connected_clients", 0),
            }

        except redis.RedisError as e:
            logger.error(f"Redis 获取统计失败: {e}")
            return {}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total * 100, 2)

    def ping(self) -> bool:
        """检查 Redis 连接是否正常"""
        try:
            return self.redis.ping()
        except redis.RedisError:
            return False

    def close(self):
        """关闭 Redis 连接"""
        try:
            self.redis.close()
            logger.info("Redis 连接已关闭")
        except redis.RedisError as e:
            logger.error(f"Redis 关闭连接失败: {e}")
