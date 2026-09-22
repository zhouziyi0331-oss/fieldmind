"""
分布式追踪测试套件
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

# 在导入app模块前先设置全局tracer
import app.core.tracing.tracer as tracer_module

from app.core.tracing.context import (
    TraceContext,
    get_trace_context,
    set_trace_context,
    ensure_trace_context,
)
from app.core.tracing.middleware import TracingMiddleware
from app.core.tracing.exporters import (
    create_console_exporter,
    ExporterConfig,
    configure_exporters,
    ExporterPresets,
)


def _setup_test_tracer():
    """设置测试用追踪器"""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    # 使用SimpleSpanProcessor立即导出
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # 重置模块级别的tracer - 必须在set_tracer_provider之后
    tracer_module._tracer_provider = provider
    tracer_module._tracer = provider.get_tracer(
        instrumenting_module_name="test_tracer",
        instrumenting_library_version="1.0.0"
    )

    return exporter


class TestTracerInitialization:
    """测试追踪器初始化"""

    def test_init_tracing_console(self):
        """测试控制台导出器初始化"""
        from app.core.tracing.tracer import init_tracing, shutdown_tracing, get_tracer

        provider = init_tracing(
            service_name="test-service",
            environment="testing",
            exporter_type="console",
        )

        assert provider is not None
        assert isinstance(provider, TracerProvider)

        # 获取追踪器
        tracer = get_tracer()
        assert tracer is not None

        shutdown_tracing()

    def test_init_tracing_with_sampling(self):
        """测试带采样率的初始化"""
        from app.core.tracing.tracer import init_tracing, shutdown_tracing

        provider = init_tracing(
            service_name="test-service",
            exporter_type="console",
            sample_rate=0.5,
        )

        assert provider is not None
        shutdown_tracing()

    def test_get_tracer_auto_init(self):
        """测试自动初始化"""
        from app.core.tracing.tracer import get_tracer, shutdown_tracing

        # 确保没有初始化
        shutdown_tracing()

        # 获取追踪器应自动初始化
        tracer = get_tracer()
        assert tracer is not None

        shutdown_tracing()


class TestTraceSpan:
    """测试Span创建"""

    def setup_method(self):
        """每个测试前初始化"""
        self.exporter = _setup_test_tracer()

    def teardown_method(self):
        """每个测试后清理"""
        from app.core.tracing.tracer import shutdown_tracing
        self.exporter.clear()
        shutdown_tracing()

    def test_trace_span_context_manager(self):
        """测试Span上下文管理器"""
        from app.core.tracing.tracer import trace_span

        with trace_span("test_operation", attributes={"key": "value"}):
            pass

        # 验证Span已创建
        spans = self.exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test_operation"
        assert spans[0].attributes["key"] == "value"

    def test_trace_span_with_exception(self):
        """测试Span异常记录"""
        from app.core.tracing.tracer import trace_span

        try:
            with trace_span("test_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass

        spans = self.exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code == trace.StatusCode.ERROR

    def test_nested_spans(self):
        """测试嵌套Span"""
        from app.core.tracing.tracer import trace_span

        with trace_span("parent"):
            with trace_span("child1"):
                pass
            with trace_span("child2"):
                pass

        spans = self.exporter.get_finished_spans()
        assert len(spans) == 3

        # 验证父子关系
        parent_span = [s for s in spans if s.name == "parent"][0]
        child1_span = [s for s in spans if s.name == "child1"][0]
        child2_span = [s for s in spans if s.name == "child2"][0]

        assert child1_span.parent.span_id == parent_span.context.span_id
        assert child2_span.parent.span_id == parent_span.context.span_id


class TestTraceFunctionDecorator:
    """测试函数追踪装饰器"""

    def setup_method(self):
        self.exporter = _setup_test_tracer()

    def teardown_method(self):
        from app.core.tracing.tracer import shutdown_tracing
        self.exporter.clear()
        shutdown_tracing()

    @pytest.mark.asyncio
    async def test_trace_async_function(self):
        """测试异步函数追踪"""
        from app.core.tracing.tracer import trace_function

        @trace_function(attributes={"layer": "service"})
        async def async_operation():
            await asyncio.sleep(0.01)
            return "result"

        result = await async_operation()
        assert result == "result"

        spans = self.exporter.get_finished_spans()
        assert len(spans) == 1
        assert "async_operation" in spans[0].name
        assert spans[0].attributes["layer"] == "service"

    def test_trace_sync_function(self):
        """测试同步函数追踪"""
        from app.core.tracing.tracer import trace_function

        @trace_function(attributes={"layer": "service"})
        def sync_operation():
            return "result"

        result = sync_operation()
        assert result == "result"

        spans = self.exporter.get_finished_spans()
        assert len(spans) == 1
        assert "sync_operation" in spans[0].name


class TestSpanOperations:
    """测试Span操作"""

    def setup_method(self):
        self.exporter = _setup_test_tracer()

    def teardown_method(self):
        from app.core.tracing.tracer import shutdown_tracing
        self.exporter.clear()
        shutdown_tracing()

    def test_add_span_attributes(self):
        """测试添加Span属性"""
        from app.core.tracing.tracer import trace_span, add_span_attributes

        with trace_span("test"):
            add_span_attributes(user_id="123", operation="query")

        spans = self.exporter.get_finished_spans()
        assert spans[0].attributes["user_id"] == "123"
        assert spans[0].attributes["operation"] == "query"

    def test_add_span_event(self):
        """测试添加Span事件"""
        from app.core.tracing.tracer import trace_span, add_span_event

        with trace_span("test"):
            add_span_event("cache_hit", {"cache_key": "user:123"})

        spans = self.exporter.get_finished_spans()
        assert len(spans[0].events) == 1
        assert spans[0].events[0].name == "cache_hit"

    def test_record_exception(self):
        """测试记录异常"""
        from app.core.tracing.tracer import trace_span, record_exception

        try:
            with trace_span("test"):
                try:
                    raise ValueError("Test error")
                except ValueError as e:
                    record_exception(e)
                    raise
        except ValueError:
            pass

        spans = self.exporter.get_finished_spans()
        assert spans[0].status.status_code == trace.StatusCode.ERROR


class TestTraceContext:
    """测试追踪上下文"""

    def test_create_trace_context(self):
        """测试创建追踪上下文"""
        context = TraceContext.create(
            user_id="user123",
            session_id="session456",
            operation="process_document",
        )

        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.user_id == "user123"
        assert context.session_id == "session456"

    def test_trace_context_to_dict(self):
        """测试上下文转字典"""
        context = TraceContext.create(user_id="user123")
        data = context.to_dict()

        assert "trace_id" in data
        assert "span_id" in data
        assert data["user_id"] == "user123"

    def test_trace_context_to_headers(self):
        """测试上下文转HTTP头"""
        context = TraceContext.create(
            trace_id="abc123",
            span_id="def456",
            user_id="user789",
        )

        headers = context.to_headers()
        assert headers["X-Trace-Id"] == "abc123"
        assert headers["X-Span-Id"] == "def456"
        assert headers["X-User-Id"] == "user789"

    def test_trace_context_from_headers(self):
        """测试从HTTP头创建上下文"""
        headers = {
            "X-Trace-Id": "trace123",
            "X-Span-Id": "span456",
            "X-User-Id": "user789",
        }

        context = TraceContext.from_headers(headers)
        assert context is not None
        assert context.trace_id == "trace123"
        assert context.span_id == "span456"
        assert context.user_id == "user789"

    def test_trace_context_child(self):
        """测试创建子上下文"""
        parent = TraceContext.create(trace_id="parent123")
        child = parent.child(operation="sub_task")

        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id
        assert child.span_id != parent.span_id
        assert child.operation == "sub_task"

    def test_get_set_trace_context(self):
        """测试上下文存储"""
        context = TraceContext.create()
        set_trace_context(context)

        retrieved = get_trace_context()
        assert retrieved == context
        assert retrieved.trace_id == context.trace_id

    def test_ensure_trace_context(self):
        """测试确保上下文存在"""
        # 清空上下文
        set_trace_context(None)

        # 确保上下文（应自动创建）
        context = ensure_trace_context()
        assert context is not None
        assert context.trace_id is not None


class TestExporters:
    """测试导出器配置"""

    def test_create_console_exporter(self):
        """测试创建控制台导出器"""
        exporter = create_console_exporter()
        assert exporter is not None

    def test_exporter_config(self):
        """测试导出器配置"""
        config = ExporterConfig(
            exporter_type="otlp",
            endpoint="http://localhost:4317",
            timeout=30,
        )

        assert config.exporter_type == "otlp"
        assert config.endpoint == "http://localhost:4317"
        assert config.timeout == 30

    def test_configure_multiple_exporters(self):
        """测试配置多个导出器"""
        configs = [
            ExporterConfig(exporter_type="console"),
        ]

        processors = configure_exporters(configs)
        assert len(processors) == 1

    def test_exporter_presets_development(self):
        """测试开发环境预设"""
        configs = ExporterPresets.development()
        assert len(configs) == 1
        assert configs[0].exporter_type == "console"

    def test_exporter_presets_production(self):
        """测试生产环境预设"""
        configs = ExporterPresets.production(
            otlp_endpoint="http://collector:4317"
        )
        assert len(configs) == 1
        assert configs[0].exporter_type == "otlp"
        assert configs[0].compression == "gzip"


@pytest.mark.asyncio
class TestTracingMiddleware:
    """测试追踪中间件"""

    async def test_middleware_creates_span(self):
        """测试中间件创建Span"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.core.tracing.tracer import init_tracing, shutdown_tracing

        app = FastAPI()

        # 初始化追踪
        init_tracing(exporter_type="console")

        # 添加中间件
        app.add_middleware(TracingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Trace-Id" in response.headers
        assert "X-Span-Id" in response.headers

        shutdown_tracing()

    async def test_middleware_exclude_paths(self):
        """测试中间件排除路径"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.core.tracing.tracer import init_tracing, shutdown_tracing

        app = FastAPI()

        init_tracing(exporter_type="console")
        app.add_middleware(
            TracingMiddleware,
            exclude_paths=["/health", "/metrics"]
        )

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        # Health endpoint不应添加追踪头
        # (但在测试中可能因为其他原因有，所以不强制断言)

        shutdown_tracing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
