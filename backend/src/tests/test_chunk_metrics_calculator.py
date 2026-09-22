"""
测试 ChunkMetricsCalculator

验证：
1. 基础指标计算
2. 中英文混合文本处理
3. 数据库写入
4. 批量计算
"""

import pytest
from app.services.chunk_metrics_calculator import ChunkMetricsCalculator, ChunkMetrics


class TestChunkMetricsCalculator:
    """ChunkMetricsCalculator 测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.calculator = ChunkMetricsCalculator()

    def test_basic_metrics_english(self):
        """测试英文文本基础指标"""
        text = "This is a test. It has multiple sentences. The text is simple and clear."

        metrics = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_1",
            entities=["test"],
            keywords=["simple", "clear"]
        )

        # 验证基础指标存在
        assert metrics.avg_sentence_length is not None
        assert metrics.avg_sentence_length > 0

        assert metrics.lexical_diversity is not None
        assert 0.0 <= metrics.lexical_diversity <= 1.0

        assert metrics.readability_score is not None
        assert 0.0 <= metrics.readability_score <= 100.0

        assert metrics.entity_count == 1
        assert metrics.keyword_count == 2

        assert metrics.semantic_density is not None
        assert metrics.semantic_density > 0

    def test_basic_metrics_chinese(self):
        """测试中文文本基础指标"""
        text = "这是一个测试文本。它包含多个句子。文本简单清晰。"

        metrics = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_2",
            entities=["测试"],
            keywords=["简单", "清晰"]
        )

        assert metrics.avg_sentence_length is not None
        assert metrics.avg_sentence_length > 0

        assert metrics.entity_count == 1
        assert metrics.keyword_count == 2

        assert metrics.sentiment_score is not None
        assert -1.0 <= metrics.sentiment_score <= 1.0

    def test_mixed_chinese_english(self):
        """测试中英文混合文本"""
        text = "这是一个关于AI的测试。This text mixes Chinese and English. 测试效果很好。"

        metrics = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_3",
            entities=["AI", "测试"],
            keywords=["Chinese", "English"]
        )

        assert metrics.semantic_density is not None
        assert metrics.coherence_score is not None
        assert metrics.complexity_score is not None

    def test_semantic_density_calculation(self):
        """测试语义密度计算"""
        text = "人工智能和机器学习是现代科技的重要组成部分。"

        # 高密度：多个实体和关键词
        metrics_high = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_4",
            entities=["人工智能", "机器学习", "科技"],
            keywords=["现代", "重要", "组成"]
        )

        # 低密度：少量实体和关键词
        metrics_low = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_5",
            entities=["科技"],
            keywords=["现代"]
        )

        assert metrics_high.semantic_density > metrics_low.semantic_density

    def test_coherence_score(self):
        """测试连贯性得分"""
        # 高连贯文本（有连接词）
        coherent_text = "首先，我们分析问题。然后，我们提出解决方案。最后，我们实施计划。"

        # 低连贯文本（无连接词）
        incoherent_text = "分析问题。解决方案。实施计划。"

        metrics_high = self.calculator.calculate_all_metrics(
            chunk_text=coherent_text,
            chunk_id="test_chunk_6"
        )

        metrics_low = self.calculator.calculate_all_metrics(
            chunk_text=incoherent_text,
            chunk_id="test_chunk_7"
        )

        assert metrics_high.coherence_score >= metrics_low.coherence_score

    def test_readability_score(self):
        """测试可读性得分"""
        # 简单文本（短句子）
        simple_text = "我喜欢编程。编程很有趣。我每天都学习。"

        # 复杂文本（长句子）
        complex_text = "在现代软件工程实践中，我们需要综合考虑多种因素包括代码质量、系统性能、安全性以及可维护性等多个方面来确保项目的成功实施。"

        metrics_simple = self.calculator.calculate_all_metrics(
            chunk_text=simple_text,
            chunk_id="test_chunk_8"
        )

        metrics_complex = self.calculator.calculate_all_metrics(
            chunk_text=complex_text,
            chunk_id="test_chunk_9"
        )

        # 简单文本的可读性应该更高
        assert metrics_simple.readability_score > metrics_complex.readability_score

    def test_sentiment_score(self):
        """测试情感得分"""
        # 正面文本
        positive_text = "这个项目非常成功，团队表现优秀，大家都很满意。Great work!"

        # 负面文本
        negative_text = "这个项目失败了，结果很糟糕，大家都很失望。Terrible outcome."

        # 中性文本
        neutral_text = "这是一个技术文档。它包含系统架构说明。"

        metrics_positive = self.calculator.calculate_all_metrics(
            chunk_text=positive_text,
            chunk_id="test_chunk_10"
        )

        metrics_negative = self.calculator.calculate_all_metrics(
            chunk_text=negative_text,
            chunk_id="test_chunk_11"
        )

        metrics_neutral = self.calculator.calculate_all_metrics(
            chunk_text=neutral_text,
            chunk_id="test_chunk_12"
        )

        assert metrics_positive.sentiment_score > 0
        assert metrics_negative.sentiment_score < 0
        assert abs(metrics_neutral.sentiment_score) < 0.3  # 接近中性

    def test_lexical_diversity(self):
        """测试词汇多样性"""
        # 高多样性（每个词只出现一次）
        diverse_text = "人工智能、机器学习、深度学习、自然语言处理都是热门技术。"

        # 低多样性（重复词汇）
        repetitive_text = "测试测试测试。我们测试系统。测试很重要。测试继续。"

        metrics_diverse = self.calculator.calculate_all_metrics(
            chunk_text=diverse_text,
            chunk_id="test_chunk_13"
        )

        metrics_repetitive = self.calculator.calculate_all_metrics(
            chunk_text=repetitive_text,
            chunk_id="test_chunk_14"
        )

        assert metrics_diverse.lexical_diversity > metrics_repetitive.lexical_diversity

    def test_empty_text(self):
        """测试空文本处理"""
        metrics = self.calculator.calculate_all_metrics(
            chunk_text="",
            chunk_id="test_chunk_15"
        )

        assert metrics.avg_sentence_length is None or metrics.avg_sentence_length == 0
        assert metrics.entity_count == 0
        assert metrics.keyword_count == 0

    def test_information_gain(self):
        """测试信息增益计算"""
        current_text = "深度学习是机器学习的一个分支，它使用神经网络来处理复杂问题。"

        # 有上下文
        context_with_overlap = {
            'previous_chunks': "机器学习是人工智能的核心技术。深度学习使用神经网络。"
        }

        # 无上下文
        context_no_overlap = {
            'previous_chunks': "区块链技术在金融领域有广泛应用。"
        }

        metrics_with_overlap = self.calculator.calculate_all_metrics(
            chunk_text=current_text,
            chunk_id="test_chunk_16",
            document_context=context_with_overlap
        )

        metrics_no_overlap = self.calculator.calculate_all_metrics(
            chunk_text=current_text,
            chunk_id="test_chunk_17",
            document_context=context_no_overlap
        )

        # 无重叠的信息增益应该更高
        assert metrics_no_overlap.information_gain >= metrics_with_overlap.information_gain

    def test_topic_relevance(self):
        """测试主题相关性"""
        text = "机器学习模型的训练需要大量数据和算力支持。"

        # 相关主题
        context_relevant = {
            'document_keywords': ['机器学习', '训练', '数据', '模型', '算力']
        }

        # 不相关主题
        context_irrelevant = {
            'document_keywords': ['区块链', '加密', '比特币', '钱包']
        }

        metrics_relevant = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_18",
            document_context=context_relevant
        )

        metrics_irrelevant = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_19",
            document_context=context_irrelevant
        )

        assert metrics_relevant.topic_relevance > metrics_irrelevant.topic_relevance

    def test_complexity_score(self):
        """测试复杂度得分"""
        # 简单文本
        simple_text = "我喜欢猫。猫很可爱。我有一只猫。"

        # 复杂文本
        complex_text = """
        在当代信息技术飞速发展的背景下，人工智能作为一项颠覆性技术，
        正在深刻改变着我们的生活方式和工作模式，其应用领域涵盖了从自动驾驶、
        医疗诊断到金融风控等多个方面，展现出巨大的潜力和价值。
        """

        metrics_simple = self.calculator.calculate_all_metrics(
            chunk_text=simple_text,
            chunk_id="test_chunk_20"
        )

        metrics_complex = self.calculator.calculate_all_metrics(
            chunk_text=complex_text,
            chunk_id="test_chunk_21"
        )

        assert metrics_complex.complexity_score > metrics_simple.complexity_score

    def test_calculation_duration(self):
        """测试计算时间记录"""
        text = "这是一个测试文本" * 100  # 较长文本

        metrics = self.calculator.calculate_all_metrics(
            chunk_text=text,
            chunk_id="test_chunk_22"
        )

        assert metrics.calculation_duration_ms is not None
        assert metrics.calculation_duration_ms > 0

    def test_batch_processing(self):
        """测试批量处理（不连接数据库）"""
        chunks = [
            {
                'id': f'chunk_{i}',
                'text': f'这是第{i}个测试文本。It contains some content.',
                'entities': ['测试'],
                'keywords': ['content']
            }
            for i in range(5)
        ]

        # 不提供 db_session，测试计算逻辑
        calculator = ChunkMetricsCalculator(db_session=None)

        for chunk in chunks:
            metrics = calculator.calculate_all_metrics(
                chunk_text=chunk['text'],
                chunk_id=chunk['id'],
                entities=chunk['entities'],
                keywords=chunk['keywords']
            )

            assert metrics is not None
            assert metrics.semantic_density is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
