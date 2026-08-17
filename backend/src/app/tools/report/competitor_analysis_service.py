"""
业务服务05：竞争对手分析服务 (CompetitorAnalysisService)

定位：识别周边同类和替代性文化遗产地的竞争格局，明确差异化定位
属于：乡村遗产业务第一阶段（现场扫描与价值判断）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session


class CompetitorAnalysisService:
    """竞争对手分析服务"""

    def __init__(self, db: Session):
        self.db = db

    async def analyze(self, project_id: int) -> Dict[str, Any]:
        """
        执行竞争对手分析

        Returns:
            {
                'competitor_map': List[Dict],  # 竞争格局图谱
                'unique_value_proposition': str,  # 独特价值主张UVP
                'positioning_matrix': Dict,  # 定位矩阵
                'avoidable_traps': List[str]  # 可避免的竞争陷阱
            }
        """
        from app.models.project import ProjectDocument

        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            return self._get_empty_result()

        context = self._extract_context(documents)

        # 1. 竞争分类
        competitors = self._classify_competitors(context)

        # 2. 核心指标对比
        comparison = self._compare_metrics(context, competitors)

        # 3. SWOT交叉分析
        swot = self._swot_analysis(context)

        # 4. 差异化机会点
        differentiation = self._find_differentiation(context, competitors)

        # 5. 遗产专有：类型比较法
        heritage_comparison = self._heritage_type_comparison(context)

        # 6. 独特价值主张UVP
        uvp = self._generate_uvp(context, differentiation, heritage_comparison)

        return {
            'service_id': 'competitor_analysis',
            'service_name': '竞争对手分析',
            'competitor_map': competitors,
            'swot_analysis': swot,
            'differentiation_opportunities': differentiation,
            'heritage_type_comparison': heritage_comparison,
            'unique_value_proposition': uvp,
            'competitor_lessons': comparison.get('lessons', []),
            'status': 'completed'
        }

    def _extract_context(self, documents) -> str:
        texts = []
        for doc in documents[:5]:
            if doc.text_content:
                texts.append(doc.text_content[:2000])
        return "\n\n".join(texts)

    def _classify_competitors(self, context: str) -> List[Dict[str, Any]]:
        """竞争分类：直接竞争和间接竞争"""
        competitors = []

        # 直接竞争：同类型遗产地
        if any(kw in context for kw in ['附近', '周边', '同类', '类似']):
            competitors.append({
                'type': 'direct',
                'category': '同类型遗产地',
                'threat_level': 'high',
                'note': '同质化风险高，需强差异化'
            })

        # 间接竞争：替代性文化消费
        competitors.append({
            'type': 'indirect',
            'category': '替代性文化消费',
            'examples': ['博物馆', '剧院', 'Citywalk', '其他古镇'],
            'threat_level': 'medium',
            'note': '争夺周末闲暇时间'
        })

        return competitors

    def _compare_metrics(self, context: str, competitors: List[Dict]) -> Dict[str, Any]:
        """核心指标对比"""
        return {
            'metrics': ['客单价', '年接待量', '产品种类', '文化体验深度', '网络口碑'],
            'lessons': [
                '头部竞争对手的优势在于品牌和流量',
                '本地优势在于文化独特性和真实性',
                '避免价格战，聚焦体验深度'
            ]
        }

    def _swot_analysis(self, context: str) -> Dict[str, List[str]]:
        """SWOT交叉分析"""
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []

        # Strengths
        if any(kw in context for kw in ['独特', '唯一', '稀缺', '活态']):
            strengths.append('文化独特性')
        if any(kw in context for kw in ['传承人', '老艺人', '原住民']):
            strengths.append('活态传承')

        # Weaknesses
        if any(kw in context for kw in ['偏远', '交通不便', '知名度低']):
            weaknesses.append('可达性和知名度不足')
        if any(kw in context for kw in ['设施简陋', '缺乏', '没有']):
            weaknesses.append('基础设施不完善')

        # Opportunities
        opportunities.append('文化认同消费升级')
        opportunities.append('寻根经济崛起')

        # Threats
        threats.append('同质化竞争')
        threats.append('过度商业化导致文化流失')

        return {
            'strengths': strengths if strengths else ['待发掘'],
            'weaknesses': weaknesses if weaknesses else ['待评估'],
            'opportunities': opportunities,
            'threats': threats
        }

    def _find_differentiation(self, context: str, competitors: List[Dict]) -> List[Dict[str, str]]:
        """差异化机会点挖掘"""
        opportunities = []

        # 检查是否有独特文化元素
        unique_elements = {
            '仪式': '仪式感体验',
            '技艺': '手工技艺传承',
            '记忆': '集体记忆唤醒',
            '信仰': '信仰文化参与',
            '节庆': '节庆IP打造'
        }

        for keyword, opportunity in unique_elements.items():
            if keyword in context:
                opportunities.append({
                    'element': keyword,
                    'opportunity': opportunity,
                    'differentiation_strength': 'high'
                })

        return opportunities if opportunities else [{
            'element': '待挖掘',
            'opportunity': '需深入调研识别独特性',
            'differentiation_strength': 'unknown'
        }]

    def _heritage_type_comparison(self, context: str) -> Dict[str, Any]:
        """遗产专有：类型比较法"""
        heritage_types = {
            '物质遗产': ['古建', '文物', '遗址', '古道', '古树'],
            '非物质遗产': ['技艺', '仪式', '戏曲', '民俗', '传说'],
            '自然遗产': ['梯田', '山水', '生态', '景观'],
            '混合遗产': []
        }

        detected_types = []
        for heritage_type, keywords in heritage_types.items():
            if any(kw in context for kw in keywords):
                detected_types.append(heritage_type)

        # 判断遗产类型
        if len(detected_types) >= 2:
            final_type = '混合遗产'
            note = f'包含{"+".join(detected_types)}，复合型优势'
        elif detected_types:
            final_type = detected_types[0]
            note = f'专注于{final_type}'
        else:
            final_type = '待识别'
            note = '需要现场调研明确遗产类型'

        return {
            'heritage_type': final_type,
            'detected_elements': detected_types,
            'note': note,
            'competitive_scope': self._get_competitive_scope(final_type)
        }

    def _get_competitive_scope(self, heritage_type: str) -> str:
        """根据遗产类型确定竞争范围"""
        scopes = {
            '自然遗产': '周边自然景区、国家公园',
            '非物质遗产': '同工艺类非遗馆、博物馆',
            '物质遗产': '古镇古村、文保单位',
            '混合遗产': '综合性文化旅游目的地'
        }
        return scopes.get(heritage_type, '待评估')

    def _generate_uvp(self, context: str, differentiation: List[Dict], heritage_comp: Dict) -> str:
        """生成独特价值主张UVP"""
        if not differentiation or differentiation[0]['element'] == '待挖掘':
            return '待深入调研后提炼'

        # 基于差异化机会点生成UVP
        key_elements = [d['element'] for d in differentiation[:2]]
        heritage_type = heritage_comp['heritage_type']

        uvp_templates = {
            '仪式': f'唯一可参与{key_elements[0]}的活态{heritage_type}',
            '技艺': f'跟随传承人学习{key_elements[0]}的沉浸式体验',
            '记忆': f'唤醒家族记忆的{heritage_type}寻根之旅',
            '信仰': f'在地信仰文化的真实体验空间',
            '节庆': f'基于{key_elements[0]}打造的文化节庆IP'
        }

        first_element = key_elements[0] if key_elements else '文化'
        return uvp_templates.get(first_element, f'真实的{heritage_type}文化体验')

    def _get_empty_result(self) -> Dict[str, Any]:
        return {
            'service_id': 'competitor_analysis',
            'service_name': '竞争对手分析',
            'competitor_map': [],
            'swot_analysis': {},
            'differentiation_opportunities': [],
            'unique_value_proposition': '暂无数据',
            'status': 'no_data'
        }
