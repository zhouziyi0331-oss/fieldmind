"""
API Gateway 模块

统一的API入口，提供认证、限流、路由、监控等功能
"""
from app.api.gateway.core import APIGateway, get_api_gateway
from app.api.gateway.auth import (
    AuthenticationMiddleware,
    AuthService,
    require_auth,
    require_roles
)
from app.api.gateway.rate_limit import (
    RateLimitMiddleware,
    TokenBucket,
    SlidingWindow,
    rate_limit
)
from app.api.gateway.router import RouterManager, get_router_manager
from app.api.gateway.main import create_gateway_app, app

__all__ = [
    # 核心
    'APIGateway',
    'get_api_gateway',
    'create_gateway_app',
    'app',

    # 认证
    'AuthenticationMiddleware',
    'AuthService',
    'require_auth',
    'require_roles',

    # 限流
    'RateLimitMiddleware',
    'TokenBucket',
    'SlidingWindow',
    'rate_limit',

    # 路由
    'RouterManager',
    'get_router_manager'
]
