"""
Chunk Metrics Calculator - 文本块指标计算服务

职责：
- 计算15个chunk指标（semantic, quality, complexity）
- 写入 document_chunks 表
- 记录到 metric_calculation_history 表
- 支持批量计算和增量更新

指标分类：
1. Semantic（语义）：semantic_density, coherence_score, information_gain, topic_relevance
2. Quality（质量）：readability_score, sentiment_score
3. Complexity（复杂度）：avg_sentence_length, lexical_diversity, complexity_score
4. Count（统计）：entity_count, keyword_count
"""

import re
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetrics:
    """Chunk指标数据类"""
    # Semantic metrics
    semantic_density: Optional[float] = None
    coherence_score: Optional[float] = None
    information_gain: Optional[float] = None
    topic_relevance: Optional[float] = None

    # Quality metrics
    readability_score: Optional[float] = None
    sentiment_score: Optional[float] = None

    # Complexity metrics
    avg_sentence_length: Optional[float] = None
    lexical_diversity: Optional[float] = None
    complexity_score: Optional[float] = None

    # Count metrics
    entity_count: int = 0
    keyword_count: int = 0

    # Metadata
    calculation_duration_ms: Optional[int] = None


class ChunkMetricsCalculator:
    """
    Chunk指标计算器

    功能：
    1. 计算15个文本指标
    2. 支持中英文混合文本
    3. 批量计算优化
    4. 写入数据库（chunks表 + history表）
    """

    def __init__(self, db_session=None):
        """
        初始化指标计算器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

        # 延迟加载NLP工具
        self._jieba = None
        self._stopwords = None

        # 缓存指标ID（避免重复查询）
        self._metric_id_cache = {}

        logger.info("ChunkMetricsCalculator initialized")

    def _load_jieba(self):
        """延迟加载jieba"""
        if self._jieba is None:
            import jieba
            import jieba.analyse
            self._jieba = jieba
            logger.info("Loaded jieba for Chinese text processing")
        return self._jieba

    def _load_stopwords(self) -> set:
        """加载停用词表"""
        if self._stopwords is None:
            # 简单的中英文停用词
            self._stopwords = {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'
            }
        return self._stopwords

    def calculate_all_metrics(
        self,
        chunk_text: str,
        chunk_id: str,
        document_context: Optional[Dict[str, Any]] = None,
        entities: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> ChunkMetrics:
        """
        计算所有指标

        Args:
            chunk_text: chunk文本内容
            chunk_id: chunk ID
            document_context: 文档上下文（用于计算相关性）
            entities: 已提取的实体列表
            keywords: 已提取的关键词列表

        Returns:
            ChunkMetrics: 计算结果
        """
        start_time = time.time()

        if not chunk_text or len(chunk_text.strip()) == 0:
            logger.warning(f"Empty chunk text for chunk_id={chunk_id}")
            return ChunkMetrics()

        logger.info(f"Calculating metrics for chunk {chunk_id} (length={len(chunk_text)})")

        # 基础统计
        word_count = self._count_words(chunk_text)
        char_count = len(chunk_text)
        sentence_count = self._count_sentences(chunk_text)

        # 1. Semantic metrics
        semantic_density = self._calculate_semantic_density(
            chunk_text, entities, keywords, word_count
        )
        coherence_score = self._calculate_coherence(chunk_text, sentence_count)
        information_gain = self._calculate_information_gain(
            chunk_text, document_context
        )
        topic_relevance = self._calculate_topic_relevance(
            chunk_text, document_context
        )

        # 2. Quality metrics
        readability_score = self._calculate_readability(
            chunk_text, word_count, sentence_count
        )
        sentiment_score = self._calculate_sentiment(chunk_text)

        # 3. Complexity metrics
        avg_sentence_length = self._calculate_avg_sentence_length(
            word_count, sentence_count
        )
        lexical_diversity = self._calculate_lexical_diversity(chunk_text, word_count)
        complexity_score = self._calculate_complexity(
            chunk_text, avg_sentence_length, lexical_diversity
        )

        # 4. Count metrics
        entity_count = len(entities) if entities else 0
        keyword_count = len(keywords) if keywords else 0

        duration_ms = int((time.time() - start_time) * 1000)

        metrics = ChunkMetrics(
            semantic_density=semantic_density,
            coherence_score=coherence_score,
            information_gain=information_gain,
            topic_relevance=topic_relevance,
            readability_score=readability_score,
            sentiment_score=sentiment_score,
            avg_sentence_length=avg_sentence_length,
            lexical_diversity=lexical_diversity,
            complexity_score=complexity_score,
            entity_count=entity_count,
            keyword_count=keyword_count,
            calculation_duration_ms=duration_ms
        )

        logger.info(f"Metrics calculated in {duration_ms}ms")
        return metrics

    # ========== Semantic Metrics ==========

    def _calculate_semantic_density(
        self,
        text: str,
        entities: Optional[List[str]],
        keywords: Optional[List[str]],
        word_count: int
    ) -> float:
        """
        语义密度 = (实体数 + 关键词数) / 总词数

        范围：0.0 - 1.0（实际通常在 0.05 - 0.30）
        """
        if word_count == 0:
            return 0.0

        entity_count = len(entities) if entities else 0
        keyword_count = len(keywords) if keywords else 0

        density = (entity_count + keyword_count) / word_count
        return min(density, 1.0)  # 限制最大值为1.0

    def _calculate_coherence(self, text: str, sentence_count: int) -> float:
        """
        连贯性得分 - 简化版本

        基于：
        1. 句子长度方差（低方差 = 高连贯）
        2. 连接词出现频率
        3. 代词使用（指代前文）

        范围：0.0 - 1.0
        """
        if sentence_count < 2:
            return 1.0  # 单句默认完全连贯

        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return 1.0

        # 1. 句子长度一致性（方差越小越好）
        lengths = [len(s) for s in sentences]
        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        length_score = 1.0 / (1.0 + variance / 1000.0)  # 归一化

        # 2. 连接词得分
        connectors = ['但是', '因此', '所以', '然而', '而且', '并且', '同时', '另外',
                     'however', 'therefore', 'moreover', 'furthermore', 'additionally']
        connector_count = sum(1 for word in connectors if word in text.lower())
        connector_score = min(connector_count / (sentence_count * 0.3), 1.0)

        # 3. 代词使用（简化版）
        pronouns = ['他', '她', '它', '这', '那', '其', 'he', 'she', 'it', 'this', 'that']
        pronoun_count = sum(1 for word in pronouns if word in text.lower())
        pronoun_score = min(pronoun_count / (sentence_count * 0.5), 1.0)

        # 综合得分（权重：长度40%，连接词30%，代词30%）
        coherence = (length_score * 0.4 + connector_score * 0.3 + pronoun_score * 0.3)
        return round(coherence, 3)

    def _calculate_information_gain(
        self,
        text: str,
        document_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        信息增益 = 1 - cosine_similarity(当前chunk, 上下文)

        简化版：基于词汇重叠率
        范围：0.0 - 1.0（值越高表示新信息越多）
        """
        if not document_context or 'previous_chunks' not in document_context:
            return 0.8  # 默认中等信息增益

        current_words = set(self._tokenize(text))
        if len(current_words) == 0:
            return 0.0

        # 计算与前文的词汇重叠
        previous_text = document_context.get('previous_chunks', '')
        if not previous_text:
            return 0.8

        previous_words = set(self._tokenize(previous_text))
        if len(previous_words) == 0:
            return 0.8

        overlap = len(current_words & previous_words)
        union = len(current_words | previous_words)

        if union == 0:
            return 0.5

        similarity = overlap / union
        information_gain = 1.0 - similarity

        return round(information_gain, 3)

    def _calculate_topic_relevance(
        self,
        text: str,
        document_context: Optional[Dict[str, Any]]
    ) -> float:
        """
        主题相关性 - chunk与文档主题的相关度

        简化版：基于主题词重叠
        范围：0.0 - 1.0
        """
        if not document_context or 'document_keywords' not in document_context:
            return 0.7  # 默认中等相关性

        doc_keywords = set(document_context.get('document_keywords', []))
        if len(doc_keywords) == 0:
            return 0.7

        chunk_words = set(self._tokenize(text))
        if len(chunk_words) == 0:
            return 0.0

        # 计算主题词命中率
        hits = len(chunk_words & doc_keywords)
        relevance = hits / len(doc_keywords)

        return round(min(relevance, 1.0), 3)

    # ========== Quality Metrics ==========

    def _calculate_readability(
        self,
        text: str,
        word_count: int,
        sentence_count: int
    ) -> float:
        """
        可读性得分 - 简化版 Flesch Reading Ease

        简化公式：基于平均句长和平均词长
        范围：0.0 - 100.0（越高越易读）
        """
        if sentence_count == 0 or word_count == 0:
            return 50.0  # 默认中等可读性

        avg_sentence_length = word_count / sentence_count
        avg_word_length = len(text) / word_count

        # 简化的可读性公式
        # 句子越短、词越短 = 可读性越高
        readability = 100.0 - (avg_sentence_length * 1.5) - (avg_word_length * 5.0)

        # 限制范围
        readability = max(0.0, min(100.0, readability))

        return round(readability, 2)

    def _calculate_sentiment(self, text: str) -> float:
        """
        情感得分 - 简化版

        基于情感词典的简单统计
        范围：-1.0（负面）到 +1.0（正面）
        """
        # 简单的情感词典
        positive_words = {'好', '棒', '优秀', '成功', '喜欢', '满意', '高兴', '快乐',
                         'good', 'great', 'excellent', 'success', 'happy', 'like', 'love'}
        negative_words = {'坏', '差', '失败', '讨厌', '不满', '难过', '糟糕',
                         'bad', 'poor', 'fail', 'hate', 'sad', 'terrible', 'awful'}

        text_lower = text.lower()
        words = self._tokenize(text_lower)

        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0  # 中性

        sentiment = (positive_count - negative_count) / total_sentiment_words
        return round(sentiment, 3)

    # ========== Complexity Metrics ==========

    def _calculate_avg_sentence_length(
        self,
        word_count: int,
        sentence_count: int
    ) -> float:
        """
        平均句长 = 总词数 / 句子数

        范围：通常 5 - 30 词/句
        """
        if sentence_count == 0:
            return 0.0
        return round(word_count / sentence_count, 2)

    def _calculate_lexical_diversity(self, text: str, word_count: int) -> float:
        """
        词汇多样性（TTR: Type-Token Ratio）

        = 唯一词数 / 总词数
        范围：0.0 - 1.0（越高越多样）
        """
        if word_count == 0:
            return 0.0

        words = self._tokenize(text)
        unique_words = set(words)

        diversity = len(unique_words) / word_count
        return round(diversity, 3)

    def _calculate_complexity(
        self,
        text: str,
        avg_sentence_length: float,
        lexical_diversity: float
    ) -> float:
        """
        综合复杂度得分

        基于：
        1. 平均句长（30%）
        2. 词汇多样性（30%）
        3. 长词比例（40%）

        范围：0.0 - 10.0（越高越复杂）
        """
        # 1. 句长复杂度（归一化到0-10）
        sentence_complexity = min(avg_sentence_length / 3.0, 10.0)

        # 2. 词汇多样性复杂度（直接转换到0-10）
        diversity_complexity = lexical_diversity * 10.0

        # 3. 长词复杂度
        words = self._tokenize(text)
        if len(words) == 0:
            long_word_ratio = 0.0
        else:
            long_words = [w for w in words if len(w) > 6]
            long_word_ratio = len(long_words) / len(words)
        long_word_complexity = long_word_ratio * 10.0

        # 综合得分
        complexity = (
            sentence_complexity * 0.3 +
            diversity_complexity * 0.3 +
            long_word_complexity * 0.4
        )

        return round(complexity, 2)

    # ========== Helper Methods ==========

    def _count_words(self, text: str) -> int:
        """统计词数（支持中英文混合）"""
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)

        # 中文字符（每个字符算一个词）
        chinese_chars = re.findall(r'[一-鿿]', text)

        return len(english_words) + len(chinese_chars)

    def _count_sentences(self, text: str) -> int:
        """统计句子数"""
        # 中英文句子分隔符
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        sentences = re.split(r'[。！？.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _tokenize(self, text: str) -> List[str]:
        """分词（支持中英文）"""
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())

        # 中文分词
        chinese_text = re.sub(r'[a-zA-Z0-9\s]', '', text)
        if chinese_text:
            jieba = self._load_jieba()
            chinese_words = list(jieba.cut(chinese_text))
        else:
            chinese_words = []

        # 合并并过滤停用词
        stopwords = self._load_stopwords()
        all_words = english_words + chinese_words
        filtered_words = [w for w in all_words if w not in stopwords and len(w) > 1]

        return filtered_words

    # ========== Database Operations ==========

    def save_metrics_to_db(
        self,
        chunk_id: str,
        metrics: ChunkMetrics
    ) -> bool:
        """
        保存指标到数据库

        1. 更新 document_chunks 表
        2. 记录到 metric_calculation_history 表

        Args:
            chunk_id: chunk ID
            metrics: 计算的指标

        Returns:
            bool: 是否成功
        """
        if not self.db:
            logger.warning("No db_session provided, skipping save")
            return False

        try:
            from sqlalchemy import text

            # 1. 更新 document_chunks 表
            update_sql = text("""
                UPDATE document_chunks
                SET
                    semantic_density = :semantic_density,
                    coherence_score = :coherence_score,
                    information_gain = :information_gain,
                    topic_relevance = :topic_relevance,
                    readability_score = :readability_score,
                    sentiment_score = :sentiment_score,
                    avg_sentence_length = :avg_sentence_length,
                    lexical_diversity = :lexical_diversity,
                    complexity_score = :complexity_score,
                    entity_count = :entity_count,
                    keyword_count = :keyword_count
                WHERE id = :chunk_id
            """)

            self.db.execute(update_sql, {
                'chunk_id': chunk_id,
                'semantic_density': metrics.semantic_density,
                'coherence_score': metrics.coherence_score,
                'information_gain': metrics.information_gain,
                'topic_relevance': metrics.topic_relevance,
                'readability_score': metrics.readability_score,
                'sentiment_score': metrics.sentiment_score,
                'avg_sentence_length': metrics.avg_sentence_length,
                'lexical_diversity': metrics.lexical_diversity,
                'complexity_score': metrics.complexity_score,
                'entity_count': metrics.entity_count,
                'keyword_count': metrics.keyword_count
            })

            # 2. 记录到 metric_calculation_history 表
            self._save_to_history(chunk_id, metrics)

            self.db.commit()
            logger.info(f"Metrics saved to DB for chunk {chunk_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save metrics to DB: {e}")
            self.db.rollback()
            return False

    def _save_to_history(self, chunk_id: str, metrics: ChunkMetrics):
        """保存到指标计算历史表"""
        from sqlalchemy import text

        # 指标名称到值的映射
        metric_map = {
            'semantic_density': metrics.semantic_density,
            'coherence_score': metrics.coherence_score,
            'information_gain': metrics.information_gain,
            'topic_relevance': metrics.topic_relevance,
            'readability_score': metrics.readability_score,
            'sentiment_score': metrics.sentiment_score,
            'avg_sentence_length': metrics.avg_sentence_length,
            'lexical_diversity': metrics.lexical_diversity,
            'complexity_score': metrics.complexity_score,
            'entity_count': float(metrics.entity_count),
            'keyword_count': float(metrics.keyword_count)
        }

        for metric_name, metric_value in metric_map.items():
            if metric_value is None:
                continue

            # 获取 metric_id
            metric_id = self._get_metric_id(metric_name)
            if not metric_id:
                logger.warning(f"Metric '{metric_name}' not found in dictionary")
                continue

            # 插入历史记录
            insert_sql = text("""
                INSERT INTO metric_calculation_history
                (entity_type, entity_id, metric_id, metric_value, calculation_method, calculation_duration_ms, calculated_at)
                VALUES ('chunk', :chunk_id, :metric_id, :metric_value, 'ChunkMetricsCalculator', :duration_ms, :now)
            """)

            self.db.execute(insert_sql, {
                'chunk_id': chunk_id,
                'metric_id': metric_id,
                'metric_value': metric_value,
                'duration_ms': metrics.calculation_duration_ms,
                'now': datetime.utcnow()
            })

    def _get_metric_id(self, metric_name: str) -> Optional[int]:
        """获取指标ID（带缓存）"""
        if metric_name in self._metric_id_cache:
            return self._metric_id_cache[metric_name]

        from sqlalchemy import text
        result = self.db.execute(
            text("SELECT id FROM metric_dictionary WHERE metric_name = :name"),
            {'name': metric_name}
        ).fetchone()

        if result:
            metric_id = result[0]
            self._metric_id_cache[metric_name] = metric_id
            return metric_id

        return None

    def batch_calculate_and_save(
        self,
        chunks: List[Dict[str, Any]],
        document_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        批量计算并保存指标

        Args:
            chunks: chunk列表，每个包含 {id, text, entities, keywords}
            document_context: 文档上下文

        Returns:
            Dict: 统计信息
        """
        total = len(chunks)
        success = 0
        failed = 0
        start_time = time.time()

        logger.info(f"Batch calculating metrics for {total} chunks")

        for chunk in chunks:
            try:
                metrics = self.calculate_all_metrics(
                    chunk_text=chunk.get('text', ''),
                    chunk_id=chunk.get('id'),
                    document_context=document_context,
                    entities=chunk.get('entities'),
                    keywords=chunk.get('keywords')
                )

                if self.save_metrics_to_db(chunk.get('id'), metrics):
                    success += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.get('id')}: {e}")
                failed += 1

        duration = time.time() - start_time

        result = {
            'total': total,
            'success': success,
            'failed': failed,
            'duration_seconds': round(duration, 2),
            'avg_time_per_chunk_ms': round(duration * 1000 / total, 2) if total > 0 else 0
        }

        logger.info(f"Batch calculation completed: {result}")
        return result
