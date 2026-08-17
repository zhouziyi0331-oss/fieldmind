"""
乡村文化遗产商业可行性验证Skill - 基于大地遗产方法论
Rural Cultural Heritage Business Feasibility Verification Skill

核心理念：以运营思维贯穿始终，将文化遗产从"保护对象"转化为"可被验证的商业模式"
核心立场（防伪反假）：不做符号贴贴伪包装——文化符号贴贴、任何村都能做的通用包。
所有包装必须从文化整体分析中生长出来，经得起商业验证

应用场景：乡村文化遗产地整体商业开发、旅游项目前可行性研判、子项文化空间的商业化升级
核心输出：一份包含价值判断、商业机会、产品体系、财务测算和风险预案的《商业可行性验证报告》

方法论来源：大地遗产（大地风景文旅集团文化遗产方法）——三大挖掘方向、三大转化模式、四大核心理念、EPCO模式
"""

from typing import Dict, List
from dataclasses import dataclass
from .skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords


# Skill定义元数据
SKILL_DEFINITION = {
    "skill_id": "business_feasibility",
    "skill_name": "乡村文化遗产商业可行性验证",
    "description": "基于大地遗产方法论的文化遗产商业可行性验证，包含资源扫描、价值判断、机会识别、概念方案、可行性验证、风险评估全流程",
    "category": "专业方法",
    "version": "2.0.0",
    "dimensions": [
        "resource_scan_context",      # 现场扫描-资源本底与在地语境
        "value_opportunity",          # 价值判断与机会识别
        "concept_product",            # 概念方案与产品体系
        "feasibility_verification"    # 六维可行性验证（资源/需求/供给/独特/规模/利益）
    ]
}


