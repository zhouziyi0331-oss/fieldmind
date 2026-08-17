"""
文化分类器 - 衣食住行在地五维度分类

用于田野调查材料的文化遗产资产盘点
"""

from typing import Dict, List, Tuple
import logging
import re
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CulturalDimension:
    """文化维度定义"""
    dimension_id: str
    dimension_name: str
    keywords: List[str]
    examples: List[str]  # 用于语义匹配的示例句


# 五大文化维度定义
CULTURAL_DIMENSIONS = {
    "衣": CulturalDimension(
        dimension_id="clothing",
        dimension_name="衣",
        keywords=[
            # 服饰类
            "服饰", "衣服", "衣着", "穿戴", "服装", "衣裳", "布料", "织物",
            # 民族服饰
            "蜡染", "刺绣", "挑花", "织锦", "银饰", "头饰", "腰带", "绣花",
            "苗服", "布依服饰", "侗族服饰", "民族服装", "盛装", "便装",
            # 制作工艺
            "织布", "纺织", "染色", "缝纫", "裁剪", "绣工", "银匠", "手工制作",
            # 材料
            "棉布", "麻布", "丝绸", "蓝靛", "植物染料", "银器",
        ],
        examples=[
            "她穿着绣花的民族服装",
            "村里还有老人会蜡染手艺",
            "这件衣服是手工织的布做的",
            "银饰是请银匠打的",
            "年轻人已经不穿传统服饰了",
        ]
    ),

    "食": CulturalDimension(
        dimension_id="food",
        dimension_name="食",
        keywords=[
            # 主食
            "糯米", "糯食", "米饭", "粑粑", "糍粑", "年糕", "粽子", "米酒",
            # 特色食品
            "腌菜", "腊肉", "豆腐", "米豆腐", "酸汤", "酸菜", "泡菜", "豆豉",
            # 饮品
            "酒", "米酒", "糯米酒", "苞谷酒", "茶", "油茶",
            # 节庆饮食
            "长桌宴", "百家宴", "杀猪饭", "坝坝宴", "流水席",
            # 食材与烹饪
            "稻米", "玉米", "苞谷", "蔬菜", "野菜", "腌制", "发酵", "烟熏",
            "火塘", "柴火", "蒸", "煮", "炒", "烤",
        ],
        examples=[
            "家家户户都会做糯米饭",
            "过年要杀猪腌腊肉",
            "酸汤是当地特色菜",
            "节日摆长桌宴招待客人",
            "用传统方法酿米酒",
        ]
    ),

    "住": CulturalDimension(
        dimension_id="housing",
        dimension_name="住",
        keywords=[
            # 建筑类型
            "吊脚楼", "木楼", "干栏式", "四合院", "土楼", "石板房", "茅草房",
            "祖屋", "老屋", "新房", "楼房",
            # 建筑结构
            "木结构", "穿斗", "抬梁", "榫卯", "雕花", "门楼", "天井", "堂屋",
            "厢房", "神龛", "火塘", "吊脚", "栏杆",
            # 建筑材料
            "木料", "杉木", "松木", "石头", "石板", "泥土", "夯土", "青瓦", "茅草",
            # 空间
            "村寨", "寨子", "院落", "院子", "庭院", "晒坝", "场坝", "村口",
            "房前屋后", "宅基地",
            # 营造
            "建房", "造房", "修房", "立柱", "上梁", "封顶", "木匠", "石匠", "泥水匠",
        ],
        examples=[
            "这栋吊脚楼有上百年历史",
            "木结构用榫卯连接，不用一颗钉子",
            "火塘是全家人围坐的地方",
            "建房要请木匠师傅",
            "年轻人都搬到新楼房了",
        ]
    ),

    "行": CulturalDimension(
        dimension_id="transportation",
        dimension_name="行",
        keywords=[
            # 道路
            "山路", "石板路", "青石路", "土路", "公路", "机耕道", "古道", "驿道",
            "小路", "田埂", "桥", "石桥", "风雨桥", "吊桥", "木桥",
            # 交通工具
            "步行", "走路", "背篓", "扁担", "挑担", "马", "骡子", "牛车",
            "摩托车", "汽车", "面包车", "客车", "班车",
            # 迁移流动
            "外出", "打工", "务工", "出门", "进城", "回家", "返乡",
            "搬迁", "移民", "走亲戚", "赶集", "赶场",
            # 时间距离
            "几里路", "几小时", "半天", "天亮出发", "走到天黑",
        ],
        examples=[
            "以前只有山路，要走好几个小时",
            "现在通了公路，开车半小时就到",
            "年轻人都外出打工了",
            "每逢赶集日，村民背着背篓进城",
            "这座石桥是祖辈修的",
        ]
    ),

    "在地": CulturalDimension(
        dimension_id="locality",
        dimension_name="在地",
        keywords=[
            # 土地
            "土地", "田地", "耕地", "水田", "旱地", "梯田", "荒地", "林地",
            "承包地", "自留地", "宅基地", "集体土地",
            # 土地利用
            "种地", "耕种", "播种", "收割", "犁地", "插秧", "收成",
            "土地流转", "流转", "承包", "租赁", "征地", "退耕还林",
            # 自然资源
            "山林", "森林", "树木", "竹林", "水源", "河流", "溪水", "井", "泉水",
            "草场", "牧场", "矿产",
            # 地域认同
            "祖地", "故土", "家乡", "村子", "寨子", "这片地", "这里", "本地",
            "地方", "风水", "龙脉", "神山", "圣地",
            # 资源纠纷
            "地界", "边界", "界碑", "纠纷", "争议", "占地", "越界",
        ],
        examples=[
            "这片土地是祖辈传下来的",
            "村里实行土地流转，引进公司种植",
            "山林是集体所有",
            "水源地要保护好",
            "因为地界发生纠纷",
            "年轻人不愿种地，很多田地荒了",
        ]
    ),
}


