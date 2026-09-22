"""
用户喂养服务

提供用户主动输入、知识喂养和偏好学习功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.user_engagement import UserFeedingSession


class UserFeedingService:
    """用户喂养服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def create_feeding_session(
        self,
        user_id: int,
        project_id: int,
        session_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> UserFeedingSession:
        """
        创建喂养会话

        Args:
            user_id: 用户ID
            project_id: 项目ID
            session_type: 会话类型（correction, preference, guidance, example）
            content: 喂养内容
            context: 上下文信息
            importance: 重要性（0-1）

        Returns:
            创建的喂养会话
        """
        session = UserFeedingSession(
            user_id=user_id,
            project_id=project_id,
            session_type=session_type,
            content=content,
            context=context or {},
            importance=importance,
            applied_count=0,
            last_applied=None,
            created_at=datetime.utcnow()
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_feeding_sessions(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        session_type: Optional[str] = None,
        limit: int = 50
    ) -> List[UserFeedingSession]:
        """
        获取喂养会话列表

        Args:
            user_id: 用户ID
            project_id: 可选，项目ID
            session_type: 可选，会话类型
            limit: 返回数量

        Returns:
            喂养会话列表
        """
        query = self.db.query(UserFeedingSession).filter(
            UserFeedingSession.user_id == user_id
        )

        if project_id:
            query = query.filter(UserFeedingSession.project_id == project_id)

        if session_type:
            query = query.filter(UserFeedingSession.session_type == session_type)

        sessions = query.order_by(
            desc(UserFeedingSession.created_at)
        ).limit(limit).all()

        return sessions

    def record_application(
        self,
        session_id: int
    ) -> UserFeedingSession:
        """
        记录喂养内容的应用

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话
        """
        session = self.db.query(UserFeedingSession).filter(
            UserFeedingSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"喂养会话 {session_id} 不存在")

        session.applied_count += 1
        session.last_applied = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def update_importance(
        self,
        session_id: int,
        importance: float
    ) -> UserFeedingSession:
        """
        更新会话重要性

        Args:
            session_id: 会话ID
            importance: 新重要性（0-1）

        Returns:
            更新后的会话
        """
        session = self.db.query(UserFeedingSession).filter(
            UserFeedingSession.id == session_id
        ).first()

        if not session:
            raise ValueError(f"喂养会话 {session_id} 不存在")

        session.importance = max(0.0, min(1.0, importance))

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_feeding_summary(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取喂养摘要

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            喂养摘要数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        sessions = self.db.query(UserFeedingSession).filter(
            and_(
                UserFeedingSession.user_id == user_id,
                UserFeedingSession.project_id == project_id,
                UserFeedingSession.created_at >= start_date
            )
        ).all()

        # 按类型统计
        type_counts = {}
        for session in sessions:
            session_type = session.session_type
            type_counts[session_type] = type_counts.get(session_type, 0) + 1

        # 计算平均重要性
        avg_importance = (
            sum(s.importance for s in sessions) / len(sessions)
            if sessions else 0
        )

        # 统计应用情况
        total_applications = sum(s.applied_count for s in sessions)
        applied_sessions = [s for s in sessions if s.applied_count > 0]

        return {
            "period_days": days,
            "total_sessions": len(sessions),
            "type_breakdown": type_counts,
            "avg_importance": round(avg_importance, 2),
            "total_applications": total_applications,
            "applied_count": len(applied_sessions),
            "application_rate": round(len(applied_sessions) / len(sessions), 2) if sessions else 0,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def get_most_valuable_feedings(
        self,
        user_id: int,
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最有价值的喂养内容

        Args:
            user_id: 用户ID
            project_id: 项目ID
            limit: 返回数量

        Returns:
            喂养内容列表
        """
        sessions = self.db.query(UserFeedingSession).filter(
            and_(
                UserFeedingSession.user_id == user_id,
                UserFeedingSession.project_id == project_id
            )
        ).all()

        # 计算价值分数
        scored_sessions = []
        for session in sessions:
            # 价值 = 重要性 * 0.4 + 应用次数归一化 * 0.6
            value_score = (
                session.importance * 0.4 +
                min(session.applied_count / 10, 1.0) * 0.6
            )
            scored_sessions.append((value_score, session))

        # 排序
        scored_sessions.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "id": session.id,
                "type": session.session_type,
                "content": session.content,
                "value_score": round(score, 2),
                "importance": session.importance,
                "applied_count": session.applied_count,
                "created_at": session.created_at.isoformat()
            }
            for score, session in scored_sessions[:limit]
        ]

    def search_feedings(
        self,
        user_id: int,
        keyword: str,
        project_id: Optional[int] = None,
        limit: int = 20
    ) -> List[UserFeedingSession]:
        """
        搜索喂养内容

        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            project_id: 可选，项目ID
            limit: 返回数量

        Returns:
            匹配的喂养会话
        """
        query = self.db.query(UserFeedingSession).filter(
            UserFeedingSession.user_id == user_id
        )

        if project_id:
            query = query.filter(UserFeedingSession.project_id == project_id)

        sessions = query.all()

        # 关键词匹配
        matched = [
            session for session in sessions
            if keyword.lower() in session.content.lower()
        ]

        # 按时间排序
        matched.sort(key=lambda x: x.created_at, reverse=True)

        return matched[:limit]

    def get_feeding_by_type(
        self,
        user_id: int,
        project_id: int,
        session_type: str
    ) -> List[UserFeedingSession]:
        """
        按类型获取喂养内容

        Args:
            user_id: 用户ID
            project_id: 项目ID
            session_type: 会话类型

        Returns:
            喂养会话列表
        """
        sessions = self.db.query(UserFeedingSession).filter(
            and_(
                UserFeedingSession.user_id == user_id,
                UserFeedingSession.project_id == project_id,
                UserFeedingSession.session_type == session_type
            )
        ).order_by(
            desc(UserFeedingSession.importance),
            desc(UserFeedingSession.created_at)
        ).all()

        return sessions

    def get_recent_corrections(
        self,
        user_id: int,
        project_id: int,
        limit: int = 10
    ) -> List[UserFeedingSession]:
        """
        获取最近的用户纠正

        Args:
            user_id: 用户ID
            project_id: 项目ID
            limit: 返回数量

        Returns:
            纠正会话列表
        """
        return self.get_feeding_by_type(
            user_id=user_id,
            project_id=project_id,
            session_type="correction"
        )[:limit]

    def get_user_preferences(
        self,
        user_id: int,
        project_id: int
    ) -> List[UserFeedingSession]:
        """
        获取用户偏好设置

        Args:
            user_id: 用户ID
            project_id: 项目ID

        Returns:
            偏好会话列表
        """
        return self.get_feeding_by_type(
            user_id=user_id,
            project_id=project_id,
            session_type="preference"
        )

    def delete_feeding(
        self,
        session_id: int,
        user_id: int
    ) -> bool:
        """
        删除喂养会话

        Args:
            session_id: 会话ID
            user_id: 用户ID（验证权限）

        Returns:
            是否成功删除
        """
        session = self.db.query(UserFeedingSession).filter(
            and_(
                UserFeedingSession.id == session_id,
                UserFeedingSession.user_id == user_id
            )
        ).first()

        if not session:
            return False

        self.db.delete(session)
        self.db.commit()

        return True

    def get_feeding_trend(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取喂养趋势

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            每日喂养统计
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        sessions = self.db.query(UserFeedingSession).filter(
            and_(
                UserFeedingSession.user_id == user_id,
                UserFeedingSession.project_id == project_id,
                UserFeedingSession.created_at >= start_date
            )
        ).all()

        # 按日期分组
        daily_stats = {}
        for session in sessions:
            date_key = session.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "count": 0,
                    "by_type": {}
                }
            daily_stats[date_key]["count"] += 1

            session_type = session.session_type
            if session_type not in daily_stats[date_key]["by_type"]:
                daily_stats[date_key]["by_type"][session_type] = 0
            daily_stats[date_key]["by_type"][session_type] += 1

        # 转换为列表并排序
        trend = sorted(daily_stats.values(), key=lambda x: x["date"])

        return trend
