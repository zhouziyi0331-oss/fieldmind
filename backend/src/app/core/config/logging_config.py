"""
结构化日志配置
生产级日志系统：分级、轮转、结构化输出
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from functools import lru_cache

from .constants import Environment


class JsonFormatter(logging.Formatter):
    """JSON格式日志"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加额外字段
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'project_id'):
            log_data['project_id'] = record.project_id
        if hasattr(record, 'document_id'):
            log_data['document_id'] = record.document_id

        # 异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }

        # 额外的上下文数据
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色终端日志"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # 格式化消息
        formatted = super().format(record)

        # 恢复原始levelname
        record.levelname = levelname

        return formatted


class ContextFilter(logging.Filter):
    """上下文信息过滤器"""

    def __init__(self):
        super().__init__()
        self.context: Dict[str, Any] = {}

    def set_context(self, **kwargs):
        """设置上下文"""
        self.context.update(kwargs)

    def clear_context(self):
        """清除上下文"""
        self.context.clear()

    def filter(self, record: logging.LogRecord) -> bool:
        # 将上下文添加到日志记录
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


# 全局上下文过滤器
_context_filter = ContextFilter()


def setup_logging(
    level: str = "INFO",
    log_format: str = "text",
    log_file: Optional[Path] = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
    compression: bool = True
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式 (text, json)
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
        compression: 是否压缩旧日志
    """
    # 解析日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 添加上下文过滤器
    root_logger.addFilter(_context_filter)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if log_format == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        # 彩色文本格式
        text_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
        console_handler.setFormatter(ColoredFormatter(text_format))

    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 根据轮转策略选择处理器
        if "MB" in rotation or "GB" in rotation:
            # 按大小轮转
            size_str = rotation.upper().replace(" ", "")
            if "GB" in size_str:
                max_bytes = int(size_str.replace("GB", "")) * 1024 * 1024 * 1024
            else:
                max_bytes = int(size_str.replace("MB", "")) * 1024 * 1024

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=10,
                encoding='utf-8'
            )
        else:
            # 按时间轮转 (daily, weekly, midnight)
            file_handler = TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )

        file_handler.setLevel(numeric_level)

        # 文件日志始终使用JSON格式（便于日志分析）
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

    # 配置第三方库日志级别
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    # 启动日志
    root_logger.info(
        f"日志系统初始化完成",
        extra={
            'extra_data': {
                'level': level,
                'format': log_format,
                'file': str(log_file) if log_file else None
            }
        }
    )


@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器（带缓存）

    Args:
        name: 日志器名称

    Returns:
        Logger实例
    """
    return logging.getLogger(name)


def set_log_context(**kwargs):
    """设置全局日志上下文"""
    _context_filter.set_context(**kwargs)


def clear_log_context():
    """清除全局日志上下文"""
    _context_filter.clear_context()


class LogContext:
    """日志上下文管理器"""

    def __init__(self, **kwargs):
        self.context = kwargs

    def __enter__(self):
        set_log_context(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_log_context()


# 便捷函数
def log_error(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    **context
):
    """记录错误日志"""
    extra_data = context.copy()
    if error:
        extra_data['error_type'] = type(error).__name__
        extra_data['error_message'] = str(error)

    logger.error(message, exc_info=error, extra={'extra_data': extra_data})


def log_warning(
    logger: logging.Logger,
    message: str,
    **context
):
    """记录警告日志"""
    logger.warning(message, extra={'extra_data': context})


def log_info(
    logger: logging.Logger,
    message: str,
    **context
):
    """记录信息日志"""
    logger.info(message, extra={'extra_data': context})


def log_debug(
    logger: logging.Logger,
    message: str,
    **context
):
    """记录调试日志"""
    logger.debug(message, extra={'extra_data': context})


def log_critical(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    **context
):
    """记录严重错误日志"""
    extra_data = context.copy()
    if error:
        extra_data['error_type'] = type(error).__name__
        extra_data['error_message'] = str(error)

    logger.critical(message, exc_info=error, extra={'extra_data': extra_data})


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    **context
):
    """记录性能日志"""
    context['operation'] = operation
    context['duration_seconds'] = round(duration, 3)
    logger.info(f"性能: {operation} 完成", extra={'extra_data': context})
