"""
请求追踪中间件
为每个请求生成唯一ID，用于日志追踪和调试
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件

    为每个请求分配唯一的request_id，并添加到响应头
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 从请求头获取或生成新的 request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # 将 request_id 存储到请求状态中
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """
    自定义CORS中间件

    处理跨域请求
    """

    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 处理 OPTIONS 预检请求
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # 处理实际请求
        response = await call_next(request)

        # 添加 CORS 头
        origin = request.headers.get("origin")
        if origin and (self.allow_origins == ["*"] or origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


def register_middlewares(app):
    """
    注册所有中间件到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    # 请求ID中间件
    app.add_middleware(RequestIDMiddleware)

    # CORS中间件（如果需要）
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["http://localhost:3000"],
    #     allow_methods=["*"],
    #     allow_headers=["*"]
    # )
