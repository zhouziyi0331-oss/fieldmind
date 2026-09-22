"""
测试统一文档分块器

测试覆盖：
1. 基础分块功能
2. 四种分块策略
3. 时间戳映射
4. Overlap功能
5. 质量评分
6. 批量处理
7. 输出模式转换
8. 边界情况
"""

import pytest
from app.tools.document.unified_document_chunker import (
    UnifiedDocumentChunker,
    ChunkStrategy,
    ChunkQuality,
    ChunkResult,
    create_chunker,
    chunk_document,
    batch_chunk_documents
)


# ============== Test Data ==============

SAMPLE_TEXT_SHORT = "这是一个简短的测试文本。"

SAMPLE_TEXT_MEDIUM = """
这是第一段内容。包含一些基本信息。
这段内容会被正常处理。

这是第二段内容。它稍微长一些。
包含更多的信息和细节。
应该会被切分成一个chunk。

这是第三段内容。
""".strip()

SAMPLE_TEXT_LONG = """
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

机器学习是人工智能的核心。通过算法使机器能从大量历史数据中学习规律，从而对新的样本做智能识别或对未来做预测。机器学习已广泛应用于数据挖掘、计算机视觉、自然语言处理、生物特征识别、搜索引擎、医学诊断、检测信用卡欺诈、证券市场分析、DNA序列测序、语音和手写识别、战略游戏和机器人等领域。

深度学习是机器学习的一个分支，它试图使用包含复杂结构或由多重非线性变换构成的多个处理层对数据进行高层抽象的算法。深度学习是机器学习研究中的一个新的领域，其动机在于建立、模拟人脑进行分析学习的神经网络，它模仿人脑的机制来解释数据，例如图像，声音和文本。
""".strip()

SAMPLE_TRANSCRIPT = [
    {"text": "这是第一段内容。", "start": 0.0, "end": 2.5},
    {"text": "包含一些基本信息。", "start": 2.5, "end": 4.8},
    {"text": "这段内容会被正常处理。", "start": 4.8, "end": 7.2},
]


# ============== Basic Chunking Tests ==============

