"""权限服务

提供角色、权限、项目成员的管理功能
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.permission import (
    Role,
    Permission,
    ProjectMember,
    ResourceOwnership,
    PermissionAction,
    ResourceType as PermissionResourceType,
)
from app.core.logging import logger


class PermissionService:
    """权限服务"""

    # ==================== 角色管理 ====================

    @staticmethod
    async def create_role(
        db: Session,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        is_system: bool = False,
        is_default: bool = False,
        project_id: Optional[str] = None,
        priority: int = 0,
        permission_ids: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> Role:
        """创建角色

        Args:
            db: 数据库会话
            name: 角色名称（如: owner, admin, member）
            display_name: 显示名称
            description: 描述
            is_system: 是否为系统角色
            is_default: 是否为默认角色
            project_id: 项目ID（null表示系统级角色）
            priority: 优先级（数字越大权限越高）
            permission_ids: 权限ID列表
            created_by: 创建者ID

        Returns:
            创建的角色对象
        """
        try:
            role = Role(
                name=name,
                display_name=display_name,
                description=description,
                is_system=is_system,
                is_default=is_default,
                project_id=project_id,
                priority=priority,
                created_by=created_by,
            )

            # 关联权限
            if permission_ids:
                permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
                role.permissions = permissions

            db.add(role)
            db.commit()
            db.refresh(role)

            logger.info(f"Role created: {name} (id={role.id})")
            return role

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create role: {str(e)}")
            raise

    @staticmethod
    async def get_role(db: Session, role_id: str) -> Optional[Role]:
        """获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()

    @staticmethod
    async def list_roles(
        db: Session,
        project_id: Optional[str] = None,
        is_system: Optional[bool] = None,
        is_active: bool = True,
    ) -> List[Role]:
        """列出角色

        Args:
            db: 数据库会话
            project_id: 项目ID（null表示系统级角色）
            is_system: 是否为系统角色
            is_active: 是否激活

        Returns:
            角色列表
        """
        query = db.query(Role).filter(Role.is_active == is_active)

        if project_id is not None:
            query = query.filter(Role.project_id == project_id)

        if is_system is not None:
            query = query.filter(Role.is_system == is_system)

        return query.order_by(Role.priority.desc()).all()

    @staticmethod
    async def update_role(
        db: Session,
        role_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        permission_ids: Optional[List[str]] = None,
    ) -> Role:
        """更新角色"""
        role = await PermissionService.get_role(db, role_id)
        if not role:
            raise ValueError(f"Role not found: {role_id}")

        if display_name:
            role.display_name = display_name
        if description is not None:
            role.description = description
        if priority is not None:
            role.priority = priority

        if permission_ids is not None:
            permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            role.permissions = permissions

        db.commit()
        db.refresh(role)

        return role

    @staticmethod
    async def delete_role(db: Session, role_id: str) -> bool:
        """删除角色（软删除）"""
        role = await PermissionService.get_role(db, role_id)
        if not role:
            return False

        if role.is_system:
            raise ValueError("Cannot delete system role")

        role.is_active = False
        db.commit()

        return True

    # ==================== 权限管理 ====================

    @staticmethod
    async def create_permission(
        db: Session,
        code: str,
        display_name: str,
        resource_type: PermissionResourceType,
        action: PermissionAction,
        description: Optional[str] = None,
        scope: Optional[Dict[str, Any]] = None,
        is_system: bool = False,
    ) -> Permission:
        """创建权限

        Args:
            db: 数据库会话
            code: 权限代码（如: project:view, document:edit）
            display_name: 显示名称
            resource_type: 资源类型
            action: 操作类型
            description: 描述
            scope: 权限范围（如: {"scope": "own"} 表示只能操作自己的资源）
            is_system: 是否为系统权限

        Returns:
            创建的权限对象
        """
        try:
            permission = Permission(
                code=code,
                display_name=display_name,
                resource_type=resource_type,
                action=action,
                description=description,
                scope=scope,
                is_system=is_system,
            )

            db.add(permission)
            db.commit()
            db.refresh(permission)

            logger.info(f"Permission created: {code}")
            return permission

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create permission: {str(e)}")
            raise

    @staticmethod
    async def list_permissions(
        db: Session,
        resource_type: Optional[PermissionResourceType] = None,
        action: Optional[PermissionAction] = None,
        is_active: bool = True,
    ) -> List[Permission]:
        """列出权限"""
        query = db.query(Permission).filter(Permission.is_active == is_active)

        if resource_type:
            query = query.filter(Permission.resource_type == resource_type)
        if action:
            query = query.filter(Permission.action == action)

        return query.all()

    # ==================== 项目成员管理 ====================

    @staticmethod
    async def add_project_member(
        db: Session,
        project_id: str,
        user_id: str,
        role_id: str,
        invited_by: Optional[str] = None,
        note: Optional[str] = None,
    ) -> ProjectMember:
        """添加项目成员

        Args:
            db: 数据库会话
            project_id: 项目ID
            user_id: 用户ID
            role_id: 角色ID
            invited_by: 邀请者ID
            note: 备注

        Returns:
            项目成员对象
        """
        try:
            # 检查是否已存在
            existing = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active == True,
                )
                .first()
            )

            if existing:
                raise ValueError(f"User {user_id} is already a member of project {project_id}")

            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role_id=role_id,
                invited_by=invited_by,
                note=note,
            )

            db.add(member)
            db.commit()
            db.refresh(member)

            logger.info(f"Project member added: user={user_id}, project={project_id}, role={role_id}")
            return member

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add project member: {str(e)}")
            raise

    @staticmethod
    async def remove_project_member(
        db: Session,
        project_id: str,
        user_id: str,
    ) -> bool:
        """移除项目成员（软删除）"""
        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True,
            )
            .first()
        )

        if not member:
            return False

        member.is_active = False
        db.commit()

        logger.info(f"Project member removed: user={user_id}, project={project_id}")
        return True

    @staticmethod
    async def list_project_members(
        db: Session,
        project_id: str,
        is_active: bool = True,
    ) -> List[ProjectMember]:
        """列出项目成员"""
        return (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.is_active == is_active,
            )
            .all()
        )

    @staticmethod
    async def update_member_role(
        db: Session,
        project_id: str,
        user_id: str,
        new_role_id: str,
    ) -> ProjectMember:
        """更新成员角色"""
        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True,
            )
            .first()
        )

        if not member:
            raise ValueError(f"Member not found: user={user_id}, project={project_id}")

        member.role_id = new_role_id
        db.commit()
        db.refresh(member)

        return member

    # ==================== 资源所有权管理 ====================

    @staticmethod
    async def set_resource_owner(
        db: Session,
        resource_type: PermissionResourceType,
        resource_id: str,
        owner_id: str,
        project_id: Optional[str] = None,
    ) -> ResourceOwnership:
        """设置资源所有者"""
        try:
            # 检查是否已存在
            existing = (
                db.query(ResourceOwnership)
                .filter(
                    ResourceOwnership.resource_type == resource_type,
                    ResourceOwnership.resource_id == resource_id,
                )
                .first()
            )

            if existing:
                existing.owner_id = owner_id
                existing.project_id = project_id
                db.commit()
                db.refresh(existing)
                return existing

            ownership = ResourceOwnership(
                resource_type=resource_type,
                resource_id=resource_id,
                owner_id=owner_id,
                project_id=project_id,
            )

            db.add(ownership)
            db.commit()
            db.refresh(ownership)

            return ownership

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set resource owner: {str(e)}")
            raise

    @staticmethod
    async def get_resource_owner(
        db: Session,
        resource_type: PermissionResourceType,
        resource_id: str,
    ) -> Optional[str]:
        """获取资源所有者ID"""
        ownership = (
            db.query(ResourceOwnership)
            .filter(
                ResourceOwnership.resource_type == resource_type,
                ResourceOwnership.resource_id == resource_id,
            )
            .first()
        )

        return ownership.owner_id if ownership else None

    # ==================== 权限检查 ====================

    @staticmethod
    async def check_permission(
        db: Session,
        user_id: str,
        resource_type: PermissionResourceType,
        action: PermissionAction,
        resource_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> bool:
        """检查用户是否有权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_type: 资源类型
            action: 操作类型
            resource_id: 资源ID（用于检查"own"范围权限）
            project_id: 项目ID（用于检查项目级权限）

        Returns:
            是否有权限
        """
        # 获取用户在该项目中的角色
        if project_id:
            member = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active == True,
                )
                .first()
            )

            if not member:
                return False

            role = await PermissionService.get_role(db, member.role_id)
            if not role:
                return False

        else:
            # 系统级权限检查（暂时返回True，单用户场景）
            return True

        # 检查角色的权限
        for permission in role.permissions:
            if permission.resource_type == resource_type and permission.action == action:
                # 检查权限范围
                if permission.scope:
                    scope_type = permission.scope.get("scope")
                    if scope_type == "own" and resource_id:
                        # 检查是否为资源所有者
                        owner_id = await PermissionService.get_resource_owner(
                            db, resource_type, resource_id
                        )
                        if owner_id != user_id:
                            continue

                return True

        return False

    @staticmethod
    async def get_user_permissions(
        db: Session,
        user_id: str,
        project_id: Optional[str] = None,
    ) -> List[Permission]:
        """获取用户的所有权限"""
        if project_id:
            member = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active == True,
                )
                .first()
            )

            if not member:
                return []

            role = await PermissionService.get_role(db, member.role_id)
            if not role:
                return []

            return role.permissions

        # 系统级权限（单用户场景返回所有权限）
        return db.query(Permission).filter(Permission.is_active == True).all()
