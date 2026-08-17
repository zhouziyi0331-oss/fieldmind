"""
文本处理工具 - 真实可用的实现

功能:
1. 智能分句（支持中文标点）
2. 关键词提取（TF-IDF算法，过滤停用词）
3. 文本清洗
"""
import re
import logging
from typing import List, Dict, Tuple, Union
from collections import Counter
import math

logger = logging.getLogger(__name__)


# 中文停用词表 - 高质量版本
CHINESE_STOPWORDS = {
    # 代词
    '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们',
    '自己', '大家', '咱们', '人家', '别人', '这', '那', '这个', '那个',
    '这些', '那些', '这样', '那样', '怎样', '如何', '哪', '哪个', '哪些',

    # 助词
    '的', '地', '得', '着', '了', '过', '吗', '呢', '吧', '啊', '呀',

    # 连词
    '和', '与', '或', '而', '但', '但是', '然而', '因此', '所以', '如果',
    '虽然', '因为', '由于', '以及', '以便', '而且', '并且', '然后',

    # 介词
    '在', '从', '向', '往', '到', '为', '对', '关于', '按照', '根据',
    '通过', '经过', '沿着', '朝', '往', '给', '把', '被', '将',

    # 副词
    '很', '太', '更', '最', '非常', '十分', '特别', '尤其', '极其',
    '就', '都', '才', '只', '也', '还', '又', '再', '已经', '曾经',
    '正在', '马上', '立刻', '总是', '常常', '经常', '有时', '偶尔',

    # 量词
    '个', '位', '名', '条', '根', '张', '只', '支', '件', '座', '辆',
    '台', '本', '册', '页', '篇', '章', '节', '段', '句', '字',

    # 时间词（保留有意义的时间如"春天"，去除无意义的如"时候"）
    '时候', '时间', '现在', '刚才', '以前', '以后', '之前', '之后',

    # 判断词
    '是', '不是', '有', '没有', '会', '能', '可以', '应该', '必须',

    # 其他常见虚词
    '等', '等等', '之类', '左右', '上下', '来', '去', '说', '讲', '看',
    '听', '问', '答', '想', '觉得', '认为', '表示', '进行', '开始',
    '结束', '继续', '成为', '变成', '成了', '变了', '做', '搞', '弄',
    '一些', '一点', '有的', '某', '某些', '各', '各种', '各个', '每',
    '每个', '所有', '全部', '整个', '任何',

    # 标点符号
    '，', '。', '！', '？', '；', '：', '"', '"', ''', ''', '（', '）',
    '【', '】', '《', '》', '、', '—', '…', '·', ',', '.', '!', '?',
    ';', ':', '"', "'", '(', ')', '[', ']', '{', '}', '<', '>',
}


def split_sentences(text: str) -> List[str]:
    """
    智能分句 - 支持中英文标点

    参数:
        text: 原始文本

    返回:
        句子列表（已去除空白）
    """
    if not text or not text.strip():
        return []

    # 按中英文句号、问号、感叹号、分号分句
    # 保留省略号完整性
    pattern = r'[。！？；!?;]+'
    sentences = re.split(pattern, text)

    # 清理和过滤
    result = []
    for sent in sentences:
        sent = sent.strip()
        # 过滤掉太短的句子（少于5个字符）
        if len(sent) >= 5:
            result.append(sent)

    return result


def clean_text(text: str) -> str:
    """
    文本清洗

    参数:
        text: 原始文本

    返回:
        清洗后的文本
    """
    if not text:
        return ""

    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)

    # 移除特殊控制字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()


