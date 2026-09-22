"""审计日志服务

提供审计日志的记录、查询、清理功能
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.audit_log import AuditLog, ActorType, ActionType, AuditResult
from app.core.logging import logger


class AuditService:
    """审计日志服务"""

    @staticmethod
    async def create_log(
        db: Session,
        actor_type: ActorType,
        actor_id: str,
        action: ActionType,
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        project_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ai_model: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        result: AuditResult = AuditResult.SUCCESS,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """创建审计日志记录

        Args:
            db: 数据库会话
            actor_type: 操作者类型
            actor_id: 操作者ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            resource_name: 资源名称
            project_id: 项目ID
            changes: 变更内容
            ai_model: AI模型名称
            ai_prompt: AI提示词
            result: 操作结果
            error_message: 错误信息
            duration_ms: 执行时长（毫秒）
            extra_metadata: 额外元数据

        Returns:
            创建的审计日志对象
        """
        try:
            audit_log = AuditLog(
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                project_id=project_id,
                changes=changes,
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                result=result,
                error_message=error_message,
                duration_ms=duration_ms,
                extra_metadata=extra_metadata,
            )

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            logger.info(
                f"Audit log created: {actor_type}:{action}:{resource_type}:{resource_id} - {result}"
            )

            return audit_log

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create audit log: {str(e)}")
            raise

    @staticmethod
    async def query_logs(
        db: Session,
        project_id: Optional[str] = None,
        actor_type: Optional[ActorType] = None,
        actor_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[AuditResult] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """查询审计日志

        Args:
            db: 数据库会话
            project_id: 项目ID
            actor_type: 操作者类型
            actor_id: 操作者ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            result: 操作结果
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            (日志列表, 总数)
        """
        query = db.query(AuditLog)

        # 构建过滤条件
        filters = []
        if project_id:
            filters.append(AuditLog.project_id == project_id)
        if actor_type:
            filters.append(AuditLog.actor_type == actor_type)
        if actor_id:
            filters.append(AuditLog.actor_id == actor_id)
        if action:
            filters.append(AuditLog.action == action)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)
        if result:
            filters.append(AuditLog.result == result)
        if start_time:
            filters.append(AuditLog.timestamp >= start_time)
        if end_time:
            filters.append(AuditLog.timestamp <= end_time)

        if filters:
            query = query.filter(and_(*filters))

        # 总数
        total = query.count()

        # 分页查询
        logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).offset(offset).all()

        return logs, total

    @staticmethod
    async def get_resource_history(
        db: Session,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[AuditLog]:
        """获取资源的操作历史

        Args:
            db: 数据库会话
            resource_type: 资源类型
            resource_id: 资源ID
            limit: 返回数量限制

        Returns:
            操作历史列表
        """
        logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id,
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

        return logs

    @staticmethod
    async def get_user_activity(
        db: Session,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取用户活动记录

        Args:
            db: 数据库会话
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制

        Returns:
            活动记录列表
        """
        query = db.query(AuditLog).filter(
            AuditLog.actor_type == ActorType.USER,
            AuditLog.actor_id == user_id,
        )

        if start_time:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLog.timestamp <= end_time)

        logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()

        return logs

    @staticmethod
    async def cleanup_old_logs(
        db: Session,
        retention_days: int = 15,
        batch_size: int = 1000,
    ) -> int:
        """清理过期的审计日志

        Args:
            db: 数据库会话
            retention_days: 保留天数
            batch_size: 批量删除大小

        Returns:
            删除的记录数
        """
        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)

        total_deleted = 0

        try:
            while True:
                # 批量删除
                result = (
                    db.query(AuditLog)
                    .filter(AuditLog.timestamp < cutoff_time)
                    .limit(batch_size)
                    .delete(synchronize_session=False)
                )

                db.commit()

                total_deleted += result

                if result < batch_size:
                    break

            logger.info(f"Cleaned up {total_deleted} audit logs older than {retention_days} days")

            return total_deleted

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup audit logs: {str(e)}")
            raise

    @staticmethod
    async def get_statistics(
        db: Session,
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取审计统计信息

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息字典
        """
        query = db.query(AuditLog)

        if project_id:
            query = query.filter(AuditLog.project_id == project_id)
        if start_time:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLog.timestamp <= end_time)

        total_logs = query.count()

        # 按操作者类型统计
        actor_stats = {}
        for actor_type in ActorType:
            count = query.filter(AuditLog.actor_type == actor_type).count()
            actor_stats[actor_type.value] = count

        # 按操作类型统计
        action_stats = {}
        for action_type in ActionType:
            count = query.filter(AuditLog.action == action_type).count()
            action_stats[action_type.value] = count

        # 按结果统计
        result_stats = {}
        for result_type in AuditResult:
            count = query.filter(AuditLog.result == result_type).count()
            result_stats[result_type.value] = count

        return {
            "total_logs": total_logs,
            "by_actor_type": actor_stats,
            "by_action_type": action_stats,
            "by_result": result_stats,
        }