class TestBasicChunking:
    """测试基础分块功能"""

    def test_chunk_empty_text(self):
        """测试空文本"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document("", output_mode="result")
        assert len(chunks) == 0

    def test_chunk_short_text(self):
        """测试短文本（小于min_chunk_size）"""
        chunker = UnifiedDocumentChunker(min_chunk_size=200)
        chunks = chunker.chunk_document(SAMPLE_TEXT_SHORT, output_mode="result")

        assert len(chunks) == 1
        assert chunks[0].text == SAMPLE_TEXT_SHORT
        assert chunks[0].chunk_type == "short_paragraph"

    def test_chunk_medium_text(self):
        """测试中等长度文本"""
        chunker = UnifiedDocumentChunker(
            min_chunk_size=50,
            max_chunk_size=200
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_MEDIUM, output_mode="result")

        assert len(chunks) > 0
        # 验证chunk结构
        for chunk in chunks:
            assert chunk.chunk_id
            assert chunk.text
            assert chunk.chunk_index >= 0
            assert chunk.total_chunks == len(chunks)

    def test_chunk_long_text(self):
        """测试长文本"""
        chunker = UnifiedDocumentChunker(
            min_chunk_size=100,
            max_chunk_size=300
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        assert len(chunks) >= 2
        # 验证chunk大小
        for chunk in chunks:
            # 允许一些灵活性，因为可能有短段落
            assert len(chunk.text) <= 350  # 稍微超过max也可接受

    def test_chunk_links(self):
        """测试chunk之间的链接"""
        chunker = UnifiedDocumentChunker(max_chunk_size=200)
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        if len(chunks) > 1:
            # 第一个chunk
            assert chunks[0].prev_chunk_id is None
            assert chunks[0].next_chunk_id is not None

            # 中间chunk
            if len(chunks) > 2:
                assert chunks[1].prev_chunk_id is not None
                assert chunks[1].next_chunk_id is not None

            # 最后一个chunk
            assert chunks[-1].prev_chunk_id is not None
            assert chunks[-1].next_chunk_id is None


# ============== Strategy Tests ==============

class TestChunkingStrategies:
    """测试四种分块策略"""

    def test_semantic_strategy(self):
        """测试语义边界策略"""
        chunker = UnifiedDocumentChunker(
            strategy=ChunkStrategy.SEMANTIC,
            max_chunk_size=200
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        assert len(chunks) > 0
        # 语义策略应该尊重段落边界
        for chunk in chunks:
            assert chunk.chunk_type in [
                "short_paragraph", "normal_paragraph",
                "split_paragraph", "forced_split", "merged"
            ]

    def test_fixed_strategy(self):
        """测试固定大小策略"""
        chunker = UnifiedDocumentChunker(
            strategy=ChunkStrategy.FIXED,
            target_chunk_size=100
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        assert len(chunks) > 0
        # 固定策略应该产生大小相近的chunks（除了最后一个）
        for i, chunk in enumerate(chunks[:-1]):
            assert 90 <= len(chunk.text) <= 110  # 允许10%误差
            assert chunk.chunk_type == "fixed"

    def test_sentence_strategy(self):
        """测试句子级策略"""
        chunker = UnifiedDocumentChunker(
            strategy=ChunkStrategy.SENTENCE,
            max_chunk_size=200
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        assert len(chunks) > 0
        # 句子策略应该在句子边界切分
        for chunk in chunks:
            assert chunk.chunk_type == "sentence"
            # 检查是否以句子结束符结尾（大部分情况）
            text = chunk.text.strip()
            # 允许最后一个chunk不以句号结尾
            if chunk.next_chunk_id is not None:
                assert text[-1] in '。！？.!?\n' or len(text) < 50

    def test_sliding_strategy(self):
        """测试滑动窗口策略"""
        chunker = UnifiedDocumentChunker(
            strategy=ChunkStrategy.SLIDING,
            target_chunk_size=150,
            overlap_size=30
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_type == "sliding"

        # 滑动窗口应该有重叠（通过位置验证）
        if len(chunks) > 1:
            step = 150 - 30  # window_size - overlap_size
            assert chunks[1].start_pos == step


# ============== Timestamp Mapping Tests ==============

class TestTimestampMapping:
    """测试时间戳映射功能"""

    def test_map_timestamps(self):
        """测试音频时间戳映射"""
        chunker = UnifiedDocumentChunker(max_chunk_size=100)

        text = "这是第一段内容。包含一些基本信息。这段内容会被正常处理。"
        metadata = {"transcript": SAMPLE_TRANSCRIPT}

        chunks = chunker.chunk_document(text, metadata, output_mode="result")

        # 至少有一个chunk应该映射到时间戳
        mapped_chunks = [c for c in chunks if c.start_sec is not None]
        assert len(mapped_chunks) > 0

        # 验证时间戳的有效性
        for chunk in mapped_chunks:
            assert chunk.start_sec >= 0
            assert chunk.end_sec >= chunk.start_sec

    def test_no_transcript(self):
        """测试没有transcript的情况"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(SAMPLE_TEXT_MEDIUM, output_mode="result")

        # 没有transcript时，start_sec和end_sec应该是None
        for chunk in chunks:
            assert chunk.start_sec is None
            assert chunk.end_sec is None


# ============== Overlap Tests ==============

