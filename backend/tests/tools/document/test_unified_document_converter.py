"""
统一文档转换器测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.tools.document.unified_document_converter import (
    UnifiedDocumentConverter,
    ConversionStrategy,
    ConversionQuality,
    ConversionResult,
    ConversionError,
    create_converter,
    convert_document,
    batch_convert_documents
)


class TestUnifiedDocumentConverter:
    """统一文档转换器基础测试"""

    def test_initialization(self):
        """测试初始化"""
        converter = UnifiedDocumentConverter()
        assert converter is not None
        assert converter.max_retries == 2
        assert converter.enable_structure_detection is True
        assert converter.enable_table_extraction is True

    def test_initialization_with_custom_params(self):
        """测试自定义参数初始化"""
        converter = UnifiedDocumentConverter(
            preferred_strategy=ConversionStrategy.MARKITDOWN,
            max_retries=5,
            retry_delay=1.0,
            enable_structure_detection=False,
            min_text_length=50
        )
        assert converter.preferred_strategy == ConversionStrategy.MARKITDOWN
        assert converter.max_retries == 5
        assert converter.retry_delay == 1.0
        assert converter.enable_structure_detection is False
        assert converter.min_text_length == 50

    def test_detect_available_strategies(self):
        """测试策略检测"""
        converter = UnifiedDocumentConverter()
        strategies = converter._available_strategies

        # 纯文本总是可用
        assert ConversionStrategy.PLAINTEXT in strategies

        # 至少有一个策略可用
        assert len(strategies) >= 1

    def test_strategy_priority(self):
        """测试策略优先级"""
        converter = UnifiedDocumentConverter(
            preferred_strategy=ConversionStrategy.MARKITDOWN
        )

        priority = converter._get_strategy_priority()

        # 首选策略应该在第一位（如果可用）
        if ConversionStrategy.MARKITDOWN in converter._available_strategies:
            assert priority[0] == ConversionStrategy.MARKITDOWN


class TestPlaintextConversion:
    """纯文本转换测试"""

    def test_plaintext_conversion_utf8(self):
        """测试UTF-8纯文本转换"""
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "这是一个测试文件。\n包含中文内容。\n用于测试纯文本转换。"
            f.write(test_content)
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter()
            result = converter._convert_with_plaintext(temp_path)

            assert result.text == test_content
            assert result.strategy_used == ConversionStrategy.PLAINTEXT
            assert result.quality_score > 0
            assert result.metadata['encoding'] == 'utf-8'
            assert len(result.warnings) > 0

        finally:
            os.unlink(temp_path)

    def test_plaintext_conversion_gbk(self):
        """测试GBK编码文本转换"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='gbk') as f:
            test_content = "GBK编码的中文内容"
            f.write(test_content)
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter()
            result = converter._convert_with_plaintext(temp_path)

            assert test_content in result.text
            assert result.strategy_used == ConversionStrategy.PLAINTEXT
            assert result.metadata['encoding'] in ['utf-8', 'gbk', 'gb2312']

        finally:
            os.unlink(temp_path)

    def test_plaintext_file_not_found(self):
        """测试文件不存在"""
        converter = UnifiedDocumentConverter()

        with pytest.raises(ConversionError, match="文件不存在"):
            converter.convert("/nonexistent/file.txt")

    def test_plaintext_empty_file(self):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter(min_text_length=5)

            with pytest.raises(ConversionError, match="文件内容太少"):
                converter._convert_with_plaintext(temp_path)

        finally:
            os.unlink(temp_path)


