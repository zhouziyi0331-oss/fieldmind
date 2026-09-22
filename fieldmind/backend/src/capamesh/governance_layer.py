"""
Governance Layer - 治理层

功能：
1. 路由管理
2. 缓存管理
3. 降级策略
4. 限流控制
5. 监控和指标收集
"""

import logging
import time
import hashlib
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GovernanceLayer:
    """治理层"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化治理层

        Args:
            config: 治理配置
        """
        self.config = config or self._default_config()

        # 缓存
        self.cache_backend = self.config['cache']['backend']
        self.cache_ttl = self.config['cache']['ttl_seconds']
        self.cache_enabled = self.config['cache']['enabled']
        self._memory_cache = {}  # 简单的内存缓存

        # 限流
        self.rate_limit_enabled = self.config['rate_limit']['enabled']
        self.requests_per_minute = self.config['rate_limit']['requests_per_minute']
        self._request_counts = defaultdict(list)  # {key: [timestamp, ...]}

        # 降级
        self.fallback_enabled = self.config['fallback']['enabled']
        self.fallback_rules = self.config['fallback']['rules']

        # 监控
        self.monitoring_enabled = self.config['monitoring']['enabled']
        self._metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_exceeded': 0,
            'fallback_triggered': 0,
            'errors': 0
        }

        logger.info("Governance layer initialized")

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'cache': {
                'enabled': True,
                'backend': 'memory',  # memory | redis
                'ttl_seconds': 300
            },
            'rate_limit': {
                'enabled': True,
                'requests_per_minute': 100,
                'by': 'ip'  # ip | user | global
            },
            'fallback': {
                'enabled': True,
                'rules': [
                    {
                        'condition': 'timeout',
                        'action': 'return_cached'
                    },
                    {
                        'condition': 'error',
                        'action': 'return_partial'
                    }
                ]
            },
            'monitoring': {
                'enabled': True,
                'metrics': [
                    'request_count',
                    'cache_hit_rate',
                    'error_rate',
                    'avg_response_time'
                ]
            }
        }

    def get_cached(self, cache_key: str) -> Optional[Dict]:
        """
        获取缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存的数据，如果不存在返回 None
        """
        if not self.cache_enabled:
            return None

        if self.cache_backend == 'memory':
            cached = self._memory_cache.get(cache_key)
            if cached:
                # 检查是否过期
                if time.time() - cached['timestamp'] < self.cache_ttl:
                    self._metrics['cache_hits'] += 1
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached['data']
                else:
                    # 过期，删除
                    del self._memory_cache[cache_key]

        self._metrics['cache_misses'] += 1
        return None

    def set_cache(self, cache_key: str, data: Dict):
        """
        设置缓存

        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        if not self.cache_enabled:
            return

        if self.cache_backend == 'memory':
            self._memory_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            logger.debug(f"Cache set: {cache_key}")

    def generate_cache_key(self, view_id: str, parameters: Dict) -> str:
        """
        生成缓存键

        Args:
            view_id: 视图ID
            parameters: 查询参数

        Returns:
            缓存键
        """
        # 将参数排序并序列化
        import json
        params_str = json.dumps(parameters, sort_keys=True)
        key_str = f"{view_id}:{params_str}"

        # 生成哈希
        return hashlib.md5(key_str.encode()).hexdigest()

    def check_rate_limit(self, client_id: str) -> bool:
        """
        检查是否超过速率限制

        Args:
            client_id: 客户端标识（IP或用户ID）

        Returns:
            True 如果允许请求，False 如果超过限制
        """
        if not self.rate_limit_enabled:
            return True

        now = time.time()
        one_minute_ago = now - 60

        # 清理过期的请求记录
        self._request_counts[client_id] = [
            ts for ts in self._request_counts[client_id]
            if ts > one_minute_ago
        ]

        # 检查请求数
        if len(self._request_counts[client_id]) >= self.requests_per_minute:
            self._metrics['rate_limit_exceeded'] += 1
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False

        # 记录本次请求
        self._request_counts[client_id].append(now)
        return True

    def should_fallback(self, error_type: str) -> Optional[str]:
        """
        判断是否应该降级

        Args:
            error_type: 错误类型（timeout, error, unavailable）

        Returns:
            降级动作，如果不应降级返回 None
        """
        if not self.fallback_enabled:
            return None

        for rule in self.fallback_rules:
            if rule['condition'] == error_type:
                self._metrics['fallback_triggered'] += 1
                logger.info(f"Fallback triggered: {error_type} -> {rule['action']}")
                return rule['action']

        return None

    def record_request(self, duration_ms: int, status: str):
        """
        记录请求

        Args:
            duration_ms: 请求耗时（毫秒）
            status: 请求状态（success, error）
        """
        if not self.monitoring_enabled:
            return

        self._metrics['total_requests'] += 1

        if status == 'error':
            self._metrics['errors'] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取监控指标

        Returns:
            {
                'total_requests': int,
                'cache_hit_rate': float,
                'error_rate': float,
                'rate_limit_exceeded': int,
                'fallback_triggered': int
            }
        """
        total = self._metrics['total_requests']
        cache_total = self._metrics['cache_hits'] + self._metrics['cache_misses']

        return {
            'total_requests': total,
            'cache_hits': self._metrics['cache_hits'],
            'cache_misses': self._metrics['cache_misses'],
            'cache_hit_rate': self._metrics['cache_hits'] / cache_total if cache_total > 0 else 0,
            'errors': self._metrics['errors'],
            'error_rate': self._metrics['errors'] / total if total > 0 else 0,
            'rate_limit_exceeded': self._metrics['rate_limit_exceeded'],
            'fallback_triggered': self._metrics['fallback_triggered']
        }

    def reset_metrics(self):
        """重置监控指标"""
        self._metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_exceeded': 0,
            'fallback_triggered': 0,
            'errors': 0
        }
        logger.info("Metrics reset")

    def clear_cache(self):
        """清空缓存"""
        if self.cache_backend == 'memory':
            self._memory_cache.clear()
            logger.info("Memory cache cleared")


def create_governance_layer(config: Optional[Dict] = None) -> GovernanceLayer:
    """工厂方法：创建治理层"""
    return GovernanceLayer(config)
