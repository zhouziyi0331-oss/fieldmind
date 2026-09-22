"""
API Gateway 核心类

统一的API入口，负责路由、认证、限流、监控
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import time
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

logger = logging.getLogger(__name__)


class APIGateway:
    """API Gateway 主类"""

    def __init__(
        self,
        title: str = "FieldMind API Gateway",
        version: str = "1.0.0",
        debug: bool = False
    ):
        """
        初始化API Gateway

        Args:
            title: API标题
            version: API版本
            debug: 是否开启调试模式
        """
        self.app = FastAPI(
            title=title,
            version=version,
            debug=debug,
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )

        # 配置
        self.version = version
        self.debug = debug

        # 中间件列表
        self.middlewares: List[BaseHTTPMiddleware] = []

        # 路由映射
        self.route_mappings: Dict[str, str] = {}

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'total_errors': 0,
            'total_success': 0,
            'start_time': datetime.utcnow()
        }

        # 初始化
        self._setup_cors()
        self._setup_middleware()
        self._setup_routes()

        logger.info(f"✅ API Gateway 初始化完成: {title} v{version}")

    def _setup_cors(self):
        """配置CORS"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境应该限制
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_middleware(self):
        """配置中间件"""
        # 请求ID中间件
        self.app.middleware("http")(self._request_id_middleware)

        # 请求日志中间件
        self.app.middleware("http")(self._logging_middleware)

        # 性能监控中间件
        self.app.middleware("http")(self._performance_middleware)

        # 异常处理中间件
        self.app.add_exception_handler(Exception, self._exception_handler)

    def _setup_routes(self):
        """配置路由"""
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return self._success_response({
                "status": "healthy",
                "version": self.version,
                "uptime": (datetime.utcnow() - self.stats['start_time']).total_seconds()
            })

        # 统计信息
        @self.app.get("/stats")
        async def get_stats():
            return self._success_response({
                **self.stats,
                'uptime': (datetime.utcnow() - self.stats['start_time']).total_seconds(),
                'start_time': self.stats['start_time'].isoformat()
            })

    # ==================== 中间件实现 ====================

    async def _request_id_middleware(self, request: Request, call_next):
        """请求ID中间件 - 为每个请求生成唯一ID"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

    async def _logging_middleware(self, request: Request, call_next):
        """日志中间件 - 记录所有请求"""
        start_time = time.time()

        # 请求日志
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"[{request.state.request_id}]"
        )

        response = await call_next(request)

        # 响应日志
        duration = time.time() - start_time
        logger.info(
            f"← {request.method} {request.url.path} "
            f"[{request.state.request_id}] "
            f"{response.status_code} ({duration:.3f}s)"
        )

        return response

    async def _performance_middleware(self, request: Request, call_next):
        """性能监控中间件"""
        start_time = time.time()

        # 更新统计
        self.stats['total_requests'] += 1

        response = await call_next(request)

        # 记录处理时间
        processing_time = time.time() - start_time
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"

        # 更新统计
        if response.status_code < 400:
            self.stats['total_success'] += 1
        else:
            self.stats['total_errors'] += 1

        return response

    async def _exception_handler(self, request: Request, exc: Exception):
        """统一异常处理"""
        logger.error(
            f"❌ 未处理异常: {exc}",
            exc_info=True,
            extra={'request_id': getattr(request.state, 'request_id', 'unknown')}
        )

        return self._error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=getattr(request.state, 'request_id', None)
        )

    # ==================== 响应格式化 ====================

    def _success_response(
        self,
        data: Any,
        meta: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        成功响应格式

        Args:
            data: 响应数据
            meta: 元数据
            request_id: 请求ID

        Returns:
            JSON响应
        """
        response_data = {
            "success": True,
            "data": data,
            "error": None,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version,
                **(meta or {})
            }
        }

        if request_id:
            response_data["meta"]["request_id"] = request_id

        return JSONResponse(content=response_data)

    def _error_response(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        错误响应格式

        Args:
            error_code: 错误码
            message: 错误消息
            details: 错误详情
            status_code: HTTP状态码
            request_id: 请求ID

        Returns:
            JSON响应
        """
        response_data = {
            "success": False,
            "data": None,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.version
            }
        }

        if request_id:
            response_data["meta"]["request_id"] = request_id

        return JSONResponse(
            content=response_data,
            status_code=status_code
        )

    # ==================== 路由注册 ====================

    def register_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str] = ["GET"],
        **kwargs
    ):
        """
        注册路由

        Args:
            path: 路由路径
            handler: 处理函数
            methods: HTTP方法列表
            **kwargs: 其他FastAPI路由参数
        """
        for method in methods:
            if method == "GET":
                self.app.get(path, **kwargs)(handler)
            elif method == "POST":
                self.app.post(path, **kwargs)(handler)
            elif method == "PUT":
                self.app.put(path, **kwargs)(handler)
            elif method == "DELETE":
                self.app.delete(path, **kwargs)(handler)
            elif method == "PATCH":
                self.app.patch(path, **kwargs)(handler)

        logger.info(f"✅ 路由已注册: {methods} {path}")

    def add_middleware(self, middleware: BaseHTTPMiddleware):
        """
        添加自定义中间件

        Args:
            middleware: 中间件实例
        """
        self.app.add_middleware(middleware)
        self.middlewares.append(middleware)

        logger.info(f"✅ 中间件已添加: {middleware.__class__.__name__}")

    # ==================== 工具方法 ====================

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'uptime': (datetime.utcnow() - self.stats['start_time']).total_seconds(),
            'success_rate': (
                self.stats['total_success'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            ),
            'error_rate': (
                self.stats['total_errors'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            )
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'total_errors': 0,
            'total_success': 0,
            'start_time': datetime.utcnow()
        }
        logger.info("✅ 统计信息已重置")


# 全局实例
_gateway_instance = None


def get_api_gateway(
    title: str = "FieldMind API Gateway",
    version: str = "1.0.0",
    debug: bool = False
) -> APIGateway:
    """获取API Gateway单例"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = APIGateway(
            title=title,
            version=version,
            debug=debug
        )
    return _gateway_instance
