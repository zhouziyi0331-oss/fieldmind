"""
API Gateway 主入口

整合所有组件，提供统一的API服务
"""
import logging
from fastapi import FastAPI
from app.api.gateway.core import get_api_gateway
from app.api.gateway.auth import AuthenticationMiddleware
from app.api.gateway.rate_limit import RateLimitMiddleware
from app.api.gateway.router import get_router_manager

logger = logging.getLogger(__name__)


def create_gateway_app(
    title: str = "FieldMind API Gateway",
    version: str = "1.0.0",
    debug: bool = False
) -> FastAPI:
    """
    创建API Gateway应用

    Args:
        title: 应用标题
        version: 版本号
        debug: 是否调试模式

    Returns:
        FastAPI应用实例
    """
    logger.info(f"🚀 创建API Gateway: {title} v{version}")

    # 1. 创建Gateway核心
    gateway = get_api_gateway(
        title=title,
        version=version,
        debug=debug
    )

    # 2. 添加认证中间件
    auth_middleware = AuthenticationMiddleware(
        gateway.app,
        skip_paths=[
            "/health",
            "/stats",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
    )
    gateway.app.add_middleware(AuthenticationMiddleware)

    # 3. 添加限流中间件
    rate_limit_middleware = RateLimitMiddleware(
        gateway.app,
        default_limit="100/minute",
        algorithm="token_bucket",
        skip_paths=[
            "/health",
            "/stats",
            "/api/docs",
            "/api/redoc",
            "/openapi.json"
        ]
    )
    gateway.app.add_middleware(RateLimitMiddleware)

    # 4. 注册路由
    router_manager = get_router_manager()
    gateway.app.include_router(router_manager.get_router())

    # 5. 添加启动事件
    @gateway.app.on_event("startup")
    async def startup_event():
        logger.info("✅ API Gateway 启动完成")
        logger.info(f"📋 注册路由数: {len(router_manager.get_routes_info())}")

    # 6. 添加关闭事件
    @gateway.app.on_event("shutdown")
    async def shutdown_event():
        logger.info("👋 API Gateway 关闭")

    logger.info("✅ API Gateway 应用创建完成")

    return gateway.app


# 创建应用实例
app = create_gateway_app(
    title="FieldMind API Gateway",
    version="1.0.0",
    debug=False
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
