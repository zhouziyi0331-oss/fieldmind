"""
权限检查装饰器和中间件

提供声明式的权限检查机制，用于API路由保护
"""
from functools import wraps
from typing import Optional, Callable, List, Union
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.permission import PermissionAction, ResourceType as PermissionResourceType
from app.services.permission_service import PermissionService


async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """获取权限服务依赖"""
    return PermissionService(db)


class PermissionChecker:
    """权限检查器基类"""

    def __init__(
        self,
        action: PermissionAction,
        resource_type: PermissionResourceType,
        resource_id_param: Optional[str] = None,
        project_id_param: Optional[str] = None,
        allow_owner: bool = True,
        custom_checker: Optional[Callable] = None
    ):
        """
        初始化权限检查器

        Args:
            action: 需要的权限动作
            resource_type: 资源类型
            resource_id_param: 路径/查询参数中资源ID的参数名
            project_id_param: 路径/查询参数中项目ID的参数名
            allow_owner: 是否允许资源所有者访问（即使没有显式权限）
            custom_checker: 自定义检查函数
        """
        self.action = action
        self.resource_type = resource_type
        self.resource_id_param = resource_id_param
        self.project_id_param = project_id_param
        self.allow_owner = allow_owner
        self.custom_checker = custom_checker

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> User:
        """
        执行权限检查

        Returns:
            通过检查的用户对象

        Raises:
            HTTPException: 权限不足时抛出403
        """
        # 提取资源ID和项目ID
        resource_id = None
        project_id = None

        if self.resource_id_param:
            resource_id = (
                request.path_params.get(self.resource_id_param) or
                request.query_params.get(self.resource_id_param)
            )

        if self.project_id_param:
            project_id = (
                request.path_params.get(self.project_id_param) or
                request.query_params.get(self.project_id_param)
            )
            if project_id:
                project_id = int(project_id)

        # 如果有自定义检查器，先执行
        if self.custom_checker:
            custom_result = await self.custom_checker(
                request, current_user, permission_service, resource_id, project_id
            )
            if custom_result:
                return current_user

        # 执行权限检查
        has_permission = await permission_service.check_permission(
            user_id=current_user.id,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=resource_id,
            project_id=project_id
        )

        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：需要 {self.action.value} {self.resource_type.value} 权限"
            )

        return current_user


def require_permission(
    action: PermissionAction,
    resource_type: PermissionResourceType,
    resource_id_param: Optional[str] = None,
    project_id_param: Optional[str] = None,
    allow_owner: bool = True
):
    """
    权限检查装饰器工厂函数

    用法示例：
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: int,
            user: User = Depends(require_permission(
                PermissionAction.VIEW,
                PermissionResourceType.PROJECT,
                resource_id_param="project_id"
            ))
        ):
            ...

    Args:
        action: 需要的权限动作
        resource_type: 资源类型
        resource_id_param: 路径/查询参数中资源ID的参数名
        project_id_param: 路径/查询参数中项目ID的参数名
        allow_owner: 是否允许资源所有者访问

    Returns:
        FastAPI依赖项
    """
    return PermissionChecker(
        action=action,
        resource_type=resource_type,
        resource_id_param=resource_id_param,
        project_id_param=project_id_param,
        allow_owner=allow_owner
    )


