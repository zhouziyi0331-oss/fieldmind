"""
乡土中国Skill - 基于费孝通《乡土中国》理论框架的田野调查分析
使用真实的向量语义分析，基于BGE模型

完整8维度版本，基于《乡土中国》实践钥匙：现场调查与乡村文化遗产发展指导Skill
核心理念："用乡土中国的眼看乡村，而不是用城市的眼看乡村"
"""
import logging
from typing import Dict, List, Optional, Any
import numpy as np

from .skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keywords

logger = logging.getLogger(__name__)


class XiangtuChinaSkill(SkillBase):
    """
    乡土中国理论框架分析Skill

    基于费孝通先生的经典著作《乡土中国》，从社会学角度分析中国乡村社会结构特征

    核心8维度（费孝通的8把"钥匙"）：
    1. xiangtu_nature - 乡土本色：熟人社会，面对面社群
    2. differential_mode - 差序格局：以己为中心的水波式人际关系网络
    3. ritual_order - 礼治秩序（含"无讼"）：礼治而非法治，调解优先
    4. family_gender - 家族与男女有别：家族为基本单位，性别分工
    5. elder_rule - 长老统治：长者权威，经验为王
    6. kinship_locality - 血缘与地缘：宗族聚居，落叶归根
    7. literacy_communication - 文字与乡（沟通钥匙）：口头传播，面对面沟通为主
    8. cultural_consciousness - 文化自觉（转化钥匙）：各美其美，美人之美，美美与共

    使用向量语义检索，能够识别理论概念在田野文本中的具体体现
    """

    @property
    def skill_id(self) -> str:
        return "xiangtu_china"

    @property
    def skill_name(self) -> str:
        return "乡土中国理论分析（完整8维度版）"

    @property
    def skill_description(self) -> str:
        return "基于费孝通《乡土中国》完整理论框架的社会学分析，识别乡土本色、差序格局、礼治秩序、长老统治、文化自觉等8个核心维度"

    def _initialize_dimensions(self) -> None:
        """初始化乡土中国理论的8个核心维度"""
        self.dimensions = {
            # 维度1：乡土本色（熟人社会）
            'xiangtu_nature': DimensionDefinition(
                dimension_id='xiangtu_nature',
                dimension_name='乡土本色',
                description='从基层上看去，中国社会是乡土性的——离不开泥土，不流动性，生于斯、长于斯、死于斯的熟人社会，面对面的社群',
                keywords=[
                    '熟人社会', '面对面', '乡土性', '世代定居', '不流动',
                    '土地依赖', '农业社会', '稳定性', '地方性知识',
                    '生于斯长于斯', '祖祖辈辈', '老家', '根在这里',
                    '从小到大', '认识所有人', '抬头不见低头见',
                    '邻里关系', '街坊四邻', '村里人都熟', '知根知底'
                ],
                example_sentences=[
                    '村里的人基本都认识，从小一起长大的',
                    '祖祖辈辈都生活在这里，离不开这片土地',
                    '大家都是熟人，抬头不见低头见',
                    '在村里办事不需要合同，大家都信得过',
                    '外来的人很少，本村人很少搬走',
                    '几代人都葬在村后的山上',
                    '村里的年轻人出去打工，但最终还是要回来的',
                    '老人说这里的每块地都有故事'
                ]
            ),

            # 维度2：差序格局
            'differential_mode': DimensionDefinition(
                dimension_id='differential_mode',
                dimension_name='差序格局',
                description='以"己"为中心，依亲疏远近如水波推衍的人际结构，与西方"团体格局"的清晰边界截然不同。亲疏有别，关系网络决定资源分配',
                keywords=[
                    '差序格局', '关系网', '亲疏有别', '人情',
                    '面子', '圈子', '自己人', '外人',
                    '亲戚关系', '族人', '本家', '远房亲戚',
                    '托关系', '找熟人', '走后门', '人脉',
                    '帮忙', '互惠', '欠人情', '还人情',
                    '村两委', '有威望的人', '说话管用', '核心人物'
                ],
                example_sentences=[
                    '村里办事要找对人，关键看你认识谁',
                    '这个项目能不能做，要看村里几个主要人物的态度',
                    '他家在村里说话有分量，是大姓',
                    '外来投资者很难融入村里的关系网',
                    '村民之间的合作主要靠亲戚关系',
                    '决策时会先问几个长者和大户的意见',
                    '红白喜事能看出谁在村里的人脉广',
                    '项目推进需要一层层做工作，从核心圈向外扩散'
                ]
            ),

            # 维度3：礼治秩序（含"无讼"）
            'ritual_order': DimensionDefinition(
                dimension_id='ritual_order',
                dimension_name='礼治秩序（含"无讼"）',
                description='乡土社会靠"礼治"而非法治——靠传统、靠道德约束，纠纷解决依赖长者权威与乡规民约，打官司被视为不光彩，"无讼"是基本社会特征',
                keywords=[
                    '礼治', '乡规民约', '村规', '传统规矩',
                    '无讼', '不打官司', '内部解决', '调解',
                    '长者权威', '乡贤', '德高望重', '说理',
                    '道德约束', '舆论压力', '丢脸', '不体面',
                    '村民自治', '议事会', '协商', '共识',
                    '祖辈传下来的规矩', '老理儿', '祖训', '族规'
                ],
                example_sentences=[
                    '村里有纠纷一般不会去法院，都是内部调解',
                    '村规民约规定了很多行为规范',
                    '遇到矛盾会请村里德高望重的老人来说理',
                    '打官司在村里被认为是很丢脸的事',
                    '很多事情靠口头约定和信任，不签合同',
                    '村民大会商议重要事项，少数服从多数',
                    '长辈的话在村里很有权威性',
                    '违反村规会受到舆论谴责，在村里抬不起头'
                ]
            ),

            # 维度4：家族与男女有别
            'family_gender': DimensionDefinition(
                dimension_id='family_gender',
                dimension_name='家族与男女有别',
                description='乡土社会的基本单位是家族而非个人，血缘是维系社会网络的核心，家族承担政治、经济、宗教多重功能，男女在社会分工上有别',
                keywords=[
                    '家族', '宗族', '大家族', '族长',
                    '祠堂', '家谱', '祖先崇拜', '祭祖',
                    '血缘', '同姓', '本家', '房支',
                    '男主外女主内', '性别分工', '妇女地位',
                    '家族企业', '家族议事', '族规家法',
                    '传宗接代', '重男轻女', '继承权',
                    '家族利益', '光宗耀祖', '家族名誉'
                ],
                example_sentences=[
                    '村里最大的几个姓氏各有祠堂',
                    '家族决策由族长和几个长辈共同商定',
                    '清明和春节都要集体祭祖',
                    '村里的土地和资源按家族分配',
                    '妇女主要负责家务和照顾老人孩子',
                    '公共事务中很少见到女性参与决策',
                    '大家族在村里很有影响力',
                    '家族内部的事情优先由家族内部解决'
                ]
            ),

            # 维度5：长老统治
            'elder_rule': DimensionDefinition(
                dimension_id='elder_rule',
                dimension_name='长老统治',
                description='乡土社会是"长老统治"的社会——年长者在文化传承与秩序维护中拥有权威。权威源于经验，在变化缓慢的乡土社会，老人的经验具有直接的指导价值',
                keywords=[
                    '长老', '老人', '长辈', '年长者',
                    '经验', '阅历', '资历', '威望',
                    '尊老', '孝道', '晚辈', '长幼有序',
                    '老人会', '长者意见', '老人决策',
                    '传统智慧', '祖辈经验', '听老人言',
                    '年轻人服从', '尊重长者', '敬老'
                ],
                example_sentences=[
                    '村里的重要决策都要征求几位老人的意见',
                    '老人说的话在村里很有分量',
                    '年轻人做事要听长辈的建议',
                    '村里有专门的老年人协会参与管理',
                    '传统技艺主要由老人传授',
                    '长者在纠纷调解中扮演重要角色',
                    '老人的口述历史是村庄记忆的重要载体',
                    '村民对老年人普遍尊重和照顾'
                ]
            ),

            # 维度6：血缘与地缘
            'kinship_locality': DimensionDefinition(
                dimension_id='kinship_locality',
                dimension_name='血缘与地缘',
                description='血缘与地缘深度交织，宗族聚居是基层社区的基本形态，"落叶归根"是深入骨髓的文化心理',
                keywords=[
                    '血缘', '地缘', '宗族', '聚居',
                    '同姓村', '姓氏聚集', '家族聚居区',
                    '落叶归根', '回乡', '故土', '祖籍',
                    '家乡认同', '本地人', '外地人', '籍贯',
                    '返乡', '回老家', '在外游子', '思乡',
                    '家族墓地', '祖坟', '安葬', '叶落归根'
                ],
                example_sentences=[
                    '村里主要是三个大姓，各占一片区域',
                    '同姓的人家住得比较集中',
                    '在外打工的人最终都想回乡养老',
                    '村民对家乡有很强的认同感',
                    '外出的年轻人过年一定要回来',
                    '村后山上是各家族的祖坟',
                    '很多在外成功人士会回馈家乡',
                    '"金窝银窝不如自己的草窝"是村民常说的话'
                ]
            ),

            # 维度7：文字与乡（沟通钥匙）
            'literacy_communication': DimensionDefinition(
                dimension_id='literacy_communication',
                dimension_name='文字与乡（沟通钥匙）',
                description='《乡土中国》指出乡土社会是"面对面社群"——语言、表情、动作已足够交流，文字是间接接触的工具，在熟人社会里往往"不通"。重视口头传播，面对面沟通',
                keywords=[
                    '口头传播', '面对面', '口口相传', '当面说',
                    '村广播', '大喇叭', '喊话', '通知',
                    '村民大会', '开会', '集体讨论', '当面谈',
                    '不识字', '文化程度低', '书面材料少',
                    '微信群', '电话通知', '语音消息',
                    '公示栏', '张贴', '告示', '布告',
                    '谣言', '传言', '小道消息', '流言',
                    '问卷调查效果差', '不爱填表', '看不懂文件'
                ],
                example_sentences=[
                    '村里的通知主要通过大喇叭广播',
                    '重要事情要开村民大会当面讲',
                    '老人不识字，书面材料看不懂',
                    '消息在村里传得很快，口口相传',
                    '现在用微信群通知，但还是要当面确认',
                    '公示栏贴了文件，但很少人去看',
                    '问卷调查要面对面访谈才有效',
                    '村民更相信当面说的话而不是书面承诺'
                ]
            ),

            # 维度8：文化自觉（转化钥匙）
            'cultural_consciousness': DimensionDefinition(
                dimension_id='cultural_consciousness',
                dimension_name='文化自觉（转化钥匙）',
                description='费孝通晚年提出的核心概念——各民族对自己文化的"自知之明"，谋求创造性转化，路径是"各美其美，美人之美，美美与共，天下大同"',
                keywords=[
                    '文化自觉', '文化认同', '文化自信', '文化自豪',
                    '传统文化', '本地特色', '独特性', '文化价值',
                    '文化传承', '文化保护', '文化复兴', '文化创新',
                    '各美其美', '美人之美', '文化多样性',
                    '文化自卑', '崇洋媚外', '传统断裂',
                    '年轻人不了解', '老传统没人重视', '快失传了',
                    '重新认识', '重新发现', '价值重估', '文化觉醒'
                ],
                example_sentences=[
                    '村民开始意识到本地传统文化的价值',
                    '年轻人觉得传统习俗土气，不愿意参与',
                    '老人担心很多传统技艺后继无人',
                    '村里人对外来文化更感兴趣，对本土文化不自信',
                    '有村民主动学习和传承传统手工艺',
                    '文化遗产项目让村民重新认识自己的文化',
                    '村民对本地历史和文化知之甚少',
                    '通过文化活动，村民的文化自豪感增强了'
                ]
            )
        }

    def analyze(self, text_content: str, metadata: Optional[Dict[str, Any]] = None) -> SkillResult:
        """
        执行乡土中国理论分析

        Args:
            text_content: 田野调查文本内容
            metadata: 可选的元数据信息

        Returns:
            SkillResult对象，包含所有维度的分析结果
        """
        import time
        start_time = time.time()

        try:
            logger.info("开始乡土中国理论分析")

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

            logger.info(f"乡土中国理论分析完成: {total_matches} 个匹配, 平均置信度 {avg_confidence:.3f}")

            return result

        except Exception as e:
            logger.error(f"乡土中国理论分析失败: {e}", exc_info=True)
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
        skill = XiangtuChinaSkill()
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
        logger.error(f"乡土中国理论分析失败: {e}")
        return None


