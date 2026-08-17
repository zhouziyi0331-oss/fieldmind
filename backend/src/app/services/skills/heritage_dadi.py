"""
大地文化遗产活化运营方法论Skill
Heritage Activation and Operation Methodology based on Dadi Cultural Heritage

理论来源：大地风景巍特恒泰文化遗产投顾公司工作方法论
核心转型：从"资源管理"到"内容运营"
三层结构：价值层（四大原则）→ 方法层（内容挖掘与转化）→ 落地层（EPCO机制）
"""

from typing import Dict, List
from app.services.skills.skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords


class HeritageDADISkill(SkillBase):
    """大地文化遗产活化运营分析技能"""

    @property
    def skill_id(self) -> str:
        return "heritage_dadi"

    @property
    def skill_name(self) -> str:
        return "大地文化遗产活化运营"

    @property
    def skill_description(self) -> str:
        return "基于大地风景方法论的文化遗产活化运营分析，涵盖价值原则、内容挖掘、转化模式、EPCO机制"

    def _initialize_dimensions(self) -> None:
        """
        初始化四大分析维度
        对应大地方法论的核心层级：价值层、内容挖掘、内容转化、运营机制
        """
        self.dimensions = {
            'value_principles': DimensionDefinition(
                dimension_id='value_principles',
                dimension_name='价值层-四大原则',
                description='统筹为纲、跨界赋能、多方共赢、长期为要四大指导原则的体现',
                keywords=[
                    '统筹规划', '保护旅游产业社区', '一张蓝图', '综合效益',
                    '跨界融合', '跨学科', '多领域', '文旅科商', '复合赋能',
                    '多方共赢', '利益平衡', '社区参与', '居民主体', '收益分配',
                    '长期运营', '可持续', '内容更新', '持续供给', '运营机制'
                ],
                example_sentences=[
                    '这个方案要统筹考虑保护、旅游、产业和社区发展，不能只顾一头。',
                    '我们把文化学者、艺术家、商业运营团队都请来了，形成跨界合作。',
                    '村民要参与决策和收益分配，不能让外来公司独占利益。',
                    '项目规划了三年的内容更新计划，不是一次性投入就完事。',
                    '保护、经营和社区三方利益都要照顾到，任何一方受损都不可持续。',
                    '除了旅游团队，还引入了科技公司做数字化，设计师做空间改造。',
                    '运营方案里明确了本地居民的就业岗位和分红比例。',
                    '一年后这里靠什么持续吸引人？内容供给和更新机制是关键。'
                ],
                vector=None
            ),

            'content_excavation': DimensionDefinition(
                dimension_id='content_excavation',
                dimension_name='方法层-内容挖掘',
                description='大遗产（从物到事到当代关联）、泛艺术（现代化演绎）、新乡土（与当代生活连接）',
                keywords=[
                    '遗产叙事', '历史故事', '当代关联', '追问意义', '为什么在今天仍有意义',
                    '艺术化', '设计化', '现代表达', '艺术家介入', '创意转化',
                    '乡土生活', '生活方式', '社群关系', '与当代连接', '城市人触点'
                ],
                example_sentences=[
                    '这座古桥不只是文物，它见证了当地商贸繁荣，能回应今天的乡村振兴问题。',
                    '我们请艺术家把传统剪纸元素重新设计，做成现代装置艺术。',
                    '这里的乡土生活方式，比如集体打糍粑、晒秋，能让城市家庭找到久违的邻里感。',
                    '不满足于"发现了什么"，要追问"它为什么在今天仍有意义"。',
                    '把老建筑当作可再创作的艺术素材，而不是只能隔离保护的文物。',
                    '年轻人会为这段乡土生活买单吗？触点在于慢节奏和真实的人际关系。',
                    '这件事在当下语境中能回应什么问题？城市化、孤独感还是文化认同？',
                    '民俗节庆不是简单复原，要找到它与当代生活的连接点。'
                ],
                vector=None
            ),

            'content_transformation': DimensionDefinition(
                dimension_id='content_transformation',
                dimension_name='方法层-内容转化',
                description='与旅游要素融合、与公共文化产品融合、打造内容IP三大转化模式',
                keywords=[
                    '食住行游购娱', '旅游要素', '新六要素', '场景化', '体验化',
                    '文化馆图书馆', '公共文化', '第三空间', '体验空间', '开放运营',
                    '内容IP', 'IP孵化', '可识别可复购', '品牌化', '系列活动'
                ],
                example_sentences=[
                    '文化主题与餐饮、住宿、游览融合，打造新六要素体验。',
                    '村史馆不再是静态展览，改造成可以办沙龙、做研学的体验空间。',
                    '孵化了"古村音乐节"这个IP，每年办一次，已经成为区域品牌。',
                    '每个文化内容都要找到"食住行游购娱"中的具体载体。',
                    '把图书馆功能转化为文化沙龙和手工坊，增加体验和经营属性。',
                    'IP必须是可识别、可复购、可授权的资产，而不是一次性活动。',
                    '文化元素植入到民宿设计、特色餐饮、伴手礼开发全链条。',
                    '公共文化设施要重新审视其体验与经营功能，不能只是展陈。'
                ],
                vector=None
            ),

            'epco_mechanism': DimensionDefinition(
                dimension_id='epco_mechanism',
                dimension_name='落地层-EPCO机制',
                description='设计(E)-采购(P)-施工(C)-运营(O)一体化，运营前置贯穿全链',
                keywords=[
                    'EPCO', '设计采购施工运营', '一体化', '运营前置', '全链条',
                    '运营思维', '谁来运营', '如何持续', '降本保质提效', '无缝衔接',
                    '保护与活化利用咨询', '空间综合运营', 'IP赋能', '活动推广'
                ],
                example_sentences=[
                    '规划阶段就要想清楚谁来运营、如何持续，不是建完再说。',
                    '设计、采购、施工、运营一体化管理，避免各环节脱节。',
                    '运营不是最后一个环节，而是贯穿全链条的第一思维。',
                    '规划时就引入了运营团队，确保设计方案落地后真的能运转。',
                    '顶层规划与设计、空间改造、内容植入、日常运营管理全程闭环。',
                    'EPCO模式让我们在施工阶段就预留了后期运营所需的设施接口。',
                    '四大业务模块：保护咨询、空间运营、IP赋能、活动推广协同推进。',
                    '运营前置帮我们减少了大量返工浪费，质量可控、周期缩短。'
                ],
                vector=None
            )
        }

    def analyze(self, text: str) -> SkillResult:
        """
        分析文本中的大地遗产方法论体现

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
