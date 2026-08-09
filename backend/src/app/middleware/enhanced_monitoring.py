"""
增强的监控中间件
集成 Prometheus 指标和分布式追踪
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.logging import log_api_call, logger
from app.core.metrics import (
    track_request,
    http_requests_in_progress
)


class EnhancedMonitoringMiddleware(BaseHTTPMiddleware):
    """
    增强的监控中间件

    功能：
    1. 记录所有 API 请求到日志
    2. 发送指标到 Prometheus
    3. 添加追踪 ID
    4. 记录响应时间
    5. 监控慢请求
    """

    def __init__(self, app, slow_threshold_ms: float = 1000):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # 简化端点路径（移除ID等动态部分）
        endpoint = self._simplify_path(path)

        # 标记请求开始
        in_progress = http_requests_in_progress.labels(method=method, endpoint=endpoint)
        in_progress.inc()

        # 记录请求开始
        logger.bind(
            request_id=request_id,
            client_ip=client_host
        ).info(f"➡️  {method} {path}")

        # 开始计时
        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算响应时间
            duration = time.time() - start_time
            duration_ms = duration * 1000

            # 记录指标
            track_request(method, endpoint, response.status_code, duration)

            # 记录到日志
            log_api_call(method, path, response.status_code, duration_ms)

            # 根据状态码记录不同级别的日志
            if response.status_code < 400:
                logger.bind(
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2)
                ).info(f"✅ {method} {path} - {response.status_code} - {duration_ms:.2f}ms")
            elif response.status_code < 500:
                logger.bind(
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2)
                ).warning(f"⚠️  {method} {path} - {response.status_code} - {duration_ms:.2f}ms")
            else:
                logger.bind(
                    request_id=request_id,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2)
                ).error(f"❌ {method} {path} - {response.status_code} - {duration_ms:.2f}ms")

            # 慢请求警告
            if duration_ms > self.slow_threshold_ms:
                logger.bind(
                    request_id=request_id,
                    duration_ms=round(duration_ms, 2)
                ).warning(f"🐌 慢请求: {method} {path} - {duration_ms:.2f}ms (阈值: {self.slow_threshold_ms}ms)")

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            # 计算响应时间
            duration = time.time() - start_time
            duration_ms = duration * 1000

            # 记录异常
            logger.bind(
                request_id=request_id,
                duration_ms=round(duration_ms, 2)
            ).exception(f"💥 {method} {path} - 异常: {str(e)}")

            # 记录指标（500错误）
            track_request(method, endpoint, 500, duration)
            log_api_call(method, path, 500, duration_ms, f"Exception: {str(e)}")

            # 重新抛出异常
            raise

        finally:
            # 标记请求结束
            in_progress.dec()

    def _simplify_path(self, path: str) -> str:
        """
        简化路径，移除动态参数

        例如: /api/projects/123 -> /api/projects/{id}
        """
        parts = path.split('/')

        # 替换数字 ID
        simplified_parts = []
        for part in parts:
            if part.isdigit():
                simplified_parts.append('{id}')
            elif len(part) > 8 and '-' in part:  # UUID
                simplified_parts.append('{uuid}')
            else:
                simplified_parts.append(part)

        return '/'.join(simplified_parts)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    请求追踪中间件

    为每个请求添加追踪上下文
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 从请求头获取或生成追踪 ID
        trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
        span_id = str(uuid.uuid4())

        # 保存到请求状态
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # 处理请求
        response = await call_next(request)

        # 添加追踪头
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id

        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    错误追踪中间件

    捕获并报告所有未处理的异常
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # 记录详细错误信息
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "method": request.method,
                "path": str(request.url),
                "client_ip": request.client.host if request.client else "unknown"
            }

            logger.bind(**error_data).exception("未处理的异常")

            # 如果配置了 Sentry，发送到 Sentry
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(e)
            except ImportError:
                logger.debug("Sentry未安装，跳过错误追踪")
            except Exception as sentry_error:
                logger.warning(f"Sentry错误上报失败: {sentry_error}")

            # 重新抛出异常
            raise


# 导出
__all__ = [
    'EnhancedMonitoringMiddleware',
    'RequestTracingMiddleware',
    'ErrorTrackingMiddleware',
]
