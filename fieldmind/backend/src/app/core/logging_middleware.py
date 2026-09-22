"""
日志中间件
自动记录所有API请求和响应
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import log_request, logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件

    自动记录所有HTTP请求和响应
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始
        start_time = time.time()
        request_id = getattr(request.state, "request_id", None)

        # 获取客户端IP
        client_ip = request.client.host if request.client else None

        # 获取用户ID（如果有认证）
        user_id = getattr(request.state, "user_id", None)

        # 记录请求开始
        logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_id=user_id
        ).debug(f"Request started: {request.method} {request.url.path}")

        # 处理请求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 记录请求完成
            log_request(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time,
                client_ip=client_ip,
                user_id=user_id
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # 记录请求失败
            logger.bind(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                error=str(e),
                duration_ms=round(process_time * 1000, 2)
            ).error(f"Request failed: {request.method} {request.url.path}")

            raise
