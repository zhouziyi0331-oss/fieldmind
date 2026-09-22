#!/usr/bin/env python3
"""
Week 4-5: 数据增强核心模块

功能：
1. 情感分析 - 计算 emotion_polarity, emotion_intensity, sentiment_label
2. 关键词提取 - 提取核心关键词
3. 维度分类 - 自动分类到知识维度
4. 质量评分 - 计算 quality_score, completeness_score
5. Speaker 识别 - 从文本中识别说话人

核心函数：
- create_enriched_chunk() - 创建增强型 Chunk
- enrich_existing_chunks() - 批量增强现有数据

执行时间：2026-09-13
作者：FieldMind Architecture Team
"""

import re
import json
import jieba
import jieba.analyse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter

# ============================================================================
# 配置
# ============================================================================

# 维度分类规则
DIMENSION_RULES = {
    '技术': ['技术', '开发', '代码', '系统', '架构', '算法', '编程', 'API', '数据库'],
    '产品': ['产品', '功能', '需求', '用户', '体验', '设计', '原型', '迭代'],
    '业务': ['业务', '市场', '销售', '运营', '客户', '收入', '增长', '战略'],
    '管理': ['管理', '团队', '协作', '流程', '计划', '进度', '风险', '资源'],
    '财务': ['财务', '预算', '成本', '投资', '融资', '利润', '现金流'],
    '法务': ['法务', '合同', '合规', '知识产权', '法律', '风险', '协议'],
    '人力': ['人力', '招聘', '培训', '绩效', '薪酬', '文化', '团队建设'],
    '研究': ['研究', '分析', '调研', '报告', '数据', '洞察', '趋势'],
}

# 情感词典（简化版，实际应使用更完整的词典）
POSITIVE_WORDS = {
    '好': 1.0, '很好': 1.5, '优秀': 2.0, '卓越': 2.5, '完美': 3.0,
    '成功': 2.0, '顺利': 1.5, '满意': 1.5, '高兴': 1.5, '喜欢': 1.0,
    '赞': 1.0, '棒': 1.5, '厉害': 2.0, '牛': 2.0, '强': 1.5,
    '有效': 1.0, '有用': 1.0, '清晰': 1.0, '准确': 1.5,
}

NEGATIVE_WORDS = {
    '差': -1.0, '很差': -1.5, '糟糕': -2.0, '失败': -2.5, '糟透了': -3.0,
    '问题': -1.0, '错误': -1.5, 'bug': -1.5, '故障': -2.0, '崩溃': -2.5,
    '不好': -1.0, '不行': -1.5, '不满': -1.5, '困难': -1.0, '复杂': -0.5,
    '延期': -1.0, '延迟': -1.0, '慢': -0.5, '低效': -1.5,
}

# Speaker 识别模式
SPEAKER_PATTERNS = [
    r'(?P<speaker>[^\s:：]+)[：:]\s*(?P<content>.+)',  # 张三：这是内容
    r'\[(?P<speaker>[^\]]+)\]\s*(?P<content>.+)',      # [张三] 这是内容
    r'(?P<speaker>[^\s]+)说[：":]?\s*(?P<content>.+)', # 张三说：这是内容
]


# ============================================================================
# 情感分析
# ============================================================================

class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self):
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS

    def analyze(self, text: str) -> Dict:
        """
        分析文本情感

        返回:
        {
            'polarity': float,      # 情感极性 [-1, 1]
            'intensity': float,     # 情感强度 [0, 1]
            'subjectivity': float,  # 主观性 [0, 1]
            'label': str           # 分类标签
        }
        """
        # 分词
        words = list(jieba.cut(text))

        # 计算情感分数
        positive_score = 0.0
        negative_score = 0.0
        emotion_word_count = 0

        for word in words:
            if word in self.positive_words:
                positive_score += self.positive_words[word]
                emotion_word_count += 1
            elif word in self.negative_words:
                negative_score += abs(self.negative_words[word])
                emotion_word_count += 1

        # 计算极性 (范围 [-1, 1])
        total_score = positive_score - negative_score
        word_count = len(words)

        if word_count > 0:
            polarity = max(-1.0, min(1.0, total_score / (word_count * 0.5)))
        else:
            polarity = 0.0

        # 计算强度 (范围 [0, 1])
        intensity = min(1.0, abs(total_score) / max(word_count * 0.3, 1))

        # 计算主观性 (情感词占比)
        subjectivity = min(1.0, emotion_word_count / max(word_count, 1))

        # 分类标签
        if polarity > 0.2:
            label = 'positive'
        elif polarity < -0.2:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'polarity': round(polarity, 3),
            'intensity': round(intensity, 3),
            'subjectivity': round(subjectivity, 3),
            'label': label
        }


# ============================================================================
# 关键词提取
# ============================================================================

class KeywordExtractor:
    """关键词提取器"""

    def __init__(self):
        # 配置 jieba
        jieba.setLogLevel(jieba.logging.INFO)

    def extract(self, text: str, top_k: int = 10) -> List[Dict]:
        """
        提取关键词

        返回: [{'word': str, 'weight': float}, ...]
        """
        # 使用 TF-IDF 提取关键词
        keywords_with_weights = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=True
        )

        # 格式化结果
        keywords = [
            {
                'word': word,
                'weight': round(weight, 4)
            }
            for word, weight in keywords_with_weights
        ]

        return keywords


