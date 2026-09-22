"""
权限管理API端点

提供角色、权限、项目成员管理接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.permission import (
    PermissionAction,
    ResourceType as PermissionResourceType,
    PermissionScope
)
from app.services.permission_service import PermissionService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class RoleCreate(BaseModel):
    """创建角色请求"""
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    priority: int = Field(50, description="角色优先级（0-100）", ge=0, le=100)
    is_system: bool = Field(False, description="是否系统角色")


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    priority: Optional[int] = Field(None, description="角色优先级（0-100）", ge=0, le=100)


class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    name: str
    description: Optional[str]
    priority: int
    is_system: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    """创建权限请求"""
    action: PermissionAction = Field(..., description="权限动作")
    resource_type: PermissionResourceType = Field(..., description="资源类型")
    scope: PermissionScope = Field(PermissionScope.ALL, description="权限范围")
    description: Optional[str] = Field(None, description="权限描述")


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    action: str
    resource_type: str
    scope: str
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class RolePermissionAssign(BaseModel):
    """角色权限分配请求"""
    role_id: int = Field(..., description="角色ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")


class ProjectMemberAdd(BaseModel):
    """添加项目成员请求"""
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")


class ProjectMemberUpdate(BaseModel):
    """更新项目成员请求"""
    role_id: int = Field(..., description="新角色ID")


class ProjectMemberResponse(BaseModel):
    """项目成员响应"""
    project_id: int
    user_id: int
    role_id: int
    role_name: str
    user_name: Optional[str]
    joined_at: str

    class Config:
        from_attributes = True


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    user_id: int
    system_roles: List[RoleResponse]
    project_permissions: dict  # {project_id: {role: RoleResponse, permissions: [PermissionResponse]}}
    all_permissions: List[str]  # ["VIEW:PROJECT", "CREATE:DOCUMENT", ...]


class ResourceOwnerSet(BaseModel):
    """设置资源所有者请求"""
    owner_id: int = Field(..., description="所有者用户ID")


class ResourceOwnerResponse(BaseModel):
    """资源所有者响应"""
    resource_type: str
    resource_id: str
    owner_id: int
    set_at: str

    class Config:
        from_attributes = True


# ==================== 依赖项 ====================

async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """获取权限服务"""
    return PermissionService(db)


# ==================== 角色管理 ====================

@router.post("/roles", response_model=RoleResponse, summary="创建角色")
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    创建新角色（需要管理员权限）

    - **name**: 角色名称
    - **description**: 角色描述
    - **priority**: 角色优先级（0-100，数字越大权限越高）
    - **is_system**: 是否系统角色
    """
    # TODO: 添加管理员权限检查
    new_role = await permission_service.create_role(
        name=role.name,
        description=role.description,
        priority=role.priority,
        is_system=role.is_system
    )
    return new_role


