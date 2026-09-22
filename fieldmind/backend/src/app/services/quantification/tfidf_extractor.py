"""
TF-IDF关键词提取器

基于TF-IDF算法提取文本关键词：
- 计算词频（TF）
- 计算逆文档频率（IDF）
- 提取Top-K关键词
"""

import numpy as np
import json
import logging
import jieba

logger = logging.getLogger(__name__)


def extract_tfidf_keywords_for_chunk(
    chunk_text: str,
    all_chunks: list,
    top_k: int = 10
) -> list:
    """
    基于TF-IDF提取单个chunk的关键词

    Args:
        chunk_text: 当前chunk的文本
        all_chunks: 项目所有chunk的文本列表
        top_k: 返回Top-K关键词

    Returns:
        关键词列表
    """
    if not chunk_text or not all_chunks:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        # 使用jieba分词器
        def jieba_tokenizer(text):
            return list(jieba.cut(text))

        # 构建TF-IDF向量化器
        vectorizer = TfidfVectorizer(
            max_features=500,
            tokenizer=jieba_tokenizer,
            lowercase=False,
            token_pattern=None
        )

        # 对所有chunks建立TF-IDF矩阵
        tfidf_matrix = vectorizer.fit_transform(all_chunks)
        feature_names = vectorizer.get_feature_names_out()

        # 找到当前chunk的索引
        try:
            idx = all_chunks.index(chunk_text)
        except ValueError:
            # 如果找不到，返回空列表
            return []

        # 获取当前chunk的TF-IDF向量
        vector = tfidf_matrix[idx].toarray()[0]

        # 获取Top-K关键词
        top_indices = np.argsort(vector)[-top_k:][::-1]
        top_keywords = [
            feature_names[i] for i in top_indices
            if i < len(feature_names) and vector[i] > 0
        ]

        return top_keywords

    except ImportError:
        logger.warning("sklearn未安装，使用简单TF方法")
        # 降级方案：使用简单的词频统计
        return extract_simple_keywords(chunk_text, top_k)

    except Exception as e:
        logger.error(f"TF-IDF关键词提取失败: {e}")
        return []


def extract_simple_keywords(text: str, top_k: int = 10) -> list:
    """
    简单的关键词提取（基于词频）

    Args:
        text: 文本
        top_k: Top-K关键词

    Returns:
        关键词列表
    """
    try:
        # 分词
        words = jieba.cut(text)

        # 过滤停用词和单字
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '这', '也', '上', '着', '到', '说', '为'}
        words = [w for w in words if len(w) > 1 and w not in stopwords]

        # 统计词频
        from collections import Counter
        word_freq = Counter(words)

        # 返回Top-K
        top_words = [word for word, _ in word_freq.most_common(top_k)]
        return top_words

    except Exception as e:
        logger.error(f"简单关键词提取失败: {e}")
        return []
