"""
文献市场调研Skill - Literature & Market Research Skill

基于学术文献检索和市场调研方法论的专业分析技能
整合文献综述、市场调查、竞品分析、趋势预测四大维度
"""

from typing import Dict, List
from app.services.skills.skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords


class LiteratureMarketResearchSkill(SkillBase):
    """文献市场调研技能类"""

    @property
    def skill_id(self) -> str:
        return "literature_market_research"

    @property
    def skill_name(self) -> str:
        return "文献市场调研"

    @property
    def skill_description(self) -> str:
        return "基于学术文献检索和市场调研方法论的专业分析技能，整合文献综述、市场调查、竞品分析、趋势预测"

    def _initialize_dimensions(self) -> None:
        """初始化技能的四个分析维度"""

        self.dimensions = {
            'literature_review': DimensionDefinition(
                dimension_id='literature_review',
                dimension_name='文献综述',
                description='检索相关学术文献、政策文件、行业报告，梳理研究现状和理论基础',
                keywords=[
                    '文献检索', '理论基础', '研究现状', '学术观点',
                    '政策文件', '行业报告', '文献综述', '理论框架',
                    '研究方法', '学术成果', '文献分析', '理论梳理'
                ],
                example_sentences=[
                    '查阅了近五年相关学术论文，发现乡村振兴领域研究热点集中在产业发展和文化保护',
                    '参考了国家乡村振兴战略规划文件和地方政策，明确了政策导向和支持重点',
                    '梳理了国内外乡村旅游发展理论，包括社区参与理论、可持续发展理论等',
                    '文献显示，成功的乡村项目普遍强调文化特色挖掘和居民主体地位',
                    '行业报告指出，2023年乡村旅游市场规模达到万亿级，增长潜力巨大',
                    '学术界对于乡村振兴路径存在不同观点，有的强调产业带动，有的重视文化复兴',
                    '政策文件明确提出要保护传统村落，活化利用文化遗产，这为项目提供了政策依据',
                    '相关研究表明，乡村发展需要平衡经济效益和社会文化价值'
                ],
                vector=None
            ),

            'market_survey': DimensionDefinition(
                dimension_id='market_survey',
                dimension_name='市场调查',
                description='开展实地调研、问卷访谈，收集一手市场数据和用户需求信息',
                keywords=[
                    '实地调研', '问卷调查', '访谈记录', '市场数据',
                    '用户需求', '消费行为', '市场容量', '需求分析',
                    '调研发现', '数据收集', '一手资料', '田野调查'
                ],
                example_sentences=[
                    '我们对周边三个县市的游客进行了问卷调查，共回收有效问卷500份',
                    '访谈了30位潜在客户，了解他们对乡村旅游的偏好和消费意愿',
                    '实地调研发现，周末客流量是平时的3-4倍，节假日更是爆满',
                    '市场调查显示，80%的受访者愿意为特色民宿支付300-500元/晚的价格',
                    '通过深度访谈发现，游客最看重的是环境质量和文化体验，而非豪华设施',
                    '收集了近两年的客流数据和消费记录，分析出消费高峰期和淡季规律',
                    '调研中发现，年轻家庭和中老年群体是主要客源，需求特点有明显差异',
                    '问卷结果表明，超过70%的游客希望体验农事活动和传统手工艺'
                ],
                vector=None
            ),

            'competitive_analysis': DimensionDefinition(
                dimension_id='competitive_analysis',
                dimension_name='竞品分析',
                description='研究同类项目和竞争对手，分析其优劣势、经营模式和市场定位',
                keywords=[
                    '竞争对手', '同类项目', '对比分析', '优劣势',
                    '经营模式', '市场定位', '差异化', '竞争格局',
                    '标杆学习', '案例分析', '竞品调研', '市场占有率'
                ],
                example_sentences=[
                    '调研了周边五个成功的民宿项目，分析了它们的经营模式和特色定位',
                    '竞品A主打高端精品路线，客单价高但客流量有限，我们可以走中端大众市场',
                    '通过对比发现，竞争对手在文化体验项目上做得不够深入，这是我们的机会',
                    '同类项目普遍存在淡季客源不足的问题，需要开发四季皆宜的产品',
                    '标杆项目的成功经验在于打造了独特的IP形象和品牌故事',
                    '竞争分析显示，本区域内高品质民宿供给不足，市场存在缺口',
                    '对手主要依赖线上平台获客，我们可以加强线下渠道和口碑营销',
                    '案例研究表明，成功项目都建立了稳定的回头客群体，复购率超过40%'
                ],
                vector=None
            ),

            'trend_forecast': DimensionDefinition(
                dimension_id='trend_forecast',
                dimension_name='趋势预测',
                description='基于数据分析和行业洞察，预测市场发展趋势和未来机会',
                keywords=[
                    '发展趋势', '市场预测', '未来机会', '行业走向',
                    '增长潜力', '新兴需求', '政策风向', '技术趋势',
                    '市场前景', '战略机遇', '风险预警', '趋势研判'
                ],
                example_sentences=[
                    '预计未来三年乡村旅游市场将保持20%以上的年增长率，发展前景广阔',
                    '随着乡村振兴战略深入推进，政策支持力度会持续加大，这是重要机遇期',
                    '消费升级趋势下，游客对品质和体验的要求越来越高，中高端市场潜力大',
                    '疫情后人们更注重健康和亲近自然，乡村度假需求将持续旺盛',
                    '数字化转型是大趋势，需要提前布局线上渠道和智慧旅游系统',
                    '非遗文化和在地体验成为新热点，文化深度游将是未来方向',
                    '预判碳中和政策会影响行业发展，生态环保型项目更有竞争力',
                    '基于数据分析，预测明后年周边地区游客量将增长30%，要抓住窗口期'
                ],
                vector=None
            )
        }

    def analyze(self, text: str) -> SkillResult:
        """
        分析文本，识别文献市场调研相关内容

        Args:
            text: 待分析的文本

        Returns:
            SkillResult对象，包含各维度的匹配结果
        """
        import time
        start_time = time.time()

        # 对每个维度进行语义检索
        all_matches: Dict[str, List[AnalysisMatch]] = {}
        total_matches = 0
        all_confidences = []

        for dim_id, dimension in self.dimensions.items():
            # semantic_retrieve返回 List[Tuple[str, float, str]]
            raw_matches = self.semantic_retrieve(
                text=text,
                dimension=dimension,
                threshold=0.65
            )

            # 转换为AnalysisMatch对象
            analysis_matches = []
            for sentence, score, context in raw_matches:
                match_obj = AnalysisMatch(
                    dimension_id=dim_id,
                    dimension_name=dimension.dimension_name,
                    sentence=sentence,
                    similarity=float(score),
                    context=context,
                    keywords_found=[]
                )
                analysis_matches.append(match_obj)
                all_confidences.append(float(score))

            if analysis_matches:
                all_matches[dim_id] = analysis_matches
                total_matches += len(analysis_matches)

        # 计算平均置信度
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        # 提取关键词
        keywords = extract_keywords(text, top_k=8)

        execution_time = time.time() - start_time

        return SkillResult(
            skill_id=self.skill_id,
            skill_name=self.skill_name,
            success=True,
            dimensions=all_matches,
            total_matches=total_matches,
            avg_confidence=avg_confidence,
            keywords=keywords,
            execution_time=execution_time
        )
