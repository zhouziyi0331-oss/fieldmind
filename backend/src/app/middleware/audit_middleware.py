"""审计日志中间件

自动记录所有API操作到审计日志
"""
from typing import Callable, Optional
from datetime import datetime
import time
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import logger
from app.models.audit_log import ActorType, ActionType, AuditResult


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件

    自动记录HTTP请求到审计日志
    """

    # 需要记录的HTTP方法
    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # 排除的路径前缀
    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
        "/static",
        "/ws",
    }

    # HTTP方法到操作类型的映射
    METHOD_TO_ACTION = {
        "POST": ActionType.CREATE,
        "PUT": ActionType.UPDATE,
        "PATCH": ActionType.UPDATE,
        "DELETE": ActionType.DELETE,
    }

    def __init__(self, app: ASGIApp, enabled: bool = True):
        """初始化中间件

        Args:
            app: ASGI应用
            enabled: 是否启用审计日志
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: HTTP请求
            call_next: 下一个处理器

        Returns:
            HTTP响应
        """
        # 如果未启用或不需要审计，直接通过
        if not self.enabled or not self._should_audit(request):
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 提取请求信息
        path = request.url.path
        method = request.method
        actor_id = self._extract_actor_id(request)
        actor_type = self._extract_actor_type(request)

        # 执行请求
        response = None
        error_message = None
        result = AuditResult.SUCCESS

        try:
            response = await call_next(request)

            # 检查响应状态码
            if response.status_code >= 400:
                result = AuditResult.FAILURE
                error_message = f"HTTP {response.status_code}"

            return response

        except Exception as e:
            result = AuditResult.FAILURE
            error_message = str(e)
            raise

        finally:
            # 计算执行时长
            duration_ms = int((time.time() - start_time) * 1000)

            # 异步记录审计日志
            try:
                await self._log_audit(
                    path=path,
                    method=method,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    result=result,
                    error_message=error_message,
                    duration_ms=duration_ms,
                    request=request,
                    response=response,
                )
            except Exception as audit_error:
                # 审计日志失败不应影响主流程
                logger.error(f"Failed to create audit log: {audit_error}")

    def _should_audit(self, request: Request) -> bool:
        """判断是否需要审计

        Args:
            request: HTTP请求

        Returns:
            是否需要审计
        """
        # 检查HTTP方法
        if request.method not in self.AUDITABLE_METHODS:
            return False

        # 检查路径
        path = request.url.path
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return False

        return True

    def _extract_actor_id(self, request: Request) -> str:
        """提取操作者ID

        Args:
            request: HTTP请求

        Returns:
            操作者ID
        """
        # 尝试从请求头获取用户ID
        user_id = request.headers.get("X-User-Id")
        if user_id:
            return user_id

        # 尝试从session获取
        if hasattr(request, "session"):
            user_id = request.session.get("user_id")
            if user_id:
                return str(user_id)

        # 尝试从认证信息获取
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                return str(user.id)

        # 默认为匿名用户
        return "anonymous"

    def _extract_actor_type(self, request: Request) -> ActorType:
        """提取操作者类型

        Args:
            request: HTTP请求

        Returns:
            操作者类型
        """
        # 检查是否为AI操作
        ai_model = request.headers.get("X-AI-Model")
        if ai_model:
            return ActorType.AI

        # 检查是否为系统操作
        is_system = request.headers.get("X-System-Operation")
        if is_system:
            return ActorType.SYSTEM

        # 默认为用户操作
        return ActorType.USER

    def _extract_resource_info(self, path: str, method: str) -> tuple[str, str]:
        """从路径提取资源信息

        Args:
            path: 请求路径
            method: HTTP方法

        Returns:
            (resource_type, resource_id)
        """
        # 移除前缀
        path = path.strip("/")
        parts = path.split("/")

        # 尝试识别资源类型和ID
        # 例如: /api/v1/documents/123 -> (documents, 123)
        resource_type = "unknown"
        resource_id = "unknown"

        if len(parts) >= 3:
            resource_type = parts[2]  # 跳过 "api" 和 "v1"

        if len(parts) >= 4:
            # 最后一个部分可能是资源ID
            last_part = parts[-1]
            if last_part and not last_part.isalpha():
                resource_id = last_part

        return resource_type, resource_id

    async def _log_audit(
        self,
        path: str,
        method: str,
        actor_id: str,
        actor_type: ActorType,
        result: AuditResult,
        error_message: Optional[str],
        duration_ms: int,
        request: Request,
        response: Optional[Response],
    ):
        """记录审计日志

        Args:
            path: 请求路径
            method: HTTP方法
            actor_id: 操作者ID
            actor_type: 操作者类型
            result: 操作结果
            error_message: 错误信息
            duration_ms: 执行时长
            request: HTTP请求
            response: HTTP响应
        """
        from app.core.database import SessionLocal
        from app.services.audit_service import AuditService

        # 提取资源信息
        resource_type, resource_id = self._extract_resource_info(path, method)

        # 获取操作类型
        action = self.METHOD_TO_ACTION.get(method, ActionType.UPDATE)

        # 提取项目ID（如果有）
        project_id = request.headers.get("X-Project-Id")

        # 提取AI模型信息（如果是AI操作）
        ai_model = None
        ai_prompt = None
        if actor_type == ActorType.AI:
            ai_model = request.headers.get("X-AI-Model")
            ai_prompt = request.headers.get("X-AI-Prompt")

        # 构建额外元数据
        extra_metadata = {
            "path": path,
            "method": method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "query_params": dict(request.query_params),
        }

        # 如果有响应状态码，记录
        if response:
            extra_metadata["status_code"] = response.status_code

        # 创建数据库会话
        db = SessionLocal()

        try:
            await AuditService.create_log(
                db=db,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=None,
                project_id=project_id,
                changes=None,
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                result=result,
                error_message=error_message,
                duration_ms=duration_ms,
                extra_metadata=extra_metadata,
            )
        finally:
            db.close()


def setup_audit_middleware(app, enabled: bool = True):
    """设置审计日志中间件

    Args:
        app: FastAPI应用
        enabled: 是否启用
    """
    if enabled:
        app.add_middleware(AuditMiddleware, enabled=enabled)
        logger.info("✅ 审计日志中间件已启用")
    else:
        logger.info("⚠️  审计日志中间件已禁用")
