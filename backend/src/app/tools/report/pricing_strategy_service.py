"""
业务服务06：定价策略服务 (PricingStrategyService)
为门票、研学课程、民宿、餐饮、文创等业态制定价格体系
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session


class PricingStrategyService:
    """定价策略服务"""

    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        """执行定价策略分析"""
        from app.models.project import ProjectDocument

        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        context = self._extract_context(documents) if documents else ""

        # 1. 成本加成法
        base_pricing = self._cost_plus_pricing(context)

        # 2. 价值定价法
        value_pricing = self._value_based_pricing(context)

        # 3. 遗产专有：圈层定价（核心圈免费，外围圈收费）
        sacred_pricing = self._sacred_circle_pricing(context)

        # 4. 价格梯度设计
        price_tiers = self._design_price_tiers(context, base_pricing, value_pricing)

        return {
            'service_id': 'pricing_strategy',
            'service_name': '定价策略',
            'base_pricing': base_pricing,
            'value_pricing': value_pricing,
            'sacred_circle_pricing': sacred_pricing,
            'price_tiers': price_tiers,
            'pricing_calendar': self._seasonal_pricing(context),
            'status': 'completed'
        }

    def _extract_context(self, documents) -> str:
        texts = []
        for doc in documents[:3]:
            if doc.text_content:
                texts.append(doc.text_content[:1000])
        return "\n".join(texts)

    def _cost_plus_pricing(self, context: str) -> Dict[str, Any]:
        """成本加成法"""
        return {
            'method': 'cost_plus',
            'base_cost': 'estimated',
            'markup_rate': '30-50%',
            'note': '确保基本利润的最低定价'
        }

    def _value_based_pricing(self, context: str) -> Dict[str, Any]:
        """价值定价法"""
        premium_factors = []

        if any(kw in context for kw in ['非遗', '大师', '传承人', '稀缺']):
            premium_factors.append('非遗大师课程溢价能力强')

        if any(kw in context for kw in ['独特', '唯一', '活态']):
            premium_factors.append('独特体验可溢价')

        return {
            'method': 'value_based',
            'premium_factors': premium_factors if premium_factors else ['待挖掘'],
            'suggested_premium': '20-100%' if premium_factors else '0-20%'
        }

    def _sacred_circle_pricing(self, context: str) -> Dict[str, Any]:
        """遗产专有：圈层定价"""
        has_sacred = any(kw in context for kw in ['祭祀', '祠堂', '神诞', '仪式'])

        if has_sacred:
            return {
                'strategy': 'sacred_circle',
                'core_circle': '祠堂仪式核心区免费（维护神圣性）',
                'outer_circle': '外围观礼、体验、伴手礼可定价',
                'note': '核心免费是文化伦理，外围定价是商业模式'
            }
        else:
            return {
                'strategy': 'not_applicable',
                'note': '非宗教信仰类遗产，不适用圈层定价'
            }

    def _design_price_tiers(self, context: str, base: Dict, value: Dict) -> List[Dict[str, Any]]:
        """价格梯度设计"""
        return [
            {
                'product': '门票/参观',
                'retail_price': '50-80元',
                'early_bird': '40-60元',
                'group_price': '30-50元'
            },
            {
                'product': '研学课程',
                'retail_price': '200-500元/人',
                'note': '含材料费和传承人授课费'
            },
            {
                'product': '民宿',
                'peak_season': '300-800元/晚',
                'off_season': '200-500元/晚'
            }
        ]

    def _seasonal_pricing(self, context: str) -> List[Dict[str, str]]:
        """季节性定价日历"""
        return [
            {'period': '春节/清明', 'strategy': '旺季价格，但用价格调节承载量'},
            {'period': '淡季', 'strategy': '优惠价引流，配合文化活动'},
            {'period': '祭祀节庆', 'strategy': '不是涨价窗口，而是内容高峰'}
        ]
