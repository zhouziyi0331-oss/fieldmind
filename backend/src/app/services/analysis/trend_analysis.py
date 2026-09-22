"""
趋势分析服务
识别数据趋势、预测发展方向、分析变化模式
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from collections import defaultdict
import json
from .base_analysis import BaseAnalysisService


class TrendAnalysisService(BaseAnalysisService):
    """趋势分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='trend')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行趋势分析"""
        trends = []

        # 趋势1: 文档增长趋势
        doc_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM documents
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        doc_timeline = db_session.execute(doc_timeline_query, {'project_id': project_id}).fetchall()

        if len(doc_timeline) > 1:
            doc_counts = [row['count'] for row in doc_timeline]
            doc_trend = self._calculate_trend(doc_counts)
            trends.append({
                'aspect': 'document_growth',
                'direction': doc_trend['direction'],
                'rate': doc_trend['rate'],
                'data_points': len(doc_timeline),
                'description': f'文档增长呈{doc_trend["direction_cn"]}趋势，增长率{doc_trend["rate"]:.1f}%'
            })

        # 趋势2: 实体发现趋势
        entity_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM entities
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        entity_timeline = db_session.execute(entity_timeline_query, {'project_id': project_id}).fetchall()

        if len(entity_timeline) > 1:
            entity_counts = [row['count'] for row in entity_timeline]
            entity_trend = self._calculate_trend(entity_counts)
            trends.append({
                'aspect': 'entity_discovery',
                'direction': entity_trend['direction'],
                'rate': entity_trend['rate'],
                'data_points': len(entity_timeline),
                'description': f'实体发现呈{entity_trend["direction_cn"]}趋势，变化率{entity_trend["rate"]:.1f}%'
            })

        # 趋势3: 关系构建趋势
        relation_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM relations
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        relation_timeline = db_session.execute(relation_timeline_query, {'project_id': project_id}).fetchall()

        if len(relation_timeline) > 1:
            relation_counts = [row['count'] for row in relation_timeline]
            relation_trend = self._calculate_trend(relation_counts)
            trends.append({
                'aspect': 'relation_building',
                'direction': relation_trend['direction'],
                'rate': relation_trend['rate'],
                'data_points': len(relation_timeline),
                'description': f'关系构建呈{relation_trend["direction_cn"]}趋势，变化率{relation_trend["rate"]:.1f}%'
            })

        # 趋势4: 知识节点演化趋势
        knowledge_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM knowledge_nodes
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        knowledge_timeline = db_session.execute(knowledge_timeline_query, {'project_id': project_id}).fetchall()

        if len(knowledge_timeline) > 1:
            knowledge_counts = [row['count'] for row in knowledge_timeline]
            knowledge_trend = self._calculate_trend(knowledge_counts)
            trends.append({
                'aspect': 'knowledge_evolution',
                'direction': knowledge_trend['direction'],
                'rate': knowledge_trend['rate'],
                'data_points': len(knowledge_timeline),
                'description': f'知识演化呈{knowledge_trend["direction_cn"]}趋势，增长率{knowledge_trend["rate"]:.1f}%'
            })

        # 趋势5: 实体类型多样性趋势
        entity_type_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(DISTINCT entity_type) as type_count
            FROM entities
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        entity_type_timeline = db_session.execute(entity_type_timeline_query, {'project_id': project_id}).fetchall()

        if len(entity_type_timeline) > 1:
            type_counts = [row['type_count'] for row in entity_type_timeline]
            diversity_trend = self._calculate_trend(type_counts)
            trends.append({
                'aspect': 'entity_type_diversity',
                'direction': diversity_trend['direction'],
                'rate': diversity_trend['rate'],
                'data_points': len(entity_type_timeline),
                'description': f'实体类型多样性呈{diversity_trend["direction_cn"]}趋势，变化率{diversity_trend["rate"]:.1f}%'
            })

        # 趋势6: 思考模式活跃度趋势
        thinking_timeline_query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM thinking_patterns
            WHERE project_id = :project_id
            AND created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        thinking_timeline = db_session.execute(thinking_timeline_query, {'project_id': project_id}).fetchall()

        if len(thinking_timeline) > 1:
            thinking_counts = [row['count'] for row in thinking_timeline]
            thinking_trend = self._calculate_trend(thinking_counts)
            trends.append({
                'aspect': 'thinking_activity',
                'direction': thinking_trend['direction'],
                'rate': thinking_trend['rate'],
                'data_points': len(thinking_timeline),
                'description': f'思考活跃度呈{thinking_trend["direction_cn"]}趋势，变化率{thinking_trend["rate"]:.1f}%'
            })

        # 计算整体趋势摘要
        positive_trends = sum(1 for t in trends if t['direction'] == 'increasing')
        negative_trends = sum(1 for t in trends if t['direction'] == 'decreasing')
        stable_trends = sum(1 for t in trends if t['direction'] == 'stable')

        overall_direction = 'positive'
        if negative_trends > positive_trends:
            overall_direction = 'negative'
        elif stable_trends > positive_trends + negative_trends:
            overall_direction = 'stable'

        # 计算平均增长率（只包含增长趋势）
        growth_rates = [t['rate'] for t in trends if t['direction'] == 'increasing']
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

        return {
            'total_trends_analyzed': len(trends),
            'trends': trends,
            'trend_distribution': {
                'increasing': positive_trends,
                'decreasing': negative_trends,
                'stable': stable_trends
            },
            'overall_direction': overall_direction,
            'average_growth_rate': round(avg_growth_rate, 2),
            'has_data': len(trends) > 0,
            'confidence_score': 0.85 if len(trends) >= 3 else 0.60
        }

    def _calculate_trend(self, values: List[int]) -> Dict[str, Any]:
        """计算趋势方向和变化率"""
        if len(values) < 2:
            return {
                'direction': 'unknown',
                'direction_cn': '未知',
                'rate': 0.0
            }

        # 简单线性趋势：比较前半段和后半段的平均值
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / (len(values) - mid) if len(values) > mid else 0

        if first_half_avg == 0:
            rate = 0.0
            direction = 'stable'
            direction_cn = '稳定'
        else:
            rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100

            if rate > 10:
                direction = 'increasing'
                direction_cn = '上升'
            elif rate < -10:
                direction = 'decreasing'
                direction_cn = '下降'
            else:
                direction = 'stable'
                direction_cn = '稳定'

        return {
            'direction': direction,
            'direction_cn': direction_cn,
            'rate': round(rate, 2)
        }
