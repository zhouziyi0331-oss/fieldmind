"""
独立测试脚本 - ChunkMetricsCalculator

不依赖数据库和其他服务，纯粹测试计算逻辑
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.chunk_metrics_calculator import ChunkMetricsCalculator


def test_english_text():
    """测试英文文本"""
    print("\n" + "="*60)
    print("测试1: 英文文本基础指标")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    text = "This is a test. It has multiple sentences. The text is simple and clear."

    metrics = calculator.calculate_all_metrics(
        chunk_text=text,
        chunk_id="test_chunk_1",
        entities=["test"],
        keywords=["simple", "clear"]
    )

    print(f"文本: {text}")
    print(f"\n计算结果:")
    print(f"  - 语义密度: {metrics.semantic_density:.3f}")
    print(f"  - 连贯性得分: {metrics.coherence_score:.3f}")
    print(f"  - 可读性得分: {metrics.readability_score:.2f}")
    print(f"  - 平均句长: {metrics.avg_sentence_length:.2f}")
    print(f"  - 词汇多样性: {metrics.lexical_diversity:.3f}")
    print(f"  - 复杂度得分: {metrics.complexity_score:.2f}")
    print(f"  - 情感得分: {metrics.sentiment_score:.3f}")
    print(f"  - 实体数量: {metrics.entity_count}")
    print(f"  - 关键词数量: {metrics.keyword_count}")
    print(f"  - 计算耗时: {metrics.calculation_duration_ms}ms")

    assert metrics.semantic_density > 0
    assert metrics.entity_count == 1
    assert metrics.keyword_count == 2
    print("\n✅ 英文文本测试通过")


def test_chinese_text():
    """测试中文文本"""
    print("\n" + "="*60)
    print("测试2: 中文文本基础指标")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    text = "这是一个测试文本。它包含多个句子。文本简单清晰。"

    metrics = calculator.calculate_all_metrics(
        chunk_text=text,
        chunk_id="test_chunk_2",
        entities=["测试", "文本"],
        keywords=["简单", "清晰"]
    )

    print(f"文本: {text}")
    print(f"\n计算结果:")
    print(f"  - 语义密度: {metrics.semantic_density:.3f}")
    print(f"  - 连贯性得分: {metrics.coherence_score:.3f}")
    print(f"  - 可读性得分: {metrics.readability_score:.2f}")
    print(f"  - 平均句长: {metrics.avg_sentence_length:.2f}")
    print(f"  - 词汇多样性: {metrics.lexical_diversity:.3f}")
    print(f"  - 复杂度得分: {metrics.complexity_score:.2f}")
    print(f"  - 情感得分: {metrics.sentiment_score:.3f}")
    print(f"  - 实体数量: {metrics.entity_count}")
    print(f"  - 关键词数量: {metrics.keyword_count}")
    print(f"  - 计算耗时: {metrics.calculation_duration_ms}ms")

    assert metrics.semantic_density > 0
    assert metrics.entity_count == 2
    assert metrics.keyword_count == 2
    print("\n✅ 中文文本测试通过")


def test_mixed_text():
    """测试中英文混合文本"""
    print("\n" + "="*60)
    print("测试3: 中英文混合文本")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    text = "这是一个关于AI的测试。This text mixes Chinese and English. 测试效果很好。"

    metrics = calculator.calculate_all_metrics(
        chunk_text=text,
        chunk_id="test_chunk_3",
        entities=["AI", "测试"],
        keywords=["Chinese", "English", "效果"]
    )

    print(f"文本: {text}")
    print(f"\n计算结果:")
    print(f"  - 语义密度: {metrics.semantic_density:.3f}")
    print(f"  - 连贯性得分: {metrics.coherence_score:.3f}")
    print(f"  - 可读性得分: {metrics.readability_score:.2f}")
    print(f"  - 平均句长: {metrics.avg_sentence_length:.2f}")
    print(f"  - 词汇多样性: {metrics.lexical_diversity:.3f}")
    print(f"  - 复杂度得分: {metrics.complexity_score:.2f}")
    print(f"  - 情感得分: {metrics.sentiment_score:.3f}")
    print(f"  - 实体数量: {metrics.entity_count}")
    print(f"  - 关键词数量: {metrics.keyword_count}")

    assert metrics.entity_count == 2
    assert metrics.keyword_count == 3
    print("\n✅ 混合文本测试通过")


def test_sentiment():
    """测试情感分析"""
    print("\n" + "="*60)
    print("测试4: 情感分析")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    # 正面文本
    positive_text = "这个项目非常成功，团队表现优秀，大家都很满意。Great work!"
    metrics_positive = calculator.calculate_all_metrics(
        chunk_text=positive_text,
        chunk_id="test_positive"
    )

    # 负面文本
    negative_text = "这个项目失败了，结果很糟糕，大家都很失望。Terrible outcome."
    metrics_negative = calculator.calculate_all_metrics(
        chunk_text=negative_text,
        chunk_id="test_negative"
    )

    # 中性文本
    neutral_text = "这是一个技术文档。它包含系统架构说明。"
    metrics_neutral = calculator.calculate_all_metrics(
        chunk_text=neutral_text,
        chunk_id="test_neutral"
    )

    print(f"正面文本情感得分: {metrics_positive.sentiment_score:.3f}")
    print(f"负面文本情感得分: {metrics_negative.sentiment_score:.3f}")
    print(f"中性文本情感得分: {metrics_neutral.sentiment_score:.3f}")

    assert metrics_positive.sentiment_score > 0, "正面文本应该有正情感得分"
    assert metrics_negative.sentiment_score < 0, "负面文本应该有负情感得分"
    assert abs(metrics_neutral.sentiment_score) < 0.3, "中性文本应该接近0"
    print("\n✅ 情感分析测试通过")


def test_readability():
    """测试可读性"""
    print("\n" + "="*60)
    print("测试5: 可读性评估")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    # 简单文本
    simple_text = "我喜欢编程。编程很有趣。我每天都学习。"
    metrics_simple = calculator.calculate_all_metrics(
        chunk_text=simple_text,
        chunk_id="test_simple"
    )

    # 复杂文本
    complex_text = """在现代软件工程实践中，我们需要综合考虑多种因素包括代码质量、系统性能、
    安全性以及可维护性等多个方面来确保项目的成功实施。"""
    metrics_complex = calculator.calculate_all_metrics(
        chunk_text=complex_text,
        chunk_id="test_complex"
    )

    print(f"简单文本可读性: {metrics_simple.readability_score:.2f}")
    print(f"复杂文本可读性: {metrics_complex.readability_score:.2f}")

    assert metrics_simple.readability_score > metrics_complex.readability_score, \
        "简单文本的可读性应该更高"
    print("\n✅ 可读性评估测试通过")


def test_complexity():
    """测试复杂度"""
    print("\n" + "="*60)
    print("测试6: 复杂度评估")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    # 简单文本
    simple_text = "我喜欢猫。猫很可爱。我有一只猫。"
    metrics_simple = calculator.calculate_all_metrics(
        chunk_text=simple_text,
        chunk_id="test_simple_2"
    )

    # 复杂文本
    complex_text = """在当代信息技术飞速发展的背景下，人工智能作为一项颠覆性技术，
    正在深刻改变着我们的生活方式和工作模式，其应用领域涵盖了从自动驾驶、
    医疗诊断到金融风控等多个方面，展现出巨大的潜力和价值。"""
    metrics_complex = calculator.calculate_all_metrics(
        chunk_text=complex_text,
        chunk_id="test_complex_2"
    )

    print(f"简单文本:")
    print(f"  - 平均句长: {metrics_simple.avg_sentence_length:.2f}")
    print(f"  - 词汇多样性: {metrics_simple.lexical_diversity:.3f}")
    print(f"  - 复杂度得分: {metrics_simple.complexity_score:.2f}")

    print(f"\n复杂文本:")
    print(f"  - 平均句长: {metrics_complex.avg_sentence_length:.2f}")
    print(f"  - 词汇多样性: {metrics_complex.lexical_diversity:.3f}")
    print(f"  - 复杂度得分: {metrics_complex.complexity_score:.2f}")

    assert metrics_complex.complexity_score > metrics_simple.complexity_score, \
        "复杂文本的复杂度得分应该更高"
    print("\n✅ 复杂度评估测试通过")


def test_information_gain():
    """测试信息增益"""
    print("\n" + "="*60)
    print("测试7: 信息增益计算")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    current_text = "深度学习是机器学习的一个分支，它使用神经网络来处理复杂问题。"

    # 有重叠的上下文
    context_overlap = {
        'previous_chunks': "机器学习是人工智能的核心技术。深度学习使用神经网络。"
    }

    # 无重叠的上下文
    context_no_overlap = {
        'previous_chunks': "区块链技术在金融领域有广泛应用。"
    }

    metrics_overlap = calculator.calculate_all_metrics(
        chunk_text=current_text,
        chunk_id="test_overlap",
        document_context=context_overlap
    )

    metrics_no_overlap = calculator.calculate_all_metrics(
        chunk_text=current_text,
        chunk_id="test_no_overlap",
        document_context=context_no_overlap
    )

    print(f"文本: {current_text}")
    print(f"\n与前文有重叠时的信息增益: {metrics_overlap.information_gain:.3f}")
    print(f"与前文无重叠时的信息增益: {metrics_no_overlap.information_gain:.3f}")

    assert metrics_no_overlap.information_gain >= metrics_overlap.information_gain, \
        "无重叠时的信息增益应该更高"
    print("\n✅ 信息增益测试通过")


def test_batch_processing():
    """测试批量处理"""
    print("\n" + "="*60)
    print("测试8: 批量处理性能")
    print("="*60)

    calculator = ChunkMetricsCalculator()

    chunks = [
        {
            'id': f'chunk_{i}',
            'text': f'这是第{i}个测试文本。It contains some content about AI and machine learning.',
            'entities': ['AI', '机器学习'],
            'keywords': ['测试', 'content']
        }
        for i in range(10)
    ]

    import time
    start_time = time.time()

    for chunk in chunks:
        metrics = calculator.calculate_all_metrics(
            chunk_text=chunk['text'],
            chunk_id=chunk['id'],
            entities=chunk['entities'],
            keywords=chunk['keywords']
        )
        assert metrics is not None

    duration = time.time() - start_time
    avg_time = duration / len(chunks) * 1000

    print(f"处理了 {len(chunks)} 个chunks")
    print(f"总耗时: {duration:.2f}秒")
    print(f"平均每个chunk: {avg_time:.2f}ms")

    print("\n✅ 批量处理测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("ChunkMetricsCalculator 独立测试")
    print("="*60)

    try:
        test_english_text()
        test_chinese_text()
        test_mixed_text()
        test_sentiment()
        test_readability()
        test_complexity()
        test_information_gain()
        test_batch_processing()

        print("\n" + "="*60)
        print("✅✅✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