class CulturalClassifier:
    """文化分类器 - 衣食住行在地"""

    def __init__(self):
        """初始化分类器"""
        logger.info("初始化文化分类器...")

        # 加载轻量级向量模型
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2',
            device='cpu'
        )

        # 预计算维度向量
        self.dimension_vectors = {}
        for dim_id, dimension in CULTURAL_DIMENSIONS.items():
            if dimension.examples:
                vectors = self.embedding_model.encode(dimension.examples)
                # 取平均向量作为维度表征
                self.dimension_vectors[dim_id] = np.mean(vectors, axis=0)

        logger.info("文化分类器初始化完成")

    def classify(
        self,
        text: str,
        keyword_threshold: int = 1,
        semantic_threshold: float = 0.6
    ) -> Dict[str, List[str]]:
        """
        对文本进行文化分类

        Args:
            text: 待分类文本
            keyword_threshold: 关键词匹配至少命中数
            semantic_threshold: 语义相似度阈值

        Returns:
            {
                "衣": ["蜡染", "刺绣"],
                "食": ["糯米", "腊肉", "长桌宴"],
                ...
            }
        """
        result = {}

        for dim_id, dimension in CULTURAL_DIMENSIONS.items():
            dim_name = dimension.dimension_name
            matched_keywords = []

            # 方法1：关键词精确匹配
            for keyword in dimension.keywords:
                if keyword in text:
                    matched_keywords.append(keyword)

            # 方法2：语义相似度匹配（对于词表未覆盖的内容）
            if dim_id in self.dimension_vectors:
                semantic_matches = self._semantic_match(
                    text,
                    self.dimension_vectors[dim_id],
                    semantic_threshold
                )
                matched_keywords.extend(semantic_matches)

            # 去重
            matched_keywords = list(set(matched_keywords))

            if len(matched_keywords) >= keyword_threshold:
                result[dim_name] = matched_keywords

        return result

    def _semantic_match(
        self,
        text: str,
        dimension_vector: np.ndarray,
        threshold: float
    ) -> List[str]:
        """
        语义匹配：提取与维度语义相关的短语

        Args:
            text: 待分析文本
            dimension_vector: 维度的向量表征
            threshold: 相似度阈值

        Returns:
            匹配到的关键短语列表
        """
        # 简单分句
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        if not sentences:
            return []

        matched_phrases = []

        try:
            # 编码句子
            sentence_vectors = self.embedding_model.encode(sentences)

            # 计算相似度
            similarities = cosine_similarity(
                sentence_vectors,
                dimension_vector.reshape(1, -1)
            ).flatten()

            # 筛选高相似度句子
            for i, sim in enumerate(similarities):
                if sim >= threshold:
                    # 提取关键短语（简化版：取前10个字）
                    phrase = sentences[i][:20] + ("..." if len(sentences[i]) > 20 else "")
                    matched_phrases.append(phrase)

        except Exception as e:
            logger.warning(f"语义匹配失败: {e}")

        return matched_phrases[:3]  # 最多返回3个语义匹配

    def extract_professional_terms(self, text: str) -> List[str]:
        """
        提取专业名词（基于词表）

        Args:
            text: 待分析文本

        Returns:
            专业名词列表
        """
        professional_terms = []

        # 从所有维度关键词中提取
        for dimension in CULTURAL_DIMENSIONS.values():
            for keyword in dimension.keywords:
                if keyword in text and len(keyword) >= 2:
                    professional_terms.append(keyword)

        # 去重并按出现频率排序
        from collections import Counter
        term_counts = Counter(professional_terms)

        return [term for term, _ in term_counts.most_common(20)]


# 全局实例
cultural_classifier = CulturalClassifier()
