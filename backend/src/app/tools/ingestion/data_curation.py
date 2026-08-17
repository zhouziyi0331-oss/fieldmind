"""
数据治理模块 - Data Curation Layer
负责将非结构化文本转换为可统计的结构化数据

核心功能：
1. 文本清洗（去除口语填充词、标点归一化）
2. 主题分类（衣食住行社交经济信仰）
3. 实体抽取（人名、地名、时间）
4. 结构化存储（PostgreSQL分析型宽表）
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清洗器"""

    # 口语填充词（停用词）
    FILLER_WORDS = [
        '嗯', '啊', '呃', '哦', '诶', '唉',
        '那个', '这个', '就是说', '然后呢', '对吧',
        '你知道', '怎么说呢', '其实吧', '我觉得',
    ]

    # 标点符号归一化映射
    PUNCTUATION_MAP = {
        '"': '"',  # 中文引号转英文
        '"': '"',
        ''': "'",
        ''': "'",
        '，': ',',  # 可选：统一为英文标点
        '。': '.',
        '？': '?',
        '！': '!',
        '；': ';',
        '：': ':',
    }

    @staticmethod
    def clean_filler_words(text: str) -> str:
        """去除口语填充词"""
        for word in TextCleaner.FILLER_WORDS:
            text = text.replace(word, '')
        return text

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """标点符号归一化"""
        for old, new in TextCleaner.PUNCTUATION_MAP.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def remove_excessive_spaces(text: str) -> str:
        """去除多余空格"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def clean(text: str) -> str:
        """完整清洗流程"""
        if not text:
            return ""

        # 1. 去除填充词
        text = TextCleaner.clean_filler_words(text)

        # 2. 归一化标点
        text = TextCleaner.normalize_punctuation(text)

        # 3. 去除多余空格
        text = TextCleaner.remove_excessive_spaces(text)

        return text


class TopicClassifier:
    """主题分类器 - 基于关键词的规则分类"""

    # 主题关键词字典
    TOPIC_KEYWORDS = {
        '衣': ['衣服', '服装', '纺织', '刺绣', '布料', '穿戴', '织布', '裁缝', '染色'],
        '食': ['吃', '食物', '饮食', '做饭', '烹饪', '菜', '肉', '粮食', '杀猪', '酒', '宴席'],
        '住': ['房子', '建房', '住宅', '院子', '装修', '祠堂', '村舍', '窑洞'],
        '行': ['路', '交通', '出行', '车', '走', '桥', '道路'],
        '社交': ['婚礼', '丧事', '祭祀', '节日', '聚会', '拜访', '亲戚', '邻居'],
        '经济': ['钱', '收入', '支出', '买', '卖', '生意', '工资', '贷款', '债务'],
        '信仰': ['神', '庙', '祭祀', '迷信', '风水', '占卜', '祖先'],
    }

    @staticmethod
    def classify(text: str) -> List[str]:
        """
        对文本进行主题分类
        返回匹配的所有主题（可多标签）
        """
        matched_topics = []

        for topic, keywords in TopicClassifier.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    matched_topics.append(topic)
                    break  # 该主题已匹配，跳到下一个主题

        # 如果没有匹配任何主题，标记为"其他"
        if not matched_topics:
            matched_topics.append('其他')

        return matched_topics


class EntityExtractor:
    """实体抽取器 - 提取人名、地名"""

    @staticmethod
    def extract_persons(text: str) -> List[str]:
        """提取人名"""
        persons = []
        words = pseg.cut(text)

        for word in words:
            if word.flag == 'nr':  # nr = 人名
                persons.append(word.word)

        return list(set(persons))  # 去重

    @staticmethod
    def extract_locations(text: str) -> List[str]:
        """提取地名"""
        locations = []
        words = pseg.cut(text)

        for word in words:
            if word.flag == 'ns':  # ns = 地名
                locations.append(word.word)

        return list(set(locations))  # 去重

    @staticmethod
    def extract_all(text: str) -> Dict[str, List[str]]:
        """提取所有实体"""
        return {
            'persons': EntityExtractor.extract_persons(text),
            'locations': EntityExtractor.extract_locations(text),
        }


class DataCurationPipeline:
    """数据治理Pipeline - 整合所有清洗和结构化步骤"""

    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.topic_classifier = TopicClassifier()
        self.entity_extractor = EntityExtractor()

    def process(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        完整的数据治理流程

        输入：原始文本
        输出：结构化数据记录
        """
        if not text:
            return None

        # 1. 文本清洗
        cleaned_text = self.text_cleaner.clean(text)

        if not cleaned_text:
            return None

        # 2. 主题分类
        topics = self.topic_classifier.classify(cleaned_text)

        # 3. 实体抽取
        entities = self.entity_extractor.extract_all(cleaned_text)

        # 4. 构建结构化记录
        structured_record = {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'topics': topics,  # List[str]
            'persons': entities['persons'],  # List[str]
            'locations': entities['locations'],  # List[str]
            'metadata': metadata or {},
            'processed_at': datetime.now().isoformat(),
        }

        logger.info(f"📊 数据治理完成: topics={topics}, persons={entities['persons'][:3]}")

        return structured_record


# 去重工具
class Deduplicator:
    """文本去重器 - 基于相似度的重复检测"""

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算两段文本的相似度（简单版：Jaccard相似度）"""
        if not text1 or not text2:
            return 0.0

        # 分词
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))

        # Jaccard相似度
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    @staticmethod
    def is_duplicate(text1: str, text2: str, threshold: float = 0.95) -> bool:
        """判断两段文本是否重复"""
        similarity = Deduplicator.calculate_similarity(text1, text2)
        return similarity >= threshold


if __name__ == "__main__":
    # 测试代码
    pipeline = DataCurationPipeline()

    test_text = "嗯，那个，我觉得这个杀猪菜啊，就是说，是我们村的传统美食，你知道吗？"
    result = pipeline.process(test_text)

    print("=" * 70)
    print("📊 数据治理测试")
    print("=" * 70)
    print(f"原文: {result['original_text']}")
    print(f"清洗后: {result['cleaned_text']}")
    print(f"主题: {result['topics']}")
    print(f"人名: {result['persons']}")
    print(f"地名: {result['locations']}")
