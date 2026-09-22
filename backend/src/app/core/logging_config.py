"""
结构化日志系统 - Week 3 Day 3-4
统一日志格式、日志级别管理、日志聚合
"""
import logging
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import traceback


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # 性能指标
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration * 1000

        # 请求信息
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data, ensure_ascii=False)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，添加上下文信息"""

    def process(self, msg, kwargs):
        """处理日志消息，添加额外字段"""
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        # 合并上下文字段
        kwargs["extra"].update(self.extra)

        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True
) -> logging.Logger:
    """
    配置日志系统

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        structured: 是否使用结构化日志

    Returns:
        配置好的 logger
    """
    # 创建根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

    root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())

        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> LoggerAdapter:
    """
    获取带上下文的 logger

    Args:
        name: logger 名称
        context: 上下文信息

    Returns:
        LoggerAdapter
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context or {})


# ==================== 日志装饰器 ====================

def log_execution(
    log_args: bool = False,
    log_result: bool = False,
    log_level: str = "info"
):
    """
    日志装饰器：记录函数执行

    Args:
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_level: 日志级别
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"

            # 记录开始
            log_data = {"function": func_name}
            if log_args:
                log_data["args"] = str(args)[:200]  # 限制长度
                log_data["kwargs"] = str(kwargs)[:200]

            logger.log(
                getattr(logging, log_level.upper()),
                f"Executing {func_name}",
                extra={"extra_fields": log_data}
            )

            # 执行函数
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)

                # 记录成功
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_ms"] = duration * 1000
                log_data["status"] = "success"

                if log_result:
                    log_data["result"] = str(result)[:200]

                logger.log(
                    getattr(logging, log_level.upper()),
                    f"Completed {func_name}",
                    extra={"extra_fields": log_data}
                )

                return result

            except Exception as e:
                # 记录失败
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_ms"] = duration * 1000
                log_data["status"] = "error"
                log_data["error"] = str(e)

                logger.error(
                    f"Failed {func_name}: {e}",
                    exc_info=True,
                    extra={"extra_fields": log_data}
                )
                raise

        return wrapper
    return decorator


def log_execution_async(
    log_args: bool = False,
    log_result: bool = False,
    log_level: str = "info"
):
    """
    异步日志装饰器：记录异步函数执行

    Args:
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_level: 日志级别
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"

            log_data = {"function": func_name}
            if log_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = str(kwargs)[:200]

            logger.log(
                getattr(logging, log_level.upper()),
                f"Executing {func_name}",
                extra={"extra_fields": log_data}
            )

            start_time = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)

                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_ms"] = duration * 1000
                log_data["status"] = "success"

                if log_result:
                    log_data["result"] = str(result)[:200]

                logger.log(
                    getattr(logging, log_level.upper()),
                    f"Completed {func_name}",
                    extra={"extra_fields": log_data}
                )

                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_ms"] = duration * 1000
                log_data["status"] = "error"
                log_data["error"] = str(e)

                logger.error(
                    f"Failed {func_name}: {e}",
                    exc_info=True,
                    extra={"extra_fields": log_data}
                )
                raise

        return wrapper
    return decorator


# ==================== 日志上下文管理器 ====================

class LogContext:
    """日志上下文管理器"""

    def __init__(self, logger: logging.Logger, **context):
        """
        初始化日志上下文

        Args:
            logger: Logger 实例
            **context: 上下文字段
        """
        self.logger = logger
        self.context = context

    def __enter__(self):
        return LoggerAdapter(self.logger, self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"Exception in context: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={"extra_fields": self.context}
            )


# ==================== 初始化 ====================

# 默认配置
_default_logger = None


def init_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "./logs/fieldmind.log",
    structured: bool = True
):
    """
    初始化全局日志配置

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        structured: 是否使用结构化日志
    """
    global _default_logger
    _default_logger = setup_logging(log_level, log_file, structured)
    return _default_logger