class BusinessFeasibilitySkill(SkillBase):
    """乡村文化遗产商业可行性验证技能"""

    @property
    def skill_id(self) -> str:
        return "business_feasibility"

    @property
    def skill_name(self) -> str:
        return "乡村文化遗产商业可行性验证"

    @property
    def skill_description(self) -> str:
        return "基于大地遗产方法论的文化遗产商业可行性验证，包含资源扫描、价值判断、机会识别、概念方案、可行性验证、风险评估全流程"

    def _initialize_dimensions(self) -> None:
        """初始化商业可行性验证的四个核心维度"""
        self.dimensions = {
            'resource_scan_context': DimensionDefinition(
                dimension_id='resource_scan_context',
                dimension_name='现场扫描-资源本底与在地语境',
                description='三维度资源地图（物质遗存、非物质遗存、自然基底）+ 社区利益相关方调研 + 基础设施与市场可达性 + 政策与产权基础',
                keywords=[
                    '古建筑', '古道', '古树', '传统村落', '文物', '遗址',
                    '民俗', '手艺', '仪式', '传说', '方言', '谚语', '传承人',
                    '山水格局', '生态', '景观', '梯田', '溪流',
                    '人口结构', '外流', '返乡', '社区', '村民', '意愿', '认知',
                    '交通', '距离', '网络', '知名度', '周边景区',
                    '保护级别', '用地政策', '宅基地', '闲置房屋', '产权'
                ],
                example_sentences=[
                    '村里保存着明清时期的祠堂和民居，古建筑群保存完整，是省级文保单位。',
                    '当地有600年历史的稻作文化，插秧节等传统节庆保留至今，传承人健在。',
                    '山水格局优美，森林覆盖率高，溪流清澈，四季分明，适合发展生态旅游。',
                    '常住人口以老人为主，年轻人外出打工，但部分返乡青年有创业意愿。',
                    '距离最近的城市车程1小时，高速出口10公里，交通便利适合周末游。',
                    '村内有闲置古建筑可改造，但涉及文物保护审批，改造需遵守严格规范。',
                    '村民对文化遗产有认知和自豪感，愿意参与旅游项目，但担心收益分配。',
                    '周边已有几个成熟古镇景区，存在竞争，需要差异化定位找到独特价值。'
                ],
                vector=None
            ),

            'value_opportunity': DimensionDefinition(
                dimension_id='value_opportunity',
                dimension_name='价值判断与机会识别',
                description='遗产价值重新发现（故事性、体验性、稀缺性、延展性）+ 商业适配性评分 + 九大商业机会图谱识别 + 机会优先级矩阵',
                keywords=[
                    '故事', '传说', '历史', '情感共鸣', '传播力',
                    '体验', '参与', '沉浸', '互动', '记忆点',
                    '独特', '唯一', '稀缺', '不可复制', '垄断',
                    'IP', '衍生', '产品线', '延展',
                    '文化空间', '研学', '美食', '节庆', '数字内容', '场景餐饮', '民宿', '文创产品', '社群会员',
                    '适配性', '转化', '付费点', '商业模式', '运营者',
                    '旗舰项目', '战略项目', '现金牛', '基础配套'
                ],
                example_sentences=[
                    '这个传说有强烈的情感共鸣点，可以讲出打动人心的文化故事，传播潜力大。',
                    '游客能在这里获得独特体验，跟着老农插秧、学古法制作米酒，参与感强记忆深刻。',
                    '这种活态传承的稻作文化在周边独一无二，具有稀缺性和不可复制性。',
                    '可以衍生出研学课程、节庆IP、文创产品等完整产品矩阵，延展空间大。',
                    '识别出九类商业机会：文化空间运营（祠堂书院）、深度研学产品、在地美食开发、节庆活动策划、数字内容生产、场景餐饮、主题民宿群、文化产品体系、社群会员运营。',
                    '祠堂改造成文化空间，既彰显文化价值又有高商业可行性，列为旗舰项目优先推进。',
                    '美食开发虽然文化价值中等，但商业可行性高，可快速产生现金流支持其他项目。',
                    '数字内容生产是战略项目，高文化价值但商业化需时间，寻求专项资金支持长期培育。'
                ],
                vector=None
            ),

            'concept_product': DimensionDefinition(
                dimension_id='concept_product',
                dimension_name='概念方案与产品体系',
                description='第一重门：砍掉伪包装（符号贴贴/无付费点/一次性活动/伪在地/自嗨/超纲）+ 要素完整性筛查（毗邻/载体/付费点/运营者）+ 两个破局思维应用 + 产品概念设计 + 最小验证实验',
                keywords=[
                    '毗邻', '载体', '付费点', '运营者', '要素完整',
                    '时间破局', '空间破局', '角色破局', '组合破局', '反向破局',
                    '日常化', '功能化', 'NPC化', '跨界融合',
                    '价值主张', '体验流程', '文化解码', '收入模式',
                    'MVP', '最小可行产品', '种子用户', '付费转化', '复购', '转介绍',
                    '预售', '试课', '众筹', '反响', '迭代'
                ],
                example_sentences=[
                    '这个方案毗邻明确（600年稻作）、载体清晰（稻田+农户庭院）、付费点具体（家庭研学）、运营者可行（合作社+返乡青年），要素完整通过筛查。',
                    '应用时间破局：将一年一次的插秧节转化为日常可体验，春耕时节天天都能下田插秧。',
                    '应用角色破局：让游客不只是旁观者，而是成为农户带教的徒弟，NPC化深度参与。',
                    '应用组合破局：稻作文化 × 下午茶场景，稻田餐桌体验，传统与现代消费场景融合。',
                    '价值主张：给都市家庭一个让孩子真正理解"粒粒皆辛苦"的沉浸式稻作研学。',
                    '体验流程设计：种子用户全程参与从插秧到收割到做成米饭的完整循环，建立情感连接。',
                    '收入模式：单次体验付费 + 年卡会员制 + 稻米订购 + 文创衍生，构建多层次收入。',
                    '最小验证实验：面向本地研学机构做20组家庭付费试课，测付费转化率与复购意愿，实测转化率达60%验证通过进入正式设计。'
                ],
                vector=None
            ),

            'feasibility_verification': DimensionDefinition(
                dimension_id='feasibility_verification',
                dimension_name='六维可行性验证',
                description='资源真实性（去伪存真）+ 需求真实性（真付费人群）+ 供给可行性（人材本链场）+ 价值独特性（壁垒在哪）+ 规模与持续（能赚钱活得久）+ 利益兼容（多方共赢）+ 市场验证 + 财务验证 + 运营验证 + 风险识别与对策',
                keywords=[
                    '真实依据', '历史证据', '去伪存真', '本土文化根基',
                    '付费人群', '购买理由', '支付意愿', '调研', '预售数据',
                    '技能', '人力', '材料', '成本', '供应链', '培训', '场地',
                    '壁垒', '复制难度', '本地独占', '护城河',
                    '收入', '利润', '投资回收期', '复购', '季节性', '可持续',
                    '社区受益', '保护红线', '环境承载', '利益分配', '共赢机制',
                    '市场容量', '竞争', '客源', '渠道',
                    '投资测算', '现金流', '盈亏平衡', 'ROI',
                    '运营团队', '经验', '营销', '标准化', '服务质量',
                    '政策风险', '市场风险', '运营风险', '文化风险', '资金风险', '自然风险',
                    '规避', '转移', '保险', '预案', '应急'
                ],
                example_sentences=[
                    '经查地方志和访谈传承人，600年稻作文化有扎实历史依据，不是符号拼贴，资源真实性验证通过。',
                    '调研显示城市家庭研学市场需求真实存在，愿意为高品质农耕体验支付300-500元/家庭，付费意愿明确。',
                    '本地有传承人和农户可培训成教练，稻田和农具齐备，供应链可行，但需解决淡季人力闲置问题。',
                    '活态稻作文化+宗族体系是本地独占资源，外地难以复制，价值独特性强形成天然壁垒。',
                    '测算年度营收可达80万，扣除成本净利润约30万，投资回收期3年，通过会员制解决季节性问题建立可持续模式。',
                    '农户直接受益参与分红，不违反文物保护规定，环境承载力评估合格，利益兼容性验证通过。',
                    '目标市场是省会城市1小时交通圈内的亲子家庭，市场容量约10万家庭，差异化定位避开周边古镇竞争。',
                    '启动资金50万（村集体20万+贷款30万），现金流预测前半年压力大需储备，盈亏平衡点在运营8个月时。',
                    '村支书有经商经验，组建年轻运营团队，与研学机构合作建立客源渠道，运营能力基本具备但需提升服务标准化。',
                    '识别六大风险：政策风险（用地审批）、市场风险（需求波动）、运营风险（人才流失）、文化风险（过度商业化）、资金风险（现金流断裂）、自然风险（气候灾害）。',
                    '对策矩阵：高风险采取规避/转移（购买保险、签长期协议），中风险采取缓解/对冲（多元经营、弹性用工），低风险采取接受/监控（建立预警、储备预案）。',
                    '最小验证实验结果：20组试课家庭，付费转化60%，复购意愿80%，NPS推荐值65%，验证通过进入正式实施。'
                ],
                vector=None
            )
        }

    def analyze(self, text: str) -> SkillResult:
        """
        分析田野文本中的乡村文化遗产商业可行性相关内容

        Args:
            text: 待分析的田野调查文本

        Returns:
            SkillResult: 包含各维度分析结果的对象
        """
        import time
        start_time = time.time()

        # 转换为SkillResult所需的格式
        dimensions_dict: Dict[str, List[AnalysisMatch]] = {}
        total_matches = 0
        all_confidences = []

        # 对每个维度进行语义检索
        for dim_id, dimension in self.dimensions.items():
            # 使用语义检索找到相关内容
            raw_matches = self.semantic_retrieve(
                text=text,
                dimension=dimension,
                threshold=0.65
            )

            # 将tuple转换为AnalysisMatch对象
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
                dimensions_dict[dim_id] = analysis_matches
                total_matches += len(analysis_matches)

        # 提取关键词
        keywords = extract_keywords(text, top_k=15)

        # 计算平均置信度
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        execution_time = time.time() - start_time

        return SkillResult(
            skill_id=self.skill_id,
            skill_name=self.skill_name,
            success=total_matches > 0,
            dimensions=dimensions_dict,
            total_matches=total_matches,
            avg_confidence=avg_confidence,
            keywords=keywords,
            execution_time=execution_time
        )