@router.get("/roles", response_model=List[RoleResponse], summary="获取角色列表")
async def list_roles(
    is_system: Optional[bool] = Query(None, description="筛选系统/自定义角色"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    获取角色列表

    - **is_system**: 可选，筛选系统角色或自定义角色
    """
    roles = await permission_service.list_roles(is_system=is_system)
    return roles


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="获取角色详情")
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """获取指定角色的详细信息"""
    role = await permission_service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    更新角色信息（需要管理员权限）

    - **name**: 新角色名称
    - **description**: 新角色描述
    - **priority**: 新优先级
    """
    # TODO: 添加管理员权限检查
    updated_role = await permission_service.update_role(
        role_id=role_id,
        name=role_update.name,
        description=role_update.description,
        priority=role_update.priority
    )
    if not updated_role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return updated_role


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    删除角色（需要管理员权限）

    注意：不能删除系统角色
    """
    # TODO: 添加管理员权限检查
    success = await permission_service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法删除该角色（可能是系统角色或不存在）")
    return {"message": "角色已删除"}


# ==================== 权限管理 ====================

@router.post("/permissions", response_model=PermissionResponse, summary="创建权限")
async def create_permission(
    permission: PermissionCreate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    创建新权限（需要管理员权限）

    - **action**: 权限动作（VIEW, CREATE, UPDATE, DELETE, MANAGE, EXECUTE）
    - **resource_type**: 资源类型（PROJECT, DOCUMENT, WORKFLOW等）
    - **scope**: 权限范围（ALL, OWN, PROJECT）
    - **description**: 权限描述
    """
    # TODO: 添加管理员权限检查
    new_permission = await permission_service.create_permission(
        action=permission.action,
        resource_type=permission.resource_type,
        scope=permission.scope,
        description=permission.description
    )
    return new_permission


@router.get("/permissions", response_model=List[PermissionResponse], summary="获取权限列表")
async def list_permissions(
    resource_type: Optional[PermissionResourceType] = Query(None, description="筛选资源类型"),
    action: Optional[PermissionAction] = Query(None, description="筛选动作"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    获取权限列表

    - **resource_type**: 可选，筛选特定资源类型的权限
    - **action**: 可选，筛选特定动作的权限
    """
    permissions = await permission_service.list_permissions(
        resource_type=resource_type,
        action=action
    )
    return permissions


@router.post("/roles/{role_id}/permissions", summary="分配角色权限")
async def assign_role_permissions(
    role_id: int,
    assignment: RolePermissionAssign,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    为角色分配权限（需要管理员权限）

    - **permission_ids**: 权限ID列表
    """
    # TODO: 添加管理员权限检查
    # 实现权限分配逻辑
    from sqlalchemy import insert
    from app.models.permission import RolePermission

    # 先删除旧的权限关联
    await permission_service.db.execute(
        f"DELETE FROM role_permissions WHERE role_id = {role_id}"
    )

    # 添加新的权限关联
    for perm_id in assignment.permission_ids:
        stmt = insert(RolePermission).values(
            role_id=role_id,
            permission_id=perm_id
        )
        await permission_service.db.execute(stmt)

    await permission_service.db.commit()

    return {"message": f"已为角色分配 {len(assignment.permission_ids)} 个权限"}


# ==================== 项目成员管理 ====================

@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, summary="添加项目成员")
async def add_project_member(
    project_id: int,
    member: ProjectMemberAdd,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    添加项目成员（需要项目管理权限）

    - **user_id**: 用户ID
    - **role_id**: 角色ID
    """
    # TODO: 添加项目管理权限检查
    new_member = await permission_service.add_project_member(
        project_id=project_id,
        user_id=member.user_id,
        role_id=member.role_id
    )

    # 构造响应
    from sqlalchemy import select
    from app.models.permission import Role

    role_result = await permission_service.db.execute(
        select(Role).where(Role.id == member.role_id)
    )
    role = role_result.scalar_one_or_none()

    return ProjectMemberResponse(
        project_id=project_id,
        user_id=member.user_id,
        role_id=member.role_id,
        role_name=role.name if role else "未知",
        user_name=None,  # TODO: 从用户表获取
        joined_at=new_member.joined_at.isoformat()
    )


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberResponse], summary="获取项目成员列表")
async def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """获取项目的所有成员"""
    # TODO: 添加项目访问权限检查
    members = await permission_service.list_project_members(project_id)

    # 转换为响应格式
    from sqlalchemy import select
    from app.models.permission import Role

    result = []
    for member in members:
        role_result = await permission_service.db.execute(
            select(Role).where(Role.id == member.role_id)
        )
        role = role_result.scalar_one_or_none()

        result.append(ProjectMemberResponse(
            project_id=member.project_id,
            user_id=member.user_id,
            role_id=member.role_id,
            role_name=role.name if role else "未知",
            user_name=None,  # TODO: 从用户表获取
            joined_at=member.joined_at.isoformat()
        ))

    return result


@router.put("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberResponse, summary="更新项目成员角色")
async def update_project_member(
    project_id: int,
    user_id: int,
    update: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    更新项目成员的角色（需要项目管理权限）

    - **role_id**: 新角色ID
    """
    # TODO: 添加项目管理权限检查
    updated_member = await permission_service.update_member_role(
        project_id=project_id,
        user_id=user_id,
        role_id=update.role_id
    )

    if not updated_member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    # 构造响应
    from sqlalchemy import select
    from app.models.permission import Role

    role_result = await permission_service.db.execute(
        select(Role).where(Role.id == update.role_id)
    )
    role = role_result.scalar_one_or_none()

    return ProjectMemberResponse(
        project_id=project_id,
        user_id=user_id,
        role_id=update.role_id,
        role_name=role.name if role else "未知",
        user_name=None,
        joined_at=updated_member.joined_at.isoformat()
    )


@router.delete("/projects/{project_id}/members/{user_id}", summary="移除项目成员")
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """移除项目成员（需要项目管理权限）"""
    # TODO: 添加项目管理权限检查
    success = await permission_service.remove_project_member(
        project_id=project_id,
        user_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    return {"message": "项目成员已移除"}


# ==================== 资源所有权管理 ====================

@router.post("/resources/{resource_type}/{resource_id}/owner", response_model=ResourceOwnerResponse, summary="设置资源所有者")
async def set_resource_owner(
    resource_type: PermissionResourceType,
    resource_id: str,
    owner: ResourceOwnerSet,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    设置资源所有者（需要资源管理权限）

    - **owner_id**: 新所有者的用户ID
    """
    # TODO: 添加资源管理权限检查
    ownership = await permission_service.set_resource_owner(
        resource_type=resource_type,
        resource_id=resource_id,
        owner_id=owner.owner_id
    )

    return ResourceOwnerResponse(
        resource_type=ownership.resource_type.value,
        resource_id=ownership.resource_id,
        owner_id=ownership.owner_id,
        set_at=ownership.set_at.isoformat()
    )


@router.get("/resources/{resource_type}/{resource_id}/owner", summary="获取资源所有者")
async def get_resource_owner(
    resource_type: PermissionResourceType,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """获取资源的所有者ID"""
    owner_id = await permission_service.get_resource_owner(
        resource_type=resource_type,
        resource_id=resource_id
    )

    if owner_id is None:
        raise HTTPException(status_code=404, detail="资源所有者未设置")

    return {"resource_type": resource_type.value, "resource_id": resource_id, "owner_id": owner_id}


# ==================== 用户权限查询 ====================

@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse, summary="获取用户权限")
async def get_user_permissions(
    user_id: int,
    project_id: Optional[int] = Query(None, description="筛选特定项目的权限"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    获取用户的所有权限

    - **project_id**: 可选，筛选特定项目的权限
    """
    # TODO: 添加权限检查（只能查看自己或下属的权限）
    permissions = await permission_service.get_user_permissions(
        user_id=user_id,
        project_id=project_id
    )

    # 构造响应（简化版本）
    return UserPermissionsResponse(
        user_id=user_id,
        system_roles=[],
        project_permissions={},
        all_permissions=permissions  # 返回权限字符串列表
    )


@router.get("/users/me/permissions", summary="获取当前用户权限")
async def get_my_permissions(
    project_id: Optional[int] = Query(None, description="筛选特定项目的权限"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """获取当前登录用户的所有权限"""
    permissions = await permission_service.get_user_permissions(
        user_id=current_user.id,
        project_id=project_id
    )

    return {
        "user_id": current_user.id,
        "permissions": permissions
    }


@router.post("/check", summary="检查权限")
async def check_permission(
    action: PermissionAction = Query(..., description="权限动作"),
    resource_type: PermissionResourceType = Query(..., description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    检查当前用户是否有特定权限

    - **action**: 权限动作
    - **resource_type**: 资源类型
    - **resource_id**: 可选，资源ID
    - **project_id**: 可选，项目ID
    """
    has_permission = await permission_service.check_permission(
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        project_id=project_id
    )

    return {
        "has_permission": has_permission,
        "user_id": current_user.id,
        "action": action.value,
        "resource_type": resource_type.value,
        "resource_id": resource_id,
        "project_id": project_id
    }