class TestQualityScoring:
    """质量评分测试"""

    def test_quality_score_calculation(self):
        """测试质量分数计算"""
        converter = UnifiedDocumentConverter()

        # 长文本 + 丰富结构 + 表格 + Unstructured策略 = 高分
        elements = [
            {'type': 'Title', 'text': '标题'},
            {'type': 'NarrativeText', 'text': '段落1'},
            {'type': 'NarrativeText', 'text': '段落2'},
            {'type': 'ListItem', 'text': '列表项'},
            {'type': 'Table', 'text': '表格'},
        ]
        tables = ['表格1', '表格2']
        text = 'a' * 1500  # 长文本

        score = converter._calculate_quality_score(
            text, elements, tables, ConversionStrategy.UNSTRUCTURED
        )

        assert score >= 80  # 应该是高分
        assert score <= 100

    def test_quality_score_poor_text(self):
        """测试低质量文本评分"""
        converter = UnifiedDocumentConverter()

        text = "短文本"  # 很短
        elements = None
        tables = None

        score = converter._calculate_quality_score(
            text, elements, tables, ConversionStrategy.PLAINTEXT
        )

        assert score < 50  # 应该是低分

    def test_quality_level_mapping(self):
        """测试质量等级映射"""
        converter = UnifiedDocumentConverter()

        assert converter._score_to_quality_level(95) == ConversionQuality.EXCELLENT
        assert converter._score_to_quality_level(80) == ConversionQuality.GOOD
        assert converter._score_to_quality_level(60) == ConversionQuality.FAIR
        assert converter._score_to_quality_level(30) == ConversionQuality.POOR


class TestConversionWithFallback:
    """转换降级测试"""

    def test_plaintext_fallback(self):
        """测试降级到纯文本"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "测试内容，用于降级测试。" * 10
            f.write(test_content)
            temp_path = f.name

        try:
            # 强制使用PLAINTEXT策略
            converter = UnifiedDocumentConverter(
                preferred_strategy=ConversionStrategy.PLAINTEXT
            )
            result = converter.convert(temp_path)

            assert result.text == test_content
            assert result.strategy_used == ConversionStrategy.PLAINTEXT
            assert result.quality_score > 0

        finally:
            os.unlink(temp_path)

    @patch('app.tools.document.unified_document_converter.UnifiedDocumentConverter._convert_with_unstructured')
    def test_fallback_on_error(self, mock_unstructured):
        """测试错误时自动降级"""
        # Mock Unstructured失败
        mock_unstructured.side_effect = Exception("Unstructured失败")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "降级测试内容" * 20
            f.write(test_content)
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter(
                preferred_strategy=ConversionStrategy.UNSTRUCTURED
            )

            # 即使Unstructured失败，也应该降级成功
            result = converter.convert(temp_path)

            assert result.text is not None
            assert len(result.text) > 0
            # 应该降级到其他策略
            assert result.strategy_used != ConversionStrategy.UNSTRUCTURED

        finally:
            os.unlink(temp_path)


class TestBatchConversion:
    """批量转换测试"""

    def test_batch_convert_multiple_files(self):
        """测试批量转换多个文件"""
        # 创建3个测试文件
        temp_files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            f.write(f"测试文件{i+1}的内容。" * 20)
            f.close()
            temp_files.append(f.name)

        try:
            converter = UnifiedDocumentConverter()
            results = converter.batch_convert(temp_files)

            assert len(results) == 3

            for i, result in enumerate(results):
                assert result.text is not None
                assert len(result.text) > 0
                assert f"测试文件{i+1}" in result.text

        finally:
            for f in temp_files:
                os.unlink(f)

    def test_batch_convert_with_progress(self):
        """测试带进度回调的批量转换"""
        temp_files = []
        for i in range(2):
            f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            f.write(f"文件{i}内容" * 10)
            f.close()
            temp_files.append(f.name)

        try:
            progress_calls = []

            def progress_callback(current, total, message):
                progress_calls.append((current, total, message))

            converter = UnifiedDocumentConverter()
            results = converter.batch_convert(temp_files, progress_callback=progress_callback)

            assert len(results) == 2
            assert len(progress_calls) == 2
            assert progress_calls[0][0] == 1
            assert progress_calls[1][0] == 2

        finally:
            for f in temp_files:
                os.unlink(f)

    def test_batch_convert_with_errors(self):
        """测试批量转换时部分文件失败"""
        temp_files = [
            "/nonexistent/file1.txt",  # 不存在
            None  # 将创建
        ]

        # 创建一个有效文件
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        f.write("有效文件内容" * 10)
        f.close()
        temp_files[1] = f.name

        try:
            converter = UnifiedDocumentConverter()
            results = converter.batch_convert(temp_files)

            # 应该返回2个结果（一个失败，一个成功）
            assert len(results) == 2

            # 第一个应该失败
            assert results[0].quality_score == 0.0
            assert len(results[0].warnings) > 0

            # 第二个应该成功
            assert results[1].quality_score > 0
            assert "有效文件内容" in results[1].text

        finally:
            if temp_files[1]:
                os.unlink(temp_files[1])


class TestTableExtraction:
    """表格提取测试"""

    def test_extract_tables_no_tables(self):
        """测试无表格文档"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("这是一个没有表格的文档。" * 10)
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter()
            tables = converter.extract_tables(temp_path)

            assert isinstance(tables, list)
            # 纯文本不支持表格提取
            assert len(tables) == 0

        finally:
            os.unlink(temp_path)