# Skill定义（用于注册和发现）
SKILL_DEFINITION = {
    "id": "xiangtu_china",
    "name": "乡土中国理论分析（完整8维度版）",
    "description": "基于费孝通《乡土中国》完整理论框架的社会学分析，用乡土中国的眼看乡村",
    "version": "3.0",
    "author": "费孝通",
    "category": "学术理论",
    "dimensions": {
        "xiangtu_nature": {
            "name": "乡土本色",
            "description": "熟人社会，面对面社群"
        },
        "differential_mode": {
            "name": "差序格局",
            "description": "以己为中心的水波式关系网络"
        },
        "ritual_order": {
            "name": "礼治秩序（含'无讼'）",
            "description": "礼治而非法治，调解优先"
        },
        "family_gender": {
            "name": "家族与男女有别",
            "description": "家族为基本单位，性别分工"
        },
        "elder_rule": {
            "name": "长老统治",
            "description": "长者权威，经验为王"
        },
        "kinship_locality": {
            "name": "血缘与地缘",
            "description": "宗族聚居，落叶归根"
        },
        "literacy_communication": {
            "name": "文字与乡（沟通钥匙）",
            "description": "口头传播，面对面沟通为主"
        },
        "cultural_consciousness": {
            "name": "文化自觉（转化钥匙）",
            "description": "各美其美，美人之美，美美与共"
        }
    }
}
