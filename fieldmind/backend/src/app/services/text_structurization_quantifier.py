"""
Text Structurization Quantifier - 文本结构化量化器

这是 FieldMind 的核心模块：把非结构化文本变成结构化数据

核心任务：为每个文本块计算7个量化指标
1. word_count - 字数
2. sentence_count - 句数
3. exclamation_count - 感叹号数量
4. emotion_polarity - 情感极性值（-1到1）
5. subjectivity - 主观性（0到1）
6. emotion_word_density - 情绪词密度
7. avg_word_length - 平均词长

不安装新包，使用现有依赖：
- Python 内置：len(), count(), split()
- jieba：分词
- SnowNLP：情感分析

这是从"非结构化→结构化"的关键一步
"""

import re
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QuantifiedMetrics:
    """量化指标数据类"""
    # 基础统计
    word_count: int = 0
    sentence_count: int = 0
    exclamation_count: int = 0

    # 情感指标
    emotion_polarity: float = 0.0  # -1（负面）到 1（正面）
    subjectivity: float = 0.0      # 0（客观）到 1（主观）

    # 复杂度指标
    emotion_word_density: float = 0.0
    avg_word_length: float = 0.0


class TextStructurizationQuantifier:
    """
    文本结构化量化器

    把非结构化的文本变成带有7个量化指标的结构化数据
    这是 FieldMind 最核心的功能
    """

    # 情绪词表（精选常用情绪词）
    EMOTION_WORDS = {
        # 正面情绪
        '喜欢', '高兴', '开心', '快乐', '幸福', '满意', '欣慰', '兴奋', '激动',
        '欢乐', '愉快', '舒心', '美好', '温暖', '感动', '骄傲', '自豪', '欣赏',

        # 负面情绪
        '难过', '伤心', '痛苦', '悲伤', '难受', '失望', '沮丧', '绝望', '忧愁',
        '焦虑', '担心', '害怕', '恐惧', '愤怒', '生气', '讨厌', '厌恶', '后悔',
        '遗憾', '无奈', '孤独', '寂寞', '冷漠', '麻木', '烦躁', '郁闷', '压抑',

        # 程度词
        '非常', '特别', '十分', '很', '太', '极其', '相当', '格外'
    }

    def __init__(self):
        """初始化量化器"""
        self._jieba = None
        self._snownlp = None
        logger.info("TextStructurizationQuantifier initialized")

    def _load_jieba(self):
        """延迟加载 jieba"""
        if self._jieba is None:
            import jieba
            self._jieba = jieba
            logger.debug("Loaded jieba")
        return self._jieba

    def _load_snownlp(self):
        """延迟加载 SnowNLP"""
        if self._snownlp is None:
            try:
                from snownlp import SnowNLP
                self._snownlp = SnowNLP
                logger.debug("Loaded SnowNLP")
            except ImportError:
                logger.warning("SnowNLP not available, emotion analysis will be disabled")
                self._snownlp = None
        return self._snownlp

    def quantify(self, text: str) -> QuantifiedMetrics:
        """
        量化文本 - 核心方法

        把一段非结构化文本变成7个数值

        Args:
            text: 原始文本

        Returns:
            QuantifiedMetrics: 7个量化指标
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for quantification")
            return QuantifiedMetrics()

        logger.debug(f"Quantifying text (length={len(text)})")

        # 1. 字数
        word_count = len(text)

        # 2. 句数（按中英文标点分割）
        sentence_count = self._count_sentences(text)

        # 3. 感叹号数量
        exclamation_count = text.count('！') + text.count('!')

        # 4&5. 情感极性值和主观性
        emotion_polarity, subjectivity = self._analyze_emotion(text)

        # 6. 情绪词密度
        emotion_word_density = self._calculate_emotion_density(text, word_count)

        # 7. 平均词长
        avg_word_length = self._calculate_avg_word_length(text)

        metrics = QuantifiedMetrics(
            word_count=word_count,
            sentence_count=sentence_count,
            exclamation_count=exclamation_count,
            emotion_polarity=emotion_polarity,
            subjectivity=subjectivity,
            emotion_word_density=emotion_word_density,
            avg_word_length=avg_word_length
        )

        logger.info(f"Quantified: {word_count} words, {sentence_count} sentences, "
                   f"emotion={emotion_polarity:.2f}, density={emotion_word_density:.3f}")

        return metrics

    def _count_sentences(self, text: str) -> int:
        """
        统计句子数

        按中英文句子结束标点分割
        """
        # 中英文句子结束标点
        sentences = re.split(r'[。！？.!?;；]+', text)
        # 过滤空字符串
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    def _analyze_emotion(self, text: str) -> tuple[float, float]:
        """
        分析情感

        Returns:
            (emotion_polarity, subjectivity)
            emotion_polarity: -1（负面）到 1（正面）
            subjectivity: 0（客观）到 1（主观）
        """
        SnowNLP = self._load_snownlp()

        if SnowNLP is None:
            # SnowNLP 不可用时的降级策略
            return self._simple_emotion_analysis(text)

        try:
            s = SnowNLP(text)

            # SnowNLP 的 sentiments 返回 0-1 的正面概率
            # 转换为 -1 到 1 的极性值
            positive_prob = s.sentiments
            emotion_polarity = (positive_prob - 0.5) * 2  # 0.5 → 0, 0 → -1, 1 → 1

            # 主观性：使用简单规则（情绪词密度 + "我"的频率）
            subjectivity = self._estimate_subjectivity(text)

            return round(emotion_polarity, 3), round(subjectivity, 3)

        except Exception as e:
            logger.warning(f"SnowNLP analysis failed: {e}, using fallback")
            return self._simple_emotion_analysis(text)

    def _simple_emotion_analysis(self, text: str) -> tuple[float, float]:
        """
        简单的情感分析（SnowNLP 不可用时的降级方案）

        基于情绪词统计
        """
        # 正面词
        positive_words = {'喜欢', '高兴', '开心', '快乐', '幸福', '满意', '好'}
        # 负面词
        negative_words = {'难过', '伤心', '痛苦', '失望', '讨厌', '坏', '差'}

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        total = positive_count + negative_count
        if total == 0:
            emotion_polarity = 0.0
        else:
            emotion_polarity = (positive_count - negative_count) / total

        # 主观性估计
        subjectivity = self._estimate_subjectivity(text)

        return round(emotion_polarity, 3), round(subjectivity, 3)

    def _estimate_subjectivity(self, text: str) -> float:
        """
        估计主观性

        基于：
        1. 第一人称代词频率（"我"、"我们"）
        2. 情绪词频率
        3. 程度副词频率（"非常"、"特别"）
        """
        text_length = len(text)
        if text_length == 0:
            return 0.0

        # 第一人称
        first_person_count = text.count('我') + text.count('我们')

        # 情绪词
        emotion_count = sum(1 for word in self.EMOTION_WORDS if word in text)

        # 程度副词
        degree_words = ['非常', '特别', '十分', '很', '太', '极其']
        degree_count = sum(text.count(word) for word in degree_words)

        # 综合计算
        subjectivity = min(
            (first_person_count * 0.3 + emotion_count * 0.5 + degree_count * 0.2) / text_length * 100,
            1.0
        )

        return subjectivity

    def _calculate_emotion_density(self, text: str, word_count: int) -> float:
        """
        计算情绪词密度

        情绪词数量 / 总字数
        """
        if word_count == 0:
            return 0.0

        jieba = self._load_jieba()

        # 分词
        words = list(jieba.cut(text))

        # 统计情绪词
        emotion_word_count = sum(1 for word in words if word in self.EMOTION_WORDS)

        density = emotion_word_count / word_count

        return round(density, 4)

    def _calculate_avg_word_length(self, text: str) -> float:
        """
        计算平均词长

        使用 jieba 分词后，计算平均每个词的字符数
        """
        jieba = self._load_jieba()

        # 分词
        words = list(jieba.cut(text))

        # 过滤空词和标点
        words = [w for w in words if w.strip() and not re.match(r'^[^\w]+$', w)]

        if len(words) == 0:
            return 0.0

        total_length = sum(len(word) for word in words)
        avg_length = total_length / len(words)

        return round(avg_length, 2)

    def quantify_batch(self, texts: list[str]) -> list[QuantifiedMetrics]:
        """
        批量量化文本

        Args:
            texts: 文本列表

        Returns:
            list[QuantifiedMetrics]: 量化指标列表
        """
        logger.info(f"Batch quantifying {len(texts)} texts")

        results = []
        for text in texts:
            metrics = self.quantify(text)
            results.append(metrics)

        return results

    def to_dict(self, metrics: QuantifiedMetrics) -> Dict[str, Any]:
        """
        将量化指标转换为字典

        Args:
            metrics: 量化指标

        Returns:
            Dict: 字典格式
        """
        return {
            'word_count': metrics.word_count,
            'sentence_count': metrics.sentence_count,
            'exclamation_count': metrics.exclamation_count,
            'emotion_polarity': metrics.emotion_polarity,
            'subjectivity': metrics.subjectivity,
            'emotion_word_density': metrics.emotion_word_density,
            'avg_word_length': metrics.avg_word_length
        }


def create_quantifier() -> TextStructurizationQuantifier:
    """
    工厂方法：创建量化器实例

    Returns:
        TextStructurizationQuantifier: 量化器实例
    """
    return TextStructurizationQuantifier()


# 快捷函数
def quantify_text(text: str) -> Dict[str, Any]:
    """
    快捷函数：量化单个文本

    Args:
        text: 文本

    Returns:
        Dict: 量化指标字典
    """
    quantifier = create_quantifier()
    metrics = quantifier.quantify(text)
    return quantifier.to_dict(metrics)
