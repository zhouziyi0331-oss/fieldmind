"""
RBAC权限控制系统 - Role-Based Access Control
"""
from enum import Enum
from typing import List, Set, Optional
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.core.database import get_db


class Permission(str, Enum):
    """权限枚举"""
    # 项目权限
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    # 文档权限
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_DELETE = "document:delete"

    # 分析权限
    ANALYSIS_CREATE = "analysis:create"
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_UPDATE = "analysis:update"
    ANALYSIS_DELETE = "analysis:delete"

    # 对话权限
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"

    # 提案权限
    PROPOSAL_CREATE = "proposal:create"
    PROPOSAL_READ = "proposal:read"
    PROPOSAL_EXPORT = "proposal:export"

    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 系统权限
    SYSTEM_SETTINGS = "system:settings"
    SYSTEM_MONITORING = "system:monitoring"


# 角色权限映射
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # 管理员拥有所有权限
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ,
        Permission.ANALYSIS_UPDATE,
        Permission.ANALYSIS_DELETE,
        Permission.CHAT_CREATE,
        Permission.CHAT_READ,
        Permission.PROPOSAL_CREATE,
        Permission.PROPOSAL_READ,
        Permission.PROPOSAL_EXPORT,
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.SYSTEM_SETTINGS,
        Permission.SYSTEM_MONITORING,
    },
    UserRole.RESEARCHER: {
        # 研究员：可以创建和管理自己的项目
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ,
        Permission.ANALYSIS_UPDATE,
        Permission.CHAT_CREATE,
        Permission.CHAT_READ,
        Permission.PROPOSAL_CREATE,
        Permission.PROPOSAL_READ,
        Permission.PROPOSAL_EXPORT,
    },
    UserRole.VIEWER: {
        # 查看者：只读权限
        Permission.PROJECT_READ,
        Permission.DOCUMENT_READ,
        Permission.ANALYSIS_READ,
        Permission.CHAT_READ,
        Permission.PROPOSAL_READ,
    }
}


class RBACService:
    """RBAC服务"""

    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        """检查角色是否有指定权限"""
        return permission in ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
        """检查角色是否有任意一个权限"""
        role_perms = ROLE_PERMISSIONS.get(role, set())
        return any(perm in role_perms for perm in permissions)

    @staticmethod
    def has_all_permissions(role: UserRole, permissions: List[Permission]) -> bool:
        """检查角色是否有所有权限"""
        role_perms = ROLE_PERMISSIONS.get(role, set())
        return all(perm in role_perms for perm in permissions)

    @staticmethod
    def get_role_permissions(role: UserRole) -> Set[Permission]:
        """获取角色的所有权限"""
        return ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def check_permission(role: UserRole, permission: Permission):
        """检查权限，如果没有则抛出异常"""
        if not RBACService.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission.value}"
            )


def require_permission(permission: Permission):
    """
    权限装饰器 - 用于保护API端点

    用法:
    @router.get("/projects")
    @require_permission(Permission.PROJECT_READ)
    async def get_projects(current_user: User = Depends(get_current_user)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )

            # 检查权限
            RBACService.check_permission(current_user.role, permission)

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """
    需要任意一个权限

    用法:
    @require_any_permission(Permission.PROJECT_READ, Permission.ANALYSIS_READ)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )

            if not RBACService.has_any_permission(current_user.role, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下任意权限: {[p.value for p in permissions]}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*permissions: Permission):
    """
    需要所有权限

    用法:
    @require_all_permissions(Permission.PROJECT_UPDATE, Permission.DOCUMENT_UPLOAD)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )

            if not RBACService.has_all_permissions(current_user.role, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下所有权限: {[p.value for p in permissions]}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: UserRole):
    """
    需要指定角色

    用法:
    @require_role(UserRole.ADMIN)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )

            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {[r.value for r in roles]}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
