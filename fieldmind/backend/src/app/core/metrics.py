"""
Prometheus 监控指标
定义和导出应用性能指标
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import make_asgi_app
from typing import Optional


# ============================================
# HTTP 请求指标
# ============================================

# HTTP 请求总数
http_requests_total = Counter(
    'fieldmind_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# HTTP 请求延迟
http_request_duration_seconds = Histogram(
    'fieldmind_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# 当前正在处理的请求数
http_requests_in_progress = Gauge(
    'fieldmind_http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)


# ============================================
# 文档处理指标
# ============================================

# 文档上传总数
documents_uploaded_total = Counter(
    'fieldmind_documents_uploaded_total',
    'Total documents uploaded',
    ['type']
)

# 文档处理总数
documents_processed_total = Counter(
    'fieldmind_documents_processed_total',
    'Total documents processed',
    ['type', 'status']
)

# 文档处理时间
document_processing_duration_seconds = Histogram(
    'fieldmind_document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['type', 'operation'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

# 当前正在处理的文档数
documents_processing_in_progress = Gauge(
    'fieldmind_documents_processing_in_progress',
    'Number of documents currently being processed'
)


# ============================================
# 向量存储指标
# ============================================

# 向量插入总数
vectors_inserted_total = Counter(
    'fieldmind_vectors_inserted_total',
    'Total vectors inserted'
)

# 向量搜索总数
vectors_searched_total = Counter(
    'fieldmind_vectors_searched_total',
    'Total vector searches performed'
)

# 向量搜索延迟
vector_search_duration_seconds = Histogram(
    'fieldmind_vector_search_duration_seconds',
    'Vector search duration in seconds',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0)
)

# 向量数据库大小
vector_store_size = Gauge(
    'fieldmind_vector_store_size',
    'Total number of vectors in storage'
)


# ============================================
# 存储指标
# ============================================

# 存储上传字节数
storage_uploaded_bytes = Counter(
    'fieldmind_storage_uploaded_bytes',
    'Total bytes uploaded to storage',
    ['bucket']
)

# 存储下载字节数
storage_downloaded_bytes = Counter(
    'fieldmind_storage_downloaded_bytes',
    'Total bytes downloaded from storage',
    ['bucket']
)

# 存储操作总数
storage_operations_total = Counter(
    'fieldmind_storage_operations_total',
    'Total storage operations',
    ['operation', 'bucket', 'status']
)

# 存储操作延迟
storage_operation_duration_seconds = Histogram(
    'fieldmind_storage_operation_duration_seconds',
    'Storage operation duration in seconds',
    ['operation', 'bucket'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)


# ============================================
# 数据库指标
# ============================================

# 数据库查询总数
database_queries_total = Counter(
    'fieldmind_database_queries_total',
    'Total database queries',
    ['operation', 'table', 'status']
)

# 数据库查询延迟
database_query_duration_seconds = Histogram(
    'fieldmind_database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# 数据库连接池状态
database_connection_pool_size = Gauge(
    'fieldmind_database_connection_pool_size',
    'Database connection pool size'
)

database_connection_pool_available = Gauge(
    'fieldmind_database_connection_pool_available',
    'Available connections in the pool'
)


# ============================================
# AI 服务指标
# ============================================

# AI 请求总数
ai_requests_total = Counter(
    'fieldmind_ai_requests_total',
    'Total AI service requests',
    ['provider', 'model', 'operation', 'status']
)

# AI 请求延迟
ai_request_duration_seconds = Histogram(
    'fieldmind_ai_request_duration_seconds',
    'AI service request duration in seconds',
    ['provider', 'model', 'operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
)

# AI Token 使用
ai_tokens_used = Counter(
    'fieldmind_ai_tokens_used',
    'Total AI tokens used',
    ['provider', 'model', 'type']
)


# ============================================
# 系统指标
# ============================================

# 应用信息
app_info = Info(
    'fieldmind_app',
    'FieldMind application information'
)

# 应用启动时间
app_start_time = Gauge(
    'fieldmind_app_start_time',
    'Application start time in seconds since epoch'
)

# 错误总数
errors_total = Counter(
    'fieldmind_errors_total',
    'Total errors',
    ['error_code', 'endpoint']
)


# ============================================
# 便捷记录函数
# ============================================

def record_http_request(method: str, endpoint: str, status: int, duration: float):
    """记录HTTP请求指标"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """兼容监控中间件的请求指标入口。"""
    record_http_request(method, endpoint, str(status_code), duration)


def record_document_upload(doc_type: str):
    """记录文档上传"""
    documents_uploaded_total.labels(type=doc_type).inc()


def record_document_processing(doc_type: str, operation: str, status: str, duration: float):
    """记录文档处理"""
    documents_processed_total.labels(type=doc_type, status=status).inc()
    document_processing_duration_seconds.labels(type=doc_type, operation=operation).observe(duration)


def record_vector_insert(count: int = 1):
    """记录向量插入"""
    vectors_inserted_total.inc(count)


def record_vector_search(duration: float):
    """记录向量搜索"""
    vectors_searched_total.inc()
    vector_search_duration_seconds.observe(duration)


def record_storage_operation(
    operation: str,
    bucket: str,
    status: str,
    duration: float,
    size: Optional[int] = None
):
    """记录存储操作"""
    storage_operations_total.labels(operation=operation, bucket=bucket, status=status).inc()
    storage_operation_duration_seconds.labels(operation=operation, bucket=bucket).observe(duration)

    if size:
        if operation == "upload":
            storage_uploaded_bytes.labels(bucket=bucket).inc(size)
        elif operation == "download":
            storage_downloaded_bytes.labels(bucket=bucket).inc(size)


def record_database_query(operation: str, table: str, status: str, duration: float):
    """记录数据库查询"""
    database_queries_total.labels(operation=operation, table=table, status=status).inc()
    database_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def record_ai_request(
    provider: str,
    model: str,
    operation: str,
    status: str,
    duration: float,
    tokens: Optional[int] = None
):
    """记录AI请求"""
    ai_requests_total.labels(
        provider=provider,
        model=model,
        operation=operation,
        status=status
    ).inc()

    ai_request_duration_seconds.labels(
        provider=provider,
        model=model,
        operation=operation
    ).observe(duration)

    if tokens:
        ai_tokens_used.labels(provider=provider, model=model, type="total").inc(tokens)


def record_error(error_code: str, endpoint: str):
    """记录错误"""
    errors_total.labels(error_code=error_code, endpoint=endpoint).inc()


def update_vector_store_size(size: int):
    """更新向量存储大小"""
    vector_store_size.set(size)


def update_database_pool_stats(pool_size: int, available: int):
    """更新数据库连接池统计"""
    database_connection_pool_size.set(pool_size)
    database_connection_pool_available.set(available)


# ============================================
# Prometheus 端点
# ============================================

def get_metrics_app():
    """
    获取 Prometheus metrics ASGI 应用

    用于挂载到 FastAPI 应用
    """
    return make_asgi_app()


# ============================================
# 初始化应用信息
# ============================================

def init_metrics(version: str = "1.0", environment: str = "production"):
    """
    初始化应用指标

    Args:
        version: 应用版本
        environment: 运行环境
    """
    import time

    app_info.info({
        'version': version,
        'environment': environment
    })

    app_start_time.set(time.time())