# ============================================================================
# 维度分类
# ============================================================================

class DimensionClassifier:
    """维度分类器"""

    def __init__(self):
        self.rules = DIMENSION_RULES

    def classify(self, text: str, keywords: List[Dict]) -> Dict:
        """
        分类到知识维度

        返回:
        {
            'category': str,         # 主维度
            'sub_category': str,     # 子维度
            'tags': List[str],       # 标签
            'confidence': float      # 置信度
        }
        """
        # 分词
        words = set(jieba.cut(text))

        # 计算每个维度的得分
        scores = {}
        for dimension, dimension_keywords in self.rules.items():
            score = 0
            matched_keywords = []

            for keyword in dimension_keywords:
                if keyword in text or keyword in words:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                scores[dimension] = {
                    'score': score,
                    'keywords': matched_keywords
                }

        # 选择得分最高的维度
        if scores:
            sorted_dimensions = sorted(
                scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )

            top_dimension = sorted_dimensions[0][0]
            top_score = sorted_dimensions[0][1]['score']
            matched_keywords = sorted_dimensions[0][1]['keywords']

            # 置信度计算
            total_keywords = sum(d['score'] for d in scores.values())
            confidence = round(top_score / max(total_keywords, 1), 3)

            # 子维度（使用匹配的关键词）
            sub_category = matched_keywords[0] if matched_keywords else None

            return {
                'category': top_dimension,
                'sub_category': sub_category,
                'tags': matched_keywords[:5],  # 最多 5 个标签
                'confidence': confidence
            }
        else:
            # 未分类
            return {
                'category': '通用',
                'sub_category': None,
                'tags': [],
                'confidence': 0.0
            }


# ============================================================================
# 质量评分
# ============================================================================

class QualityScorer:
    """质量评分器"""

    def score(self, text: str, keywords: List[Dict], has_entities: int = 0) -> Dict:
        """
        计算文本质量分数

        返回:
        {
            'quality_score': float,       # 综合质量 [0, 1]
            'completeness_score': float,  # 完整性 [0, 1]
            'relevance_score': float,     # 相关性 [0, 1]
        }
        """
        # 长度评分（50-500 字为最佳）
        text_length = len(text)
        if text_length < 20:
            length_score = text_length / 50.0
        elif text_length <= 500:
            length_score = 1.0
        else:
            length_score = max(0.5, 1.0 - (text_length - 500) / 1000.0)

        # 关键词质量（关键词数量和权重）
        keyword_count = len(keywords)
        keyword_score = min(1.0, keyword_count / 10.0)

        if keywords:
            avg_weight = sum(kw['weight'] for kw in keywords) / len(keywords)
            keyword_quality = min(1.0, avg_weight * 10)
        else:
            keyword_quality = 0.0

        # 实体数量评分
        entity_score = min(1.0, has_entities / 5.0)

        # 完整性评分（基于标点、结构）
        has_period = '。' in text or '.' in text
        has_comma = '，' in text or ',' in text
        has_colon = '：' in text or ':' in text

        structure_score = 0.0
        if has_period:
            structure_score += 0.4
        if has_comma:
            structure_score += 0.3
        if has_colon:
            structure_score += 0.3

        completeness_score = (length_score * 0.5 + structure_score * 0.5)

        # 相关性评分（关键词 + 实体）
        relevance_score = (keyword_score * 0.5 + keyword_quality * 0.3 + entity_score * 0.2)

        # 综合质量
        quality_score = (
            length_score * 0.2 +
            keyword_score * 0.2 +
            keyword_quality * 0.2 +
            entity_score * 0.1 +
            structure_score * 0.15 +
            completeness_score * 0.15
        )

        return {
            'quality_score': round(quality_score, 3),
            'completeness_score': round(completeness_score, 3),
            'relevance_score': round(relevance_score, 3),
        }


# ============================================================================
# Speaker 识别
# ============================================================================

class SpeakerIdentifier:
    """说话人识别器"""

    def __init__(self):
        self.patterns = [re.compile(p) for p in SPEAKER_PATTERNS]

    def identify(self, text: str) -> Optional[Dict]:
        """
        识别说话人

        返回:
        {
            'speaker_name': str,     # 说话人名称
            'speaker_role': str,     # 角色（推测）
            'confidence': float      # 置信度
        }
        """
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                speaker_name = match.group('speaker').strip()

                # 角色推测（基于名称特征）
                role = self._infer_role(speaker_name)

                return {
                    'speaker_name': speaker_name,
                    'speaker_role': role,
                    'confidence': 0.8  # 正则匹配的置信度
                }

        return None

    def _infer_role(self, speaker_name: str) -> str:
        """推测说话人角色"""
        # 角色关键词
        role_keywords = {
            'CEO': ['CEO', 'ceo', '总裁', '董事长'],
            'CTO': ['CTO', 'cto', '技术总监', '首席技术官'],
            'PM': ['PM', 'pm', '产品经理', '产品负责人'],
            'Dev': ['开发', '工程师', 'developer', 'engineer'],
            'Designer': ['设计师', 'designer', 'UI', 'UX'],
            'QA': ['测试', 'QA', 'qa', 'tester'],
            'Manager': ['经理', 'manager', '主管', '负责人'],
        }

        for role, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword in speaker_name:
                    return role

        return 'Unknown'


