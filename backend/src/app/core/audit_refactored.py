"""
审计日志装饰器（重构版）
拆分超长复杂函数为职责单一的组件
"""

from functools import wraps
from typing import Optional, Callable, Any, Tuple
from datetime import datetime
import time
import asyncio

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import ActorType, ActionType, AuditResult
from app.services.audit_service import AuditService
from app.core.logging import logger


class AuditContext:
    """审计上下文 - 封装审计所需的所有信息"""

    def __init__(self):
        self.db: Optional[Session] = None
        self.request: Optional[Request] = None
        self.current_user: Optional[Any] = None
        self.actor_type: ActorType = ActorType.USER
        self.actor_id: str = "unknown"
        self.actor_name: str = "Unknown"
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None

    def extract_from_args(self, args: tuple, kwargs: dict):
        """从函数参数中提取上下文信息"""
        # 从位置参数提取
        for arg in args:
            if isinstance(arg, Session):
                self.db = arg
            elif isinstance(arg, Request):
                self.request = arg
            elif hasattr(arg, "id"):  # 用户对象
                self.current_user = arg

        # 从关键字参数提取
        if "db" in kwargs:
            self.db = kwargs["db"]
        if "request" in kwargs:
            self.request = kwargs["request"]
        if "current_user" in kwargs:
            self.current_user = kwargs["current_user"]

    def resolve_actor(self):
        """解析操作者信息"""
        if self.current_user:
            self.actor_type = ActorType.USER
            self.actor_id = str(getattr(self.current_user, "id", "unknown"))
            self.actor_name = getattr(self.current_user, "name", "Unknown User")
        else:
            self.actor_type = ActorType.SYSTEM
            self.actor_id = "system"
            self.actor_name = "System"

    def extract_request_info(self):
        """提取请求信息"""
        if self.request:
            self.ip_address = self.request.client.host if self.request.client else None
            self.user_agent = self.request.headers.get("user-agent")


class AuditLogBuilder:
    """审计日志构建器"""

    def __init__(
        self,
        action: ActionType,
        resource_type: str,
        get_resource_id: Optional[Callable] = None,
        get_resource_name: Optional[Callable] = None,
        get_project_id: Optional[Callable] = None,
        capture_changes: bool = False,
    ):
        self.action = action
        self.resource_type = resource_type
        self.get_resource_id = get_resource_id
        self.get_resource_name = get_resource_name
        self.get_project_id = get_project_id
        self.capture_changes = capture_changes

    def build_log_data(
        self,
        context: AuditContext,
        kwargs: dict,
        result: Any,
        audit_result: AuditResult,
        duration_ms: int,
        error: Optional[Exception] = None,
    ) -> dict:
        """构建审计日志数据"""
        # 提取资源信息
        resource_id = self._extract_resource_id(kwargs, result)
        resource_name = self._extract_resource_name(kwargs, result)
        project_id = self._extract_project_id(kwargs, result)

        # 构建基础日志数据
        log_data = {
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": resource_id,
            "resource_name": resource_name,
            "project_id": project_id,
            "actor_type": context.actor_type,
            "actor_id": context.actor_id,
            "actor_name": context.actor_name,
            "result": audit_result,
            "duration_ms": duration_ms,
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
        }

        # 添加错误信息
        if error:
            log_data["error_message"] = str(error)
            log_data["error_type"] = type(error).__name__

        # 添加变更信息
        if self.capture_changes and result:
            log_data["changes"] = self._capture_changes(result)

        return log_data

    def _extract_resource_id(self, kwargs: dict, result: Any) -> Optional[str]:
        """提取资源ID"""
        if self.get_resource_id:
            try:
                resource_id = self.get_resource_id(kwargs, result)
                return str(resource_id) if resource_id else None
            except Exception as e:
                logger.warning(f"Failed to extract resource_id: {e}")
        return None

    def _extract_resource_name(self, kwargs: dict, result: Any) -> Optional[str]:
        """提取资源名称"""
        if self.get_resource_name:
            try:
                return self.get_resource_name(kwargs, result)
            except Exception as e:
                logger.warning(f"Failed to extract resource_name: {e}")
        return None

    def _extract_project_id(self, kwargs: dict, result: Any) -> Optional[int]:
        """提取项目ID"""
        if self.get_project_id:
            try:
                project_id = self.get_project_id(kwargs, result)
                return int(project_id) if project_id else None
            except Exception as e:
                logger.warning(f"Failed to extract project_id: {e}")
        return None

    def _capture_changes(self, result: Any) -> dict:
        """捕获变更内容"""
        changes = {}

        if hasattr(result, "__dict__"):
            # 记录对象属性
            for key, value in result.__dict__.items():
                if not key.startswith("_"):
                    try:
                        changes[key] = str(value)
                    except:
                        changes[key] = "<unable to serialize>"

        return changes


