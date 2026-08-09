"""
API性能监控中间件
自动追踪所有API请求的性能
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """拦截请求并记录性能"""
        start_time = time.time()

        # 执行请求
        response = await call_next(request)

        # 计算耗时
        duration = time.time() - start_time

        # 记录日志
        logger.info(
            f"⏱️ {request.method} {request.url.path} "
            f"[{response.status_code}] {duration:.3f}s"
        )

        # 添加性能header
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """记录请求详情"""
        # 记录请求
        logger.info(
            f"📥 {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"❌ {request.method} {request.url.path} - Error: {e}")
            raise
