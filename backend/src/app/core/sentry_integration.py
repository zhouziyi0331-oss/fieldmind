"""
Sentry集成模块
Sentry Integration Module

提供生产环境的错误追踪和性能监控
"""

import os
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Sentry是否可用
SENTRY_AVAILABLE = False
sentry_sdk = None

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    logger.warning("sentry-sdk未安装，错误追踪功能将被禁用")


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    enable_tracing: bool = True,
    debug: bool = False,
) -> bool:
    """
    初始化Sentry

    Args:
        dsn: Sentry DSN (默认从环境变量SENTRY_DSN读取)
        environment: 运行环境 (development/staging/production)
        release: 版本号
        traces_sample_rate: 性能追踪采样率 (0.0-1.0)
        profiles_sample_rate: 性能分析采样率 (0.0-1.0)
        enable_tracing: 是否启用性能追踪
        debug: 是否启用调试模式

    Returns:
        bool: 是否初始化成功
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK未安装，跳过初始化")
        return False

    dsn = dsn or os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("未配置SENTRY_DSN，错误追踪功能已禁用")
        return False

    try:
        # 配置日志集成
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # 捕获INFO及以上级别
            event_level=logging.ERROR  # 只有ERROR及以上作为事件发送
        )

        integrations = [
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            AsyncioIntegration(),
            logging_integration,
        ]

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            integrations=integrations,
            traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
            profiles_sample_rate=profiles_sample_rate if enable_tracing else 0.0,
            debug=debug,
            # 设置标签
            before_send=_before_send,
            # 性能监控配置
            enable_tracing=enable_tracing,
        )

        logger.info(
            f"Sentry初始化成功 [环境: {environment}, 版本: {release or 'unknown'}]"
        )
        return True

    except Exception as e:
        logger.error(f"Sentry初始化失败: {e}", exc_info=True)
        return False


def _before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    事件发送前的处理函数

    可以在这里过滤不需要上报的错误、添加额外的上下文信息等
    """
    # 过滤特定的异常
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # 不上报某些预期的异常
        if exc_type.__name__ in ["ValidationException", "ResourceNotFoundException"]:
            return None

    # 添加自定义标签
    if "tags" not in event:
        event["tags"] = {}

    event["tags"]["source"] = "fieldmind-backend"

    return event


def set_user(user_id: str, username: Optional[str] = None, email: Optional[str] = None):
    """
    设置当前用户信息

    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        "email": email,
    })


def set_tag(key: str, value: Any):
    """
    设置标签

    Args:
        key: 标签键
        value: 标签值
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.set_tag(key, value)


def set_context(name: str, context: Dict[str, Any]):
    """
    设置上下文信息

    Args:
        name: 上下文名称
        context: 上下文数据
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.set_context(name, context)


def capture_exception(
    exception: Exception,
    level: str = "error",
    tags: Optional[Dict[str, str]] = None,
    contexts: Optional[Dict[str, Dict[str, Any]]] = None,
    extras: Optional[Dict[str, Any]] = None,
):
    """
    手动捕获异常

    Args:
        exception: 异常对象
        level: 严重级别 (fatal/error/warning/info/debug)
        tags: 标签
        contexts: 上下文信息
        extras: 额外信息
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.error(f"捕获异常(Sentry不可用): {exception}", exc_info=True)
        return

    with sentry_sdk.push_scope() as scope:
        scope.level = level

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if contexts:
            for name, context in contexts.items():
                scope.set_context(name, context)

        if extras:
            for key, value in extras.items():
                scope.set_extra(key, value)

        sentry_sdk.capture_exception(exception)


def capture_message(
    message: str,
    level: str = "info",
    tags: Optional[Dict[str, str]] = None,
    extras: Optional[Dict[str, Any]] = None,
):
    """
    手动捕获消息

    Args:
        message: 消息内容
        level: 严重级别
        tags: 标签
        extras: 额外信息
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logger.log(
            logging.getLevelName(level.upper()),
            f"捕获消息(Sentry不可用): {message}"
        )
        return

    with sentry_sdk.push_scope() as scope:
        scope.level = level

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if extras:
            for key, value in extras.items():
                scope.set_extra(key, value)

        sentry_sdk.capture_message(message)


@contextmanager
def sentry_span(operation: str, description: Optional[str] = None):
    """
    性能追踪上下文管理器

    Example:
        with sentry_span("database.query", "查询用户信息"):
            users = db.query(User).all()
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        yield
        return

    with sentry_sdk.start_span(op=operation, description=description) as span:
        yield span


def start_transaction(
    name: str,
    op: str = "task",
    description: Optional[str] = None,
) -> Any:
    """
    启动事务追踪

    Args:
        name: 事务名称
        op: 操作类型
        description: 描述

    Returns:
        Transaction对象 (如果Sentry不可用则返回None)
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return None

    return sentry_sdk.start_transaction(
        name=name,
        op=op,
        description=description,
    )


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """
    添加面包屑（用户操作轨迹）

    Args:
        message: 消息
        category: 分类
        level: 级别
        data: 额外数据
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )


def wrap_handler(handler: Callable) -> Callable:
    """
    包装处理器以自动捕获异常

    Example:
        @app.route("/api/data")
        @wrap_handler
        async def get_data():
            return await fetch_data()
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return handler

    import functools
    import asyncio

    if asyncio.iscoroutinefunction(handler):
        @functools.wraps(handler)
        async def async_wrapper(*args, **kwargs):
            try:
                return await handler(*args, **kwargs)
            except Exception as e:
                capture_exception(e)
                raise
        return async_wrapper
    else:
        @functools.wraps(handler)
        def sync_wrapper(*args, **kwargs):
            try:
                return handler(*args, **kwargs)
            except Exception as e:
                capture_exception(e)
                raise
        return sync_wrapper


# 便捷函数
def is_enabled() -> bool:
    """检查Sentry是否已启用"""
    return SENTRY_AVAILABLE and sentry_sdk is not None


def flush(timeout: float = 2.0) -> bool:
    """
    强制发送所有待处理的事件

    Args:
        timeout: 超时时间(秒)

    Returns:
        bool: 是否成功
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return False

    return sentry_sdk.flush(timeout=timeout)