# ============================================================================
# 核心增强函数
# ============================================================================

class ChunkEnricher:
    """Chunk 增强器"""

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()
        self.dimension_classifier = DimensionClassifier()
        self.quality_scorer = QualityScorer()
        self.speaker_identifier = SpeakerIdentifier()

    def enrich(self, text: str, existing_data: Dict = None) -> Dict:
        """
        增强 Chunk 数据

        参数:
            text: Chunk 文本内容
            existing_data: 现有数据（可选）

        返回:
            包含所有增强字段的字典
        """
        if not text or len(text.strip()) == 0:
            return self._empty_enrichment()

        # 1. 情感分析
        sentiment = self.sentiment_analyzer.analyze(text)

        # 2. 关键词提取
        keywords = self.keyword_extractor.extract(text, top_k=10)

        # 3. 维度分类
        dimension = self.dimension_classifier.classify(text, keywords)

        # 4. Speaker 识别
        speaker = self.speaker_identifier.identify(text)

        # 5. 质量评分
        entities_count = existing_data.get('entities_count', 0) if existing_data else 0
        quality = self.quality_scorer.score(text, keywords, entities_count)

        # 6. 组装结果
        enriched = {
            # 情感字段
            'emotion_polarity': sentiment['polarity'],
            'emotion_intensity': sentiment['intensity'],
            'subjectivity': sentiment['subjectivity'],
            'sentiment_label': sentiment['label'],

            # 维度字段
            'dimension_category': dimension['category'],
            'dimension_sub_category': dimension['sub_category'],
            'dimension_tags': json.dumps(dimension['tags'], ensure_ascii=False),
            'dimension_confidence': dimension['confidence'],

            # 关键词字段
            'keywords': json.dumps(keywords, ensure_ascii=False),
            'entities_count': entities_count,

            # 质量字段
            'quality_score': quality['quality_score'],
            'completeness_score': quality['completeness_score'],
            'relevance_score': quality['relevance_score'],
            'has_context': 1 if len(text) > 50 else 0,

            # Speaker 字段
            'speaker_id': None,  # 需要后续关联到 entities 表
            'speaker_role': speaker['speaker_role'] if speaker else None,
            'speaker_confidence': speaker['confidence'] if speaker else 0.0,

            # 同步字段
            'updated_at': datetime.now().isoformat(),
        }

        # 如果识别到 speaker，记录名称（用于后续映射）
        if speaker:
            enriched['_speaker_name'] = speaker['speaker_name']

        return enriched

    def _empty_enrichment(self) -> Dict:
        """空文本的增强结果"""
        return {
            'emotion_polarity': 0.0,
            'emotion_intensity': 0.0,
            'subjectivity': 0.0,
            'sentiment_label': 'neutral',
            'dimension_category': '通用',
            'dimension_sub_category': None,
            'dimension_tags': '[]',
            'dimension_confidence': 0.0,
            'keywords': '[]',
            'entities_count': 0,
            'quality_score': 0.0,
            'completeness_score': 0.0,
            'relevance_score': 0.0,
            'has_context': 0,
            'speaker_id': None,
            'speaker_role': None,
            'speaker_confidence': 0.0,
            'updated_at': datetime.now().isoformat(),
        }


# ============================================================================
# 测试示例
# ============================================================================

def test_enrichment():
    """测试增强功能"""
    enricher = ChunkEnricher()

    # 测试文本
    test_texts = [
        "张三：这个产品设计非常优秀，用户体验很好，我们应该继续优化。",
        "技术架构存在严重问题，系统频繁崩溃，需要重构。",
        "本季度销售业绩突破历史新高，团队表现卓越。",
        "会议讨论了下一步的产品迭代计划和时间安排。",
    ]

    print("=" * 70)
    print("Chunk 增强功能测试")
    print("=" * 70)

    for i, text in enumerate(test_texts, 1):
        print(f"\n[测试 {i}] {text[:30]}...")
        print("-" * 70)

        result = enricher.enrich(text)

        print(f"情感极性:   {result['emotion_polarity']:+.3f}")
        print(f"情感强度:   {result['emotion_intensity']:.3f}")
        print(f"情感标签:   {result['sentiment_label']}")
        print(f"维度分类:   {result['dimension_category']}")
        print(f"子类别:     {result['dimension_sub_category']}")
        print(f"质量评分:   {result['quality_score']:.3f}")
        print(f"关键词:     {json.loads(result['keywords'])[:3]}")

        if result.get('_speaker_name'):
            print(f"说话人:     {result['_speaker_name']} ({result['speaker_role']})")

    print("\n" + "=" * 70)
    print("✅ 测试完成")


if __name__ == "__main__":
    test_enrichment()
