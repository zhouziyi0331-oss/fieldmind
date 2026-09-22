"""
版本控制和回滚系统

提供企业级的版本管理和回滚能力：
- 数据包版本管理
- 配置版本管理
- 模型版本管理
- 一键回滚功能
- 版本比较和审计
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import logging

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.hermes import DataPacket

logger = logging.getLogger(__name__)

Base = declarative_base()


class VersionType(str, Enum):
    """版本类型"""
    DATA_PACKET = "data_packet"
    CONFIGURATION = "configuration"
    MODEL = "model"
    STAGE = "stage"
    WORKFLOW = "workflow"


class VersionStatus(str, Enum):
    """版本状态"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


# ==================== 数据库模型 ====================

class Version(Base):
    """版本记录表"""
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(64), unique=True, nullable=False, index=True)
    version_type = Column(String(32), nullable=False, index=True)
    resource_id = Column(String(128), nullable=False, index=True)
    resource_name = Column(String(256))

    version_number = Column(Integer, nullable=False)  # 版本号
    parent_version_id = Column(String(64), ForeignKey("versions.version_id"))  # 父版本

    content = Column(JSON, nullable=False)  # 版本内容
    content_hash = Column(String(64), nullable=False)  # 内容哈希
    diff_from_parent = Column(JSON)  # 与父版本的差异

    status = Column(String(32), default=VersionStatus.ACTIVE.value)

    project_id = Column(Integer, nullable=False, index=True)
    created_by = Column(Integer)  # 创建者用户ID
    created_at = Column(DateTime, default=datetime.utcnow)

    metadata = Column(JSON)  # 额外元数据
    tags = Column(JSON)  # 版本标签
    description = Column(Text)  # 版本描述

    # 关系
    parent = relationship("Version", remote_side=[version_id], backref="children")

    # 索引
    __table_args__ = (
        Index("idx_version_resource", "resource_id", "version_number"),
        Index("idx_version_project", "project_id", "version_type"),
        Index("idx_version_status", "status", "version_type"),
    )


class RollbackHistory(Base):
    """回滚历史表"""
    __tablename__ = "rollback_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rollback_id = Column(String(64), unique=True, nullable=False)

    from_version_id = Column(String(64), nullable=False)
    to_version_id = Column(String(64), nullable=False)

    resource_id = Column(String(128), nullable=False)
    resource_type = Column(String(32), nullable=False)

    reason = Column(Text)  # 回滚原因
    rollback_by = Column(Integer, nullable=False)  # 执行回滚的用户
    rollback_at = Column(DateTime, default=datetime.utcnow)

    affected_resources = Column(JSON)  # 受影响的资源
    rollback_result = Column(JSON)  # 回滚结果

    project_id = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_rollback_resource", "resource_id", "rollback_at"),
    )


# ==================== 版本控制服务 ====================