class TestOverlapFeature:
    """测试overlap功能"""

    def test_overlap_enabled(self):
        """测试启用overlap"""
        chunker = UnifiedDocumentChunker(
            max_chunk_size=150,
            overlap_size=30,
            enable_overlap=True
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        if len(chunks) > 1:
            # 检查metadata中的overlap标记
            has_overlap = any(
                c.metadata.get("has_overlap", False)
                for c in chunks[1:]
            )
            assert has_overlap

    def test_overlap_disabled(self):
        """测试禁用overlap"""
        chunker = UnifiedDocumentChunker(
            max_chunk_size=150,
            overlap_size=30,
            enable_overlap=False
        )
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        # 没有chunk应该有overlap标记
        for chunk in chunks:
            assert not chunk.metadata.get("has_overlap", False)


# ============== Quality Scoring Tests ==============

class TestQualityScoring:
    """测试质量评分功能"""

    def test_quality_score_range(self):
        """测试质量分数范围"""
        chunker = UnifiedDocumentChunker(enable_quality_scoring=True)
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        for chunk in chunks:
            assert 0 <= chunk.quality_score <= 100
            assert chunk.quality_level in [
                ChunkQuality.EXCELLENT,
                ChunkQuality.GOOD,
                ChunkQuality.FAIR,
                ChunkQuality.POOR
            ]

    def test_quality_levels(self):
        """测试质量等级映射"""
        chunker = UnifiedDocumentChunker(enable_quality_scoring=True)
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        for chunk in chunks:
            if chunk.quality_score >= 90:
                assert chunk.quality_level == ChunkQuality.EXCELLENT
            elif chunk.quality_score >= 70:
                assert chunk.quality_level == ChunkQuality.GOOD
            elif chunk.quality_score >= 50:
                assert chunk.quality_level == ChunkQuality.FAIR
            else:
                assert chunk.quality_level == ChunkQuality.POOR

    def test_quality_disabled(self):
        """测试禁用质量评分"""
        chunker = UnifiedDocumentChunker(enable_quality_scoring=False)
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        # 禁用时，quality_score应该是0
        for chunk in chunks:
            assert chunk.quality_score == 0.0


# ============== Output Mode Tests ==============

class TestOutputModes:
    """测试输出模式"""

    def test_result_mode(self):
        """测试ChunkResult输出模式"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(
            SAMPLE_TEXT_MEDIUM,
            output_mode="result"
        )

        assert isinstance(chunks, list)
        assert all(isinstance(c, ChunkResult) for c in chunks)

    def test_dict_mode(self):
        """测试Dict输出模式（v1兼容）"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(
            SAMPLE_TEXT_MEDIUM,
            output_mode="dict"
        )

        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

        # 验证Dict格式
        if chunks:
            chunk = chunks[0]
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk
            assert "chunk_index" in chunk

    def test_dict_format_v1_compatibility(self):
        """测试Dict格式与v1的兼容性"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(
            SAMPLE_TEXT_MEDIUM,
            output_mode="dict"
        )

        if chunks:
            chunk = chunks[0]
            meta = chunk["metadata"]

            # v1格式的必要字段
            assert "start_pos" in meta
            assert "end_pos" in meta
            assert "chunk_type" in meta


# ============== Batch Processing Tests ==============

class TestBatchProcessing:
    """测试批量处理"""

    def test_batch_chunk_documents(self):
        """测试批量分块"""
        chunker = UnifiedDocumentChunker(max_chunk_size=200)

        documents = [
            {"text": SAMPLE_TEXT_SHORT, "metadata": {"doc_id": 1}},
            {"text": SAMPLE_TEXT_MEDIUM, "metadata": {"doc_id": 2}},
            {"text": SAMPLE_TEXT_LONG, "metadata": {"doc_id": 3}},
        ]

        results = chunker.batch_chunk_documents(documents)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
        assert all(len(r) > 0 for r in results)

    def test_batch_with_callback(self):
        """测试带进度回调的批量处理"""
        chunker = UnifiedDocumentChunker()

        documents = [
            {"text": SAMPLE_TEXT_SHORT, "metadata": {}},
            {"text": SAMPLE_TEXT_MEDIUM, "metadata": {}},
        ]

        progress_calls = []

        def callback(current, total):
            progress_calls.append((current, total))

        chunker.batch_chunk_documents(documents, progress_callback=callback)

        assert len(progress_calls) == 2
        assert progress_calls[-1] == (2, 2)


# ============== Utility Functions Tests ==============

class TestUtilityFunctions:
    """测试工具函数"""

    def test_get_chunk_preview(self):
        """测试chunk预览"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        previews = chunker.get_chunk_preview(chunks, preview_count=2)

        assert len(previews) <= 2
        for preview in previews:
            assert "chunk_id" in preview
            assert "preview" in preview
            assert "length" in preview
            assert "position" in preview

    def test_get_chunking_stats(self):
        """测试分块统计"""
        chunker = UnifiedDocumentChunker(enable_quality_scoring=True)
        chunks = chunker.chunk_document(SAMPLE_TEXT_LONG, output_mode="result")

        stats = chunker.get_chunking_stats(chunks)

        assert "total_chunks" in stats
        assert "avg_chunk_size" in stats
        assert "min_chunk_size" in stats
        assert "max_chunk_size" in stats
        assert "avg_quality_score" in stats
        assert "quality_distribution" in stats

        assert stats["total_chunks"] == len(chunks)
        assert stats["avg_chunk_size"] > 0


