"""
多村比较标准流程Skill - 田野调查中的跨村比较分析方法
Multi-Village Comparative Analysis SOP

类别：专业分析方法
应用场景：比较研究、区域调查、类型学分析
核心价值：识别共性与差异、发现影响因素、提炼典型模式
"""

from typing import Dict, List
from dataclasses import dataclass
from .skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords


# Skill定义元数据
SKILL_DEFINITION = {
    "skill_id": "multi_village_sop",
    "skill_name": "多村比较分析",
    "description": "基于向量语义的跨村比较研究标准流程，识别共性差异、影响因素和典型模式",
    "category": "专业方法",
    "version": "1.0.0",
    "dimensions": [
        "baseline_comparison",     # 基础对比
        "difference_analysis",     # 差异分析
        "factor_identification",   # 因素识别
        "pattern_extraction"       # 模式提炼
    ]
}


class MultiVillageSOPSkill(SkillBase):
    """多村比较分析技能"""

    @property
    def skill_id(self) -> str:
        return "multi_village_sop"

    @property
    def skill_name(self) -> str:
        return "多村比较分析"

    @property
    def skill_description(self) -> str:
        return "基于向量语义的跨村比较研究标准流程，识别共性差异、影响因素和典型模式"

    def _initialize_dimensions(self) -> None:
        """初始化多村比较的四个核心维度"""
        self.dimensions = {
            'baseline_comparison': DimensionDefinition(
                dimension_id='baseline_comparison',
                dimension_name='基础对比',
                description='对比不同村庄的基本情况：人口、地理、经济、基础设施等客观指标',
                keywords=[
                    '相比', '对比', '不同', '相同', '类似', '差不多',
                    '比A村', '比B村', '两个村', '几个村', '其他村',
                    '人口规模', '地理位置', '经济水平', '基础设施'
                ],
                example_sentences=[
                    'A村有500户2000多人，B村只有200户800多人，规模差距明显。',
                    '两个村都在山区，但A村靠近县城，交通便利，B村比较偏远。',
                    'A村人均收入3万元，B村只有1.5万元，经济水平相差一倍。',
                    '相比之下，A村的水电路网等基础设施完善，B村还比较落后。',
                    '几个村的主要产业都是种植业，但具体作物不太一样。',
                    'A村和B村的人口结构类似，都是老人小孩多，年轻人少。',
                    '调查的三个村地理环境不同，一个平原、一个丘陵、一个山区。',
                    '这两个村的历史渊源相似，都是明代移民后裔聚居地。'
                ]
            ),

            'difference_analysis': DimensionDefinition(
                dimension_id='difference_analysis',
                dimension_name='差异分析',
                description='深入分析村庄间的显著差异：发展路径、治理模式、文化特征、社会结构等',
                keywords=[
                    '差异', '不同', '区别', '相反', '相较', '反而', '但是',
                    '发展路径', '治理模式', '文化特征', '社会结构',
                    '更好', '更差', '领先', '落后', '先进', '传统'
                ],
                example_sentences=[
                    'A村走集体经济路线，B村主打个体经营，发展路径完全不同。',
                    '在治理模式上，A村村委会主导，B村则是宗族力量更强。',
                    'A村保留了很多传统习俗，B村受外来文化影响更深，更现代化。',
                    '社会结构差异明显：A村宗族观念强，B村流动人口多，更开放。',
                    'A村注重环境保护，发展生态旅游，B村则以工业为主，污染较重。',
                    '相比A村的团结互助，B村村民关系相对冷淡，各管各的。',
                    'A村干群关系融洽，村民信任村干部，B村矛盾比较突出。',
                    '教育观念上，A村重视子女教育，B村更倾向于早点出去打工。'
                ]
            ),

            'factor_identification': DimensionDefinition(
                dimension_id='factor_identification',
                dimension_name='因素识别',
                description='识别造成村庄差异的关键影响因素：地理条件、历史传统、政策支持、带头人等',
                keywords=[
                    '原因', '因素', '影响', '导致', '由于', '因为', '得益于',
                    '关键在于', '主要是', '归功于', '源于', '取决于',
                    '地理条件', '历史传统', '政策支持', '带头人', '资源禀赋'
                ],
                example_sentences=[
                    'A村发展好主要是因为有个能干的村支书，带领大家搞产业。',
                    '地理位置是关键因素，靠近景区的村旅游收入明显更高。',
                    'B村落后很大程度上源于交通不便，物资运输成本太高。',
                    '政策扶持力度不同，A村被列为示范村，得到大量项目资金。',
                    'A村有温泉资源，这个独特优势是其他村无法复制的。',
                    '历史文化底蕴深厚，古建筑多，为A村发展文旅提供了条件。',
                    '教育水平影响很大，A村大学生多，带回新理念新技术。',
                    '外出务工人员的反哺，给A村带来资金和见识，推动了发展。'
                ]
            ),

            'pattern_extraction': DimensionDefinition(
                dimension_id='pattern_extraction',
                dimension_name='模式提炼',
                description='提炼典型发展模式、成功经验或共性问题，形成可复制的规律性认识',
                keywords=[
                    '模式', '经验', '启示', '规律', '共性', '普遍', '典型',
                    '可复制', '可推广', '借鉴', '值得学习', '教训',
                    '成功模式', '发展路径', '治理经验', '问题模式'
                ],
                example_sentences=[
                    '几个发展好的村都有一个共性：都有强有力的村党支部领导。',
                    'A村的"党支部+合作社+农户"模式值得其他村借鉴。',
                    '调研发现，成功村庄普遍重视产业发展，不能只靠补贴过日子。',
                    '这种"公司+农户"的模式在多个村推广效果都不错，可复制性强。',
                    '教训是深刻的：几个失败的项目都是因为没有尊重村民意愿。',
                    '从比较中提炼出规律：资源禀赋固然重要，但人的因素更关键。',
                    '这几个村的实践表明，生态保护和经济发展可以兼顾双赢。',
                    '典型经验是：先解决基础设施，再谈产业发展，顺序不能乱。'
                ]
            )
        }

    def analyze(self, text: str) -> SkillResult:
        """
        分析田野文本中的多村比较内容

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
            matches = self.semantic_retrieve(
                text=text,
                dimension=dimension,
                threshold=0.65
            )

            # 构建AnalysisMatch对象列表
            analysis_matches = []
            for sentence, score, context in matches:
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
