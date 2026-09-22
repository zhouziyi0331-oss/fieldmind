"""
内容类特征提取器

提取文本的内容类特征：
- 情绪词密度
- 关键词密度
"""

import jieba
import logging

logger = logging.getLogger(__name__)

# 情绪词表（来自需求文档中的示例）
EMOTION_WORDS = {
    '喜欢', '讨厌', '满意', '愤怒', '开心', '失望', '激动', '惊讶',
    '好', '差', '棒', '糟', '爱', '恨', '希望', '害怕', '担心', '相信',
    '感谢', '抱歉', '幸福', '痛苦', '快乐', '悲伤', '兴奋', '焦虑',
    '高兴', '难过', '生气', '紧张', '放心', '安心', '舒服', '难受',
    '喜悦', '哀伤', '恐惧', '惊喜', '遗憾', '满足', '不满', '欣慰'
}


def extract_content_features(text: str, keyword_list: list = None) -> dict:
    """
    提取内容类特征

    Args:
        text: 输入文本
        keyword_list: 自定义关键词列表（可选）

    Returns:
        包含内容类特征的字典
    """
    if not text or not text.strip():
        return {
            'emotion_word_density': 0.0,
            'keyword_density': 0.0,
        }

    try:
        # 分词
        words = list(jieba.cut(text))
        words = [w for w in words if w.strip()]
        word_count = len(words)

        if word_count == 0:
            return {
                'emotion_word_density': 0.0,
                'keyword_density': 0.0,
            }

        # 情绪词密度
        emotion_count = sum(1 for w in words if w in EMOTION_WORDS)
        emotion_density = emotion_count / word_count

        # 关键词密度（如果传入关键词列表）
        keyword_density = 0.0
        if keyword_list:
            keyword_count = sum(1 for w in words if w in keyword_list)
            keyword_density = keyword_count / word_count

        return {
            'emotion_word_density': round(emotion_density, 4),
            'keyword_density': round(keyword_density, 4),
        }

    except Exception as e:
        logger.error(f"内容类特征提取失败: {e}")
        return {
            'emotion_word_density': 0.0,
            'keyword_density': 0.0,
        }