class AuditLogger:
    """审计日志记录器"""

    @staticmethod
    async def log_async(db: Session, log_data: dict):
        """异步记录审计日志"""
        try:
            audit_service = AuditService(db)
            await audit_service.create_log(**log_data)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)

    @staticmethod
    def log_sync(db: Session, log_data: dict):
        """同步记录审计日志"""
        try:
            audit_service = AuditService(db)
            audit_service.create_log_sync(**log_data)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)


# ===== 主装饰器（重构版）=====


def audit_log(
    action: ActionType,
    resource_type: str,
    get_resource_id: Optional[Callable] = None,
    get_resource_name: Optional[Callable] = None,
    get_project_id: Optional[Callable] = None,
    capture_changes: bool = False,
):
    """
    审计日志装饰器（重构版）

    拆分逻辑：
    1. AuditContext - 封装上下文信息提取
    2. AuditLogBuilder - 构建日志数据
    3. AuditLogger - 执行记录操作
    4. 主函数只负责流程编排

    复杂度：从 41 降低到 <5
    """

    def decorator(func: Callable) -> Callable:
        # 判断是否异步函数
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _execute_with_audit(
                    func,
                    args,
                    kwargs,
                    action,
                    resource_type,
                    get_resource_id,
                    get_resource_name,
                    get_project_id,
                    capture_changes,
                    is_async=True,
                )

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(
                    _execute_with_audit(
                        func,
                        args,
                        kwargs,
                        action,
                        resource_type,
                        get_resource_id,
                        get_resource_name,
                        get_project_id,
                        capture_changes,
                        is_async=False,
                    )
                )

            return sync_wrapper

    return decorator


async def _execute_with_audit(
    func: Callable,
    args: tuple,
    kwargs: dict,
    action: ActionType,
    resource_type: str,
    get_resource_id: Optional[Callable],
    get_resource_name: Optional[Callable],
    get_project_id: Optional[Callable],
    capture_changes: bool,
    is_async: bool,
) -> Any:
    """执行函数并记录审计日志"""
    start_time = time.time()
    result = None
    error = None
    audit_result = AuditResult.SUCCESS

    # 步骤 1: 提取上下文
    context = AuditContext()
    context.extract_from_args(args, kwargs)

    if not context.db:
        logger.warning("No database session found for audit log")
        # 仍然执行原函数
        if is_async:
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    context.resolve_actor()
    context.extract_request_info()

    # 步骤 2: 执行原函数
    try:
        if is_async:
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        return result

    except Exception as e:
        error = e
        audit_result = AuditResult.FAILURE
        raise

    finally:
        # 步骤 3: 构建审计日志
        duration_ms = int((time.time() - start_time) * 1000)

        builder = AuditLogBuilder(
            action,
            resource_type,
            get_resource_id,
            get_resource_name,
            get_project_id,
            capture_changes,
        )

        log_data = builder.build_log_data(
            context, kwargs, result, audit_result, duration_ms, error
        )

        # 步骤 4: 记录日志
        if is_async:
            await AuditLogger.log_async(context.db, log_data)
        else:
            AuditLogger.log_sync(context.db, log_data)
