"""
监控中间件
自动收集 HTTP 请求的性能指标
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import (
    record_http_request,
    http_requests_in_progress,
    record_error
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    监控中间件

    自动收集所有HTTP请求的性能指标
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 提取端点路径（去除查询参数）
        endpoint = request.url.path
        method = request.method

        # 标记请求开始
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            duration = time.time() - start_time

            # 记录指标
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
                duration=duration
            )

            # 如果是错误响应，记录错误
            if response.status_code >= 400:
                error_code = getattr(request.state, "error_code", "UNKNOWN")
                record_error(error_code=error_code, endpoint=endpoint)

            return response

        except Exception as e:
            # 记录异常
            duration = time.time() - start_time
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=500,
                duration=duration
            )
            record_error(error_code="INTERNAL_ERROR", endpoint=endpoint)
            raise

        finally:
            # 标记请求结束
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
