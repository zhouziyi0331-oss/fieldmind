"""
神圣记忆Skill - 基于景军《神圣记忆》理论框架的社会记忆分析
使用真实的向量语义分析，基于BGE模型

核心理念：将乡村文化遗产视为"活的社会记忆载体"，通过识别、激活和转化集体记忆，
实现文化遗产的价值发现与社区文化复兴

基于《神圣记忆》钥匙：社会记忆视角下的乡村文化遗产发展指导 Skill
"""
import logging
from typing import Dict, List, Optional, Any
import numpy as np

from .skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords

logger = logging.getLogger(__name__)


class SacredMemorySkill(SkillBase):
    """
    神圣记忆理论框架分析Skill

    基于景军《神圣记忆》，从社会记忆学角度分析乡村文化遗产中的集体记忆

    核心6维度（景军的6类社会记忆）：
    1. historical_memory - 历史记忆：重大历史事件的群体性记忆，村落起源、建村传说
    2. trauma_memory - 创伤/磨难记忆：灾难、迫害、迁移的集体创伤记忆
    3. ritual_memory - 仪式记忆：通过仪式行为传承和再现的记忆（庙会、祭祀、人生礼仪）
    4. genealogy_memory - 谱系记忆：通过血缘谱系维系的家族/宗教记忆
    5. symbol_memory - 文化象征记忆：凝结于特定文化符号上的集体记忆（庙宇、祠堂、图腾）
    6. identity_memory - 身份认同记忆：通过记忆定义"我们是谁"、划分"我们"与"他们"

    使用向量语义检索，识别田野文本中的社会记忆类型与特征
    """

    @property
    def skill_id(self) -> str:
        return "sacred_memory"

    @property
    def skill_name(self) -> str:
        return "神圣记忆理论分析（社会记忆6维度）"

    @property
    def skill_description(self) -> str:
        return "基于景军《神圣记忆》理论框架的社会记忆分析，识别历史记忆、创伤记忆、仪式记忆、谱系记忆、象征记忆、身份认同等6个核心维度"

    def _initialize_dimensions(self) -> None:
        """初始化神圣记忆理论的6个核心维度"""
        self.dimensions = {
            # 维度1：历史记忆
            'historical_memory': DimensionDefinition(
                dimension_id='historical_memory',
                dimension_name='历史记忆',
                description='社群共享的关于过去的集体性认知，包括村落起源、建村传说、重大历史事件、辉煌过往等',
                keywords=[
                    '历史记忆', '村史', '起源', '建村', '传说',
                    '祖先', '开基祖', '始祖', '来历', '由来',
                    '历史事件', '过去', '从前', '早年间', '当年',
                    '老辈人说', '听说', '传下来', '代代相传',
                    '历史故事', '村庄历史', '家族历史', '宗族史',
                    '名人', '先贤', '功绩', '辉煌', '荣耀',
                    '古迹', '遗址', '文物', '历史痕迹'
                ],
                example_sentences=[
                    '据老人讲，我们村是明朝时从山西迁来的',
                    '村里传说开基祖是跟随朱元璋打天下的功臣',
                    '祠堂里记载着家族几百年的历史',
                    '村名的由来有一个古老的传说',
                    '这座庙是清朝时建的，香火一直很旺',
                    '村里出过进士，匾额现在还挂着',
                    '老人经常讲当年村里如何繁荣',
                    '碑文上记录了村庄的重要历史'
                ]
            ),

            # 维度2：创伤/磨难记忆
            'trauma_memory': DimensionDefinition(
                dimension_id='trauma_memory',
                dimension_name='创伤/磨难记忆',
                description='对灾难、迫害、损失的集体创伤记忆，包括战争、饥荒、迁移、政治运动等痛苦经历',
                keywords=[
                    '创伤', '磨难', '灾难', '苦难', '受苦',
                    '战争', '逃难', '流离失所', '颠沛流离',
                    '饥荒', '灾荒', '挨饿', '饿死人', '困难时期',
                    '迁徙', '移民', '被迫离开', '背井离乡',
                    '文革', '运动', '批斗', '迫害', '受难',
                    '洪水', '地震', '瘟疫', '天灾', '人祸',
                    '失去', '死亡', '牺牲', '遇难', '悲剧',
                    '沉默', '不愿提', '不敢说', '禁忌', '伤心事'
                ],
                example_sentences=[
                    '三年困难时期村里饿死了很多人',
                    '老人不愿意谈文革时期的事情',
                    '祖辈是为了逃避战乱才迁到这里的',
                    '那次洪水淹没了半个村子，损失惨重',
                    '村里的古建筑在运动中被毁了',
                    '提起那段历史，老人们都沉默了',
                    '家族中有人在战争中牺牲',
                    '这些痛苦的记忆很少有人愿意讲'
                ]
            ),

            # 维度3：仪式记忆
            'ritual_memory': DimensionDefinition(
                dimension_id='ritual_memory',
                dimension_name='仪式记忆',
                description='通过仪式行为传承和再现的记忆，包括庙会、祭祀、婚丧嫁娶等仪式活动',
                keywords=[
                    '仪式', '庙会', '祭祀', '祭祖', '拜神',
                    '节日', '传统节日', '民俗活动', '庆典',
                    '婚礼', '丧礼', '满月', '成年礼', '人生礼仪',
                    '祈福', '还愿', '求签', '上香', '供奉',
                    '仪式规矩', '礼仪', '程序', '步骤', '讲究',
                    '传统做法', '老规矩', '祖辈传下来的',
                    '神圣', '庄严', '肃穆', '虔诚', '敬畏',
                    '参与', '热闹', '聚会', '集体活动'
                ],
                example_sentences=[
                    '每年清明节全村人都会到祠堂祭祖',
                    '庙会时整个村子都很热闹，四乡八村的人都来',
                    '婚礼必须按传统仪式来，不能省略',
                    '正月十五的舞龙活动已经传承了几百年',
                    '祭祀仪式有严格的程序，不能出错',
                    '这些传统仪式让大家有归属感',
                    '老人特别重视这些仪式，年轻人参与得少了',
                    '通过这些活动，村民之间的关系更紧密'
                ]
            ),

            # 维度4：谱系记忆
            'genealogy_memory': DimensionDefinition(
                dimension_id='genealogy_memory',
                dimension_name='谱系记忆',
                description='通过血缘谱系系统维系的家族/宗教记忆，包括家谱、族谱、辈分、祖先信息等',
                keywords=[
                    '家谱', '族谱', '谱系', '家族树', '世系',
                    '辈分', '排行', '字辈', '家族字号',
                    '祖先', '先祖', '列祖列宗', '祖宗',
                    '血统', '血脉', '血缘', '宗亲', '本家',
                    '修谱', '续谱', '谱牒', '族谱记载',
                    '祖坟', '墓地', '安葬', '祖茔',
                    '寻根', '认祖', '归宗', '认亲',
                    '家族故事', '先人事迹', '祖训', '家训'
                ],
                example_sentences=[
                    '家谱详细记录了二十代祖先的名字',
                    '村里最近在组织修订族谱',
                    '按辈分排序，他应该叫我叔叔',
                    '族谱中记载了家族的迁徙历史',
                    '祠堂里供奉着历代祖先的牌位',
                    '家谱是家族最重要的传家宝',
                    '每个人的名字都按字辈排列',
                    '通过族谱可以找到远房亲戚'
                ]
            ),

            # 维度5：文化象征记忆
            'symbol_memory': DimensionDefinition(
                dimension_id='symbol_memory',
                dimension_name='文化象征记忆',
                description='凝结于特定文化符号上的集体记忆，包括庙宇、祠堂、古树、图腾、标志物等',
                keywords=[
                    '庙宇', '祠堂', '神庙', '寺庙', '宗祠',
                    '古树', '老树', '神树', '风水树',
                    '牌坊', '碑刻', '石碑', '纪念碑',
                    '图腾', '神像', '塑像', '雕像',
                    '标志', '象征', '符号', '代表',
                    '老建筑', '古宅', '老房子', '祖屋',
                    '遗迹', '古迹', '文物', '宝贝',
                    '神圣', '崇拜', '敬畏', '象征意义'
                ],
                example_sentences=[
                    '村口的大榕树有三百年历史，是村里的标志',
                    '祠堂是全村人的精神寄托',
                    '那座庙是村民信仰的中心',
                    '老人说这棵树不能砍，有神灵保护',
                    '牌坊见证了家族的荣耀',
                    '这些老建筑承载着村庄的记忆',
                    '村里的文物让大家很自豪',
                    '神像在村民心中有特殊地位'
                ]
            ),

            # 维度6：身份认同记忆
            'identity_memory': DimensionDefinition(
                dimension_id='identity_memory',
                dimension_name='身份认同记忆',
                description='通过记忆定义"我们是谁"、划分"我们"与"他们"的边界，形成群体认同',
                keywords=[
                    '我们', '我们村', '我们家族', '本村人',
                    '外人', '外地人', '他们', '外来者',
                    '认同', '归属', '身份', '自豪', '骄傲',
                    '传统', '特色', '独特', '与众不同',
                    '文化', '风俗', '习惯', '我们的方式',
                    '根', '根源', '来历', '血统', '出身',
                    '团结', '凝聚', '向心力', '集体',
                    '自卑', '不自信', '羞于提及', '不愿说'
                ],
                example_sentences=[
                    '我们村的人团结，外人很难融入',
                    '村民对本村的文化很自豪',
                    '这是我们村独有的传统',
                    '我们跟邻村的习俗不一样',
                    '本村人互相帮助，像一家人',
                    '年轻人觉得村里的传统土气，不愿提起',
                    '通过文化活动，大家的认同感增强了',
                    '我们村的历史让人自豪'
                ]
            )
        }

    def analyze(self, text_content: str, metadata: Optional[Dict[str, Any]] = None) -> SkillResult:
        """
        执行神圣记忆理论分析

        Args:
            text_content: 田野调查文本内容
            metadata: 可选的元数据信息

        Returns:
            SkillResult对象，包含所有维度的分析结果
        """
        import time
        start_time = time.time()

        try:
            logger.info("开始神圣记忆理论分析")

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
                        context='',
                        keywords_found=[]
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

            logger.info(f"神圣记忆理论分析完成: {total_matches} 个匹配, 平均置信度 {avg_confidence:.3f}")

            return result

        except Exception as e:
            logger.error(f"神圣记忆理论分析失败: {e}", exc_info=True)
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
        skill = SacredMemorySkill()
        result = skill.analyze(content, metadata)
        # 转换为旧格式
        return {
            'skill_name': result.skill_name,
            'total_matches': result.total_matches,
            'avg_confidence': result.avg_confidence,
            'dimensions': {
                dim_id: [
                    {
                        'sentence': match.sentence,
                        'similarity': match.similarity
                    }
                    for match in matches
                ]
                for dim_id, matches in result.dimensions.items()
            }
        }
    except Exception as e:
        logger.error(f"神圣记忆理论分析失败: {e}")
        return None


# Skill定义（用于注册和发现）
SKILL_DEFINITION = {
    "id": "sacred_memory",
    "name": "神圣记忆理论分析（社会记忆6维度）",
    "description": "基于景军《神圣记忆》理论框架的社会记忆分析，从记忆视角理解乡村文化遗产",
    "version": "1.0",
    "author": "景军",
    "category": "学术理论",
    "dimensions": {
        "historical_memory": {
            "name": "历史记忆",
            "description": "重大历史事件的群体性记忆，村落起源、建村传说"
        },
        "trauma_memory": {
            "name": "创伤/磨难记忆",
            "description": "灾难、迫害、迁移的集体创伤记忆"
        },
        "ritual_memory": {
            "name": "仪式记忆",
            "description": "通过仪式行为传承和再现的记忆"
        },
        "genealogy_memory": {
            "name": "谱系记忆",
            "description": "通过血缘谱系维系的家族/宗教记忆"
        },
        "symbol_memory": {
            "name": "文化象征记忆",
            "description": "凝结于特定文化符号上的集体记忆"
        },
        "identity_memory": {
            "name": "身份认同记忆",
            "description": "通过记忆定义'我们是谁'、划分边界"
        }
    }
}