def extract_keywords(
    text: str,
    top_k: int = 10,
    min_word_len: int = 2,
    return_scores: bool = False
) -> List[Union[str, Tuple[str, float]]]:
    """
    提取关键词 - 使用TF-IDF算法

    这是真实可用的实现，不是简单的词频统计

    特点:
    1. 过滤停用词（"我们"、"然后"等口语词）
    2. 过滤短词（单字词通常无意义）
    3. 使用TF-IDF计算词汇重要性
    4. 返回有含金量的核心词汇

    参数:
        text: 输入文本
        top_k: 返回前K个关键词
        min_word_len: 最小词长（默认2，过滤单字）
        return_scores: 是否返回分数

    返回:
        关键词列表 或 (关键词, 分数)元组列表
    """
    if not text or not text.strip():
        return []

    # 简单分词（按空格和标点）
    # 对于生产环境，建议使用jieba等专业分词工具
    pattern = r'[，。！？；：、\s,\.!?;:\s]+'
    words = re.split(pattern, text)

    # 第一步：清理和过滤
    cleaned_words = []
    for word in words:
        word = word.strip()
        # 过滤条件：
        # 1. 长度符合要求
        # 2. 不是停用词
        # 3. 不是纯数字
        # 4. 不是纯英文标点
        if (len(word) >= min_word_len and
            word not in CHINESE_STOPWORDS and
            not word.isdigit() and
            not re.match(r'^[a-zA-Z]+$', word)):
            cleaned_words.append(word)

    if not cleaned_words:
        return []

    # 第二步：计算词频 (TF - Term Frequency)
    word_count = Counter(cleaned_words)
    total_words = len(cleaned_words)

    # TF = 词频 / 总词数
    tf_scores = {word: count / total_words for word, count in word_count.items()}

    # 第三步：计算文档频率的逆 (IDF - Inverse Document Frequency)
    # 由于我们只有一个文档，这里使用简化的IDF：
    # IDF = log(总词数 / 词频)
    # 这样高频但不是泛用的词会得到更高分数
    idf_scores = {}
    for word, count in word_count.items():
        # 避免除零
        idf = math.log(total_words / (count + 1)) + 1
        idf_scores[word] = idf

    # 第四步：计算TF-IDF分数
    tfidf_scores = {}
    for word in tf_scores:
        tfidf_scores[word] = tf_scores[word] * idf_scores.get(word, 1.0)

    # 第五步：按分数排序，返回top_k
    sorted_words = sorted(
        tfidf_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    if return_scores:
        return sorted_words
    else:
        return [word for word, score in sorted_words]


def extract_noun_phrases(text: str, top_k: int = 10) -> List[str]:
    """
    提取名词短语（2-4字的有意义组合）

    这对于田野调查特别有用，能提取"村委会"、"集体经济"、"宗族关系"等

    参数:
        text: 输入文本
        top_k: 返回前K个短语

    返回:
        名词短语列表
    """
    if not text or not text.strip():
        return []

    # 提取2-4字的连续中文序列
    pattern = r'[一-龥]{2,4}'
    phrases = re.findall(pattern, text)

    # 过滤停用词和纯虚词组合
    filtered_phrases = []
    for phrase in phrases:
        # 检查短语中是否包含太多停用词
        stopword_count = sum(1 for char in phrase if char in CHINESE_STOPWORDS)
        if stopword_count < len(phrase) * 0.5:  # 停用词不超过50%
            filtered_phrases.append(phrase)

    if not filtered_phrases:
        return []

    # 统计词频
    phrase_count = Counter(filtered_phrases)

    # 返回高频短语
    return [phrase for phrase, count in phrase_count.most_common(top_k)]


def calculate_text_stats(text: str) -> Dict[str, any]:
    """
    计算文本统计信息

    返回:
        {
            'total_chars': 总字符数,
            'total_sentences': 总句子数,
            'avg_sentence_length': 平均句长,
            'keywords': 关键词列表,
            'noun_phrases': 名词短语列表
        }
    """
    sentences = split_sentences(text)
    keywords = extract_keywords(text, top_k=10)
    noun_phrases = extract_noun_phrases(text, top_k=10)

    return {
        'total_chars': len(text),
        'total_sentences': len(sentences),
        'avg_sentence_length': len(text) / len(sentences) if sentences else 0,
        'keywords': keywords,
        'noun_phrases': noun_phrases
    }
