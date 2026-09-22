"""
结构化JSON日志配置
支持请求追踪、敏感信息脱敏、统一格式
"""
import logging
import sys
import json
import re
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar
from loguru import logger
import traceback

# ============================================
# 请求追踪上下文
# ============================================
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
user_id_ctx: ContextVar[str] = ContextVar('user_id', default='')

# ============================================
# 敏感信息模式
# ============================================
SENSITIVE_PATTERNS = [
    (re.compile(r'("password"\s*:\s*")[^"]*(")', re.IGNORECASE), r'\1***REDACTED***\2'),
    (re.compile(r'("token"\s*:\s*")[^"]*(")', re.IGNORECASE), r'\1***REDACTED***\2'),
    (re.compile(r'("api_key"\s*:\s*")[^"]*(")', re.IGNORECASE), r'\1***REDACTED***\2'),
    (re.compile(r'("secret"\s*:\s*")[^"]*(")', re.IGNORECASE), r'\1***REDACTED***\2'),
    (re.compile(r'("authorization"\s*:\s*")[^"]*(")', re.IGNORECASE), r'\1***REDACTED***\2'),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE), 'Bearer ***REDACTED***'),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***EMAIL***'),
    (re.compile(r'\b\d{15,19}\b'), '***CARD***'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***SSN***'),
]


def sanitize_log_data(data: Any) -> Any:
    """脱敏日志数据"""
    if isinstance(data, str):
        for pattern, replacement in SENSITIVE_PATTERNS:
            data = pattern.sub(replacement, data)
        return data
    elif isinstance(data, dict):
        return {k: sanitize_log_data(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_log_data(item) for item in data]
    else:
        return data


def json_formatter(record: dict) -> str:
    """JSON格式化器"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": record["level"].name,
        "message": record["message"],
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # 添加请求追踪信息
    request_id = request_id_ctx.get()
    if request_id:
        log_entry["request_id"] = request_id

    user_id = user_id_ctx.get()
    if user_id:
        log_entry["user_id"] = user_id

    # 添加额外字段
    extra = record.get("extra", {})
    if extra:
        log_entry["extra"] = sanitize_log_data(extra)

    # 添加异常信息
    if record["exception"]:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value),
            "traceback": "".join(traceback.format_exception(
                record["exception"].type,
                record["exception"].value,
                record["exception"].traceback
            ))
        }

    # 脱敏整个日志条目
    log_entry = sanitize_log_data(log_entry)

    return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(
    level: str = "INFO",
    json_logs: bool = True,
    log_file: str = None
):
    """配置日志系统"""
    # 移除默认handler
    logger.remove()

    # 日志格式
    if json_logs:
        log_format = json_formatter
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=not json_logs,
        serialize=json_logs,
        backtrace=True,
        diagnose=True
    )

    # 文件输出
    if log_file:
        logger.add(
            log_file,
            format=json_formatter,
            level=level,
            rotation="500 MB",
            retention="30 days",
            compression="gz",
            serialize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True
        )

    # 拦截标准logging库
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # 设置第三方库日志级别
    for name in ["uvicorn", "uvicorn.access", "fastapi", "sqlalchemy.engine"]:
        logging.getLogger(name).handlers = [InterceptHandler()]


def get_logger(name: str = None):
    """获取logger实例"""
    if name:
        return logger.bind(name=name)
    return logger


# ============================================
# 请求日志中间件
# ============================================
class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import uuid
        import time

        # 生成请求ID
        request_id = str(uuid.uuid4())
        request_id_ctx.set(request_id)

        method = scope["method"]
        path = scope["path"]
        start_time = time.time()

        # 记录请求开始
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client": scope.get("client"),
                "headers": dict(scope.get("headers", [])),
            }
        )

        status_code = 500
        response_body = b""

        async def wrapped_send(message):
            nonlocal status_code, response_body
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            logger.exception(
                f"Request failed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error": str(e)
                }
            )
            raise
        finally:
            duration = time.time() - start_time

            # 记录请求完成
            logger.info(
                f"Request completed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
