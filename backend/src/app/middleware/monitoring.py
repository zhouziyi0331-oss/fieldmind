"""
监控中间件
记录所有 API 请求和性能指标
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.logging import log_api_call, logger


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    监控中间件

    功能：
    1. 记录所有 API 请求
    2. 记录响应时间
    3. 记录错误
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 开始时间
        start_time = time.time()

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.debug(f"🔵 {method} {path} - 来自 {client_host}")

        # 处理请求
        try:
            response = await call_next(request)

            # 计算响应时间
            duration_ms = (time.time() - start_time) * 1000

            # 记录成功的请求
            status_code = response.status_code

            if status_code < 400:
                log_api_call(method, path, status_code, duration_ms)
                logger.debug(f"✅ {method} {path} - {status_code} - {duration_ms:.2f}ms")
            elif status_code < 500:
                log_api_call(method, path, status_code, duration_ms, "Client Error")
                logger.warning(f"⚠️ {method} {path} - {status_code} - {duration_ms:.2f}ms")
            else:
                log_api_call(method, path, status_code, duration_ms, "Server Error")
                logger.error(f"❌ {method} {path} - {status_code} - {duration_ms:.2f}ms")

            # 添加响应头
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            # 计算响应时间
            duration_ms = (time.time() - start_time) * 1000

            # 记录异常
            logger.exception(f"💥 {method} {path} - Exception after {duration_ms:.2f}ms: {str(e)}")
            log_api_call(method, path, 500, duration_ms, f"Exception: {str(e)}")

            # 重新抛出异常，让 FastAPI 的异常处理器处理
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    监控慢请求
    """

    def __init__(self, app, slow_threshold_ms: float = 1000):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # 记录慢请求
        if duration_ms > self.slow_threshold_ms:
            logger.warning(
                f"🐌 慢请求: {request.method} {request.url.path} - {duration_ms:.2f}ms"
            )

        return response
