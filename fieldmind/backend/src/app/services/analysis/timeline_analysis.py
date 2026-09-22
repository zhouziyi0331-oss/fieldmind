"""
时间线分析服务
构建事件时间线、识别关键时间节点、分析时序规律
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .base_analysis import BaseAnalysisService


class TimelineAnalysisService(BaseAnalysisService):
    """时间线分析服务"""

    def __init__(self):
        super().__init__(analysis_type='timeline')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行时间线分析"""
        # 查询timeline_events表
        query = text("""
            SELECT id, event_date, event_type, title, description, importance
            FROM timeline_events
            WHERE project_id = :project_id
            ORDER BY event_date
        """)
        result = db_session.execute(query, {'project_id': project_id})
        events = [dict(row._mapping) for row in result.fetchall()]

        # 识别关键节点（重要性高的事件）
        key_events = [e for e in events if e.get('importance', 0) >= 8]

        # 按类型分组
        events_by_type = {}
        for event in events:
            etype = event.get('event_type', 'unknown')
            if etype not in events_by_type:
                events_by_type[etype] = []
            events_by_type[etype].append(event)

        return {
            'total_events': len(events),
            'timeline': events,
            'key_events': key_events,
            'events_by_type': {k: len(v) for k, v in events_by_type.items()},
            'time_span': self._calculate_time_span(events),
            'confidence_score': 0.90
        }

    def _calculate_time_span(self, events: List[Dict]) -> Dict[str, Any]:
        """计算时间跨度"""
        if not events:
            return {'start': None, 'end': None, 'duration_days': 0}

        dates = [e['event_date'] for e in events if e.get('event_date')]
        if not dates:
            return {'start': None, 'end': None, 'duration_days': 0}

        return {
            'start': min(dates),
            'end': max(dates),
            'duration_days': (max(dates) - min(dates)).days if len(dates) > 1 else 0
        }
