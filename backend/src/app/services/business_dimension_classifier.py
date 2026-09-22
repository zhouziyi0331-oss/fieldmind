"""
Business Dimension Classifier - 业务维度自动分类器

这是 FieldMind 真正的数据治理核心：
- 自动识别文本属于哪个业务维度
- 支持多维度标注（一段文本可能属于多个维度）
- 基于关键词匹配 + 规则判断
- 可追溯（记录匹配到的关键词）

6个核心维度：
1. 衣食住行
2. 民俗
3. 非物质文化遗产
4. 物质文化遗产
5. 政策
6. 历史
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DimensionClassification:
    """维度分类结果"""
    primary_category: str  # 主维度
    sub_categories: List[str] = field(default_factory=list)  # 子维度
    confidence: float = 0.0  # 置信度
    matched_keywords: List[str] = field(default_factory=list)  # 匹配到的关键词
    time_period: Optional[str] = None  # 时间区间
    location: Optional[str] = None  # 地点
    culture_code: Optional[str] = None  # 文化编码


class BusinessDimensionClassifier:
    """
    业务维度分类器

    自动识别文本属于哪个业务维度
    """

    # 维度关键词字典
    DIMENSION_KEYWORDS = {
        '衣食住行': {
            '衣': [
                '衣', '服装', '服饰', '穿戴', '刺绣', '织布', '染色', '蜡染', '蓝染',
                '衣料', '布匹', '靛蓝', '挑花', '绣花', '纺织', '苗绣', '布依绣',
                '头饰', '银饰', '腰带', '围腰', '百褶裙', '对襟', '盛装'
            ],
            '食': [
                '食', '吃', '饭', '米', '糯', '酒', '茶', '菜', '耕种', '收获',
                '粮食', '作物', '水稻', '玉米', '酿酒', '糍粑', '糯米', '五色饭',
                '酸汤', '腌菜', '腊肉', '豆腐', '米酒', '节庆食物', '祭祀食品'
            ],
            '住': [
                '住', '房', '屋', '家', '宅', '村', '寨', '楼', '木结构', '吊脚楼',
                '茅草', '瓦房', '院落', '干栏', '石板房', '土墙', '建筑', '村落',
                '空间', '布局', '风水', '门楼', '火塘'
            ],
            '行': [
                '行', '路', '交通', '外出', '打工', '运输', '车', '徒步', '山路',
                '桥梁', '渡口', '马帮', '背篓', '挑担', '迁徙', '出行'
            ]
        },
        '民俗': [
            '民俗', '节日', '节庆', '六月六', '三月三', '四月八', '赶秋', '跳花',
            '对歌', '婚俗', '婚礼', '嫁娶', '聘礼', '丧葬', '葬礼', '生育', '满月',
            '祭祀', '祖先', '信仰', '禁忌', '习俗', '礼仪', '仪式', '传统',
            '山歌', '芦笙', '铜鼓', '木鼓', '唢呐', '民间信仰', '祭祖'
        ],
        '非物质文化遗产': [
            '非遗', '传承', '继承', '口传', '手艺', '技艺', '歌谣', '山歌', '民歌',
            '舞蹈', '戏曲', '传说', '故事', '工艺', '非遗传人', '传承人', '口述',
            '民间艺术', '表演', '曲艺', '说唱', '弹唱', '古歌', '史诗', '神话',
            '蜡染技艺', '刺绣技艺', '酿酒技艺', '造纸技艺', '竹编', '银饰锻造'
        ],
        '物质文化遗产': [
            '遗产', '古迹', '遗址', '建筑', '文物', '碑刻', '祠堂', '庙宇',
            '古树', '古井', '寨门', '古道', '石桥', '古寨', '历史建筑', '传统建筑',
            '古村落', '文化遗存', '保护单位', '文保', '古迹遗存'
        ],
        '政策': [
            '政策', '文件', '规定', '条例', '补贴', '扶贫', '乡村振兴', '搬迁',
            '安置', '宅基地', '土地确权', '医疗', '教育', '医保', '低保', '电网',
            '自来水', '公路', '基础设施', '政府', '干部', '村委', '驻村', '帮扶',
            '项目', '资金', '拨款', '惠民', '政策落实'
        ],
        '历史': [
            '历史', '以前', '过去', '曾经', '当年', '那时候', '老一辈', '上辈',
            '祖辈', '旧社会', '解放', '民国', '清朝', '土改', '大集体', '分田到户',
            '改革开放', '变迁', '演变', '发展', '变化', '往昔', '从前', '古时',
            '祖先', '先辈', '几代人', '世代'
        ]
    }

    # 时间关键词
    TIME_KEYWORDS = {
        '1949以前': ['解放前', '旧社会', '民国', '清朝', '古时', '很早以前'],
        '1950-1978': ['解放后', '土改', '大集体', '人民公社', '文革'],
        '1979-2000': ['改革开放', '分田到户', '包产到户', '八九十年代'],
        '2001-2010': ['2000年', '新世纪', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010'],
        '2011-2020': ['2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '十年前', '前几年'],
        '2021至今': ['2021', '2022', '2023', '2024', '2025', '2026', '现在', '今年', '去年', '前年', '近期', '最近']
    }

    # 文化编码（示例）
    CULTURE_CODES = {
        '山歌': 'S1',
        '蜡染': 'L1',
        '糯食': 'F1',
        '芦笙': 'M1',
        '铜鼓': 'M2',
        '刺绣': 'C1',
        '吊脚楼': 'A1',
        '六月六': 'F2',
        '三月三': 'F3'
    }

    def __init__(self, use_workflow_engine: bool = True):
        """初始化分类器"""



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)
        logger.info("BusinessDimensionClassifier initialized")

    def classify(self, text: str) -> DimensionClassification:
        """
        分类文本到业务维度

        Args:
            text: 原始文本

        Returns:
            DimensionClassification: 分类结果
        """
        if not text or len(text.strip()) == 0:
            return DimensionClassification(primary_category='未分类', confidence=0.0)

        # 1. 识别所有匹配的维度
        dimension_scores = self._match_dimensions(text)

        if not dimension_scores:
            return DimensionClassification(primary_category='未分类', confidence=0.0)

        # 2. 选择主维度（得分最高的）
        primary_category = max(dimension_scores.keys(), key=lambda k: dimension_scores[k]['score'])
        primary_info = dimension_scores[primary_category]

        # 3. 识别子维度（衣食住行特殊处理）
        sub_categories = []
        if primary_category == '衣食住行':
            sub_categories = self._identify_sub_categories(text, primary_info['keywords'])

        # 4. 识别时间区间
        time_period = self._identify_time_period(text)

        # 5. 识别地点
        location = self._identify_location(text)

        # 6. 识别文化编码
        culture_code = self._identify_culture_code(text)

        # 7. 计算置信度
        confidence = self._calculate_confidence(primary_info['score'], len(primary_info['keywords']))

        result = DimensionClassification(
            primary_category=primary_category,
            sub_categories=sub_categories,
            confidence=confidence,
            matched_keywords=primary_info['keywords'],
            time_period=time_period,
            location=location,
            culture_code=culture_code
        )

        logger.debug(f"Classified: {primary_category} (confidence={confidence:.2f})")
        return result

    def _match_dimensions(self, text: str) -> Dict[str, Dict]:
        """匹配所有维度"""
        dimension_scores = {}

        for dimension, keywords in self.DIMENSION_KEYWORDS.items():
            if dimension == '衣食住行':
                # 衣食住行特殊处理：需要匹配子维度
                matched = []
                score = 0
                for sub_dim, sub_keywords in keywords.items():
                    sub_matched = [kw for kw in sub_keywords if kw in text]
                    if sub_matched:
                        matched.extend(sub_matched)
                        score += len(sub_matched)

                if matched:
                    dimension_scores[dimension] = {
                        'score': score,
                        'keywords': matched
                    }
            else:
                # 其他维度：直接匹配关键词
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    # 特殊处理：非遗、政策、物质遗产的权重加倍
                    weight = 2 if dimension in ['非物质文化遗产', '政策', '物质文化遗产'] else 1
                    dimension_scores[dimension] = {
                        'score': len(matched) * weight,
                        'keywords': matched
                    }

        return dimension_scores

    def _identify_sub_categories(self, text: str, matched_keywords: List[str]) -> List[str]:
        """识别衣食住行的子维度"""
        sub_categories = []

        for sub_dim, keywords in self.DIMENSION_KEYWORDS['衣食住行'].items():
            if any(kw in matched_keywords for kw in keywords):
                sub_categories.append(sub_dim)

        return sub_categories

    def _identify_time_period(self, text: str) -> Optional[str]:
        """识别时间区间"""
        for period, keywords in self.TIME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return period

        # 如果没有明确的时间关键词，尝试提取年份
        year_match = re.search(r'(19|20)\d{2}年?', text)
        if year_match:
            year = int(year_match.group(0)[:4])
            if year < 1949:
                return '1949以前'
            elif year <= 1978:
                return '1950-1978'
            elif year <= 2000:
                return '1979-2000'
            elif year <= 2010:
                return '2001-2010'
            elif year <= 2020:
                return '2011-2020'
            else:
                return '2021至今'

        return None

    def _identify_location(self, text: str) -> Optional[str]:
        """识别地点"""
        # 简单规则：匹配"XX村"、"XX寨"、"XX镇"等
        location_patterns = [
            r'(\w{2,6}村)',
            r'(\w{2,6}寨)',
            r'(\w{2,6}镇)',
            r'(\w{2,6}乡)',
            r'(\w{2,6}县)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _identify_culture_code(self, text: str) -> Optional[str]:
        """识别文化编码"""
        for culture, code in self.CULTURE_CODES.items():
            if culture in text:
                return code

        return None

    def _calculate_confidence(self, score: int, keyword_count: int) -> float:
        """
        计算置信度

        基于：
        1. 匹配到的关键词数量
        2. 关键词的得分
        """
        # 简单规则：关键词越多，置信度越高
        if keyword_count >= 5:
            return 0.9
        elif keyword_count >= 3:
            return 0.75
        elif keyword_count >= 2:
            return 0.6
        else:
            return 0.4

    def classify_batch(self, texts: List[str]) -> List[DimensionClassification]:
        """批量分类"""
        logger.info(f"Batch classifying {len(texts)} texts")
        return [self.classify(text) for text in texts]

    def to_dict(self, classification: DimensionClassification) -> Dict:
        """转换为字典"""
        return {
            'dimension_category': classification.primary_category,
            'dimension_sub_category': ','.join(classification.sub_categories) if classification.sub_categories else None,
            'time_period': classification.time_period,
            'location': classification.location,
            'culture_code': classification.culture_code,
            'keywords_matched': json.dumps(classification.matched_keywords, ensure_ascii=False),
            'confidence_score': classification.confidence
        }


def create_classifier() -> BusinessDimensionClassifier:
    """工厂方法：创建分类器"""
    return BusinessDimensionClassifier()


def classify_text(text: str) -> Dict:
    """快捷函数：分类单个文本"""
    classifier = create_classifier()
    result = classifier.classify(text)
    return classifier.to_dict(result)
