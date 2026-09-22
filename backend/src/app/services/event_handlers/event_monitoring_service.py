"""
事件监控服务
Event Monitoring Service

功能：
1. 实时监控事件总线状态
2. 事件流量统计
3. 事件处理性能分析
4. 异常事件检测
5. 事件日志查询
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.models.unified_models import SystemEvent

logger = logging.getLogger(__name__)


class EventMonitoringService:
    """事件监控服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ============================================================
    # 实时监控
    # ============================================================

    def get_realtime_status(self) -> Dict[str, Any]:
        """
        获取实时状态

        Returns:
            实时状态信息
        """
        # 总事件数
        total_events = self.db.query(func.count(SystemEvent.id)).scalar()

        # 各状态事件数
        pending = self.db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'pending'
        ).scalar()

        processing = self.db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'processing'
        ).scalar()

        consumed = self.db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'consumed'
        ).scalar()

        failed = self.db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.status == 'failed'
        ).scalar()

        # 最近 1 小时的事件数
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = self.db.query(func.count(SystemEvent.id)).filter(
            SystemEvent.created_at >= one_hour_ago
        ).scalar()

        # 平均处理时间（秒）
        avg_processing_time = self.db.execute(text("""
            SELECT AVG(TIMESTAMPDIFF(SECOND, created_at, consumed_at))
            FROM system_events
            WHERE status = 'consumed' AND consumed_at IS NOT NULL
            LIMIT 1000
        """)).scalar()

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_events': total_events,
            'status_breakdown': {
                'pending': pending,
                'processing': processing,
                'consumed': consumed,
                'failed': failed
            },
            'success_rate': round(consumed / total_events * 100, 2) if total_events > 0 else 0,
            'recent_hour_events': recent_events,
            'avg_processing_time_seconds': round(float(avg_processing_time or 0), 2)
        }

    def get_event_flow(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取事件流量（按小时统计）

        Args:
            hours: 统计小时数

        Returns:
            事件流量数据
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # 按小时分组统计
        result = self.db.execute(text("""
            SELECT
                DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00') as hour,
                COUNT(*) as count
            FROM system_events
            WHERE created_at >= :cutoff_time
            GROUP BY hour
            ORDER BY hour
        """), {'cutoff_time': cutoff_time}).fetchall()

        flow_data = [
            {'hour': row[0], 'count': row[1]}
            for row in result
        ]

        return {
            'time_range_hours': hours,
            'total_events': sum(d['count'] for d in flow_data),
            'flow_data': flow_data
        }

    # ============================================================
    # 事件类型分析
    # ============================================================

    def get_event_type_statistics(self, limit: int = 20) -> Dict[str, Any]:
        """
        获取事件类型统计

        Args:
            limit: 返回 Top N

        Returns:
            事件类型统计
        """
        # 各类型事件数量
        result = self.db.execute(text("""
            SELECT event_type, COUNT(*) as count
            FROM system_events
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT :limit
        """), {'limit': limit}).fetchall()

        type_stats = [
            {'event_type': row[0], 'count': row[1]}
            for row in result
        ]

        # 各类型成功率
        for stat in type_stats:
            event_type = stat['event_type']
            total = stat['count']

            success = self.db.query(func.count(SystemEvent.id)).filter(
                SystemEvent.event_type == event_type,
                SystemEvent.status == 'consumed'
            ).scalar()

            stat['success_count'] = success
            stat['success_rate'] = round(success / total * 100, 2) if total > 0 else 0

        return {
            'total_types': len(type_stats),
            'type_statistics': type_stats
        }

    def get_event_category_statistics(self) -> Dict[str, Any]:
        """
        获取事件分类统计

        Returns:
            事件分类统计
        """
        result = self.db.execute(text("""
            SELECT event_category, COUNT(*) as count
            FROM system_events
            GROUP BY event_category
            ORDER BY count DESC
        """)).fetchall()

        category_stats = [
            {'category': row[0], 'count': row[1]}
            for row in result
        ]

        return {
            'total_categories': len(category_stats),
            'category_statistics': category_stats
        }

    # ============================================================
    # 性能分析
    # ============================================================

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            性能指标
        """
        # 处理时间统计（秒）
        time_stats = self.db.execute(text("""
            SELECT
                AVG(TIMESTAMPDIFF(SECOND, created_at, consumed_at)) as avg_time,
                MIN(TIMESTAMPDIFF(SECOND, created_at, consumed_at)) as min_time,
                MAX(TIMESTAMPDIFF(SECOND, created_at, consumed_at)) as max_time
            FROM system_events
            WHERE status = 'consumed' AND consumed_at IS NOT NULL
        """)).fetchone()

        # 重试统计
        retry_stats = self.db.execute(text("""
            SELECT
                AVG(retry_count) as avg_retries,
                MAX(retry_count) as max_retries,
                COUNT(*) as total_with_retries
            FROM system_events
            WHERE retry_count > 0
        """)).fetchone()

        # 按优先级统计平均处理时间
        priority_times = self.db.execute(text("""
            SELECT
                priority,
                AVG(TIMESTAMPDIFF(SECOND, created_at, consumed_at)) as avg_time,
                COUNT(*) as count
            FROM system_events
            WHERE status = 'consumed' AND consumed_at IS NOT NULL
            GROUP BY priority
            ORDER BY priority DESC
        """)).fetchall()

        return {
            'processing_time': {
                'avg_seconds': round(float(time_stats[0] or 0), 2),
                'min_seconds': round(float(time_stats[1] or 0), 2),
                'max_seconds': round(float(time_stats[2] or 0), 2)
            },
            'retry_metrics': {
                'avg_retries': round(float(retry_stats[0] or 0), 2),
                'max_retries': retry_stats[1] or 0,
                'events_with_retries': retry_stats[2] or 0
            },
            'priority_performance': [
                {
                    'priority': row[0],
                    'avg_time_seconds': round(float(row[1] or 0), 2),
                    'count': row[2]
                }
                for row in priority_times
            ]
        }

    # ============================================================
    # 异常检测
    # ============================================================

    def detect_anomalies(self) -> Dict[str, Any]:
        """
        检测异常事件

        Returns:
            异常事件列表
        """
        anomalies = []

        # 1. 失败率高的事件类型
        high_failure_types = self.db.execute(text("""
            SELECT
                event_type,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                ROUND(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as failure_rate
            FROM system_events
            GROUP BY event_type
            HAVING failure_rate > 10
            ORDER BY failure_rate DESC
            LIMIT 10
        """)).fetchall()

        if high_failure_types:
            anomalies.append({
                'type': 'high_failure_rate',
                'description': '失败率超过 10% 的事件类型',
                'data': [
                    {
                        'event_type': row[0],
                        'total': row[1],
                        'failed': row[2],
                        'failure_rate': row[3]
                    }
                    for row in high_failure_types
                ]
            })

        # 2. 处理时间过长的事件
        slow_events = self.db.execute(text("""
            SELECT
                event_id,
                event_type,
                TIMESTAMPDIFF(SECOND, created_at, consumed_at) as processing_time
            FROM system_events
            WHERE status = 'consumed'
                AND consumed_at IS NOT NULL
                AND TIMESTAMPDIFF(SECOND, created_at, consumed_at) > 60
            ORDER BY processing_time DESC
            LIMIT 10
        """)).fetchall()

        if slow_events:
            anomalies.append({
                'type': 'slow_processing',
                'description': '处理时间超过 60 秒的事件',
                'data': [
                    {
                        'event_id': row[0],
                        'event_type': row[1],
                        'processing_time_seconds': row[2]
                    }
                    for row in slow_events
                ]
            })

        # 3. 重试次数过多的事件
        high_retry_events = self.db.query(SystemEvent).filter(
            SystemEvent.retry_count >= 3
        ).order_by(SystemEvent.retry_count.desc()).limit(10).all()

        if high_retry_events:
            anomalies.append({
                'type': 'high_retry_count',
                'description': '重试次数 >= 3 的事件',
                'data': [
                    {
                        'event_id': e.event_id,
                        'event_type': e.event_type,
                        'retry_count': e.retry_count,
                        'status': e.status
                    }
                    for e in high_retry_events
                ]
            })

        # 4. 长时间待处理的事件
        old_pending = self.db.execute(text("""
            SELECT
                event_id,
                event_type,
                TIMESTAMPDIFF(MINUTE, created_at, NOW()) as age_minutes
            FROM system_events
            WHERE status = 'pending'
                AND TIMESTAMPDIFF(MINUTE, created_at, NOW()) > 30
            ORDER BY age_minutes DESC
            LIMIT 10
        """)).fetchall()

        if old_pending:
            anomalies.append({
                'type': 'old_pending_events',
                'description': '超过 30 分钟未处理的事件',
                'data': [
                    {
                        'event_id': row[0],
                        'event_type': row[1],
                        'age_minutes': row[2]
                    }
                    for row in old_pending
                ]
            })

        return {
            'total_anomalies': len(anomalies),
            'anomalies': anomalies
        }

    # ============================================================
    # 事件日志查询
    # ============================================================

    def query_events(
        self,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询事件日志

        Args:
            event_type: 事件类型
            status: 状态
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量
            offset: 偏移量

        Returns:
            事件列表
        """
        query = self.db.query(SystemEvent)

        if event_type:
            query = query.filter(SystemEvent.event_type == event_type)

        if status:
            query = query.filter(SystemEvent.status == status)

        if start_time:
            query = query.filter(SystemEvent.created_at >= start_time)

        if end_time:
            query = query.filter(SystemEvent.created_at <= end_time)

        total = query.count()

        events = query.order_by(
            SystemEvent.created_at.desc()
        ).limit(limit).offset(offset).all()

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'events': [self._event_to_dict(e) for e in events]
        }

    def get_event_details(self, event_id: str) -> Optional[Dict]:
        """
        获取事件详情

        Args:
            event_id: 事件 ID

        Returns:
            事件详情
        """
        event = self.db.query(SystemEvent).filter(
            SystemEvent.event_id == event_id
        ).first()

        if not event:
            return None

        return self._event_to_dict(event, include_payload=True)

    # ============================================================
    # 辅助方法
    # ============================================================

    def _event_to_dict(self, event: SystemEvent, include_payload: bool = False) -> Dict:
        """将事件对象转换为字典"""
        result = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'event_category': event.event_category,
            'event_name': event.event_name,
            'status': event.status,
            'priority': event.priority,
            'retry_count': event.retry_count,
            'max_retries': event.max_retries,
            'publisher': event.publisher,
            'created_at': event.created_at.isoformat() if event.created_at else None,
            'consumed_at': event.consumed_at.isoformat() if event.consumed_at else None
        }

        if include_payload:
            result['payload'] = json.loads(event.payload) if event.payload else {}
            result['subscribers'] = json.loads(event.subscribers) if event.subscribers else []
            result['consumed_by'] = json.loads(event.consumed_by) if event.consumed_by else []

        return result


# ============================================================
# 便捷函数
# ============================================================

def monitor_events(db: Session) -> EventMonitoringService:
    """
    获取事件监控服务实例

    Args:
        db: 数据库会话

    Returns:
        监控服务实例
    """
    return EventMonitoringService(db)
