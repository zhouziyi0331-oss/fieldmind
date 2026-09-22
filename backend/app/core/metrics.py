"""
Prometheus Metrics Collection
监控API请求、数据库、缓存性能指标
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
import psutil
from typing import Callable

# ============================================
# API请求指标
# ============================================
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint']
)

# ============================================
# 数据库连接池指标
# ============================================
db_connections_total = Gauge(
    'db_connections_total',
    'Total database connections'
)

db_connections_in_use = Gauge(
    'db_connections_in_use',
    'Database connections in use'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Database connections idle'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# ============================================
# Redis缓存指标
# ============================================
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses'
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration',
    ['operation']
)

# ============================================
# 系统资源指标
# ============================================
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_memory_available_bytes = Gauge(
    'system_memory_available_bytes',
    'System memory available in bytes'
)

# ============================================
# 应用信息
# ============================================
app_info = Info('app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'name': 'FieldMind Backend',
    'environment': 'production'
})

# ============================================
# 辅助函数
# ============================================
def update_system_metrics():
    """更新系统资源指标"""
    system_cpu_usage_percent.set(psutil.cpu_percent(interval=0.1))

    memory = psutil.virtual_memory()
    system_memory_usage_bytes.set(memory.used)
    system_memory_available_bytes.set(memory.available)


def update_cache_hit_rate():
    """计算并更新缓存命中率"""
    hits = cache_hits_total._value.get()
    misses = cache_misses_total._value.get()
    total = hits + misses

    if total > 0:
        hit_rate = (hits / total) * 100
        cache_hit_rate.set(hit_rate)
    else:
        cache_hit_rate.set(0)


def metrics_endpoint() -> Response:
    """生成Prometheus metrics端点响应"""
    update_system_metrics()
    update_cache_hit_rate()

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


class MetricsMiddleware:
    """Metrics收集中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # 跳过metrics端点本身
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        # 标记请求开始
        http_requests_in_progress.labels(method=method, endpoint=path).inc()
        start_time = time.time()

        # 包装send函数以捕获状态码
        status_code = 500

        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # 记录指标
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            http_requests_in_progress.labels(method=method, endpoint=path).dec()