# ============== Convenience Functions Tests ==============

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_chunker(self):
        """测试create_chunker工厂函数"""
        chunker = create_chunker(
            strategy="semantic",
            max_chunk_size=300
        )

        assert isinstance(chunker, UnifiedDocumentChunker)
        assert chunker.strategy == ChunkStrategy.SEMANTIC
        assert chunker.max_chunk_size == 300

    def test_chunk_document_function(self):
        """测试chunk_document快捷函数"""
        chunks = chunk_document(
            SAMPLE_TEXT_MEDIUM,
            strategy="semantic",
            max_size=200
        )

        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

    def test_batch_chunk_documents_function(self):
        """测试batch_chunk_documents快捷函数"""
        documents = [
            {"text": SAMPLE_TEXT_SHORT, "metadata": {}},
            {"text": SAMPLE_TEXT_MEDIUM, "metadata": {}},
        ]

        results = batch_chunk_documents(documents, strategy="semantic")

        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)


# ============== Edge Cases Tests ==============

class TestEdgeCases:
    """测试边界情况"""

    def test_single_sentence(self):
        """测试单句文本"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document("这是一句话。", output_mode="result")

        assert len(chunks) == 1

    def test_very_long_sentence(self):
        """测试超长句子（无法在语义边界切分）"""
        long_sentence = "这是一个非常长的句子" * 100
        chunker = UnifiedDocumentChunker(max_chunk_size=200)
        chunks = chunker.chunk_document(long_sentence, output_mode="result")

        assert len(chunks) > 1
        # 应该有强制切分的chunks
        forced_chunks = [c for c in chunks if c.chunk_type == "forced_split"]
        assert len(forced_chunks) > 0

    def test_whitespace_only(self):
        """测试只有空白字符的文本"""
        chunker = UnifiedDocumentChunker()
        chunks = chunker.chunk_document("   \n\n\t  ", output_mode="result")

        assert len(chunks) == 0

    def test_chunks_limit(self):
        """测试chunk数量限制"""
        # 创建一个会产生很多chunks的长文本
        long_text = "\n\n".join([f"段落{i}的内容。" * 10 for i in range(100)])

        chunker = UnifiedDocumentChunker(
            max_chunk_size=50,
            max_chunks_limit=20
        )
        chunks = chunker.chunk_document(long_text, output_mode="result")

        assert len(chunks) <= 20

    def test_metadata_preservation(self):
        """测试元数据保留"""
        chunker = UnifiedDocumentChunker()
        metadata = {"doc_id": "test123", "author": "Alice"}

        chunks = chunker.chunk_document(
            SAMPLE_TEXT_MEDIUM,
            metadata=metadata,
            output_mode="result"
        )

        for chunk in chunks:
            assert chunk.metadata.get("doc_id") == "test123"
            assert chunk.metadata.get("author") == "Alice"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
