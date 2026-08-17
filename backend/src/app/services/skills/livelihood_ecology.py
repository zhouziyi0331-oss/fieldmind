"""
生计生态Skill - 分析生计方式、收入来源与生态环境
使用真实的向量语义分析，基于BGE模型
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

from .skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords

logger = logging.getLogger(__name__)


class LivelihoodEcologySkill(SkillBase):
    """
    生计生态分析Skill

    核心维度：
    1. income_sources - 收入来源：打工、种植、养殖、经营等多元化收入结构
    2. agricultural_practice - 农业实践：耕作方式、种植结构、农业技术应用
    3. ecological_impact - 生态影响：环境保护、生态退耕、污染治理
    4. resource_dependence - 资源依赖：对土地、水资源、山林等自然资源的依赖程度

    使用向量语义检索，能够识别同义表达和语义相关内容
    """

    @property
    def skill_id(self) -> str:
        return "livelihood_ecology"

    @property
    def skill_name(self) -> str:
        return "生计生态分析"

    @property
    def skill_description(self) -> str:
        return "基于向量语义的生计方式、收入来源与生态环境关系分析"

    def _initialize_dimensions(self) -> None:
        """初始化生计生态分析的四个核心维度"""
        self.dimensions = {
            'income_sources': DimensionDefinition(
                dimension_id='income_sources',
                dimension_name='收入来源',
                description='家庭收入的主要来源和构成，包括务工、农业、养殖、经营等多元化收入结构',
                keywords=[
                    '打工', '务工', '外出', '工资', '种植', '养殖',
                    '经营', '生意', '收入', '挣钱', '补贴', '分红'
                ],
                example_sentences=[
                    '村里的主要收入来源是外出打工，年轻人大多在城里务工',
                    '家庭经济主要靠种植玉米和养殖生猪，每年收入三四万元',
                    '村民通过经营小卖部、开农家乐等方式增加收入',
                    '除了务农收入，还有土地流转的租金和各种政策补贴',
                    '青壮年劳动力外出打工，老人在家种地养家禽',
                    '村集体经济分红成为村民的一项重要收入',
                    '农闲时节外出务工，农忙时回村帮忙收割',
                    '依靠特色种植和乡村旅游，家庭年收入显著提高'
                ]
            ),
            'agricultural_practice': DimensionDefinition(
                dimension_id='agricultural_practice',
                dimension_name='农业实践',
                description='农业生产的具体实践，包括耕作方式、种植结构、农业技术、灌溉施肥等',
                keywords=[
                    '耕地', '种植', '收成', '庄稼', '农作物', '播种',
                    '收割', '灌溉', '施肥', '农药', '机械化', '温室'
                ],
                example_sentences=[
                    '村里的耕地主要种植小麦和玉米，采用轮作的方式保持地力',
                    '通过滴灌技术和科学施肥，农作物的产量明显提高',
                    '从传统人工收割到机械化作业，大大减轻了农民的劳动强度',
                    '建设温室大棚种植反季节蔬菜，提高了土地的产出效益',
                    '农业合作社统一购买种子农药，降低了生产成本',
                    '推广节水灌溉技术，提高了水资源的利用效率',
                    '春季播种时节，村民们忙着整地、选种、下种',
                    '秋收季节，联合收割机在田间来回穿梭收割庄稼'
                ]
            ),
            'ecological_impact': DimensionDefinition(
                dimension_id='ecological_impact',
                dimension_name='生态影响',
                description='生产生活对生态环境的影响，包括环境保护、污染治理、生态修复等',
                keywords=[
                    '环境', '污染', '生态', '水源', '森林', '保护',
                    '退耕', '绿化', '治理', '垃圾', '排放', '修复'
                ],
                example_sentences=[
                    '实施退耕还林政策后，山上的植被覆盖率明显提高',
                    '村里建立了垃圾分类处理系统，改善了人居环境',
                    '禁止向河道排放污水，保护了下游的饮用水源',
                    '生态移民搬迁后，原来的居住区自然恢复成林地',
                    '推广有机肥替代化肥，减少了农业面源污染',
                    '村庄周围进行绿化美化，种植了大量树木和花草',
                    '禁止在保护区内砍伐林木，森林资源得到有效保护',
                    '建设人工湿地处理生活污水，实现了生态化治理'
                ]
            ),
            'resource_dependence': DimensionDefinition(
                dimension_id='resource_dependence',
                dimension_name='资源依赖',
                description='对自然资源的依赖程度和利用方式，包括土地、水、森林等资源的获取和使用',
                keywords=[
                    '山林', '水资源', '土地', '自然', '资源', '采集',
                    '利用', '依赖', '承包', '流转', '林地', '水井'
                ],
                example_sentences=[
                    '村民的生计高度依赖土地资源，人均耕地面积直接影响收入',
                    '山区村庄靠山吃山，林下经济和山货采集是重要的收入补充',
                    '水资源短缺制约了农业发展，灌溉主要依靠打井取水',
                    '土地流转后，农民从土地的直接经营者变为租金收益者',
                    '集体林地承包给村民，通过林木采伐获得经济收益',
                    '村庄依托丰富的水资源发展水产养殖和稻田种植',
                    '山区自然资源丰富，村民采集野菜、药材贴补家用',
                    '土地资源有限，村民通过精耕细作提高单位面积产出'
                ]
            )
        }

    def analyze(self, text_content: str, metadata: Optional[Dict[str, Any]] = None) -> SkillResult:
        """
        执行生计生态分析

        Args:
            text_content: 田野调查文本内容
            metadata: 可选的元数据信息

        Returns:
            SkillResult对象，包含所有维度的分析结果
        """
        import time
        start_time = time.time()

        try:
            logger.info("开始生计生态向量语义分析")

            dimensions_result = {}
            total_matches = 0
            all_confidences = []

            # 对每个维度进行语义检索
            for dim_id, dimension in self.dimensions.items():
                logger.debug(f"分析维度: {dimension.dimension_name}")

                # 使用语义检索找到相关内容
                matches = self.semantic_retrieve(
                    text=text_content,
                    dimension=dimension,
                    threshold=0.65  # 相似度阈值
                )

                # 构建AnalysisMatch对象列表
                analysis_matches = []
                for sentence, score, aspect in matches:
                    match_obj = AnalysisMatch(
                        dimension_id=dim_id,
                        dimension_name=dimension.dimension_name,
                        sentence=sentence,
                        similarity=float(score),
                        context='',  # 暂时为空，可以后续扩展
                        keywords_found=[]  # 暂时为空，可以后续扩展
                    )
                    analysis_matches.append(match_obj)
                    all_confidences.append(float(score))

                dimensions_result[dim_id] = analysis_matches
                total_matches += len(matches)

                logger.debug(f"维度 {dimension.dimension_name} 找到 {len(matches)} 个匹配")

            # 计算整体置信度
            avg_confidence = float(np.mean(all_confidences)) if all_confidences else 0.0

            # 提取关键词
            keywords = extract_keywords(text_content, top_k=15)

            # 计算执行时间
            execution_time = time.time() - start_time

            result = SkillResult(
                skill_id=self.skill_id,
                skill_name=self.skill_name,
                success=True,
                dimensions=dimensions_result,
                total_matches=total_matches,
                avg_confidence=avg_confidence,
                keywords=keywords,
                execution_time=execution_time,
                metadata=metadata or {}
            )

            logger.info(f"生计生态分析完成: {total_matches} 个匹配, 平均置信度 {avg_confidence:.3f}")

            return result

        except Exception as e:
            logger.error(f"生计生态分析失败: {e}", exc_info=True)
            raise


# 向后兼容的函数接口
def analyze(content: str, metadata: dict = None) -> dict:
    """
    向后兼容的分析函数

    Args:
        content: 文本内容
        metadata: 元数据

    Returns:
        分析结果字典
    """
    try:
        skill = LivelihoodEcologySkill()
        result = skill.analyze(content, metadata)
        return result.to_dict()
    except Exception as e:
        logger.error(f"生计生态分析失败: {e}")
        return None


# Skill定义（用于注册和发现）
SKILL_DEFINITION = {
    "id": "livelihood_ecology",
    "name": "生计生态分析",
    "description": "基于向量语义的生计方式、收入来源与生态环境关系分析",
    "version": "2.0",
    "dimensions": {
        "income_sources": {
            "name": "收入来源",
            "description": "家庭收入的主要来源和构成"
        },
        "agricultural_practice": {
            "name": "农业实践",
            "description": "农业生产的具体实践方式"
        },
        "ecological_impact": {
            "name": "生态影响",
            "description": "生产生活对生态环境的影响"
        },
        "resource_dependence": {
            "name": "资源依赖",
            "description": "对自然资源的依赖程度和利用方式"
        }
    }
}
