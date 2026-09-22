"""
API 限流中间件
防止 API 滥用，支持不同级别的限流策略
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """基于内存的限流器（生产环境建议使用 Redis）"""

    def __init__(self):
        # 存储每个客户端的请求记录：{client_id: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(
        self,
        client_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        检查是否允许请求

        Args:
            client_id: 客户端标识（IP 或用户 ID）
            endpoint: 端点路径
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            是否允许请求
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # 获取该客户端的请求记录
        request_history = self.requests[client_id]

        # 清理过期记录
        request_history[:] = [
            (ts, ep) for ts, ep in request_history
            if ts > cutoff_time
        ]

        # 统计该端点的请求数
        endpoint_requests = sum(1 for _, ep in request_history if ep == endpoint)

        # 判断是否超限
        if endpoint_requests >= max_requests:
            return False

        # 记录本次请求
        request_history.append((current_time, endpoint))
        return True

    def cleanup(self, max_age_seconds: int = 3600):
        """清理旧记录（定期调用）"""
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                (ts, ep) for ts, ep in self.requests[client_id]
                if ts > cutoff_time
            ]

            # 删除空记录
            if not self.requests[client_id]:
                del self.requests[client_id]


# 全局限流器实例
rate_limiter = RateLimiter()


# 限流规则配置
RATE_LIMIT_RULES = {
    # 全局默认限流
    "default": {
        "max_requests": 100,
        "window_seconds": 60,  # 100 次/分钟
    },

    # 认证相关端点（更严格）
    "/api/auth/login": {
        "max_requests": 5,
        "window_seconds": 60,  # 5 次/分钟
    },
    "/api/auth/register": {
        "max_requests": 3,
        "window_seconds": 300,  # 3 次/5分钟
    },

    # 数据上传端点
    "/api/v1/projects/{project_id}/documents/upload": {
        "max_requests": 10,
        "window_seconds": 60,  # 10 次/分钟
    },

    # AI API 调用端点
    "/api/chat": {
        "max_requests": 20,
        "window_seconds": 60,  # 20 次/分钟
    },
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查和监控端点
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        # 获取客户端标识
        client_id = self._get_client_id(request)

        # 获取端点路径
        endpoint = request.url.path

        # 查找匹配的限流规则
        rule = self._find_rule(endpoint)

        # 检查限流
        if not rate_limiter.is_allowed(
            client_id=client_id,
            endpoint=endpoint,
            max_requests=rule["max_requests"],
            window_seconds=rule["window_seconds"]
        ):
            logger.warning(
                f"Rate limit exceeded: {client_id} - {endpoint}",
                extra={
                    "client_id": client_id,
                    "endpoint": endpoint,
                    "rule": rule
                }
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {rule['max_requests']} requests per {rule['window_seconds']} seconds",
                    "retry_after": rule["window_seconds"]
                },
                headers={"Retry-After": str(rule["window_seconds"])}
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流头部
        response.headers["X-RateLimit-Limit"] = str(rule["max_requests"])
        response.headers["X-RateLimit-Window"] = str(rule["window_seconds"])

        return response

    def _get_client_id(self, request: Request) -> str:
        """
        获取客户端标识

        优先级：
        1. 认证用户 ID
        2. API Key
        3. IP 地址
        """
        # 1. 从 JWT token 获取用户 ID（如果已认证）
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # 2. 从 API Key 获取（如果有）
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:10]}"

        # 3. 使用 IP 地址
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host}"

    def _find_rule(self, endpoint: str) -> dict:
        """查找匹配的限流规则"""
        # 精确匹配
        if endpoint in RATE_LIMIT_RULES:
            return RATE_LIMIT_RULES[endpoint]

        # 前缀匹配
        for pattern, rule in RATE_LIMIT_RULES.items():
            if pattern != "default" and endpoint.startswith(pattern.split("{")[0]):
                return rule

        # 返回默认规则
        return RATE_LIMIT_RULES["default"]


# 定期清理任务（应该在启动时注册）
async def cleanup_rate_limiter():
    """定期清理限流器的旧记录"""
    import asyncio

    while True:
        await asyncio.sleep(600)  # 每 10 分钟清理一次
        rate_limiter.cleanup()
        logger.debug("Rate limiter cleanup completed")
