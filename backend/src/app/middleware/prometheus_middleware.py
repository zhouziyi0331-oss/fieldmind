"""
Prometheus 监控中间件 - Week 4 Day 1-2
应用指标导出、性能监控、业务指标跟踪
"""
from prometheus_client import Counter, Histogram, Gauge, Summary, Info, generate_latest
from prometheus_client import REGISTRY, CollectorRegistry
from fastapi import Request, Response
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)


# ==================== HTTP 指标 ====================

# 请求计数
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求耗时
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 活跃请求数
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

# 请求大小
REQUEST_SIZE = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# 响应大小
RESPONSE_SIZE = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


# ==================== 业务指标 ====================

# 文档处理
DOCUMENTS_PROCESSED = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['status', 'project_id']
)

DOCUMENT_PROCESSING_DURATION = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['document_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

# 向量化
VECTORS_CREATED = Counter(
    'vectors_created_total',
    'Total vectors created',
    ['project_id']
)

VECTORIZATION_DURATION = Histogram(
    'vectorization_duration_seconds',
    'Vectorization duration in seconds',
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# 实体提取
ENTITIES_EXTRACTED = Counter(
    'entities_extracted_total',
    'Total entities extracted',
    ['entity_type', 'project_id']
)

# API 调用
AI_API_CALLS = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['model', 'status']
)

AI_API_DURATION = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration in seconds',
    ['model']
)

AI_API_TOKENS = Counter(
    'ai_api_tokens_total',
    'Total AI API tokens used',
    ['model', 'type']  # type: input/output
)

AI_API_COST = Counter(
    'ai_api_cost_dollars',
    'Total AI API cost in dollars',
    ['model']
)


# ==================== 系统指标 ====================

# 数据库连接
DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# 缓存
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

CACHE_SIZE = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)

# 队列
QUEUE_SIZE = Gauge(
    'queue_size',
    'Number of items in queue',
    ['queue_name']
)

QUEUE_PROCESSING_DURATION = Histogram(
    'queue_processing_duration_seconds',
    'Queue item processing duration in seconds',
    ['queue_name']
)


# ==================== 应用信息 ====================

APP_INFO = Info(
    'fieldmind_monitoring_app',
    'FieldMind monitoring middleware information'
)

APP_INFO.info({
    'version': '1.0.0',
    'environment': 'production'
})


# ==================== 中间件 ====================

async def prometheus_middleware(request: Request, call_next: Callable):
    """
    Prometheus 监控中间件

    记录每个请求的指标
    """
    # 增加活跃请求
    ACTIVE_REQUESTS.inc()

    # 记录请求大小
    if request.headers.get('content-length'):
        REQUEST_SIZE.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(int(request.headers['content-length']))

    # 记录开始时间
    start_time = time.time()

    try:
        # 执行请求
        response = await call_next(request)

        # 记录耗时
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        # 记录请求计数
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        # 记录响应大小
        if hasattr(response, 'body'):
            RESPONSE_SIZE.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(len(response.body))

        return response

    except Exception as e:
        # 记录错误
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()

        raise

    finally:
        # 减少活跃请求
        ACTIVE_REQUESTS.dec()


# ==================== 指标端点 ====================

def metrics_endpoint():
    """
    Prometheus 指标端点

    Returns:
        指标数据（text/plain）
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# ==================== 业务指标记录函数 ====================

def record_document_processed(
    status: str,
    project_id: int,
    duration: float,
    document_type: str
):
    """记录文档处理指标"""
    DOCUMENTS_PROCESSED.labels(
        status=status,
        project_id=project_id
    ).inc()

    DOCUMENT_PROCESSING_DURATION.labels(
        document_type=document_type
    ).observe(duration)


def record_vectorization(
    project_id: int,
    count: int,
    duration: float
):
    """记录向量化指标"""
    VECTORS_CREATED.labels(
        project_id=project_id
    ).inc(count)

    VECTORIZATION_DURATION.observe(duration)


def record_entity_extraction(
    entity_type: str,
    project_id: int,
    count: int
):
    """记录实体提取指标"""
    ENTITIES_EXTRACTED.labels(
        entity_type=entity_type,
        project_id=project_id
    ).inc(count)


def record_ai_api_call(
    model: str,
    status: str,
    duration: float,
    input_tokens: int,
    output_tokens: int,
    cost: float
):
    """记录 AI API 调用指标"""
    AI_API_CALLS.labels(
        model=model,
        status=status
    ).inc()

    AI_API_DURATION.labels(
        model=model
    ).observe(duration)

    AI_API_TOKENS.labels(
        model=model,
        type='input'
    ).inc(input_tokens)

    AI_API_TOKENS.labels(
        model=model,
        type='output'
    ).inc(output_tokens)

    AI_API_COST.labels(
        model=model
    ).inc(cost)


def record_cache_operation(
    cache_type: str,
    hit: bool
):
    """记录缓存操作指标"""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()


def record_database_query(
    query_type: str,
    duration: float
):
    """记录数据库查询指标"""
    DATABASE_QUERY_DURATION.labels(
        query_type=query_type
    ).observe(duration)


# ==================== 健康检查 ====================

HEALTH_STATUS = Gauge(
    'fieldmind_health_status',
    'Health status (1=healthy, 0=unhealthy)'
)

def update_health_status(healthy: bool):
    """更新健康状态"""
    HEALTH_STATUS.set(1 if healthy else 0)
