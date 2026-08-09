"""
日志配置模块
使用 loguru 实现结构化日志
"""

import sys
from loguru import logger
from pathlib import Path


# 日志目录
LOG_DIR = Path("/tmp/fieldmind_logs")
LOG_DIR.mkdir(exist_ok=True)

# 移除默认 handler
logger.remove()

# 控制台输出（开发环境）
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 文件输出 - 所有日志
logger.add(
    LOG_DIR / "fieldmind_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# 错误日志单独记录
logger.add(
    LOG_DIR / "errors_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",
    compression="zip",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
)

# API 调用日志
logger.add(
    LOG_DIR / "api_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    filter=lambda record: "api" in record["extra"].get("category", ""),
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {extra[method]} {extra[path]} | {extra[status_code]} | {extra[duration_ms]}ms | {message}"
)

# 性能监控日志
logger.add(
    LOG_DIR / "performance_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    filter=lambda record: "performance" in record["extra"].get("category", ""),
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {extra[metric]} | {message}"
)


def get_logger(name: str):
    """
    获取带有名称的 logger

    使用：
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    """
    return logger.bind(name=name)


def log_api_call(method: str, path: str, status_code: int, duration_ms: float, message: str = ""):
    """
    记录 API 调用
    """
    logger.bind(
        category="api",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2)
    ).info(message or f"{method} {path}")


def log_performance(metric: str, value: float, unit: str = "ms", extra_data: dict = None):
    """
    记录性能指标

    示例：
    log_performance("database_query", 15.5, "ms", {"query": "SELECT * FROM projects"})
    """
    data = extra_data or {}
    logger.bind(
        category="performance",
        metric=metric,
        value=value,
        unit=unit,
        **data
    ).info(f"{metric}: {value}{unit}")


# 导出
__all__ = ["logger", "get_logger", "log_api_call", "log_performance"]
