"""
废弃装饰器工具

用于标记旧代码为废弃状态，并在调用时发出警告
"""
import warnings
import functools
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def deprecated(reason: str, replacement: Optional[str] = None, version: str = "2.0"):
    """
    标记函数或类为废弃状态

    Args:
        reason: 废弃原因
        replacement: 推荐的替代方案
        version: 计划移除的版本号

    Example:
        @deprecated(
            reason="旧Agent架构已被6-Agent v2替代",
            replacement="app.agents.v2.knowledge_agent.KnowledgeAgent",
            version="2.0"
        )
        class OldKnowledgeAgent:
            pass
    """
    def decorator(obj: Callable) -> Callable:
        # 构造废弃消息
        msg_parts = [f"⚠️  {obj.__name__} 已废弃: {reason}"]
        if replacement:
            msg_parts.append(f"请使用: {replacement}")
        msg_parts.append(f"将在版本 {version} 中移除")
        deprecation_msg = " | ".join(msg_parts)

        # 如果是类，包装__init__方法
        if isinstance(obj, type):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)
                logger.warning(deprecation_msg)
                original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            obj.__deprecated__ = True
            obj.__deprecation_info__ = {
                'reason': reason,
                'replacement': replacement,
                'version': version
            }
            return obj

        # 如果是函数，包装整个函数
        else:
            @functools.wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(deprecation_msg, DeprecationWarning, stacklevel=2)
                logger.warning(deprecation_msg)
                return obj(*args, **kwargs)

            wrapper.__deprecated__ = True
            wrapper.__deprecation_info__ = {
                'reason': reason,
                'replacement': replacement,
                'version': version
            }
            return wrapper

    return decorator


def is_deprecated(obj) -> bool:
    """
    检查对象是否被标记为废弃

    Args:
        obj: 要检查的对象（函数或类）

    Returns:
        True if deprecated, False otherwise
    """
    return getattr(obj, '__deprecated__', False)


def get_deprecation_info(obj) -> Optional[dict]:
    """
    获取废弃信息

    Args:
        obj: 要检查的对象（函数或类）

    Returns:
        废弃信息字典，如果未废弃则返回None
    """
    return getattr(obj, '__deprecation_info__', None)
