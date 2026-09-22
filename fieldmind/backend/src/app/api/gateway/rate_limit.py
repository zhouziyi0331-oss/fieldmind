"""
限流中间件 (Rate Limiting Middleware)

支持多种限流策略，防止API滥用
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶

        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 令牌填充速率（每秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens: 消费的令牌数

        Returns:
            是否成功消费
        """
        async with self.lock:
            # 填充令牌
            now = time.time()
            elapsed = now - self.last_refill
            refill_tokens = elapsed * self.refill_rate

            self.tokens = min(self.capacity, self.tokens + refill_tokens)
            self.last_refill = now

            # 尝试消费
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_remaining(self) -> int:
        """获取剩余令牌数"""
        now = time.time()
        elapsed = now - self.last_refill
        refill_tokens = elapsed * self.refill_rate

        current_tokens = min(self.capacity, self.tokens + refill_tokens)
        return int(current_tokens)


class SlidingWindow:
    """滑动窗口算法实现"""

    def __init__(self, window_size: int, max_requests: int):
        """
        初始化滑动窗口

        Args:
            window_size: 窗口大小（秒）
            max_requests: 最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []
        self.lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        """
        检查是否允许请求

        Returns:
            是否允许
        """
        async with self.lock:
            now = time.time()

            # 清理过期记录
            cutoff = now - self.window_size
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]

            # 检查是否超限
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def get_remaining(self) -> int:
        """获取剩余配额"""
        now = time.time()
        cutoff = now - self.window_size
        current_requests = [req_time for req_time in self.requests if req_time > cutoff]

        return max(0, self.max_requests - len(current_requests))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(
        self,
        app,
        default_limit: str = "100/minute",
        algorithm: str = "token_bucket",
        skip_paths: Optional[list] = None
    ):
        """
        初始化限流中间件

        Args:
            app: FastAPI应用
            default_limit: 默认限流规则（如 "100/minute"）
            algorithm: 限流算法（token_bucket/sliding_window）
            skip_paths: 跳过限流的路径
        """
        super().__init__(app)

        self.default_limit = default_limit
        self.algorithm = algorithm

        # 跳过限流的路径
        self.skip_paths = skip_paths or [
            "/health",
            "/stats",
            "/api/docs",
            "/api/redoc",
            "/openapi.json"
        ]

        # 路径特定限流规则
        self.path_limits: Dict[str, str] = {
            "/api/v1/chat": "20/minute",
            "/api/v1/rag": "50/minute",
            "/api/v1/agents": "10/minute",
            "/api/v1/skills": "30/minute"
        }

        # 用户限流器存储
        # key: (user_id, path) -> limiter
        self.user_limiters: Dict[tuple, Any] = {}

        # IP限流器存储
        # key: (ip, path) -> limiter
        self.ip_limiters: Dict[tuple, Any] = {}

        logger.info(f"✅ 限流中间件初始化: {algorithm}, 默认 {default_limit}")

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否跳过限流
        if self._should_skip(request.url.path):
            return await call_next(request)

        # 执行限流检查
        try:
            # 获取限流key
            limiter_key = self._get_limiter_key(request)

            # 获取限流规则
            limit_rule = self._get_limit_rule(request.url.path)

            # 检查限流
            allowed, remaining, reset_time = await self._check_rate_limit(
                limiter_key,
                limit_rule
            )

            if not allowed:
                # 超出限流
                logger.warning(
                    f"⚠️ 限流触发: {limiter_key}, "
                    f"path={request.url.path}"
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(self._parse_limit(limit_rule)[0]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(reset_time)),
                        "Retry-After": str(int(reset_time - time.time()))
                    }
                )

            # 继续处理请求
            response = await call_next(request)

            # 添加限流信息到响应头
            response.headers["X-RateLimit-Limit"] = str(self._parse_limit(limit_rule)[0])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 限流检查失败: {e}")
            # 限流失败时允许通过（fail-open）
            return await call_next(request)

    def _should_skip(self, path: str) -> bool:
        """检查是否应该跳过限流"""
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    def _get_limiter_key(self, request: Request) -> tuple:
        """
        获取限流器的key

        优先级：user_id > ip

        Args:
            request: 请求对象

        Returns:
            (identifier, path) 元组
        """
        path = request.url.path

        # 优先使用user_id
        if hasattr(request.state, 'user'):
            user_id = request.state.user.get('user_id')
            return ('user', user_id, path)

        # 否则使用IP
        client_ip = request.client.host if request.client else "unknown"
        return ('ip', client_ip, path)

    def _get_limit_rule(self, path: str) -> str:
        """
        获取路径的限流规则

        Args:
            path: 请求路径

        Returns:
            限流规则字符串（如 "100/minute"）
        """
        # 检查路径特定规则
        for pattern, limit in self.path_limits.items():
            if path.startswith(pattern):
                return limit

        # 返回默认规则
        return self.default_limit

    def _parse_limit(self, limit_rule: str) -> tuple:
        """
        解析限流规则

        Args:
            limit_rule: 限流规则字符串（如 "100/minute"）

        Returns:
            (max_requests, window_size) 元组
        """
        parts = limit_rule.split('/')
        max_requests = int(parts[0])

        if len(parts) > 1:
            unit = parts[1].lower()
            if unit == 'second':
                window_size = 1
            elif unit == 'minute':
                window_size = 60
            elif unit == 'hour':
                window_size = 3600
            elif unit == 'day':
                window_size = 86400
            else:
                window_size = 60  # 默认1分钟
        else:
            window_size = 60

        return (max_requests, window_size)

    async def _check_rate_limit(
        self,
        limiter_key: tuple,
        limit_rule: str
    ) -> tuple:
        """
        检查限流

        Args:
            limiter_key: 限流器key
            limit_rule: 限流规则

        Returns:
            (allowed, remaining, reset_time) 元组
        """
        max_requests, window_size = self._parse_limit(limit_rule)

        # 获取或创建限流器
        if self.algorithm == "token_bucket":
            if limiter_key not in self.user_limiters:
                # 令牌桶：容量=max_requests, 速率=max_requests/window_size
                self.user_limiters[limiter_key] = TokenBucket(
                    capacity=max_requests,
                    refill_rate=max_requests / window_size
                )

            limiter = self.user_limiters[limiter_key]
            allowed = await limiter.consume(1)
            remaining = limiter.get_remaining()
            reset_time = time.time() + window_size

        else:  # sliding_window
            if limiter_key not in self.user_limiters:
                self.user_limiters[limiter_key] = SlidingWindow(
                    window_size=window_size,
                    max_requests=max_requests
                )

            limiter = self.user_limiters[limiter_key]
            allowed = await limiter.allow_request()
            remaining = limiter.get_remaining()
            reset_time = time.time() + window_size

        return (allowed, remaining, reset_time)

    def get_stats(self) -> Dict[str, Any]:
        """获取限流统计"""
        return {
            'total_limiters': len(self.user_limiters) + len(self.ip_limiters),
            'user_limiters': len(self.user_limiters),
            'ip_limiters': len(self.ip_limiters),
            'algorithm': self.algorithm,
            'default_limit': self.default_limit
        }


# 装饰器：为特定路由设置限流
def rate_limit(limit: str):
    """
    路由限流装饰器

    使用方法：
    @app.get("/api/endpoint")
    @rate_limit("10/minute")
    async def endpoint():
        return {"message": "success"}

    Args:
        limit: 限流规则（如 "10/minute"）
    """
    def decorator(func):
        func._rate_limit = limit
        return func

    return decorator
