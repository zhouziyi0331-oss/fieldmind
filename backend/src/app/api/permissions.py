"""
权限管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.response import success_response, error_response
from app.core.rbac import Permission, RBACService, UserRole, require_role
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/permissions", tags=["权限管理"])


class PermissionInfo(BaseModel):
    """权限信息"""
    name: str
    value: str
    description: str


class RolePermissionsResponse(BaseModel):
    """角色权限响应"""
    role: str
    permissions: List[str]


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    user_id: str
    username: str
    role: str
    permissions: List[str]


# 权限描述映射
PERMISSION_DESCRIPTIONS = {
    Permission.PROJECT_CREATE: "创建项目",
    Permission.PROJECT_READ: "查看项目",
    Permission.PROJECT_UPDATE: "更新项目",
    Permission.PROJECT_DELETE: "删除项目",
    Permission.DOCUMENT_UPLOAD: "上传文档",
    Permission.DOCUMENT_READ: "查看文档",
    Permission.DOCUMENT_DELETE: "删除文档",
    Permission.ANALYSIS_CREATE: "创建分析",
    Permission.ANALYSIS_READ: "查看分析",
    Permission.ANALYSIS_UPDATE: "更新分析",
    Permission.ANALYSIS_DELETE: "删除分析",
    Permission.CHAT_CREATE: "发起对话",
    Permission.CHAT_READ: "查看对话",
    Permission.PROPOSAL_CREATE: "生成提案",
    Permission.PROPOSAL_READ: "查看提案",
    Permission.PROPOSAL_EXPORT: "导出提案",
    Permission.USER_CREATE: "创建用户",
    Permission.USER_READ: "查看用户",
    Permission.USER_UPDATE: "更新用户",
    Permission.USER_DELETE: "删除用户",
    Permission.SYSTEM_SETTINGS: "系统设置",
    Permission.SYSTEM_MONITORING: "系统监控",
}


@router.get("/all", response_model=List[PermissionInfo])
async def get_all_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有权限列表

    需要登录
    """
    permissions = []
    for perm in Permission:
        permissions.append({
            "name": perm.name,
            "value": perm.value,
            "description": PERMISSION_DESCRIPTIONS.get(perm, "")
        })

    return permissions


@router.get("/roles", response_model=List[RolePermissionsResponse])
@require_role(UserRole.ADMIN)
async def get_role_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有角色的权限配置

    需要管理员权限
    """
    result = []
    for role in UserRole:
        permissions = RBACService.get_role_permissions(role)
        result.append({
            "role": role.value,
            "permissions": [p.value for p in permissions]
        })

    return result


@router.get("/roles/{role}", response_model=RolePermissionsResponse)
async def get_role_permission_detail(
    role: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取指定角色的权限

    需要登录
    """
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色不存在: {role}"
        )

    permissions = RBACService.get_role_permissions(user_role)

    return success_response(
        data={
            "role": user_role.value,
            "permissions": [p.value for p in permissions]
        }
    )


@router.get("/me", response_model=UserPermissionsResponse)
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的权限

    需要登录
    """
    permissions = RBACService.get_role_permissions(current_user.role)

    return success_response(
        data={
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.value,
            "permissions": [p.value for p in permissions]
        }
    )


@router.get("/check/{permission}/")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_user)
):
    """
    检查当前用户是否有指定权限

    需要登录
    """
    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限不存在: {permission}"
        )

    has_permission = RBACService.has_permission(current_user.role, perm)

    return success_response(
        data={
            "user_id": current_user.id,
            "username": current_user.username,
            "permission": permission,
            "has_permission": has_permission
        }
    )


@router.get("/matrix")
@require_role(UserRole.ADMIN)
async def get_permission_matrix(
    current_user: User = Depends(get_current_user)
):
    """
    获取权限矩阵（角色-权限对应表）

    需要管理员权限
    """
    matrix = {}

    for role in UserRole:
        role_perms = RBACService.get_role_permissions(role)
        matrix[role.value] = {}

        for perm in Permission:
            matrix[role.value][perm.value] = perm in role_perms

    return success_response(
        data={
            "roles": [r.value for r in UserRole],
            "permissions": [
                {
                    "value": p.value,
                    "description": PERMISSION_DESCRIPTIONS.get(p, "")
                }
                for p in Permission
            ],
            "matrix": matrix
        }
    )
