"""
业务服务04：市场需求分析服务 (MarketDemandAnalysisService)

定位：定量定性结合，验证"有没有人愿意来、愿意花多少钱"
属于：乡村遗产业务第一阶段（现场扫描与价值判断）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json

from app.models.project import ProjectDocument
from app.models.chunk import Chunk


class MarketDemandAnalysisService:
    """市场需求分析服务"""

    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        """
        执行市场需求分析

        Returns:
            {
                'annual_visitors': {'low': int, 'mid': int, 'high': int},
                'customer_segments': List[Dict],
                'demand_gaps': List[str],
                'local_faith_baseline': Dict,  # 遗产专有：在地信仰样本
                'cultural_calendar': List[Dict]  # 遗产专有：文化节律
            }
        """

        # 1. 提取项目相关数据
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            return self._get_empty_result()

        # 2. 提取关键信息
        context = self._extract_context(documents)

        # 3. 市场容量估算
        market_capacity = self._estimate_market_capacity(context)

        # 4. 需求分割
        customer_segments = self._segment_demand(context)

        # 5. 遗产专有：在地信仰人群基线
        local_faith = self._analyze_local_faith(context)

        # 6. 遗产专有：文化节律
        cultural_calendar = self._extract_cultural_calendar(context)

        # 7. 需求缺口分析
        demand_gaps = self._identify_gaps(context, customer_segments)

        return {
            'service_id': 'market_demand_analysis',
            'service_name': '市场需求分析',
            'annual_visitors': market_capacity,
            'customer_segments': customer_segments,
            'demand_gaps': demand_gaps,
            'local_faith_baseline': local_faith,
            'cultural_calendar': cultural_calendar,
            'status': 'completed'
        }

    def _extract_context(self, documents: List[ProjectDocument]) -> str:
        """提取项目上下文"""
        texts = []
        for doc in documents[:5]:
            if doc.text_content:
                texts.append(doc.text_content[:2000])
        return "\n\n".join(texts)

    def _estimate_market_capacity(self, context: str) -> Dict[str, int]:
        """市场容量估算"""
        # 基于关键词的初步估算
        keywords_high = ['知名', '5A', '热门', '网红', '省会', '中心城市']
        keywords_mid = ['县城', '古镇', '传统村落', '文保']
        keywords_low = ['偏远', '山区', '交通不便']

        score = 5000  # 基础分

        for kw in keywords_high:
            if kw in context:
                score += 10000

        for kw in keywords_mid:
            if kw in context:
                score += 3000

        for kw in keywords_low:
            if kw in context:
                score -= 2000

        return {
            'low': max(score - 2000, 1000),
            'mid': score,
            'high': score + 5000
        }

    def _segment_demand(self, context: str) -> List[Dict[str, Any]]:
        """需求分割"""
        segments = []

        # 观光型
        if any(kw in context for kw in ['景点', '古建', '风景', '拍照']):
            segments.append({
                'type': '观光型',
                'proportion': 0.4,
                'willingness_to_pay': 'low',
                'duration': '2-4小时'
            })

        # 体验型
        if any(kw in context for kw in ['体验', '手工', '互动', '参与']):
            segments.append({
                'type': '体验型',
                'proportion': 0.3,
                'willingness_to_pay': 'medium',
                'duration': '半天-1天'
            })

        # 深度研学型
        if any(kw in context for kw in ['研学', '课程', '教育', '学习']):
            segments.append({
                'type': '深度研学型',
                'proportion': 0.2,
                'willingness_to_pay': 'high',
                'duration': '2-3天'
            })

        # 遗产专有：寻根问祖型
        if any(kw in context for kw in ['宗祠', '祖先', '族谱', '祭祀', '姓氏']):
            segments.append({
                'type': '寻根问祖型',
                'proportion': 0.1,
                'willingness_to_pay': 'very_high',
                'duration': '定期回访',
                'heritage_specific': True  # 遗产专有标记
            })

        return segments if segments else [{
            'type': '通用型',
            'proportion': 1.0,
            'willingness_to_pay': 'medium',
            'duration': '半天'
        }]

    def _analyze_local_faith(self, context: str) -> Dict[str, Any]:
        """遗产专有：在地信仰人群基线"""
        faith_keywords = {
            '祭祀': '祭祀活动',
            '庙会': '庙会',
            '神诞': '神诞日',
            '戏台': '酬神戏',
            '香客': '香客'
        }

        activities = []
        for keyword, activity in faith_keywords.items():
            if keyword in context:
                activities.append(activity)

        return {
            'has_local_faith': len(activities) > 0,
            'faith_activities': activities,
            'note': '在地信仰人群是免费样本，比外部大数据更可靠' if activities else '未发现明显在地信仰活动'
        }

    def _extract_cultural_calendar(self, context: str) -> List[Dict[str, str]]:
        """遗产专有：文化节律"""
        calendar_keywords = {
            '春节': '农历正月',
            '清明': '农历三月',
            '端午': '农历五月',
            '中秋': '农历八月',
            '重阳': '农历九月',
            '庙会': '特定神诞日',
            '祭祖': '宗族活动日'
        }

        events = []
        for event, period in calendar_keywords.items():
            if event in context:
                events.append({
                    'event': event,
                    'period': period,
                    'demand_type': 'peak' if event in ['春节', '清明', '中秋'] else 'seasonal'
                })

        return events

    def _identify_gaps(self, context: str, segments: List[Dict]) -> List[str]:
        """需求缺口分析"""
        gaps = []

        # 检查是否有住宿
        if '民宿' not in context and '住宿' not in context:
            gaps.append('缺少住宿设施，无法承接过夜客群')

        # 检查是否有餐饮
        if '餐厅' not in context and '农家乐' not in context:
            gaps.append('缺少餐饮服务，游客体验不完整')

        # 检查是否有体验项目
        if '体验' not in context and '互动' not in context:
            gaps.append('缺少互动体验项目，观光后缺乏留客理由')

        return gaps if gaps else ['需求与供给基本匹配']

    def _get_empty_result(self) -> Dict[str, Any]:
        """空结果"""
        return {
            'service_id': 'market_demand_analysis',
            'service_name': '市场需求分析',
            'annual_visitors': {'low': 0, 'mid': 0, 'high': 0},
            'customer_segments': [],
            'demand_gaps': ['暂无调研数据'],
            'local_faith_baseline': {'has_local_faith': False, 'faith_activities': []},
            'cultural_calendar': [],
            'status': 'no_data'
        }
