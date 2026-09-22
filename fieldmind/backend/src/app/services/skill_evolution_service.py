"""
Skill Evolution Service - 技能演化服务
用于追踪、记录和优化Skill的演化过程
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging
import hashlib
import difflib

from app.models.skill_version import SkillVersion
from app.models.skill import Skill

logger = logging.getLogger(__name__)


class SkillEvolutionService:
    """技能演化服务 - 追踪Skill的生命周期和优化历史"""

    def __init__(self):
        self.logger = logger

    # ==================== 版本创建与记录 ====================

    def create_initial_version(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        skill_name: str,
        skill_content: str,
        skill_type: Optional[str] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillVersion:
        """
        创建技能的初始版本

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            skill_name: 技能名称
            skill_content: 技能内容
            skill_type: 技能类型
            user_id: 用户ID
            metadata: 元数据

        Returns:
            SkillVersion: 创建的版本对象
        """
        version = SkillVersion(
            skill_id=skill_id,
            project_id=project_id,
            user_id=user_id,
            version_number=1,
            version_tag="initial",
            skill_name=skill_name,
            skill_content=skill_content,
            skill_type=skill_type,
            change_type="created",
            change_description="Initial skill creation",
            change_summary="首次创建技能",
            is_active=True,
            metadata=metadata or {},
        )

        db.add(version)
        db.commit()
        db.refresh(version)

        self.logger.info(f"✅ 创建初始版本: {skill_name} v{version.version_number}")
        return version

    def record_adjustment(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        new_skill_content: str,
        adjustment_description: str,
        user_id: Optional[int] = None,
        optimization_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillVersion:
        """
        记录技能的调整（用户手动修改）

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            new_skill_content: 新的技能内容
            adjustment_description: 调整描述
            user_id: 用户ID
            optimization_reason: 优化原因
            metadata: 元数据

        Returns:
            SkillVersion: 新版本对象
        """
        # 获取最新版本
        latest_version = self._get_latest_version(db, skill_id, project_id)
        if not latest_version:
            raise ValueError(f"未找到技能 {skill_id} 的版本历史")

        # 计算版本号
        new_version_number = latest_version.version_number + 1

        # 计算变更差异
        change_summary = self._generate_change_summary(
            latest_version.skill_content, new_skill_content
        )

        # 创建新版本
        new_version = SkillVersion(
            skill_id=skill_id,
            project_id=project_id,
            user_id=user_id,
            version_number=new_version_number,
            skill_name=latest_version.skill_name,
            skill_content=new_skill_content,
            skill_type=latest_version.skill_type,
            change_type="adjusted",
            change_description=adjustment_description,
            change_summary=change_summary,
            optimization_reason=optimization_reason,
            parent_version_id=latest_version.id,
            is_active=True,
            metadata=metadata or {},
        )

        # 标记旧版本为非活跃
        latest_version.is_active = False
        latest_version.superseded_by_id = new_version.id

        db.add(new_version)
        db.commit()
        db.refresh(new_version)

        self.logger.info(
            f"📝 记录调整: {latest_version.skill_name} v{latest_version.version_number} → v{new_version_number}"
        )
        return new_version

    def record_optimization(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        optimized_content: str,
        optimization_reason: str,
        optimization_metrics: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SkillVersion:
        """
        记录技能的优化（自动优化或基于反馈的优化）

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            optimized_content: 优化后的内容
            optimization_reason: 优化原因
            optimization_metrics: 优化指标
            user_id: 用户ID
            metadata: 元数据

        Returns:
            SkillVersion: 新版本对象
        """
        latest_version = self._get_latest_version(db, skill_id, project_id)
        if not latest_version:
            raise ValueError(f"未找到技能 {skill_id} 的版本历史")

        new_version_number = latest_version.version_number + 1
        change_summary = self._generate_change_summary(
            latest_version.skill_content, optimized_content
        )

        new_version = SkillVersion(
            skill_id=skill_id,
            project_id=project_id,
            user_id=user_id,
            version_number=new_version_number,
            skill_name=latest_version.skill_name,
            skill_content=optimized_content,
            skill_type=latest_version.skill_type,
            change_type="optimized",
            change_description=f"Auto-optimization: {optimization_reason}",
            change_summary=change_summary,
            optimization_reason=optimization_reason,
            optimization_metrics=optimization_metrics or {},
            parent_version_id=latest_version.id,
            is_active=True,
            metadata=metadata or {},
        )

        latest_version.is_active = False
        latest_version.superseded_by_id = new_version.id

        db.add(new_version)
        db.commit()
        db.refresh(new_version)

        self.logger.info(
            f"🚀 记录优化: {latest_version.skill_name} v{latest_version.version_number} → v{new_version_number}"
        )
        return new_version

    # ==================== 使用统计 ====================

    def record_usage(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        success: bool,
        execution_time: Optional[float] = None,
    ) -> None:
        """
        记录技能的使用情况

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            success: 是否成功
            execution_time: 执行时间（秒）
        """
        active_version = self._get_active_version(db, skill_id, project_id)
        if not active_version:
            self.logger.warning(f"未找到技能 {skill_id} 的活跃版本")
            return

        active_version.usage_count += 1
        if success:
            active_version.success_count += 1
        else:
            active_version.failure_count += 1

        # 更新平均执行时间
        if execution_time is not None:
            if active_version.avg_execution_time is None:
                active_version.avg_execution_time = execution_time
            else:
                # 计算移动平均
                total_time = (
                    active_version.avg_execution_time * (active_version.usage_count - 1)
                    + execution_time
                )
                active_version.avg_execution_time = total_time / active_version.usage_count

        db.commit()
        self.logger.debug(
            f"📊 记录使用: {active_version.skill_name} v{active_version.version_number} "
            f"(成功: {success}, 执行时间: {execution_time}s)"
        )

    # ==================== 查询方法 ====================

    def get_version_history(
        self, db: Session, skill_id: int, project_id: int, limit: int = 50
    ) -> List[SkillVersion]:
        """
        获取技能的版本历史

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            limit: 返回数量限制

        Returns:
            List[SkillVersion]: 版本列表（按时间倒序）
        """
        versions = (
            db.query(SkillVersion)
            .filter(
                and_(
                    SkillVersion.skill_id == skill_id,
                    SkillVersion.project_id == project_id,
                )
            )
            .order_by(desc(SkillVersion.version_number))
            .limit(limit)
            .all()
        )
        return versions

    def get_active_version(
        self, db: Session, skill_id: int, project_id: int
    ) -> Optional[SkillVersion]:
        """获取活跃版本"""
        return self._get_active_version(db, skill_id, project_id)

    def get_version_by_number(
        self, db: Session, skill_id: int, project_id: int, version_number: int
    ) -> Optional[SkillVersion]:
        """根据版本号获取版本"""
        return (
            db.query(SkillVersion)
            .filter(
                and_(
                    SkillVersion.skill_id == skill_id,
                    SkillVersion.project_id == project_id,
                    SkillVersion.version_number == version_number,
                )
            )
            .first()
        )

    def compare_versions(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        version_a: int,
        version_b: int,
    ) -> Dict[str, Any]:
        """
        比较两个版本的差异

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            version_a: 版本A号
            version_b: 版本B号

        Returns:
            Dict: 比较结果
        """
        ver_a = self.get_version_by_number(db, skill_id, project_id, version_a)
        ver_b = self.get_version_by_number(db, skill_id, project_id, version_b)

        if not ver_a or not ver_b:
            raise ValueError("版本不存在")

        # 计算内容差异
        diff = list(
            difflib.unified_diff(
                ver_a.skill_content.splitlines(),
                ver_b.skill_content.splitlines(),
                lineterm="",
            )
        )

        return {
            "version_a": ver_a.to_dict(),
            "version_b": ver_b.to_dict(),
            "diff": "\n".join(diff),
            "performance_comparison": {
                "version_a": {
                    "success_rate": ver_a.success_rate,
                    "avg_execution_time": ver_a.avg_execution_time,
                    "usage_count": ver_a.usage_count,
                },
                "version_b": {
                    "success_rate": ver_b.success_rate,
                    "avg_execution_time": ver_b.avg_execution_time,
                    "usage_count": ver_b.usage_count,
                },
            },
        }

    # ==================== 优化建议 ====================

    def generate_optimization_suggestions(
        self, db: Session, skill_id: int, project_id: int
    ) -> List[Dict[str, Any]]:
        """
        基于使用统计生成优化建议

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            List[Dict]: 优化建议列表
        """
        active_version = self._get_active_version(db, skill_id, project_id)
        if not active_version:
            return []

        suggestions = []

        # 建议1：低成功率警告
        if active_version.success_rate is not None and active_version.success_rate < 0.7:
            suggestions.append({
                "type": "low_success_rate",
                "severity": "high",
                "message": f"技能成功率较低 ({active_version.success_rate:.1%})，建议检查逻辑",
                "current_value": active_version.success_rate,
                "threshold": 0.7,
            })

        # 建议2：性能优化
        if (
            active_version.avg_execution_time is not None
            and active_version.avg_execution_time > 5.0
        ):
            suggestions.append({
                "type": "high_execution_time",
                "severity": "medium",
                "message": f"平均执行时间较长 ({active_version.avg_execution_time:.2f}s)，建议优化性能",
                "current_value": active_version.avg_execution_time,
                "threshold": 5.0,
            })

        # 建议3：对比历史版本
        history = self.get_version_history(db, skill_id, project_id, limit=5)
        if len(history) > 1:
            # 找到成功率最高的历史版本
            best_version = max(
                [v for v in history if v.success_rate is not None],
                key=lambda v: v.success_rate,
                default=None,
            )
            if (
                best_version
                and best_version.id != active_version.id
                and best_version.success_rate > active_version.success_rate + 0.1
            ):
                suggestions.append({
                    "type": "better_historical_version",
                    "severity": "medium",
                    "message": f"历史版本 v{best_version.version_number} 表现更好 "
                    f"(成功率 {best_version.success_rate:.1%} vs {active_version.success_rate:.1%})",
                    "suggested_version": best_version.version_number,
                    "current_success_rate": active_version.success_rate,
                    "suggested_success_rate": best_version.success_rate,
                })

        # 建议4：使用频率低
        if active_version.usage_count < 5 and (datetime.utcnow() - active_version.created_at).days > 7:
            suggestions.append({
                "type": "low_usage",
                "severity": "low",
                "message": f"技能使用频率较低 (仅 {active_version.usage_count} 次)，考虑归档或重新设计",
                "usage_count": active_version.usage_count,
                "days_since_creation": (datetime.utcnow() - active_version.created_at).days,
            })

        return suggestions

    # ==================== 版本管理 ====================

    def deprecate_version(
        self, db: Session, version_id: int, reason: Optional[str] = None
    ) -> None:
        """弃用某个版本"""
        version = db.query(SkillVersion).filter(SkillVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本 {version_id} 不存在")

        version.is_deprecated = True
        version.is_active = False
        version.deprecated_at = datetime.utcnow()
        if reason:
            if not version.metadata:
                version.metadata = {}
            version.metadata["deprecation_reason"] = reason

        db.commit()
        self.logger.info(f"🚫 弃用版本: v{version.version_number} - {reason}")

    def rollback_to_version(
        self, db: Session, skill_id: int, project_id: int, target_version_number: int
    ) -> SkillVersion:
        """
        回滚到指定版本（创建新版本，内容与目标版本相同）

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            target_version_number: 目标版本号

        Returns:
            SkillVersion: 新创建的版本
        """
        target_version = self.get_version_by_number(
            db, skill_id, project_id, target_version_number
        )
        if not target_version:
            raise ValueError(f"目标版本 v{target_version_number} 不存在")

        current_version = self._get_latest_version(db, skill_id, project_id)
        new_version_number = current_version.version_number + 1

        rollback_version = SkillVersion(
            skill_id=skill_id,
            project_id=project_id,
            user_id=target_version.user_id,
            version_number=new_version_number,
            version_tag=f"rollback-to-v{target_version_number}",
            skill_name=target_version.skill_name,
            skill_content=target_version.skill_content,
            skill_type=target_version.skill_type,
            change_type="updated",
            change_description=f"Rolled back to version {target_version_number}",
            change_summary=f"回滚到 v{target_version_number}",
            parent_version_id=current_version.id,
            is_active=True,
            metadata={"rollback_target": target_version_number},
        )

        current_version.is_active = False
        current_version.superseded_by_id = rollback_version.id

        db.add(rollback_version)
        db.commit()
        db.refresh(rollback_version)

        self.logger.info(
            f"⏪ 回滚: v{current_version.version_number} → v{target_version_number} (新版本: v{new_version_number})"
        )
        return rollback_version

    # ==================== 内部辅助方法 ====================

    def _get_latest_version(
        self, db: Session, skill_id: int, project_id: int
    ) -> Optional[SkillVersion]:
        """获取最新版本（不管是否活跃）"""
        return (
            db.query(SkillVersion)
            .filter(
                and_(
                    SkillVersion.skill_id == skill_id,
                    SkillVersion.project_id == project_id,
                )
            )
            .order_by(desc(SkillVersion.version_number))
            .first()
        )

    def _get_active_version(
        self, db: Session, skill_id: int, project_id: int
    ) -> Optional[SkillVersion]:
        """获取活跃版本"""
        return (
            db.query(SkillVersion)
            .filter(
                and_(
                    SkillVersion.skill_id == skill_id,
                    SkillVersion.project_id == project_id,
                    SkillVersion.is_active == True,
                )
            )
            .first()
        )

    def _generate_change_summary(self, old_content: str, new_content: str) -> str:
        """生成变更摘要"""
        if old_content == new_content:
            return "无变更"

        # 简单的行数统计
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        diff = list(difflib.ndiff(old_lines, new_lines))
        added = sum(1 for line in diff if line.startswith("+ "))
        removed = sum(1 for line in diff if line.startswith("- "))

        return f"新增 {added} 行，删除 {removed} 行"


# 全局单例
_skill_evolution_service: Optional[SkillEvolutionService] = None


def get_skill_evolution_service() -> SkillEvolutionService:
    """获取技能演化服务单例"""
    global _skill_evolution_service
    if _skill_evolution_service is None:
        _skill_evolution_service = SkillEvolutionService()
    return _skill_evolution_service