class VersionControlService:
    """版本控制服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_version(
        self,
        version_type: VersionType,
        resource_id: str,
        resource_name: str,
        content: Dict[str, Any],
        project_id: int,
        created_by: Optional[int] = None,
        parent_version_id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Version:
        """
        创建新版本

        Args:
            version_type: 版本类型
            resource_id: 资源ID
            resource_name: 资源名称
            content: 版本内容
            project_id: 项目ID
            created_by: 创建者
            parent_version_id: 父版本ID
            description: 版本描述
            tags: 版本标签

        Returns:
            Version 对象
        """

        # 计算内容哈希
        content_hash = self._compute_hash(content)

        # 获取当前最大版本号
        latest = self.db.query(Version).filter(
            Version.resource_id == resource_id,
            Version.version_type == version_type.value
        ).order_by(Version.version_number.desc()).first()

        version_number = (latest.version_number + 1) if latest else 1

        # 计算与父版本的差异
        diff = None
        if parent_version_id:
            parent = self.get_version(parent_version_id)
            if parent:
                diff = self._compute_diff(parent.content, content)

        # 创建版本记录
        version = Version(
            version_id=self._generate_version_id(version_type, resource_id, version_number),
            version_type=version_type.value,
            resource_id=resource_id,
            resource_name=resource_name,
            version_number=version_number,
            parent_version_id=parent_version_id,
            content=content,
            content_hash=content_hash,
            diff_from_parent=diff,
            status=VersionStatus.ACTIVE.value,
            project_id=project_id,
            created_by=created_by,
            description=description,
            tags=tags or [],
            metadata={}
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        logger.info(f"✅ 版本已创建: {version.version_id} (v{version_number})")
        return version

    def get_version(self, version_id: str) -> Optional[Version]:
        """获取指定版本"""
        return self.db.query(Version).filter(
            Version.version_id == version_id
        ).first()

    def get_latest_version(
        self,
        version_type: VersionType,
        resource_id: str,
        status: Optional[VersionStatus] = VersionStatus.ACTIVE
    ) -> Optional[Version]:
        """获取最新版本"""
        query = self.db.query(Version).filter(
            Version.version_type == version_type.value,
            Version.resource_id == resource_id
        )

        if status:
            query = query.filter(Version.status == status.value)

        return query.order_by(Version.version_number.desc()).first()

    def list_versions(
        self,
        version_type: Optional[VersionType] = None,
        resource_id: Optional[str] = None,
        project_id: Optional[int] = None,
        status: Optional[VersionStatus] = None,
        limit: int = 100
    ) -> List[Version]:
        """列出版本"""
        query = self.db.query(Version)

        if version_type:
            query = query.filter(Version.version_type == version_type.value)
        if resource_id:
            query = query.filter(Version.resource_id == resource_id)
        if project_id:
            query = query.filter(Version.project_id == project_id)
        if status:
            query = query.filter(Version.status == status.value)

        return query.order_by(Version.created_at.desc()).limit(limit).all()

    def rollback(
        self,
        resource_id: str,
        version_type: VersionType,
        target_version_id: str,
        rollback_by: int,
        reason: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        回滚到指定版本

        Args:
            resource_id: 资源ID
            version_type: 版本类型
            target_version_id: 目标版本ID
            rollback_by: 执行回滚的用户
            reason: 回滚原因
            project_id: 项目ID

        Returns:
            回滚结果
        """

        # 获取目标版本
        target_version = self.get_version(target_version_id)
        if not target_version:
            raise ValueError(f"目标版本不存在: {target_version_id}")

        # 获取当前版本
        current_version = self.get_latest_version(version_type, resource_id)
        if not current_version:
            raise ValueError(f"当前版本不存在: {resource_id}")

        if current_version.version_id == target_version_id:
            logger.warning(f"目标版本即为当前版本: {target_version_id}")
            return {"status": "no_change", "message": "目标版本即为当前版本"}

        # 标记当前版本为回滚状态
        current_version.status = VersionStatus.ROLLED_BACK.value

        # 创建新版本（内容为目标版本的内容）
        new_version = self.create_version(
            version_type=version_type,
            resource_id=resource_id,
            resource_name=target_version.resource_name,
            content=target_version.content,
            project_id=project_id or target_version.project_id,
            created_by=rollback_by,
            parent_version_id=current_version.version_id,
            description=f"回滚到 v{target_version.version_number}",
            tags=["rollback"]
        )

        # 记录回滚历史
        rollback_record = RollbackHistory(
            rollback_id=self._generate_rollback_id(),
            from_version_id=current_version.version_id,
            to_version_id=target_version_id,
            resource_id=resource_id,
            resource_type=version_type.value,
            reason=reason,
            rollback_by=rollback_by,
            project_id=project_id or target_version.project_id,
            rollback_result={
                "new_version_id": new_version.version_id,
                "new_version_number": new_version.version_number
            }
        )

        self.db.add(rollback_record)
        self.db.commit()

        logger.info(
            f"✅ 回滚成功: {resource_id} "
            f"v{current_version.version_number} -> v{target_version.version_number}"
        )

        return {
            "status": "success",
            "from_version": current_version.version_number,
            "to_version": target_version.version_number,
            "new_version_id": new_version.version_id,
            "rollback_id": rollback_record.rollback_id
        }

    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict[str, Any]:
        """
        比较两个版本

        Returns:
            {
                "version_1": {...},
                "version_2": {...},
                "diff": {...},
                "changes_summary": {...}
            }
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            raise ValueError("版本不存在")

        diff = self._compute_diff(v1.content, v2.content)

        return {
            "version_1": {
                "version_id": v1.version_id,
                "version_number": v1.version_number,
                "created_at": v1.created_at.isoformat()
            },
            "version_2": {
                "version_id": v2.version_id,
                "version_number": v2.version_number,
                "created_at": v2.created_at.isoformat()
            },
            "diff": diff,
            "changes_summary": self._summarize_changes(diff)
        }

    def get_version_history(
        self,
        resource_id: str,
        version_type: VersionType,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取版本历史"""
        versions = self.list_versions(
            version_type=version_type,
            resource_id=resource_id,
            limit=limit
        )

        return [
            {
                "version_id": v.version_id,
                "version_number": v.version_number,
                "status": v.status,
                "created_by": v.created_by,
                "created_at": v.created_at.isoformat(),
                "description": v.description,
                "tags": v.tags,
                "content_hash": v.content_hash
            }
            for v in versions
        ]

    def get_rollback_history(
        self,
        resource_id: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        query = self.db.query(RollbackHistory)

        if resource_id:
            query = query.filter(RollbackHistory.resource_id == resource_id)
        if project_id:
            query = query.filter(RollbackHistory.project_id == project_id)

        records = query.order_by(RollbackHistory.rollback_at.desc()).limit(limit).all()

        return [
            {
                "rollback_id": r.rollback_id,
                "from_version_id": r.from_version_id,
                "to_version_id": r.to_version_id,
                "resource_id": r.resource_id,
                "reason": r.reason,
                "rollback_by": r.rollback_by,
                "rollback_at": r.rollback_at.isoformat(),
                "result": r.rollback_result
            }
            for r in records
        ]

    # ==================== 辅助方法 ====================

    def _compute_hash(self, content: Dict[str, Any]) -> str:
        """计算内容哈希"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _generate_version_id(
        self,
        version_type: VersionType,
        resource_id: str,
        version_number: int
    ) -> str:
        """生成版本ID"""
        return f"{version_type.value}_{resource_id}_v{version_number}"

    def _generate_rollback_id(self) -> str:
        """生成回滚ID"""
        import uuid
        return f"rollback_{uuid.uuid4().hex[:12]}"

    def _compute_diff(
        self,
        content1: Dict[str, Any],
        content2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算两个内容的差异"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {}
        }

        # 找出新增和修改的键
        for key in content2:
            if key not in content1:
                diff["added"][key] = content2[key]
            elif content1[key] != content2[key]:
                diff["modified"][key] = {
                    "old": content1[key],
                    "new": content2[key]
                }

        # 找出删除的键
        for key in content1:
            if key not in content2:
                diff["removed"][key] = content1[key]

        return diff

    def _summarize_changes(self, diff: Dict[str, Any]) -> Dict[str, int]:
        """汇总变更统计"""
        return {
            "added_count": len(diff.get("added", {})),
            "removed_count": len(diff.get("removed", {})),
            "modified_count": len(diff.get("modified", {})),
            "total_changes": (
                len(diff.get("added", {})) +
                len(diff.get("removed", {})) +
                len(diff.get("modified", {}))
            )
        }


# ==================== 便捷装饰器 ====================

def versioned(
    version_type: VersionType,
    resource_id_key: str = "id",
    resource_name_key: str = "name"
):
    """
    版本控制装饰器

    用法:
        @versioned(
            version_type=VersionType.CONFIGURATION,
            resource_id_key="config_id",
            resource_name_key="config_name"
        )
        async def update_config(config_id: str, data: Dict, db: Session):
            # 更新逻辑
            return updated_data
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行原函数
            result = await func(*args, **kwargs)

            # 提取参数
            db = kwargs.get("db")
            resource_id = kwargs.get(resource_id_key) or result.get(resource_id_key)
            resource_name = result.get(resource_name_key, "")
            project_id = kwargs.get("project_id", 0)
            user_id = kwargs.get("user_id")

            if db and resource_id:
                # 创建版本
                version_service = VersionControlService(db)
                version_service.create_version(
                    version_type=version_type,
                    resource_id=str(resource_id),
                    resource_name=resource_name,
                    content=result,
                    project_id=project_id,
                    created_by=user_id
                )

            return result

        return wrapper

    return decorator
