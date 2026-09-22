"""
结构化日志配置
支持 JSON 格式、敏感信息脱敏、多级别日志
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（JSON 格式）"""

    SENSITIVE_KEYS = ['password', 'token', 'secret', 'api_key', 'authorization']

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # 添加 extra 字段（脱敏处理）
        if hasattr(record, "extra_data"):
            log_data["extra"] = self._sanitize_data(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)

    def _sanitize_data(self, data: Any) -> Any:
        """脱敏敏感信息"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        else:
            return data


class PlainTextFormatter(logging.Formatter):
    """纯文本日志格式化器（开发环境）"""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    log_dir: str = "./logs"
):
    """
    配置日志系统

    Args:
        environment: 环境（development/staging/production）
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if environment == "development" else logging.INFO)

    if environment == "production":
        # 生产环境使用 JSON 格式
        console_handler.setFormatter(StructuredFormatter())
    else:
        # 开发环境使用纯文本格式
        console_handler.setFormatter(PlainTextFormatter())

    root_logger.addHandler(console_handler)

    # 文件处理器（所有日志）
    all_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(
        StructuredFormatter() if environment == "production" else PlainTextFormatter()
    )
    root_logger.addHandler(all_handler)

    # 错误日志文件
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(f"✅ 日志系统已初始化 (环境: {environment}, 级别: {log_level})")


# 导入 logging.handlers
import logging.handlers


# 便捷日志记录器
class Logger:
    """应用日志记录器"""

    @staticmethod
    def info(message: str, **kwargs):
        """信息日志"""
        logger = logging.getLogger(__name__)
        logger.info(message, extra={"extra_data": kwargs})

    @staticmethod
    def warning(message: str, **kwargs):
        """警告日志"""
        logger = logging.getLogger(__name__)
        logger.warning(message, extra={"extra_data": kwargs})

    @staticmethod
    def error(message: str, exc_info: bool = False, **kwargs):
        """错误日志"""
        logger = logging.getLogger(__name__)
        logger.error(message, exc_info=exc_info, extra={"extra_data": kwargs})

    @staticmethod
    def debug(message: str, **kwargs):
        """调试日志"""
        logger = logging.getLogger(__name__)
        logger.debug(message, extra={"extra_data": kwargs})

    @staticmethod
    def critical(message: str, **kwargs):
        """严重错误日志"""
        logger = logging.getLogger(__name__)
        logger.critical(message, extra={"extra_data": kwargs})


# 导出默认 logger 实例
logger = logging.getLogger("app")


def log_ai_request(model: str, prompt: str, response: str = None, **kwargs):
    """记录 AI 请求日志"""
    logger.info(
        f"AI Request: {model}",
        extra={
            "extra_data": {
                "model": model,
                "prompt_length": len(prompt),
                "response_length": len(response) if response else 0,
                **kwargs
            }
        }
    )


def log_document_processing(doc_id: int, action: str, **kwargs):
    """记录文档处理日志"""
    logger.info(
        f"Document Processing: {action}",
        extra={
            "extra_data": {
                "doc_id": doc_id,
                "action": action,
                **kwargs
            }
        }
    )
