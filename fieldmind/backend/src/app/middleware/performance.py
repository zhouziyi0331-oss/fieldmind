"""
中间件：请求追踪和性能监控
自动记录所有 API 请求的性能指标
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.prometheus_service import prometheus
from app.services.sentry_service import sentry

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 开始计时
        start_time = time.time()

        # 设置请求 ID（用于追踪）
        request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")
        request.state.request_id = request_id

        # 添加 Sentry 面包屑
        sentry.add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="http.request",
            level="info",
            data={
                "method": request.method,
                "url": str(request.url),
                "request_id": request_id,
            }
        )

        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # 捕获未处理的异常
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "error": str(e)
                }
            )

            # 发送到 Sentry
            sentry.capture_exception(e, request_context={
                "method": request.method,
                "url": str(request.url),
                "request_id": request_id,
                "duration": duration,
            })

            # 记录 Prometheus 指标
            prometheus.track_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration
            )

            raise

        # 计算请求时长
        duration = time.time() - start_time

        # 记录到 Prometheus
        prometheus.track_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=status_code,
            duration=duration
        )

        # 记录慢请求
        if duration > 1.0:  # 超过 1 秒
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "status_code": status_code,
                }
            )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


class UserContextMiddleware(BaseHTTPMiddleware):
    """用户上下文中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 从 JWT token 中提取用户信息（简化版）
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            # 这里应该解析 JWT token 获取用户信息
            # 简化版本，仅作示例
            try:
                # 设置用户信息到 Sentry
                sentry.set_user(
                    user_id=None,  # 从 token 解析
                    email=None,    # 从 token 解析
                )
            except Exception as e:
                logger.debug(f"Failed to set user context: {e}")

        response = await call_next(request)
        return response
