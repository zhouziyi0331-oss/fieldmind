"""
方言处理服务
深度文化背景 - 方言词 + 标准词映射 + 地域标注 + 文化背景
"""
import logging
from typing import List, Dict, Any, Optional

from app.models.enriched_chunk import DialectTerm, DialectProcessingResult

logger = logging.getLogger(__name__)


class DialectNormalizationService:
    """方言处理服务 - 深度文化背景"""

    def __init__(self):
        # 方言词典（分地域）⭐
        self.dialect_dict = self._load_dialect_dictionaries()

        # 文化背景数据库 ⭐
        self.cultural_db = self._load_cultural_context_database()

        logger.info("方言处理服务初始化完成")

    def _load_dialect_dictionaries(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """加载方言词典（按地域分类）"""
        return {
            "贵州": {
                "赶场": {
                    "standard": "集市",
                    "cultural_meaning": "农村地区定期举行的集市贸易活动",
                    "usage_context": "多用于描述乡镇定期集市，通常每五天或每十天一次",
                    "etymology": "来自'赶集'的说法，强调赶去参加的动作"
                },
                "洋芋": {
                    "standard": "土豆",
                    "cultural_meaning": "马铃薯的方言说法",
                    "usage_context": "日常饮食中常用，是西南地区主要粮食作物之一",
                    "etymology": "因马铃薯来自外国（洋），形状似芋头而得名"
                },
                "背篼": {
                    "standard": "背篓",
                    "cultural_meaning": "用竹篾编制的背负用具",
                    "usage_context": "山区农耕劳作、运输货物的传统工具",
                    "etymology": "因背在身后、形似篼而得名"
                },
                "坝坝": {
                    "standard": "广场",
                    "cultural_meaning": "平整的空地或广场",
                    "usage_context": "用于晒谷、集会、娱乐等公共活动",
                    "etymology": "指平整的土坝或空地"
                },
                "坎坎": {
                    "standard": "台阶",
                    "cultural_meaning": "阶梯、台阶",
                    "usage_context": "山地建筑中常见的台阶",
                    "etymology": "指高低不平的坎"
                },
                "搭白": {
                    "standard": "闲聊",
                    "cultural_meaning": "聊天、说话",
                    "usage_context": "日常交际用语",
                    "etymology": "说闲话、搭讪"
                },
                "巴适": {
                    "standard": "舒服",
                    "cultural_meaning": "舒适、合适、很好",
                    "usage_context": "表达满意、舒适的感觉",
                    "etymology": "形容非常合适、舒服"
                },
                "幺妹": {
                    "standard": "小姑娘",
                    "cultural_meaning": "年轻女孩的称呼",
                    "usage_context": "对年轻女性的亲切称呼",
                    "etymology": "幺指最小，妹指女孩"
                },
            },
            "云南": {
                "板扎": {
                    "standard": "很好",
                    "cultural_meaning": "非常好、很棒",
                    "usage_context": "表示赞赏、肯定",
                    "etymology": "形容扎实、可靠"
                },
                "搓": {
                    "standard": "吃",
                    "cultural_meaning": "吃饭",
                    "usage_context": "日常用餐场景",
                    "etymology": "搓饭的说法"
                },
            },
            "四川": {
                "雄起": {
                    "standard": "加油",
                    "cultural_meaning": "鼓励、加油、振作",
                    "usage_context": "体育比赛、鼓励场合",
                    "etymology": "呼喊加油助威"
                },
                "摆龙门阵": {
                    "standard": "聊天",
                    "cultural_meaning": "闲聊、聊天、讲故事",
                    "usage_context": "休闲娱乐、社交场合",
                    "etymology": "指围坐聊天如摆阵一般"
                },
            },
            "西南通用": {
                "火塘": {
                    "standard": "火炉",
                    "cultural_meaning": "室内取暖、烧水做饭的火堆",
                    "usage_context": "传统民居中的核心设施，是家庭活动中心",
                    "etymology": "在地上挖坑或用石头围成的火堆"
                },
                "腊肉": {
                    "standard": "腊肉",
                    "cultural_meaning": "用烟熏制的猪肉",
                    "usage_context": "传统食品保存方式，节日食品",
                    "etymology": "腊月制作的肉"
                },
            },
        }

    def _load_cultural_context_database(self) -> Dict[str, Dict[str, str]]:
        """加载文化背景数据库

        为方言词提供更深层的文化解释
        """
        return {
            "赶场": {
                "meaning": "农村地区定期举行的集市贸易活动，是乡村经济和社会生活的重要组成部分",
                "context": "西南山区交通不便，村民集中在固定日期到乡镇集市交易，称为'赶场'。场期通常为每五天或十天一次，如'逢一、四、七赶场'",
                "etymology": "来自'赶集'，'场'指集市场所，'赶'强调从远处赶来参加",
                "cultural_significance": "赶场不仅是经济活动，更是社交、信息交流、娱乐的重要场合，体现了乡村社会的周期性节奏"
            },
            "洋芋": {
                "meaning": "马铃薯的方言说法，是西南地区重要的粮食作物",
                "context": "在贵州、云南等山区，洋芋是主要粮食作物之一，有'洋芋饭'、'洋芋粑'等多种吃法",
                "etymology": "因马铃薯来自外国（洋），形状似芋头，故称洋芋",
                "cultural_significance": "洋芋在山区农业和饮食文化中占重要地位，反映了山区农业适应性和饮食习惯"
            },
            "背篼": {
                "meaning": "用竹篾编制的背负用具，是山区重要的运输工具",
                "context": "山区道路崎岖，背篼是最实用的运输工具，用于背负农产品、柴火等",
                "etymology": "因背在身后、形似篼（竹编容器）而得名",
                "cultural_significance": "背篼是山区农耕文化的象征，体现了山区人民的劳作方式和生活智慧"
            },
            "火塘": {
                "meaning": "室内取暖、烧水做饭的火堆，是传统民居的核心设施",
                "context": "火塘位于堂屋中央，全家围坐火塘吃饭、聊天、待客，是家庭活动的中心",
                "etymology": "在地上挖坑或用石头围成，生火取暖做饭",
                "cultural_significance": "火塘是家庭和社会生活的中心，象征家庭的团聚和温暖，也是文化传承的重要场所"
            },
        }

    def process_dialect(
        self,
        text: str,
        region: Optional[str] = None
    ) -> DialectProcessingResult:
        """处理方言 - 保留原文 + 规范化 + 文化背景

        Args:
            text: 输入文本
            region: 地域（优先匹配该地域方言）

        Returns:
            方言处理结果
        """
        # 1. 识别方言词
        dialect_terms = self._identify_dialect_terms(text, region)

        # 2. 生成规范化文本
        normalized_text = self._normalize_text(text, dialect_terms)

        # 3. 添加文化背景
        dialect_terms = self._add_cultural_context(dialect_terms)

        logger.info(f"方言处理完成: {len(dialect_terms)} 个方言词")

        return DialectProcessingResult(
            original_text=text,
            normalized_text=normalized_text,
            dialect_terms=dialect_terms,
            processing_metadata={
                "region": region,
                "num_dialect_terms": len(dialect_terms),
                "preservation_mode": "dual"  # 原文和规范化都保留
            }
        )

    def _identify_dialect_terms(
        self,
        text: str,
        region: Optional[str] = None
    ) -> List[DialectTerm]:
        """识别方言词"""
        dialect_terms = []

        # 优先匹配指定地域的方言
        regions_to_search = []
        if region:
            # 先搜索指定地域
            if region in self.dialect_dict:
                regions_to_search.append(region)
            # 再搜索通用地域
            regions_to_search.append("西南通用")
        else:
            # 搜索所有地域
            regions_to_search = list(self.dialect_dict.keys())

        # 遍历地域词典
        for region_name in regions_to_search:
            if region_name not in self.dialect_dict:
                continue

            region_dict = self.dialect_dict[region_name]

            for dialect_word, info in region_dict.items():
                # 查找方言词在文本中的所有位置
                start = 0
                while True:
                    pos = text.find(dialect_word, start)
                    if pos == -1:
                        break

                    # 检查是否已经识别过（避免重复）
                    if not self._is_overlapping(pos, pos + len(dialect_word), dialect_terms):
                        term = DialectTerm(
                            term=dialect_word,
                            standard=info['standard'],
                            region=region_name,
                            start=pos,
                            end=pos + len(dialect_word),
                            cultural_meaning=info.get('cultural_meaning', ''),
                            usage_context=info.get('usage_context', ''),
                            etymology=info.get('etymology')
                        )
                        dialect_terms.append(term)

                    start = pos + len(dialect_word)

        # 按位置排序
        dialect_terms.sort(key=lambda t: t.start)

        return dialect_terms

    def _is_overlapping(
        self,
        start: int,
        end: int,
        existing_terms: List[DialectTerm]
    ) -> bool:
        """检查是否与已识别的方言词重叠"""
        for term in existing_terms:
            if not (end <= term.start or start >= term.end):
                return True
        return False

    def _normalize_text(
        self,
        text: str,
        dialect_terms: List[DialectTerm]
    ) -> str:
        """生成规范化文本

        替换方言词为标准词，但保持原文顺序
        """
        if not dialect_terms:
            return text

        # 按位置倒序替换（避免位置偏移）
        normalized = text
        for term in reversed(dialect_terms):
            normalized = (
                normalized[:term.start] +
                term.standard +
                normalized[term.end:]
            )

        return normalized

    def _add_cultural_context(
        self,
        dialect_terms: List[DialectTerm]
    ) -> List[DialectTerm]:
        """添加文化背景 ⭐

        不仅仅是词的映射，还要解释：
        - 为什么用这个方言词？
        - 在当地文化中有什么特殊含义？
        - 使用场景和语境是什么？
        """
        enriched_terms = []

        for term in dialect_terms:
            # 从文化数据库查询更深层的文化背景
            cultural_info = self.cultural_db.get(term.term, {})

            if cultural_info:
                # 如果有更详细的文化背景，更新
                term.cultural_meaning = cultural_info.get('meaning', term.cultural_meaning)
                term.usage_context = cultural_info.get('context', term.usage_context)

                # 添加文化意义（如果有）
                if 'cultural_significance' in cultural_info:
                    term.usage_context += f" | 文化意义: {cultural_info['cultural_significance']}"

            enriched_terms.append(term)

        return enriched_terms

    def get_dialect_statistics(
        self,
        dialect_terms: List[DialectTerm]
    ) -> Dict[str, Any]:
        """获取方言统计信息"""
        if not dialect_terms:
            return {
                "total_terms": 0,
                "regions": [],
                "coverage": 0.0
            }

        # 统计地域分布
        regions = {}
        for term in dialect_terms:
            regions[term.region] = regions.get(term.region, 0) + 1

        return {
            "total_terms": len(dialect_terms),
            "regions": list(regions.keys()),
            "region_distribution": regions,
            "terms": [term.term for term in dialect_terms]
        }
