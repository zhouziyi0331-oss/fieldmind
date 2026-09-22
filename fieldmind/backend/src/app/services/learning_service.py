"""
学习日志服务

提供AI学习记录、状态追踪和成果展示功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.user_engagement import LearningLog, LearningStatus


class LearningLogService:
    """学习日志服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_learning_log(
        self,
        user_id: int,
        project_id: int,
        learning_content: str,
        learning_source: str,
        user_feedback: Optional[str] = None,
        confidence_before: float = 0.0,
        confidence_after: float = 0.0,
        applied_count: int = 0
    ) -> LearningLog:
        """
        创建学习日志

        Args:
            user_id: 用户ID
            project_id: 项目ID
            learning_content: 学习内容描述
            learning_source: 学习来源（user_correction, pattern_observation等）
            user_feedback: 用户反馈
            confidence_before: 学习前置信度（0-1）
            confidence_after: 学习后置信度（0-1）
            applied_count: 应用次数

        Returns:
            创建的学习日志
        """
        log = LearningLog(
            user_id=user_id,
            project_id=project_id,
            learning_content=learning_content,
            learning_source=learning_source,
            user_feedback=user_feedback,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            status=LearningStatus.LEARNED,
            applied_count=applied_count,
            last_applied=None,
            learned_at=datetime.utcnow()
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_learning_logs(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        status: Optional[LearningStatus] = None,
        limit: int = 50
    ) -> List[LearningLog]:
        """
        获取学习日志列表

        Args:
            user_id: 用户ID
            project_id: 可选，项目ID
            status: 可选，学习状态
            limit: 返回数量

        Returns:
            学习日志列表
        """
        query = self.db.query(LearningLog).filter(
            LearningLog.user_id == user_id
        )

        if project_id:
            query = query.filter(LearningLog.project_id == project_id)

        if status:
            query = query.filter(LearningLog.status == status)

        logs = query.order_by(
            desc(LearningLog.learned_at)
        ).limit(limit).all()

        return logs

    def record_application(
        self,
        log_id: int
    ) -> LearningLog:
        """
        记录学习内容的应用

        Args:
            log_id: 学习日志ID

        Returns:
            更新后的日志
        """
        log = self.db.query(LearningLog).filter(
            LearningLog.id == log_id
        ).first()

        if not log:
            raise ValueError(f"学习日志 {log_id} 不存在")

        log.applied_count += 1
        log.last_applied = datetime.utcnow()
        log.status = LearningStatus.APPLIED

        self.db.commit()
        self.db.refresh(log)

        return log

    def update_status(
        self,
        log_id: int,
        status: LearningStatus,
        user_feedback: Optional[str] = None
    ) -> LearningLog:
        """
        更新学习状态

        Args:
            log_id: 学习日志ID
            status: 新状态
            user_feedback: 可选，用户反馈

        Returns:
            更新后的日志
        """
        log = self.db.query(LearningLog).filter(
            LearningLog.id == log_id
        ).first()

        if not log:
            raise ValueError(f"学习日志 {log_id} 不存在")

        log.status = status
        if user_feedback:
            log.user_feedback = user_feedback

        self.db.commit()
        self.db.refresh(log)

        return log

    def get_learning_summary(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取学习摘要

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            学习摘要数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(LearningLog).filter(
            and_(
                LearningLog.user_id == user_id,
                LearningLog.project_id == project_id,
                LearningLog.learned_at >= start_date
            )
        ).all()

        # 统计各状态数量
        status_counts = {}
        for log in logs:
            status = log.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # 统计学习来源
        source_counts = {}
        for log in logs:
            source = log.learning_source
            source_counts[source] = source_counts.get(source, 0) + 1

        # 计算平均置信度提升
        confidence_gains = [
            log.confidence_after - log.confidence_before
            for log in logs
            if log.confidence_before is not None and log.confidence_after is not None
        ]
        avg_confidence_gain = (
            sum(confidence_gains) / len(confidence_gains)
            if confidence_gains else 0
        )

        # 统计应用次数
        total_applications = sum(log.applied_count for log in logs)
        applied_logs = [log for log in logs if log.applied_count > 0]

        return {
            "period_days": days,
            "total_learnings": len(logs),
            "status_breakdown": status_counts,
            "source_breakdown": source_counts,
            "avg_confidence_gain": round(avg_confidence_gain, 2),
            "total_applications": total_applications,
            "applied_count": len(applied_logs),
            "application_rate": round(len(applied_logs) / len(logs), 2) if logs else 0,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def get_top_learnings(
        self,
        user_id: int,
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最有价值的学习记录

        Args:
            user_id: 用户ID
            project_id: 项目ID
            limit: 返回数量

        Returns:
            学习记录列表
        """
        logs = self.db.query(LearningLog).filter(
            and_(
                LearningLog.user_id == user_id,
                LearningLog.project_id == project_id
            )
        ).all()

        # 计算每条学习的价值分数
        scored_logs = []
        for log in logs:
            # 价值 = 置信度提升 * 0.4 + 应用次数 * 0.3 + 状态权重 * 0.3
            confidence_gain = (
                (log.confidence_after or 0) - (log.confidence_before or 0)
            )

            status_weight = {
                LearningStatus.LEARNED: 0.5,
                LearningStatus.APPLIED: 1.0,
                LearningStatus.VERIFIED: 0.8,
                LearningStatus.REJECTED: 0.0
            }.get(log.status, 0.5)

            value_score = (
                confidence_gain * 0.4 +
                min(log.applied_count / 10, 1.0) * 0.3 +
                status_weight * 0.3
            )

            scored_logs.append((value_score, log))

        # 排序并返回
        scored_logs.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "id": log.id,
                "content": log.learning_content,
                "source": log.learning_source,
                "value_score": round(score, 2),
                "applied_count": log.applied_count,
                "confidence_gain": round(
                    (log.confidence_after or 0) - (log.confidence_before or 0), 2
                ),
                "status": log.status.value,
                "learned_at": log.learned_at.isoformat()
            }
            for score, log in scored_logs[:limit]
        ]

    def search_learnings(
        self,
        user_id: int,
        keyword: str,
        project_id: Optional[int] = None,
        limit: int = 20
    ) -> List[LearningLog]:
        """
        搜索学习日志

        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            project_id: 可选，项目ID
            limit: 返回数量

        Returns:
            匹配的学习日志
        """
        query = self.db.query(LearningLog).filter(
            LearningLog.user_id == user_id
        )

        if project_id:
            query = query.filter(LearningLog.project_id == project_id)

        logs = query.all()

        # 关键词匹配
        matched = [
            log for log in logs
            if keyword.lower() in log.learning_content.lower() or
               (log.user_feedback and keyword.lower() in log.user_feedback.lower())
        ]

        # 按时间排序
        matched.sort(key=lambda x: x.learned_at, reverse=True)

        return matched[:limit]

    def get_learning_trend(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取学习趋势

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            每日学习统计
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(LearningLog).filter(
            and_(
                LearningLog.user_id == user_id,
                LearningLog.project_id == project_id,
                LearningLog.learned_at >= start_date
            )
        ).all()

        # 按日期分组
        daily_stats = {}
        for log in logs:
            date_key = log.learned_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "count": 0,
                    "applications": 0
                }
            daily_stats[date_key]["count"] += 1
            daily_stats[date_key]["applications"] += log.applied_count

        # 转换为列表并排序
        trend = sorted(daily_stats.values(), key=lambda x: x["date"])

        return trend

    def delete_learning(
        self,
        log_id: int,
        user_id: int
    ) -> bool:
        """
        删除学习日志

        Args:
            log_id: 学习日志ID
            user_id: 用户ID（验证权限）

        Returns:
            是否成功删除
        """
        log = self.db.query(LearningLog).filter(
            and_(
                LearningLog.id == log_id,
                LearningLog.user_id == user_id
            )
        ).first()

        if not log:
            return False

        self.db.delete(log)
        self.db.commit()

        return True
