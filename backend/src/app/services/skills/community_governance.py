"""
社区治理Skill - 真实可用的向量语义版本

理论框架: 基于社区治理理论和田野调查经验
分析维度: 权力结构、决策机制、矛盾调解、资源分配

特点:
1. 使用BGE向量进行语义检索，不是简单关键词匹配
2. 基于真实的社区治理理论框架
3. 能识别同义表达和语义相关内容
"""
import logging
from typing import Dict, Any, Optional

from app.services.skills.skill_base import (
    SkillBase,
    DimensionDefinition,
    SkillResult
)

logger = logging.getLogger(__name__)


class CommunityGovernanceSkill(SkillBase):
    """
    社区治理分析Skill

    理论基础:
    - 村民自治制度
    - 基层治理结构
    - 乡村权力网络
    - 集体资源管理
    """

    def __init__(self):
        """初始化社区治理skill"""
        super().__init__()

    @property
    def skill_id(self) -> str:
        return "community_governance"

    @property
    def skill_name(self) -> str:
        return "社区治理分析"

    @property
    def skill_description(self) -> str:
        return "基于社区治理理论，分析村庄的权力结构、决策机制、矛盾调解和资源分配模式"

    def _initialize_dimensions(self):
        """
        初始化四个核心维度

        每个维度包含:
        1. 理论定义
        2. 关键概念
        3. 真实的示例句子（用于构建语义向量）
        """
        self.dimensions = {
            'power_structure': DimensionDefinition(
                dimension_id='power_structure',
                dimension_name='权力结构',
                description='村庄权力分配格局、权威来源、领导体制与决策权力分布',
                keywords=[
                    '村委会', '党支部', '村支书', '村主任', '村长',
                    '村干部', '两委', '党员', '村民代表',
                    '族长', '宗族', '家族', '长辈', '威望',
                    '权力', '权威', '领导', '管理'
                ],
                example_sentences=[
                    '村党支部书记在村里具有最高的决策权力和权威',
                    '村委会主任负责村庄日常事务的管理和协调',
                    '村两委班子成员共同商议村里的重要事项',
                    '族长在宗族内部事务中拥有很大的话语权和影响力',
                    '村民代表大会是村级权力机构的重要组成部分',
                    '老党员在村民中享有较高的威望和信任',
                    '村干部的权力来源既有行政任命也有村民选举',
                    '家族长辈在村庄传统事务中具有决定性作用'
                ]
            ),

            'decision_making': DimensionDefinition(
                dimension_id='decision_making',
                dimension_name='决策机制',
                description='村庄集体决策的程序、方式、参与主体及民主化程度',
                keywords=[
                    '村民大会', '村民代表大会', '党员大会',
                    '投票', '选举', '表决', '举手',
                    '商议', '协商', '讨论', '征求意见',
                    '民主', '公开', '透明', '公示',
                    '决策', '决定', '通过', '批准'
                ],
                example_sentences=[
                    '村里的重大事项都要通过村民代表大会投票表决',
                    '村委会召集村民代表商议土地承包方案',
                    '村两委联席会议讨论并决定集体资产的使用',
                    '村务公开栏定期公示村级财务和重要决策',
                    '涉及村民切身利益的事项需要征求全体村民意见',
                    '党员大会对村干部候选人进行民主推荐',
                    '村庄建设规划经过多次协商会议才最终确定',
                    '村民通过举手表决的方式通过了新的村规民约'
                ]
            ),

            'conflict_resolution': DimensionDefinition(
                dimension_id='conflict_resolution',
                dimension_name='矛盾调解',
                description='村庄内部矛盾纠纷的调解机制、调解主体及处理效果',
                keywords=[
                    '纠纷', '矛盾', '冲突', '争议', '纷争',
                    '调解', '调解员', '调解委员会',
                    '协调', '化解', '处理', '解决',
                    '仲裁', '裁决', '评理', '说和',
                    '民事', '邻里', '家庭', '土地纠纷'
                ],
                example_sentences=[
                    '村调解委员会成功化解了两家人的土地边界纠纷',
                    '村干部出面协调邻里之间的矛盾和冲突',
                    '村里有专门的人民调解员负责处理民事纠纷',
                    '宗族长辈帮助调解家族内部的财产争议',
                    '通过多次调解和沟通，双方当事人达成和解',
                    '村支书亲自出面协调解决了集体资产分配的争议',
                    '村规民约规定了邻里纠纷的处理程序和调解方式',
                    '乡镇司法所配合村委会调解重大矛盾纠纷'
                ]
            ),

            'resource_allocation': DimensionDefinition(
                dimension_id='resource_allocation',
                dimension_name='资源分配',
                description='村庄集体资源、土地、资金、项目等的分配方式与管理机制',
                keywords=[
                    '土地', '承包地', '宅基地', '集体土地',
                    '分配', '分摊', '划分', '调整',
                    '补贴', '补偿', '分红', '收益',
                    '项目', '资金', '资源', '资产',
                    '集体', '公共', '共有', '村集体经济',
                    '承包', '租赁', '流转', '征用'
                ],
                example_sentences=[
                    '村集体土地按照人口平均分配给各家各户承包经营',
                    '征地补偿款由村委会统一管理并按规定分配给村民',
                    '村集体经济收益每年进行一次分红',
                    '扶贫项目资金的使用和分配要经过村民代表大会审议',
                    '宅基地的分配遵循一户一宅的原则和村规民约',
                    '村里的公共资源和设施由全体村民共同所有和使用',
                    '土地流转收益在村集体和农户之间合理分配',
                    '国家补贴资金按照耕地面积分配到各承包户'
                ]
            )
        }


# 全局单例函数（保持向后兼容）
_skill_instance = None


def get_skill() -> CommunityGovernanceSkill:
    """获取skill实例（单例模式）"""
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = CommunityGovernanceSkill()
    return _skill_instance


def analyze(content: str, metadata: dict = None) -> dict:
    """
    兼容旧接口的分析函数

    参数:
        content: 文本内容
        metadata: 元数据

    返回:
        分析结果字典（兼容旧格式）
    """
    try:
        skill = get_skill()
        result: SkillResult = skill.analyze(content, metadata)

        if not result.success:
            return None

        # 转换为旧格式（兼容现有代码）
        output = {
            "skill_name": result.skill_name,
            "dimensions": {}
        }

        for dim_id, matches in result.dimensions.items():
            dimension_def = skill.dimensions.get(dim_id)
            if dimension_def:
                output["dimensions"][dim_id] = {
                    "name": dimension_def.dimension_name,
                    "matched_count": len(matches),
                    "contexts": [match.sentence for match in matches[:3]],
                    # 新增字段（向量版本特有）
                    "avg_similarity": sum(m.similarity for m in matches) / len(matches),
                    "keywords_found": list(set(
                        kw for match in matches for kw in match.keywords_found
                    ))
                }

        return output

    except Exception as e:
        logger.error(f"社区治理分析失败: {e}")
        return None


# 导出skill定义（用于配置和展示）
def get_definition() -> Dict[str, Any]:
    """获取skill定义"""
    skill = get_skill()
    return skill.get_definition()
