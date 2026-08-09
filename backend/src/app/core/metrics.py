"""
Prometheus 监控指标
提供标准的 Prometheus 格式指标
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
from typing import Dict
import time
import psutil
import os
import logging

logger = logging.getLogger(__name__)

# 创建独立的 registry
registry = CollectorRegistry()

# ============================================
# HTTP 请求指标
# ============================================

# 请求计数器
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

# 请求延迟
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry
)

# 进行中的请求
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# ============================================
# 业务指标
# ============================================

# 项目数量
projects_total = Gauge(
    'projects_total',
    'Total number of projects',
    registry=registry
)

# 文档数量
documents_total = Gauge(
    'documents_total',
    'Total number of documents',
    registry=registry
)

# 分析任务数量
analysis_tasks_total = Counter(
    'analysis_tasks_total',
    'Total number of analysis tasks',
    ['type', 'status'],
    registry=registry
)

# 对话数量
conversations_total = Counter(
    'conversations_total',
    'Total number of conversations',
    registry=registry
)

# 提案生成数量
proposals_generated_total = Counter(
    'proposals_generated_total',
    'Total number of proposals generated',
    ['type'],
    registry=registry
)

# ============================================
# 数据库指标
# ============================================

# 数据库查询延迟
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry
)

# 数据库连接池
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=registry
)

# 数据库错误
db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['type'],
    registry=registry
)

# ============================================
# 缓存指标
# ============================================

# 缓存命中
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_name'],
    registry=registry
)

# 缓存未命中
cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name'],
    registry=registry
)

# ============================================
# 系统指标
# ============================================

# CPU 使用率
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

# 内存使用率
system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage',
    registry=registry
)

# 磁盘使用率
system_disk_usage = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage',
    registry=registry
)

# 进程内存
process_memory_bytes = Gauge(
    'process_memory_bytes',
    'Process memory usage in bytes',
    registry=registry
)

# 进程线程数
process_threads = Gauge(
    'process_threads',
    'Number of threads in the process',
    registry=registry
)

# ============================================
# 应用信息
# ============================================

app_info = Info(
    'fieldmind_app',
    'FieldMind application information',
    registry=registry
)

# 设置应用信息
app_info.info({
    'version': '1.0.0',
    'environment': os.getenv('ENVIRONMENT', 'development')
})

# ============================================
# 更新系统指标的函数
# ============================================

def update_system_metrics():
    """更新系统指标"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage.set(cpu_percent)

        # 内存
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.percent)

        # 磁盘
        disk = psutil.disk_usage('/')
        system_disk_usage.set(disk.percent)

        # 进程信息
        process = psutil.Process(os.getpid())
        process_memory_bytes.set(process.memory_info().rss)
        process_threads.set(process.num_threads())

    except Exception as e:
        logger.warning(f"更新系统指标失败: {e}")


def update_business_metrics():
    """更新业务指标"""
    try:
        from app.core.database import SessionLocal
        from app.models.project import Project
        from app.models.document import Document

        db = SessionLocal()

        # 项目数量
        project_count = db.query(Project).count()
        projects_total.set(project_count)

        # 文档数量
        doc_count = db.query(Document).count()
        documents_total.set(doc_count)

        db.close()

    except Exception as e:
        logger.warning(f"更新业务指标失败: {e}")


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/metrics", tags=["监控指标"])


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint

    用法:
    - Prometheus: scrape_configs 中添加此端点
    - Grafana: 创建 Prometheus 数据源并导入仪表板
    """
    # 更新指标
    update_system_metrics()
    update_business_metrics()

    # 生成 Prometheus 格式
    metrics_output = generate_latest(registry)

    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/summary")
async def metrics_summary() -> Dict:
    """
    指标摘要 (JSON格式)

    用于快速查看系统状态
    """
    update_system_metrics()

    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "process": {
            "memory_mb": psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2),
            "threads": psutil.Process(os.getpid()).num_threads()
        },
        "registry": {
            "collectors": len(list(registry._collector_to_names.keys()))
        }
    }


# ============================================
# 辅助函数
# ============================================

def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """记录HTTP请求"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_db_query(operation: str, duration: float):
    """记录数据库查询"""
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def track_cache_hit(cache_name: str):
    """记录缓存命中"""
    cache_hits_total.labels(cache_name=cache_name).inc()


def track_cache_miss(cache_name: str):
    """记录缓存未命中"""
    cache_misses_total.labels(cache_name=cache_name).inc()


# 导出
__all__ = [
    'router',
    'http_requests_total',
    'http_request_duration_seconds',
    'http_requests_in_progress',
    'projects_total',
    'documents_total',
    'analysis_tasks_total',
    'conversations_total',
    'proposals_generated_total',
    'db_query_duration_seconds',
    'cache_hits_total',
    'cache_misses_total',
    'track_request',
    'track_db_query',
    'track_cache_hit',
    'track_cache_miss',
]