def require_any_permission(
    permissions: List[tuple[PermissionAction, PermissionResourceType]],
    resource_id_param: Optional[str] = None,
    project_id_param: Optional[str] = None
):
    """
    要求满足任意一个权限（OR逻辑）

    用法示例：
        @router.get("/resources/{resource_id}")
        async def get_resource(
            resource_id: int,
            user: User = Depends(require_any_permission([
                (PermissionAction.VIEW, PermissionResourceType.DOCUMENT),
                (PermissionAction.VIEW, PermissionResourceType.PROJECT)
            ]))
        ):
            ...
    """
    async def check_any(
        request: Request,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> User:
        resource_id = None
        project_id = None

        if resource_id_param:
            resource_id = (
                request.path_params.get(resource_id_param) or
                request.query_params.get(resource_id_param)
            )

        if project_id_param:
            project_id = (
                request.path_params.get(project_id_param) or
                request.query_params.get(project_id_param)
            )
            if project_id:
                project_id = int(project_id)

        # 检查是否满足任意一个权限
        for action, resource_type in permissions:
            has_permission = await permission_service.check_permission(
                user_id=current_user.id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id
            )
            if has_permission:
                return current_user

        raise HTTPException(
            status_code=403,
            detail="权限不足：需要以下任意权限之一 - " + ", ".join(
                f"{action.value} {rt.value}" for action, rt in permissions
            )
        )

    return check_any


def require_all_permissions(
    permissions: List[tuple[PermissionAction, PermissionResourceType]],
    resource_id_param: Optional[str] = None,
    project_id_param: Optional[str] = None
):
    """
    要求满足所有权限（AND逻辑）

    用法示例：
        @router.delete("/projects/{project_id}")
        async def delete_project(
            project_id: int,
            user: User = Depends(require_all_permissions([
                (PermissionAction.DELETE, PermissionResourceType.PROJECT),
                (PermissionAction.MANAGE, PermissionResourceType.PROJECT)
            ]))
        ):
            ...
    """
    async def check_all(
        request: Request,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> User:
        resource_id = None
        project_id = None

        if resource_id_param:
            resource_id = (
                request.path_params.get(resource_id_param) or
                request.query_params.get(resource_id_param)
            )

        if project_id_param:
            project_id = (
                request.path_params.get(project_id_param) or
                request.query_params.get(project_id_param)
            )
            if project_id:
                project_id = int(project_id)

        # 检查是否满足所有权限
        for action, resource_type in permissions:
            has_permission = await permission_service.check_permission(
                user_id=current_user.id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                project_id=project_id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足：需要 {action.value} {resource_type.value} 权限"
                )

        return current_user

    return check_all


def require_project_role(
    project_id_param: str = "project_id",
    min_role_priority: int = 50  # 默认要求至少是成员角色
):
    """
    要求用户在项目中具有特定优先级以上的角色

    用法示例：
        @router.post("/projects/{project_id}/invite")
        async def invite_member(
            project_id: int,
            user: User = Depends(require_project_role(min_role_priority=80))  # 至少管理员
        ):
            ...

    Args:
        project_id_param: 项目ID参数名
        min_role_priority: 最小角色优先级（数字越大权限越高）
    """
    async def check_role(
        request: Request,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> User:
        project_id = (
            request.path_params.get(project_id_param) or
            request.query_params.get(project_id_param)
        )

        if not project_id:
            raise HTTPException(status_code=400, detail="缺少项目ID参数")

        project_id = int(project_id)

        # 获取用户在项目中的成员记录
        from sqlalchemy import select
        from app.models.permission import ProjectMember, Role

        result = await permission_service.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(status_code=403, detail="您不是该项目的成员")

        # 获取角色信息
        role_result = await permission_service.db.execute(
            select(Role).where(Role.id == member.role_id)
        )
        role_obj = role_result.scalar_one_or_none()

        if not role_obj or role_obj.priority < min_role_priority:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：需要角色优先级至少为 {min_role_priority}"
            )

        return current_user

    return check_role


def require_resource_owner(
    resource_type: PermissionResourceType,
    resource_id_param: str
):
    """
    要求用户是资源的所有者

    用法示例：
        @router.put("/documents/{document_id}/transfer")
        async def transfer_ownership(
            document_id: int,
            user: User = Depends(require_resource_owner(
                PermissionResourceType.DOCUMENT,
                "document_id"
            ))
        ):
            ...
    """
    async def check_owner(
        request: Request,
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> User:
        resource_id = (
            request.path_params.get(resource_id_param) or
            request.query_params.get(resource_id_param)
        )

        if not resource_id:
            raise HTTPException(status_code=400, detail="缺少资源ID参数")

        # 获取资源所有者
        owner_id = await permission_service.get_resource_owner(
            resource_type=resource_type,
            resource_id=resource_id
        )

        if owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="权限不足：您不是该资源的所有者")

        return current_user

    return check_owner
