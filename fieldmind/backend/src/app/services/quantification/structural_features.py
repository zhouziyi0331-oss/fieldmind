"""
结构性特征提取器

提取文本的结构性特征：
- 字数
- 句数
- 段落数
- 平均词长
- 平均句长
"""

import re
import jieba
import logging

logger = logging.getLogger(__name__)


def extract_structural_features(text: str) -> dict:
    """
    提取结构性特征

    Args:
        text: 输入文本

    Returns:
        包含结构性特征的字典
    """
    if not text or not text.strip():
        return {
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'avg_word_length': 0.0,
            'avg_sentence_length': 0.0,
        }

    try:
        # 分词
        words = list(jieba.cut(text))
        words = [w for w in words if w.strip()]  # 过滤空白词

        # 分句
        sentences = re.split(r'[。！？\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 分段
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        # 计算平均词长
        total_word_len = sum(len(w) for w in words)
        avg_word_length = total_word_len / len(words) if words else 0

        # 计算平均句长（词数）
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
        }

    except Exception as e:
        logger.error(f"结构性特征提取失败: {e}")
        return {
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'avg_word_length': 0.0,
            'avg_sentence_length': 0.0,
        }
