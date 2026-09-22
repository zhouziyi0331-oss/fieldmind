"""
Sentry 错误追踪集成
提供生产级错误监控和性能追踪
"""

import logging
from typing import Optional
from functools import wraps

logger = logging.getLogger(__name__)


class SentryService:
    """Sentry 错误追踪服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.enabled = False
        self.sentry_sdk = None
        self._init_sentry()

    def _init_sentry(self):
        """初始化 Sentry SDK"""
        try:
            from app.config import settings

            if not settings.SENTRY_ENABLED:
                logger.info("Sentry 未启用")
                return

            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.redis import RedisIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            # 日志集成配置
            logging_integration = LoggingIntegration(
                level=logging.INFO,  # 捕获 INFO 及以上级别
                event_level=logging.ERROR  # ERROR 及以上作为事件发送
            )

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                release=settings.VERSION,

                # 集成
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    logging_integration,
                ],

                # 性能监控
                traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
                profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,

                # 错误采样
                sample_rate=1.0,

                # 请求数据
                send_default_pii=False,  # 不发送 PII 数据
                max_breadcrumbs=50,

                # 过滤敏感数据
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb,
            )

            self.sentry_sdk = sentry_sdk
            self.enabled = True
            logger.info(f"✅ Sentry 已启用 (环境: {settings.ENVIRONMENT})")

        except ImportError:
            logger.warning("⚠️  sentry-sdk 未安装，错误追踪功能不可用")
        except Exception as e:
            logger.error(f"❌ Sentry 初始化失败: {e}")

    def _before_send(self, event, hint):
        """
        发送前处理事件，过滤敏感信息
        """
        # 过滤密码字段
        if 'request' in event:
            if 'data' in event['request']:
                data = event['request']['data']
                if isinstance(data, dict):
                    for key in ['password', 'token', 'secret', 'api_key']:
                        if key in data:
                            data[key] = '***REDACTED***'

        # 过滤环境变量中的敏感信息
        if 'contexts' in event and 'runtime' in event['contexts']:
            runtime = event['contexts']['runtime']
            if 'env' in runtime:
                for key in list(runtime['env'].keys()):
                    if any(s in key.lower() for s in ['password', 'secret', 'token', 'key']):
                        runtime['env'][key] = '***REDACTED***'

        return event

    def _before_breadcrumb(self, crumb, hint):
        """
        记录面包屑前处理，过滤敏感信息
        """
        # 过滤 SQL 查询中的敏感数据
        if crumb.get('category') == 'query':
            if 'message' in crumb:
                message = crumb['message']
                # 简单的密码过滤
                if 'password' in message.lower():
                    crumb['message'] = 'SQL query with sensitive data [REDACTED]'

        return crumb

    def capture_exception(self, error: Exception, **context):
        """
        捕获异常并发送到 Sentry

        Args:
            error: 异常对象
            **context: 额外的上下文信息
        """
        if not self.enabled:
            return

        try:
            with self.sentry_sdk.push_scope() as scope:
                # 添加上下文
                for key, value in context.items():
                    scope.set_context(key, value)

                self.sentry_sdk.capture_exception(error)
        except Exception as e:
            logger.error(f"发送错误到 Sentry 失败: {e}")

    def capture_message(self, message: str, level: str = "info", **context):
        """
        捕获消息并发送到 Sentry

        Args:
            message: 消息内容
            level: 级别 (debug, info, warning, error, fatal)
            **context: 额外的上下文信息
        """
        if not self.enabled:
            return

        try:
            with self.sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)

                self.sentry_sdk.capture_message(message, level=level)
        except Exception as e:
            logger.error(f"发送消息到 Sentry 失败: {e}")

    def set_user(self, user_id: Optional[int] = None, email: Optional[str] = None, **kwargs):
        """
        设置当前用户信息

        Args:
            user_id: 用户 ID
            email: 用户邮箱
            **kwargs: 其他用户属性
        """
        if not self.enabled:
            return

        try:
            user_data = {}
            if user_id:
                user_data['id'] = user_id
            if email:
                user_data['email'] = email
            user_data.update(kwargs)

            self.sentry_sdk.set_user(user_data)
        except Exception as e:
            logger.error(f"设置 Sentry 用户信息失败: {e}")

    def set_context(self, name: str, data: dict):
        """
        设置自定义上下文

        Args:
            name: 上下文名称
            data: 上下文数据
        """
        if not self.enabled:
            return

        try:
            self.sentry_sdk.set_context(name, data)
        except Exception as e:
            logger.error(f"设置 Sentry 上下文失败: {e}")

    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info", **data):
        """
        添加面包屑（用于追踪事件流）

        Args:
            message: 消息内容
            category: 类别
            level: 级别
            **data: 额外数据
        """
        if not self.enabled:
            return

        try:
            self.sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data
            )
        except Exception as e:
            logger.error(f"添加 Sentry 面包屑失败: {e}")

    def start_transaction(self, name: str, op: str = "function"):
        """
        开始性能追踪事务

        Args:
            name: 事务名称
            op: 操作类型

        Returns:
            事务对象（可用作上下文管理器）
        """
        if not self.enabled:
            return _DummyTransaction()

        try:
            return self.sentry_sdk.start_transaction(name=name, op=op)
        except Exception as e:
            logger.error(f"开始 Sentry 事务失败: {e}")
            return _DummyTransaction()


class _DummyTransaction:
    """虚拟事务对象（当 Sentry 未启用时使用）"""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def start_child(self, *args, **kwargs):
        return self


# 全局 Sentry 实例
sentry = SentryService()


def track_errors(func):
    """
    错误追踪装饰器

    Example:
        @track_errors
        def process_document(doc_id: int):
            # 自动追踪错误
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 收集上下文
            context = {
                "function": func.__name__,
                "args": str(args)[:200],  # 限制长度
                "kwargs": str(kwargs)[:200],
            }
            sentry.capture_exception(e, function_context=context)
            raise  # 重新抛出异常

    return wrapper


def track_performance(op: str = "function"):
    """
    性能追踪装饰器

    Args:
        op: 操作类型

    Example:
        @track_performance(op="database.query")
        def get_user(user_id: int):
            # 自动追踪执行时间
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry.start_transaction(name=func.__name__, op=op):
                return func(*args, **kwargs)
        return wrapper
    return decorator
