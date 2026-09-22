"""
协作与权限服务 (Collaboration & Permission Service)
实现项目成员管理、角色权限控制、操作日志
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProjectRole(str, Enum):
    """项目角色枚举"""
    OWNER = "owner"           # 拥有者（创建者）
    ADMIN = "admin"           # 管理员（可管理成员、修改项目设置）
    EDITOR = "editor"         # 编辑者（可上传、分析、生成报告）
    VIEWER = "viewer"         # 查看者（只读）


class PermissionType(str, Enum):
    """权限类型"""
    # 项目管理
    PROJECT_DELETE = "project_delete"
    PROJECT_EDIT = "project_edit"
    PROJECT_VIEW = "project_view"

    # 成员管理
    MEMBER_INVITE = "member_invite"
    MEMBER_REMOVE = "member_remove"
    MEMBER_ROLE_CHANGE = "member_role_change"

    # 文档管理
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_VIEW = "document_view"

    # 分析功能
    ANALYSIS_RUN = "analysis_run"
    REPORT_GENERATE = "report_generate"
    REPORT_VIEW = "report_view"


# 角色权限映射
ROLE_PERMISSIONS = {
    ProjectRole.OWNER: [
        # 全部权限
        PermissionType.PROJECT_DELETE,
        PermissionType.PROJECT_EDIT,
        PermissionType.PROJECT_VIEW,
        PermissionType.MEMBER_INVITE,
        PermissionType.MEMBER_REMOVE,
        PermissionType.MEMBER_ROLE_CHANGE,
        PermissionType.DOCUMENT_UPLOAD,
        PermissionType.DOCUMENT_DELETE,
        PermissionType.DOCUMENT_VIEW,
        PermissionType.ANALYSIS_RUN,
        PermissionType.REPORT_GENERATE,
        PermissionType.REPORT_VIEW,
    ],
    ProjectRole.ADMIN: [
        PermissionType.PROJECT_EDIT,
        PermissionType.PROJECT_VIEW,
        PermissionType.MEMBER_INVITE,
        PermissionType.MEMBER_REMOVE,
        PermissionType.DOCUMENT_UPLOAD,
        PermissionType.DOCUMENT_DELETE,
        PermissionType.DOCUMENT_VIEW,
        PermissionType.ANALYSIS_RUN,
        PermissionType.REPORT_GENERATE,
        PermissionType.REPORT_VIEW,
    ],
    ProjectRole.EDITOR: [
        PermissionType.PROJECT_VIEW,
        PermissionType.DOCUMENT_UPLOAD,
        PermissionType.DOCUMENT_VIEW,
        PermissionType.ANALYSIS_RUN,
        PermissionType.REPORT_GENERATE,
        PermissionType.REPORT_VIEW,
    ],
    ProjectRole.VIEWER: [
        PermissionType.PROJECT_VIEW,
        PermissionType.DOCUMENT_VIEW,
        PermissionType.REPORT_VIEW,
    ],
}


class CollaborationService:
    """
    协作与权限服务

    功能：
    1. 项目成员管理
    2. 角色权限控制
    3. 操作日志记录
    4. 邀请链接生成
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        pass

    def add_member(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        role: ProjectRole,
        invited_by: int
    ) -> Dict[str, Any]:
        """
        添加项目成员

        Args:
            project_id: 项目 ID
            user_id: 用户 ID
            role: 角色
            invited_by: 邀请人 ID

        Returns:
            成员信息
        """
        from app.models.collaboration import ProjectMember

        # 检查是否已存在
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if existing:
            return {
                "error": "用户已是项目成员",
                "member_id": existing.id
            }

        # 创建成员记录
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role.value,
            invited_by=invited_by,
            joined_at=datetime.now()
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        # 记录操作日志
        self._log_action(
            db=db,
            project_id=project_id,
            user_id=invited_by,
            action="member_added",
            details={"new_member_id": user_id, "role": role.value}
        )

        logger.info(f"用户 {user_id} 加入项目 {project_id}，角色 {role.value}")

        return {
            "member_id": member.id,
            "user_id": user_id,
            "role": role.value,
            "joined_at": member.joined_at.isoformat()
        }

    def remove_member(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        removed_by: int
    ) -> Dict[str, Any]:
        """移除项目成员"""
        from app.models.collaboration import ProjectMember

        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if not member:
            return {"error": "成员不存在"}

        # 不能移除项目拥有者
        if member.role == ProjectRole.OWNER.value:
            return {"error": "不能移除项目拥有者"}

        db.delete(member)
        db.commit()

        # 记录操作日志
        self._log_action(
            db=db,
            project_id=project_id,
            user_id=removed_by,
            action="member_removed",
            details={"removed_user_id": user_id}
        )

        return {"success": True, "message": "成员已移除"}

    def change_member_role(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        new_role: ProjectRole,
        changed_by: int
    ) -> Dict[str, Any]:
        """修改成员角色"""
        from app.models.collaboration import ProjectMember

        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if not member:
            return {"error": "成员不存在"}

        # 不能修改拥有者的角色
        if member.role == ProjectRole.OWNER.value:
            return {"error": "不能修改拥有者的角色"}

        old_role = member.role
        member.role = new_role.value
        db.commit()

        # 记录操作日志
        self._log_action(
            db=db,
            project_id=project_id,
            user_id=changed_by,
            action="role_changed",
            details={"target_user_id": user_id, "old_role": old_role, "new_role": new_role.value}
        )

        return {
            "success": True,
            "user_id": user_id,
            "new_role": new_role.value
        }

    def get_project_members(
        self,
        db: Session,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """获取项目所有成员"""
        from app.models.collaboration import ProjectMember

        members = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

        return [
            {
                "member_id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                "invited_by": m.invited_by
            }
            for m in members
        ]

    def check_permission(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        permission: PermissionType
    ) -> bool:
        """
        检查用户是否有特定权限

        Returns:
            True: 有权限
            False: 无权限
        """
        from app.models.collaboration import ProjectMember

        # 获取用户在项目中的角色
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()

        if not member:
            return False

        # 检查角色权限
        role = ProjectRole(member.role)
        allowed_permissions = ROLE_PERMISSIONS.get(role, [])

        return permission in allowed_permissions

    def generate_invite_link(
        self,
        db: Session,
        project_id: int,
        role: ProjectRole,
        created_by: int,
        expires_in_days: int = 7
    ) -> Dict[str, Any]:
        """
        生成邀请链接

        Args:
            expires_in_days: 有效期（天）

        Returns:
            {
                "invite_code": str,
                "invite_link": str,
                "expires_at": str
            }
        """
        from app.models.collaboration import ProjectInvite
        import secrets

        # 生成邀请码
        invite_code = secrets.token_urlsafe(16)

        # 计算过期时间
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(days=expires_in_days)

        # 创建邀请记录
        invite = ProjectInvite(
            project_id=project_id,
            invite_code=invite_code,
            role=role.value,
            created_by=created_by,
            expires_at=expires_at,
            is_used=False
        )

        db.add(invite)
        db.commit()

        return {
            "invite_code": invite_code,
            "invite_link": f"/projects/join/{invite_code}",
            "role": role.value,
            "expires_at": expires_at.isoformat()
        }

    def _log_action(
        self,
        db: Session,
        project_id: int,
        user_id: int,
        action: str,
        details: Dict = None
    ):
        """记录操作日志"""
        from app.models.collaboration import ProjectActivityLog
        import json

        log = ProjectActivityLog(
            project_id=project_id,
            user_id=user_id,
            action=action,
            details=json.dumps(details or {}, ensure_ascii=False),
            created_at=datetime.now()
        )

        db.add(log)
        db.commit()

    def get_activity_log(
        self,
        db: Session,
        project_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取项目活动日志"""
        from app.models.collaboration import ProjectActivityLog

        logs = db.query(ProjectActivityLog).filter(
            ProjectActivityLog.project_id == project_id
        ).order_by(ProjectActivityLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]


# 全局实例
collaboration_service = CollaborationService()
