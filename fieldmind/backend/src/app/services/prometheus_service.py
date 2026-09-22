"""
Prometheus 指标导出服务
提供应用性能和业务指标监控
"""

import logging
import time
from typing import Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class PrometheusService:
    """Prometheus 指标服务"""

    def __init__(self):
        self.enabled = False
        self.registry = None
        self._init_prometheus()

    def _init_prometheus(self):
        """初始化 Prometheus 指标"""
        try:
            from app.config import settings

            if not settings.PROMETHEUS_ENABLED:
                logger.info("Prometheus 未启用")
                return

            from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
            from prometheus_client import REGISTRY

            self.registry = REGISTRY

            # ==================== HTTP 请求指标 ====================

            # 请求计数器
            self.http_requests_total = Counter(
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint', 'status_code'],
                registry=self.registry
            )

            # 请求延迟直方图
            self.http_request_duration_seconds = Histogram(
                'http_request_duration_seconds',
                'HTTP request latency',
                ['method', 'endpoint'],
                buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
                registry=self.registry
            )

            # 当前活跃请求
            self.http_requests_in_progress = Gauge(
                'http_requests_in_progress',
                'Current HTTP requests in progress',
                ['method', 'endpoint'],
                registry=self.registry
            )

            # ==================== 数据库指标 ====================

            # 数据库查询计数
            self.db_queries_total = Counter(
                'db_queries_total',
                'Total database queries',
                ['operation', 'table'],
                registry=self.registry
            )

            # 数据库查询延迟
            self.db_query_duration_seconds = Histogram(
                'db_query_duration_seconds',
                'Database query latency',
                ['operation', 'table'],
                buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
                registry=self.registry
            )

            # 数据库连接池状态
            self.db_connections_active = Gauge(
                'db_connections_active',
                'Active database connections',
                registry=self.registry
            )

            self.db_connections_idle = Gauge(
                'db_connections_idle',
                'Idle database connections',
                registry=self.registry
            )

            # ==================== 缓存指标 ====================

            # 缓存命中/未命中
            self.cache_hits_total = Counter(
                'cache_hits_total',
                'Total cache hits',
                ['cache_name'],
                registry=self.registry
            )

            self.cache_misses_total = Counter(
                'cache_misses_total',
                'Total cache misses',
                ['cache_name'],
                registry=self.registry
            )

            # 缓存操作延迟
            self.cache_operation_duration_seconds = Histogram(
                'cache_operation_duration_seconds',
                'Cache operation latency',
                ['operation', 'cache_name'],
                buckets=(0.0001, 0.001, 0.005, 0.01, 0.05, 0.1),
                registry=self.registry
            )

            # ==================== 业务指标 ====================

            # 文档处理
            self.documents_processed_total = Counter(
                'documents_processed_total',
                'Total documents processed',
                ['status'],
                registry=self.registry
            )

            self.document_processing_duration_seconds = Histogram(
                'document_processing_duration_seconds',
                'Document processing time',
                buckets=(1, 5, 10, 30, 60, 120, 300, 600),
                registry=self.registry
            )

            # AI API 调用
            self.ai_api_calls_total = Counter(
                'ai_api_calls_total',
                'Total AI API calls',
                ['provider', 'model', 'status'],
                registry=self.registry
            )

            self.ai_api_duration_seconds = Histogram(
                'ai_api_duration_seconds',
                'AI API call duration',
                ['provider', 'model'],
                buckets=(0.5, 1, 2, 5, 10, 20, 30, 60),
                registry=self.registry
            )

            # 后台任务队列
            self.background_tasks_queued = Gauge(
                'background_tasks_queued',
                'Background tasks in queue',
                ['task_type'],
                registry=self.registry
            )

            self.background_tasks_completed_total = Counter(
                'background_tasks_completed_total',
                'Total background tasks completed',
                ['task_type', 'status'],
                registry=self.registry
            )

            # ==================== 系统指标 ====================

            # 应用信息
            self.app_info = Info(
                'app',
                'Application information',
                registry=self.registry
            )
            self.app_info.info({
                'version': settings.VERSION,
                'environment': settings.ENVIRONMENT,
            })

            # 应用启动时间
            self.app_start_time = Gauge(
                'app_start_time_seconds',
                'Application start time',
                registry=self.registry
            )
            self.app_start_time.set_to_current_time()

            self.enabled = True
            logger.info("✅ Prometheus 指标已启用")

        except ImportError:
            logger.warning("⚠️  prometheus-client 未安装，监控功能不可用")
        except Exception as e:
            logger.error(f"❌ Prometheus 初始化失败: {e}")

    # ==================== 便捷方法 ====================

    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录 HTTP 请求"""
        if not self.enabled:
            return

        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.error(f"记录请求指标失败: {e}")

    def track_db_query(self, operation: str, table: str, duration: float):
        """记录数据库查询"""
        if not self.enabled:
            return

        try:
            self.db_queries_total.labels(
                operation=operation,
                table=table
            ).inc()

            self.db_query_duration_seconds.labels(
                operation=operation,
                table=table
            ).observe(duration)
        except Exception as e:
            logger.error(f"记录数据库指标失败: {e}")

    def track_cache_hit(self, cache_name: str = "default"):
        """记录缓存命中"""
        if not self.enabled:
            return

        try:
            self.cache_hits_total.labels(cache_name=cache_name).inc()
        except Exception as e:
            logger.error(f"记录缓存命中失败: {e}")

    def track_cache_miss(self, cache_name: str = "default"):
        """记录缓存未命中"""
        if not self.enabled:
            return

        try:
            self.cache_misses_total.labels(cache_name=cache_name).inc()
        except Exception as e:
            logger.error(f"记录缓存未命中失败: {e}")

    def track_document_processed(self, status: str, duration: Optional[float] = None):
        """记录文档处理"""
        if not self.enabled:
            return

        try:
            self.documents_processed_total.labels(status=status).inc()
            if duration is not None:
                self.document_processing_duration_seconds.observe(duration)
        except Exception as e:
            logger.error(f"记录文档处理指标失败: {e}")

    def track_ai_api_call(self, provider: str, model: str, status: str, duration: float):
        """记录 AI API 调用"""
        if not self.enabled:
            return

        try:
            self.ai_api_calls_total.labels(
                provider=provider,
                model=model,
                status=status
            ).inc()

            self.ai_api_duration_seconds.labels(
                provider=provider,
                model=model
            ).observe(duration)
        except Exception as e:
            logger.error(f"记录 AI API 指标失败: {e}")

    def update_db_pool_stats(self, active: int, idle: int):
        """更新数据库连接池统计"""
        if not self.enabled:
            return

        try:
            self.db_connections_active.set(active)
            self.db_connections_idle.set(idle)
        except Exception as e:
            logger.error(f"更新连接池指标失败: {e}")

    def update_task_queue_size(self, task_type: str, size: int):
        """更新任务队列大小"""
        if not self.enabled:
            return

        try:
            self.background_tasks_queued.labels(task_type=task_type).set(size)
        except Exception as e:
            logger.error(f"更新队列指标失败: {e}")


# 全局 Prometheus 实例
prometheus = PrometheusService()


def track_time(metric_name: str, **labels):
    """
    时间追踪装饰器

    Example:
        @track_time("function_duration", operation="process")
        def process_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 根据 metric_name 记录到对应的指标
                if metric_name == "db_query":
                    prometheus.track_db_query(
                        labels.get('operation', 'unknown'),
                        labels.get('table', 'unknown'),
                        duration
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                raise

        return wrapper
    return decorator
