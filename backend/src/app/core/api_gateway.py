"""
API 网关服务
统一入口、认证、限流、监控
"""

from typing import Dict, Any, Optional, Callable
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ===== 限流器 =====


class RateLimiter:
    """基于令牌桶算法的限流器"""

    def __init__(self):
        self.buckets: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def is_allowed(
        self, key: str, max_requests: int = 100, time_window: int = 60
    ) -> bool:
        """
        检查是否允许请求

        Args:
            key: 限流键（IP、用户ID等）
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）

        Returns:
            是否允许请求
        """
        now = time.time()

        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = {"count": 0, "reset_time": now + time_window}

            bucket = self.buckets[key]

            # 重置时间窗口
            if now >= bucket["reset_time"]:
                bucket["count"] = 0
                bucket["reset_time"] = now + time_window

            # 检查是否超限
            if bucket["count"] >= max_requests:
                return False

            # 增加计数
            bucket["count"] += 1
            return True

    def get_remaining(self, key: str, max_requests: int = 100) -> int:
        """获取剩余配额"""
        with self.lock:
            if key not in self.buckets:
                return max_requests

            bucket = self.buckets[key]
            return max(0, max_requests - bucket["count"])


# ===== 请求日志 =====


class RequestLogger:
    """请求日志记录器"""

    def __init__(self):
        self.logs: list = []
        self.max_logs = 10000
        self.lock = threading.Lock()

    def log(self, log_entry: Dict[str, Any]):
        """记录请求"""
        with self.lock:
            self.logs.append(log_entry)

            # 保持日志数量上限
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs :]

    def get_recent(self, limit: int = 100) -> list:
        """获取最近的日志"""
        with self.lock:
            return self.logs[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            if not self.logs:
                return {"total_requests": 0, "avg_response_time": 0, "error_rate": 0}

            total = len(self.logs)
            total_time = sum(log.get("duration", 0) for log in self.logs)
            errors = sum(1 for log in self.logs if log.get("status_code", 200) >= 400)

            return {
                "total_requests": total,
                "avg_response_time": total_time / total if total > 0 else 0,
                "error_rate": errors / total if total > 0 else 0,
                "requests_by_endpoint": self._count_by_field("path"),
                "requests_by_status": self._count_by_field("status_code"),
            }

    def _count_by_field(self, field: str) -> Dict:
        """按字段统计"""
        counts = defaultdict(int)
        for log in self.logs:
            value = log.get(field)
            if value:
                counts[str(value)] += 1
        return dict(counts)


# ===== API 监控 =====


class APIMonitor:
    """API 监控器"""

    def __init__(self):
        self.metrics: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "total_time": 0, "errors": 0, "last_called": None}
        )
        self.lock = threading.Lock()

    def record(self, endpoint: str, duration: float, success: bool):
        """记录 API 调用"""
        with self.lock:
            metric = self.metrics[endpoint]
            metric["count"] += 1
            metric["total_time"] += duration
            if not success:
                metric["errors"] += 1
            metric["last_called"] = datetime.now().isoformat()

    def get_metrics(self, endpoint: Optional[str] = None) -> Dict:
        """获取指标"""
        with self.lock:
            if endpoint:
                metric = self.metrics.get(endpoint)
                if not metric:
                    return {}

                return {
                    "endpoint": endpoint,
                    "total_calls": metric["count"],
                    "avg_response_time": (
                        metric["total_time"] / metric["count"]
                        if metric["count"] > 0
                        else 0
                    ),
                    "error_rate": (
                        metric["errors"] / metric["count"] if metric["count"] > 0 else 0
                    ),
                    "last_called": metric["last_called"],
                }

            # 返回所有端点
            return {
                endpoint: {
                    "total_calls": metric["count"],
                    "avg_response_time": (
                        metric["total_time"] / metric["count"]
                        if metric["count"] > 0
                        else 0
                    ),
                    "error_rate": (
                        metric["errors"] / metric["count"] if metric["count"] > 0 else 0
                    ),
                    "last_called": metric["last_called"],
                }
                for endpoint, metric in self.metrics.items()
            }


# ===== API 网关 =====


class APIGateway:
    """API 网关服务"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.request_logger = RequestLogger()
        self.monitor = APIMonitor()
        self.enabled = True

    async def process_request(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        流程:
        1. 限流检查
        2. 认证验证（可选）
        3. 请求日志
        4. 转发请求
        5. 响应处理
        6. 监控记录
        """
        if not self.enabled:
            return await call_next(request)

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        try:
            # 1. 限流检查
            if not self.rate_limiter.is_allowed(
                client_ip, max_requests=100, time_window=60
            ):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "请求过于频繁，请稍后再试",
                    },
                )

            # 2. 认证验证（TODO: 实现 JWT 验证）
            # auth_header = request.headers.get("Authorization")
            # if not self._verify_auth(auth_header):
            #     return JSONResponse(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         content={"error": "Unauthorized"}
            #     )

            # 3. 转发请求
            response = await call_next(request)

            # 4. 计算耗时
            duration = time.time() - start_time

            # 5. 记录日志
            self.request_logger.log(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )

            # 6. 记录监控
            self.monitor.record(
                endpoint=f"{method} {path}",
                duration=duration,
                success=response.status_code < 400,
            )

            # 7. 添加响应头
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-RateLimit-Remaining"] = str(
                self.rate_limiter.get_remaining(client_ip)
            )

            return response

        except Exception as e:
            logger.error(f"网关处理请求失败: {e}", exc_info=True)

            duration = time.time() - start_time

            # 记录错误
            self.request_logger.log(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "status_code": 500,
                    "duration": duration,
                    "error": str(e),
                }
            )

            self.monitor.record(
                endpoint=f"{method} {path}", duration=duration, success=False
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal Server Error", "message": "服务器内部错误"},
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取网关统计信息"""
        return {
            "request_logs": self.request_logger.get_stats(),
            "api_metrics": self.monitor.get_metrics(),
            "gateway_status": {
                "enabled": self.enabled,
                "uptime": "N/A",  # TODO: 记录启动时间
            },
        }

    def get_recent_logs(self, limit: int = 100) -> list:
        """获取最近的请求日志"""
        return self.request_logger.get_recent(limit)

    def reset_rate_limit(self, key: str):
        """重置限流"""
        with self.rate_limiter.lock:
            if key in self.rate_limiter.buckets:
                del self.rate_limiter.buckets[key]


# 全局实例
api_gateway = APIGateway()