class TestDocumentSummary:
    """文档摘要测试"""

    def test_get_document_summary(self):
        """测试获取文档摘要"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "这是测试文档内容。\n\n包含多个段落。\n\n用于测试摘要功能。"
            f.write(test_content)
            temp_path = f.name

        try:
            converter = UnifiedDocumentConverter()
            summary = converter.get_document_summary(temp_path)

            assert 'text_length' in summary
            assert 'word_count' in summary
            assert 'quality_score' in summary
            assert 'quality_level' in summary
            assert 'strategy_used' in summary

            assert summary['text_length'] > 0
            assert summary['word_count'] > 0

        finally:
            os.unlink(temp_path)


class TestSupportedFormats:
    """格式支持测试"""

    def test_is_supported_common_formats(self):
        """测试常见格式支持"""
        converter = UnifiedDocumentConverter()

        # 纯文本格式总是支持
        assert converter.is_supported("test.txt")
        assert converter.is_supported("test.md")
        assert converter.is_supported("test.csv")
        assert converter.is_supported("test.json")

    def test_is_supported_case_insensitive(self):
        """测试大小写不敏感"""
        converter = UnifiedDocumentConverter()

        assert converter.is_supported("TEST.TXT")
        assert converter.is_supported("Test.Txt")


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_create_converter(self):
        """测试create_converter"""
        converter = create_converter(max_retries=5)
        assert converter.max_retries == 5

    def test_convert_document(self):
        """测试convert_document"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("快速转换测试" * 10)
            temp_path = f.name

        try:
            result = convert_document(temp_path)
            assert result.text is not None
            assert "快速转换测试" in result.text

        finally:
            os.unlink(temp_path)

    def test_batch_convert_documents(self):
        """测试batch_convert_documents"""
        temp_files = []
        for i in range(2):
            f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            f.write(f"批量测试{i}" * 10)
            f.close()
            temp_files.append(f.name)

        try:
            results = batch_convert_documents(temp_files)
            assert len(results) == 2

        finally:
            for f in temp_files:
                os.unlink(f)


class TestConversionResult:
    """ConversionResult测试"""

    def test_conversion_result_structure(self):
        """测试ConversionResult结构"""
        result = ConversionResult(
            text="测试文本",
            strategy_used=ConversionStrategy.PLAINTEXT,
            quality_score=75.5,
            quality_level=ConversionQuality.GOOD,
            processing_time=1.5
        )

        assert result.text == "测试文本"
        assert result.strategy_used == ConversionStrategy.PLAINTEXT
        assert result.quality_score == 75.5
        assert result.quality_level == ConversionQuality.GOOD
        assert result.processing_time == 1.5
        assert result.elements is None
        assert result.tables is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
