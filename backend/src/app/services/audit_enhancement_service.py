"""审计日志增强服务

提供高级审计功能：
- 实时事件推送
- 异常行为检测
- 合规性报告
- 数据导出
"""
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from functools import wraps
import asyncio
import json
import csv
import io
from collections import defaultdict

from app.models.audit_log import AuditLog, ActorType, ActionType, AuditResult
from app.services.audit_service import AuditService
from app.services.event_emitter import get_event_emitter
from app.core.logging import logger


class AuditDecorator:
    """审计日志装饰器

    自动记录函数调用和结果
    """

    @staticmethod
    def log_operation(
        resource_type: str,
        action: ActionType,
        get_resource_id: Optional[Callable] = None,
        get_resource_name: Optional[Callable] = None,
        get_project_id: Optional[Callable] = None,
        track_changes: bool = False,
    ):
        """操作审计装饰器

        Args:
            resource_type: 资源类型
            action: 操作类型
            get_resource_id: 提取资源ID的函数
            get_resource_name: 提取资源名称的函数
            get_project_id: 提取项目ID的函数
            track_changes: 是否追踪变更内容
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = datetime.utcnow()

                # 提取参数
                db = kwargs.get('db') or (args[0] if args else None)
                actor_id = kwargs.get('current_user_id', 'system')
                actor_type = kwargs.get('actor_type', ActorType.USER)

                # 提取资源信息
                resource_id = get_resource_id(*args, **kwargs) if get_resource_id else 'unknown'
                resource_name = get_resource_name(*args, **kwargs) if get_resource_name else None
                project_id = get_project_id(*args, **kwargs) if get_project_id else None

                # 执行原函数
                result = None
                error_message = None
                audit_result = AuditResult.SUCCESS
                changes = None

                try:
                    result = await func(*args, **kwargs)

                    # 追踪变更
                    if track_changes and hasattr(result, '__dict__'):
                        changes = {
                            "after": {k: str(v) for k, v in result.__dict__.items() if not k.startswith('_')}
                        }

                    return result

                except Exception as e:
                    audit_result = AuditResult.FAILURE
                    error_message = str(e)
                    raise

                finally:
                    # 计算执行时长
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                    # 创建审计日志
                    if db:
                        try:
                            await AuditService.create_log(
                                db=db,
                                actor_type=actor_type,
                                actor_id=str(actor_id),
                                action=action,
                                resource_type=resource_type,
                                resource_id=str(resource_id),
                                resource_name=resource_name,
                                project_id=str(project_id) if project_id else None,
                                changes=changes,
                                result=audit_result,
                                error_message=error_message,
                                duration_ms=duration_ms,
                            )
                        except Exception as audit_error:
                            logger.error(f"Failed to create audit log: {audit_error}")

            return wrapper
        return decorator


class AnomalyDetector:
    """异常行为检测器"""

    def __init__(self):
        self.thresholds = {
            "rapid_operations": 10,  # 1分钟内操作次数
            "failed_operations": 5,   # 连续失败次数
            "unusual_hours": (22, 6),  # 非工作时间（22:00-6:00）
            "bulk_delete": 10,        # 批量删除阈值
        }

    async def detect_rapid_operations(
        self,
        db: Session,
        actor_id: str,
        time_window_minutes: int = 1,
    ) -> Dict[str, Any]:
        """检测快速连续操作

        Args:
            db: 数据库会话
            actor_id: 操作者ID
            time_window_minutes: 时间窗口（分钟）

        Returns:
            检测结果
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        count = db.query(AuditLog).filter(
            AuditLog.actor_id == actor_id,
            AuditLog.timestamp >= cutoff_time,
        ).count()

        is_anomaly = count > self.thresholds["rapid_operations"]

        return {
            "type": "rapid_operations",
            "is_anomaly": is_anomaly,
            "count": count,
            "threshold": self.thresholds["rapid_operations"],
            "time_window_minutes": time_window_minutes,
        }

    async def detect_failed_operations(
        self,
        db: Session,
        actor_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """检测连续失败操作

        Args:
            db: 数据库会话
            actor_id: 操作者ID
            limit: 检查最近的操作数

        Returns:
            检测结果
        """
        recent_logs = (
            db.query(AuditLog)
            .filter(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

        consecutive_failures = 0
        for log in recent_logs:
            if log.result == AuditResult.FAILURE:
                consecutive_failures += 1
            else:
                break

        is_anomaly = consecutive_failures >= self.thresholds["failed_operations"]

        return {
            "type": "failed_operations",
            "is_anomaly": is_anomaly,
            "consecutive_failures": consecutive_failures,
            "threshold": self.thresholds["failed_operations"],
        }

    async def detect_unusual_time_activity(
        self,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """检测异常时间段的活动

        Args:
            db: 数据库会话
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            检测结果
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()

        # 查询非工作时间的操作
        unusual_start_hour, unusual_end_hour = self.thresholds["unusual_hours"]

        logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
        ).all()

        unusual_activities = []
        for log in logs:
            hour = log.timestamp.hour
            if hour >= unusual_start_hour or hour < unusual_end_hour:
                unusual_activities.append({
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "actor_id": log.actor_id,
                    "action": log.action.value,
                    "resource_type": log.resource_type,
                })

        return {
            "type": "unusual_time_activity",
            "is_anomaly": len(unusual_activities) > 0,
            "count": len(unusual_activities),
            "unusual_hours": f"{unusual_start_hour}:00-{unusual_end_hour}:00",
            "activities": unusual_activities[:50],  # 最多返回50条
        }

    async def detect_bulk_deletes(
        self,
        db: Session,
        actor_id: str,
        time_window_minutes: int = 5,
    ) -> Dict[str, Any]:
        """检测批量删除操作

        Args:
            db: 数据库会话
            actor_id: 操作者ID
            time_window_minutes: 时间窗口（分钟）

        Returns:
            检测结果
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        delete_count = db.query(AuditLog).filter(
            AuditLog.actor_id == actor_id,
            AuditLog.action == ActionType.DELETE,
            AuditLog.timestamp >= cutoff_time,
        ).count()

        is_anomaly = delete_count > self.thresholds["bulk_delete"]

        return {
            "type": "bulk_delete",
            "is_anomaly": is_anomaly,
            "count": delete_count,
            "threshold": self.thresholds["bulk_delete"],
            "time_window_minutes": time_window_minutes,
        }

    async def run_all_checks(
        self,
        db: Session,
        actor_id: str,
    ) -> List[Dict[str, Any]]:
        """运行所有异常检测

        Args:
            db: 数据库会话
            actor_id: 操作者ID

        Returns:
            所有异常检测结果
        """
        results = []

        # 快速操作检测
        rapid_ops = await self.detect_rapid_operations(db, actor_id)
        if rapid_ops["is_anomaly"]:
            results.append(rapid_ops)

        # 连续失败检测
        failed_ops = await self.detect_failed_operations(db, actor_id)
        if failed_ops["is_anomaly"]:
            results.append(failed_ops)

        # 批量删除检测
        bulk_deletes = await self.detect_bulk_deletes(db, actor_id)
        if bulk_deletes["is_anomaly"]:
            results.append(bulk_deletes)

        return results


class ComplianceReporter:
    """合规性报告生成器"""

    async def generate_user_activity_report(
        self,
        db: Session,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """生成用户活动报告

        Args:
            db: 数据库会话
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            活动报告
        """
        logs = db.query(AuditLog).filter(
            AuditLog.actor_id == user_id,
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
        ).all()

        # 统计操作类型
        action_counts = defaultdict(int)
        resource_counts = defaultdict(int)
        success_count = 0
        failure_count = 0
        total_duration = 0

        for log in logs:
            action_counts[log.action.value] += 1
            resource_counts[log.resource_type] += 1
            if log.result == AuditResult.SUCCESS:
                success_count += 1
            else:
                failure_count += 1
            if log.duration_ms:
                total_duration += log.duration_ms

        return {
            "user_id": user_id,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "summary": {
                "total_operations": len(logs),
                "successful_operations": success_count,
                "failed_operations": failure_count,
                "success_rate": success_count / len(logs) if logs else 0,
                "avg_duration_ms": total_duration / len(logs) if logs else 0,
            },
            "by_action": dict(action_counts),
            "by_resource": dict(resource_counts),
        }

    async def generate_project_audit_report(
        self,
        db: Session,
        project_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """生成项目审计报告

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            审计报告
        """
        logs = db.query(AuditLog).filter(
            AuditLog.project_id == project_id,
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
        ).all()

        # 统计用户活动
        user_activity = defaultdict(int)
        ai_activity = defaultdict(int)

        for log in logs:
            if log.actor_type == ActorType.USER:
                user_activity[log.actor_id] += 1
            elif log.actor_type == ActorType.AI:
                ai_activity[log.ai_model or "unknown"] += 1

        # 按日期统计
        daily_activity = defaultdict(int)
        for log in logs:
            date_key = log.timestamp.date().isoformat()
            daily_activity[date_key] += 1

        return {
            "project_id": project_id,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "summary": {
                "total_operations": len(logs),
                "unique_users": len(user_activity),
                "ai_operations": sum(ai_activity.values()),
            },
            "user_activity": dict(user_activity),
            "ai_activity": dict(ai_activity),
            "daily_activity": dict(daily_activity),
        }

    async def generate_security_audit_report(
        self,
        db: Session,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """生成安全审计报告

        Args:
            db: 数据库会话
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            安全报告
        """
        logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
        ).all()

        # 统计失败操作
        failed_logs = [log for log in logs if log.result == AuditResult.FAILURE]
        failed_by_user = defaultdict(int)
        failed_by_action = defaultdict(int)

        for log in failed_logs:
            failed_by_user[log.actor_id] += 1
            failed_by_action[log.action.value] += 1

        # 统计删除操作
        delete_logs = [log for log in logs if log.action == ActionType.DELETE]

        # 统计AI修改操作
        ai_modify_logs = [log for log in logs if log.action == ActionType.AI_MODIFY]

        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "failed_operations": {
                "total": len(failed_logs),
                "by_user": dict(failed_by_user),
                "by_action": dict(failed_by_action),
            },
            "delete_operations": {
                "total": len(delete_logs),
                "details": [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "actor_id": log.actor_id,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                    }
                    for log in delete_logs[:100]  # 最多返回100条
                ],
            },
            "ai_modifications": {
                "total": len(ai_modify_logs),
                "by_model": dict(
                    defaultdict(int,
                        {log.ai_model: ai_modify_logs.count(log)
                         for log in ai_modify_logs if log.ai_model}
                    )
                ),
            },
        }


class AuditExporter:
    """审计日志导出器"""

    async def export_to_json(
        self,
        logs: List[AuditLog],
    ) -> str:
        """导出为JSON格式

        Args:
            logs: 审计日志列表

        Returns:
            JSON字符串
        """
        data = []
        for log in logs:
            data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "actor_type": log.actor_type.value,
                "actor_id": log.actor_id,
                "action": log.action.value,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "project_id": log.project_id,
                "changes": log.changes,
                "ai_model": log.ai_model,
                "result": log.result.value,
                "error_message": log.error_message,
                "duration_ms": log.duration_ms,
                "extra_metadata": log.extra_metadata,
            })

        return json.dumps(data, indent=2, ensure_ascii=False)

    async def export_to_csv(
        self,
        logs: List[AuditLog],
    ) -> str:
        """导出为CSV格式

        Args:
            logs: 审计日志列表

        Returns:
            CSV字符串
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow([
            "ID",
            "Timestamp",
            "Actor Type",
            "Actor ID",
            "Action",
            "Resource Type",
            "Resource ID",
            "Resource Name",
            "Project ID",
            "Result",
            "Error Message",
            "Duration (ms)",
        ])

        # 写入数据
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat(),
                log.actor_type.value,
                log.actor_id,
                log.action.value,
                log.resource_type,
                log.resource_id,
                log.resource_name or "",
                log.project_id or "",
                log.result.value,
                log.error_message or "",
                log.duration_ms or "",
            ])

        return output.getvalue()


class AuditEnhancementService:
    """审计日志增强服务"""

    def __init__(self):
        self.event_emitter = get_event_emitter()
        self.anomaly_detector = AnomalyDetector()
        self.compliance_reporter = ComplianceReporter()
        self.exporter = AuditExporter()

    async def log_with_events(
        self,
        db: Session,
        session_id: str,
        **kwargs,
    ) -> AuditLog:
        """创建审计日志并发送WebSocket事件

        Args:
            db: 数据库会话
            session_id: 会话ID
            **kwargs: 审计日志参数

        Returns:
            创建的审计日志
        """
        # 创建审计日志
        audit_log = await AuditService.create_log(db=db, **kwargs)

        # 发送WebSocket事件
        await self.event_emitter.emit(
            event_type="audit.log.created",
            data={
                "session_id": session_id,
                "log_id": audit_log.id,
                "timestamp": audit_log.timestamp.isoformat(),
                "actor_type": audit_log.actor_type.value,
                "actor_id": audit_log.actor_id,
                "action": audit_log.action.value,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "result": audit_log.result.value,
            }
        )

        # 异常检测
        if audit_log.result == AuditResult.FAILURE:
            anomalies = await self.anomaly_detector.run_all_checks(
                db=db,
                actor_id=audit_log.actor_id,
            )

            if anomalies:
                await self.event_emitter.emit(
                    event_type="audit.anomaly.detected",
                    data={
                        "session_id": session_id,
                        "actor_id": audit_log.actor_id,
                        "anomalies": anomalies,
                    }
                )

        return audit_log
