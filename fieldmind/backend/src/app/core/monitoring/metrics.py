"""
Prometheus 监控指标模块

提供生产级的指标收集、追踪和导出功能。

核心功能：
1. HTTP 请求指标（计数、延迟、错误率）
2. 业务处理指标（文档处理、embedding、网络分析）
3. 资源使用指标（数据库连接池、Redis、内存）
4. 自定义业务指标（处理阶段、文档类型、AI 服务）

使用示例：
    # 追踪 HTTP 请求
    with track_request(method="POST", endpoint="/api/upload"):
        process_request()

    # 追踪文档处理
    with track_processing(stage="multimodal", doc_type="pdf"):
        process_document()

    # 追踪数据库操作
    with track_database_operation(operation="query", table="documents"):
        execute_query()
"""

import time
import psutil
from contextlib import contextmanager
from typing import Optional, Dict, Any
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)

from app.core.config import get_settings, get_logger, ErrorCode

logger = get_logger(__name__)
settings = get_settings()


class MetricsManager:
    """
    统一的指标管理器

    负责创建和管理所有 Prometheus 指标，提供统一的接口。
    """

    def __init__(self):
        """初始化所有指标"""
        self.registry = CollectorRegistry()

        # ====== 系统信息指标 ======
        self.system_info = Info(
            'fieldmind_system',
            'FieldMind 系统信息',
            registry=self.registry
        )
        self.system_info.info({
            'version': '2.0.0',
            'environment': settings.environment.value,
            'python_version': '3.11',
        })

        # ====== HTTP 请求指标 ======
        self.http_requests_total = Counter(
            'fieldmind_http_requests_total',
            'HTTP 请求总数',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'fieldmind_http_request_duration_seconds',
            'HTTP 请求处理时长（秒）',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )

        self.http_requests_in_progress = Gauge(
            'fieldmind_http_requests_in_progress',
            '正在处理的 HTTP 请求数',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # ====== 文档处理指标 ======
        self.document_processing_total = Counter(
            'fieldmind_document_processing_total',
            '文档处理总数',
            ['stage', 'doc_type', 'status'],
            registry=self.registry
        )

        self.document_processing_duration_seconds = Histogram(
            'fieldmind_document_processing_duration_seconds',
            '文档处理时长（秒）',
            ['stage', 'doc_type'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
            registry=self.registry
        )

        self.documents_in_processing = Gauge(
            'fieldmind_documents_in_processing',
            '正在处理的文档数',
            ['stage'],
            registry=self.registry
        )

        # ====== AI 服务指标 ======
        self.ai_requests_total = Counter(
            'fieldmind_ai_requests_total',
            'AI 服务请求总数',
            ['provider', 'model', 'operation', 'status'],
            registry=self.registry
        )

        self.ai_request_duration_seconds = Histogram(
            'fieldmind_ai_request_duration_seconds',
            'AI 服务请求时长（秒）',
            ['provider', 'model', 'operation'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
            registry=self.registry
        )

        self.ai_tokens_used_total = Counter(
            'fieldmind_ai_tokens_used_total',
            'AI 服务使用的 token 总数',
            ['provider', 'model', 'token_type'],
            registry=self.registry
        )

        # ====== 向量数据库指标 ======
        self.vector_operations_total = Counter(
            'fieldmind_vector_operations_total',
            '向量数据库操作总数',
            ['operation', 'collection', 'status'],
            registry=self.registry
        )

        self.vector_operation_duration_seconds = Histogram(
            'fieldmind_vector_operation_duration_seconds',
            '向量数据库操作时长（秒）',
            ['operation', 'collection'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )

        self.vector_embeddings_total = Counter(
            'fieldmind_vector_embeddings_total',
            '生成的向量 embedding 总数',
            ['model', 'doc_type'],
            registry=self.registry
        )

        # ====== 图数据库指标 ======
        self.graph_operations_total = Counter(
            'fieldmind_graph_operations_total',
            '图数据库操作总数',
            ['operation', 'label', 'status'],
            registry=self.registry
        )

        self.graph_operation_duration_seconds = Histogram(
            'fieldmind_graph_operation_duration_seconds',
            '图数据库操作时长（秒）',
            ['operation', 'label'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )

        self.graph_nodes_total = Gauge(
            'fieldmind_graph_nodes_total',
            '图数据库节点总数',
            ['label'],
            registry=self.registry
        )

        self.graph_relationships_total = Gauge(
            'fieldmind_graph_relationships_total',
            '图数据库关系总数',
            ['type'],
            registry=self.registry
        )

        # ====== 数据库连接池指标 ======
        self.database_connections_active = Gauge(
            'fieldmind_database_connections_active',
            '数据库活跃连接数',
            ['pool'],
            registry=self.registry
        )

        self.database_connections_idle = Gauge(
            'fieldmind_database_connections_idle',
            '数据库空闲连接数',
            ['pool'],
            registry=self.registry
        )

        self.database_operations_total = Counter(
            'fieldmind_database_operations_total',
            '数据库操作总数',
            ['operation', 'table', 'status'],
            registry=self.registry
        )

        self.database_operation_duration_seconds = Histogram(
            'fieldmind_database_operation_duration_seconds',
            '数据库操作时长（秒）',
            ['operation', 'table'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )

        # ====== Redis 缓存指标 ======
        self.cache_operations_total = Counter(
            'fieldmind_cache_operations_total',
            '缓存操作总数',
            ['operation', 'status'],
            registry=self.registry
        )

        self.cache_hit_ratio = Gauge(
            'fieldmind_cache_hit_ratio',
            '缓存命中率',
            registry=self.registry
        )

        self.cache_keys_total = Gauge(
            'fieldmind_cache_keys_total',
            '缓存键总数',
            registry=self.registry
        )

        # ====== 系统资源指标 ======
        self.system_cpu_usage_percent = Gauge(
            'fieldmind_system_cpu_usage_percent',
            'CPU 使用率（%）',
            registry=self.registry
        )

        self.system_memory_usage_bytes = Gauge(
            'fieldmind_system_memory_usage_bytes',
            '内存使用量（字节）',
            registry=self.registry
        )

        self.system_memory_usage_percent = Gauge(
            'fieldmind_system_memory_usage_percent',
            '内存使用率（%）',
            registry=self.registry
        )

        self.system_disk_usage_percent = Gauge(
            'fieldmind_system_disk_usage_percent',
            '磁盘使用率（%）',
            ['path'],
            registry=self.registry
        )

        # ====== 错误指标 ======
        self.errors_total = Counter(
            'fieldmind_errors_total',
            '错误总数',
            ['error_code', 'error_type', 'component'],
            registry=self.registry
        )

        # ====== 业务指标 ======
        self.documents_total = Gauge(
            'fieldmind_documents_total',
            '文档总数',
            ['status'],
            registry=self.registry
        )

        self.knowledge_graph_entities_total = Gauge(
            'fieldmind_knowledge_graph_entities_total',
            '知识图谱实体总数',
            ['entity_type'],
            registry=self.registry
        )

        self.workflow_executions_total = Counter(
            'fieldmind_workflow_executions_total',
            '工作流执行总数',
            ['workflow', 'status'],
            registry=self.registry
        )

        logger.info("✅ Prometheus 指标管理器初始化完成")

    def update_system_metrics(self):
        """更新系统资源指标"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.system_cpu_usage_percent.set(cpu_percent)

            # 内存使用
            memory = psutil.virtual_memory()
            self.system_memory_usage_bytes.set(memory.used)
            self.system_memory_usage_percent.set(memory.percent)

            # 磁盘使用
            disk = psutil.disk_usage('/')
            self.system_disk_usage_percent.labels(path='/').set(disk.percent)

        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")

    def get_metrics(self) -> bytes:
        """
        获取所有指标的 Prometheus 格式输出

        Returns:
            bytes: Prometheus 格式的指标数据
        """
        # 更新系统指标
        self.update_system_metrics()

        return generate_latest(self.registry)


# 全局指标管理器实例
metrics_manager = MetricsManager()


# ====== 上下文管理器和装饰器 ======

@contextmanager
def track_request(method: str, endpoint: str, status_code: Optional[int] = None):
    """
    追踪 HTTP 请求

    Args:
        method: HTTP 方法（GET, POST, etc.）
        endpoint: API 端点
        status_code: HTTP 状态码（在 finally 中设置）

    Example:
        with track_request("POST", "/api/upload") as tracker:
            result = process_request()
            tracker.set_status(200)
    """
    start_time = time.time()
    metrics_manager.http_requests_in_progress.labels(
        method=method,
        endpoint=endpoint
    ).inc()

    class Tracker:
        def __init__(self):
            self.status_code = status_code or 200

        def set_status(self, code: int):
            self.status_code = code

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status_code = 500
        logger.error(f"请求处理失败: {method} {endpoint} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=tracker.status_code
        ).inc()

        metrics_manager.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        metrics_manager.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()


@contextmanager
def track_processing(stage: str, doc_type: str, status: str = "success"):
    """
    追踪文档处理

    Args:
        stage: 处理阶段（multimodal, semantic, network, etc.）
        doc_type: 文档类型（pdf, video, audio, etc.）
        status: 处理状态（success, failure）

    Example:
        with track_processing("multimodal", "pdf") as tracker:
            process_document()
            # 如果失败，可以设置: tracker.set_status("failure")
    """
    start_time = time.time()
    metrics_manager.documents_in_processing.labels(stage=stage).inc()

    class Tracker:
        def __init__(self):
            self.status = status

        def set_status(self, s: str):
            self.status = s

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status = "failure"
        logger.error(f"文档处理失败: {stage}/{doc_type} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.document_processing_total.labels(
            stage=stage,
            doc_type=doc_type,
            status=tracker.status
        ).inc()

        metrics_manager.document_processing_duration_seconds.labels(
            stage=stage,
            doc_type=doc_type
        ).observe(duration)

        metrics_manager.documents_in_processing.labels(stage=stage).dec()


@contextmanager
def track_database_operation(operation: str, table: str, status: str = "success"):
    """
    追踪数据库操作

    Args:
        operation: 操作类型（query, insert, update, delete）
        table: 表名
        status: 操作状态（success, failure）
    """
    start_time = time.time()

    class Tracker:
        def __init__(self):
            self.status = status

        def set_status(self, s: str):
            self.status = s

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status = "failure"
        logger.error(f"数据库操作失败: {operation} on {table} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.database_operations_total.labels(
            operation=operation,
            table=table,
            status=tracker.status
        ).inc()

        metrics_manager.database_operation_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)


@contextmanager
def track_ai_operation(
    provider: str,
    model: str,
    operation: str,
    status: str = "success"
):
    """
    追踪 AI 服务操作

    Args:
        provider: AI 服务提供商（openai, anthropic, whisper）
        model: 模型名称（gpt-4, claude-3-opus, etc.）
        operation: 操作类型（chat, embedding, transcribe）
        status: 操作状态（success, failure）
    """
    start_time = time.time()

    class Tracker:
        def __init__(self):
            self.status = status
            self.tokens_used = {'input': 0, 'output': 0}

        def set_status(self, s: str):
            self.status = s

        def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
            self.tokens_used['input'] = input_tokens
            self.tokens_used['output'] = output_tokens

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status = "failure"
        logger.error(f"AI 服务操作失败: {provider}/{model}/{operation} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.ai_requests_total.labels(
            provider=provider,
            model=model,
            operation=operation,
            status=tracker.status
        ).inc()

        metrics_manager.ai_request_duration_seconds.labels(
            provider=provider,
            model=model,
            operation=operation
        ).observe(duration)

        # 记录 token 使用量
        if tracker.tokens_used['input'] > 0:
            metrics_manager.ai_tokens_used_total.labels(
                provider=provider,
                model=model,
                token_type='input'
            ).inc(tracker.tokens_used['input'])

        if tracker.tokens_used['output'] > 0:
            metrics_manager.ai_tokens_used_total.labels(
                provider=provider,
                model=model,
                token_type='output'
            ).inc(tracker.tokens_used['output'])


@contextmanager
def track_vector_operation(operation: str, collection: str, status: str = "success"):
    """
    追踪向量数据库操作

    Args:
        operation: 操作类型（add, query, update, delete）
        collection: 集合名称
        status: 操作状态（success, failure）
    """
    start_time = time.time()

    class Tracker:
        def __init__(self):
            self.status = status

        def set_status(self, s: str):
            self.status = s

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status = "failure"
        logger.error(f"向量数据库操作失败: {operation} on {collection} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.vector_operations_total.labels(
            operation=operation,
            collection=collection,
            status=tracker.status
        ).inc()

        metrics_manager.vector_operation_duration_seconds.labels(
            operation=operation,
            collection=collection
        ).observe(duration)


@contextmanager
def track_graph_operation(operation: str, label: str, status: str = "success"):
    """
    追踪图数据库操作

    Args:
        operation: 操作类型（create_node, create_rel, query, update, delete）
        label: 节点标签或关系类型
        status: 操作状态（success, failure）
    """
    start_time = time.time()

    class Tracker:
        def __init__(self):
            self.status = status

        def set_status(self, s: str):
            self.status = s

    tracker = Tracker()

    try:
        yield tracker
    except Exception as e:
        tracker.status = "failure"
        logger.error(f"图数据库操作失败: {operation} on {label} - {e}")
        raise
    finally:
        duration = time.time() - start_time

        metrics_manager.graph_operations_total.labels(
            operation=operation,
            label=label,
            status=tracker.status
        ).inc()

        metrics_manager.graph_operation_duration_seconds.labels(
            operation=operation,
            label=label
        ).observe(duration)


def record_error(
    error_code: ErrorCode,
    error_type: str,
    component: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    记录错误

    Args:
        error_code: 错误码（来自 ErrorCode 枚举）
        error_type: 错误类型（ValueError, DatabaseError, etc.）
        component: 组件名称（multimodal_processor, workflow_chain, etc.）
        details: 额外的错误详情
    """
    metrics_manager.errors_total.labels(
        error_code=error_code.value,
        error_type=error_type,
        component=component
    ).inc()

    logger.error(
        f"记录错误: [{error_code.value}] {error_type} in {component}",
        extra={
            'error_code': error_code.value,
            'error_type': error_type,
            'component': component,
            'details': details or {}
        }
    )


def get_metrics_handler():
    """
    获取 Prometheus 指标处理器（用于 FastAPI 端点）

    Returns:
        tuple: (content, content_type)

    Example:
        @app.get("/metrics")
        async def metrics():
            content, content_type = get_metrics_handler()
            return Response(content=content, media_type=content_type)
    """
    return metrics_manager.get_metrics(), CONTENT_TYPE_LATEST
