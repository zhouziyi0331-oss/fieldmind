"""
文档处理管线测试
"""

import pytest
from pathlib import Path
from io import BytesIO


class TestDocumentExtractor:
    """文档提取器测试"""

    @pytest.mark.unit
    def test_pdf_extractor(self, sample_pdf):
        """测试 PDF 提取"""
        from app.processors.document_extractor import PDFExtractor

        result = PDFExtractor.extract(str(sample_pdf))

        assert "text" in result
        assert "metadata" in result
        assert "pages" in result
        assert result["word_count"] > 0

    @pytest.mark.unit
    def test_text_extractor(self, temp_dir):
        """测试文本提取"""
        from app.processors.document_extractor import TextExtractor

        # 创建测试文本文件
        text_file = temp_dir / "test.txt"
        text_file.write_text("This is a test document.", encoding="utf-8")

        result = TextExtractor.extract(str(text_file))

        assert result["text"] == "This is a test document."
        assert result["word_count"] == 5

    @pytest.mark.unit
    def test_unsupported_type(self, temp_file):
        """测试不支持的文件类型"""
        from app.processors.document_extractor import DocumentExtractor
        from app.core.exceptions import DocumentProcessingException

        with pytest.raises(DocumentProcessingException):
            DocumentExtractor.extract(
                str(temp_file),
                mime_type="application/unsupported"
            )


class TestTextChunker:
    """文本分块器测试"""

    @pytest.mark.unit
    def test_basic_chunking(self):
        """测试基础分块"""
        from app.processors.text_chunker import TextChunker

        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        text = "这是第一段。" * 20  # 120字符
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(chunk.token_count <= 50 for chunk in chunks)

    @pytest.mark.unit
    def test_empty_text(self):
        """测试空文本"""
        from app.processors.text_chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk("")

        assert len(chunks) == 0

    @pytest.mark.unit
    def test_chunk_overlap(self):
        """测试分块重叠"""
        from app.processors.text_chunker import TextChunker

        chunker = TextChunker(chunk_size=20, chunk_overlap=5)

        text = "A" * 50
        chunks = chunker.chunk(text)

        # 检查是否有重叠
        assert len(chunks) > 1

    @pytest.mark.unit
    def test_markdown_chunker(self):
        """测试 Markdown 分块"""
        from app.processors.text_chunker import MarkdownChunker

        chunker = MarkdownChunker(chunk_size=100)

        markdown_text = """
# Heading 1

This is paragraph 1.

## Heading 2

This is paragraph 2.
"""

        chunks = chunker.chunk(markdown_text)

        assert len(chunks) > 0
        # 检查元数据中是否包含标题
        assert any("heading" in chunk.metadata for chunk in chunks)


class TestVectorGenerator:
    """向量生成器测试"""

    @pytest.mark.unit
    def test_mock_embedding(self):
        """测试 Mock 向量生成"""
        from app.processors.vector_generator import MockEmbedding

        generator = MockEmbedding(dimension=128)

        texts = ["text 1", "text 2", "text 3"]
        embeddings = generator.generate(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 128 for emb in embeddings)

    @pytest.mark.unit
    def test_vector_normalization(self):
        """测试向量归一化"""
        from app.processors.vector_generator import MockEmbedding
        import numpy as np

        generator = MockEmbedding(dimension=128)

        embeddings = generator.generate(["test"])
        vector = np.array(embeddings[0])

        # 检查是否归一化
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.unit
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-slow"),
        reason="需要 OpenAI API key"
    )
    def test_openai_embedding(self):
        """测试 OpenAI 向量生成"""
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        from app.processors.vector_generator import OpenAIEmbedding

        generator = OpenAIEmbedding()

        texts = ["test text"]
        embeddings = generator.generate(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536  # text-embedding-ada-002 维度


@pytest.mark.integration
class TestDocumentPipeline:
    """文档处理管线测试"""

    @pytest.mark.database
    @pytest.mark.storage
    @pytest.mark.vector
    def test_complete_pipeline(
        self,
        db_session,
        storage_client,
        vector_store,
        temp_dir
    ):
        """测试完整处理管线"""
        from app.processors.document_pipeline import DocumentPipeline
        from tests.utils import DBHelper, FileHelper

        # 1. 创建测试文档
        doc = DBHelper.create_test_document(
            db_session,
            type="document",
            mime_type="text/plain"
        )

        # 2. 创建测试文件并上传到存储
        test_file = temp_dir / "test.txt"
        FileHelper.create_test_text(str(test_file), lines=50)

        bucket = "documents"
        object_name = f"test/{doc.id}/test.txt"

        storage_client.upload_file(
            bucket=bucket,
            object_name=object_name,
            file_path=str(test_file)
        )

        # 更新文档存储路径
        doc.storage_path = f"{bucket}/{object_name}"
        db_session.commit()

        # 3. 使用 Mock 向量生成器（避免调用真实 API）
        from app.processors.vector_generator import MockEmbedding

        pipeline = DocumentPipeline(
            storage=storage_client,
            vector_store=vector_store,
            chunk_size=100,
            chunk_overlap=20
        )

        # 替换为 Mock 生成器
        pipeline.vector_generator.generator = MockEmbedding(dimension=1536)

        # 4. 执行处理
        result = pipeline.process(doc.id)

        # 5. 验证结果
        assert result["status"] == "processed"
        assert result["chunks"] > 0
        assert result["vectors"] > 0

        # 6. 验证数据库记录
        from app.models.document_chunk import DocumentChunk

        chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).all()

        assert len(chunks) > 0

        # 7. 验证向量存储
        for chunk in chunks:
            exists = vector_store.vector_exists(chunk.id)
            assert exists is True

    @pytest.mark.unit
    def test_pipeline_error_handling(
        self,
        db_session,
        storage_client,
        vector_store
    ):
        """测试管线错误处理"""
        from app.processors.document_pipeline import DocumentPipeline
        from app.core.exceptions import DocumentProcessingException

        pipeline = DocumentPipeline(
            storage=storage_client,
            vector_store=vector_store
        )

        # 处理不存在的文档
        with pytest.raises(DocumentProcessingException):
            pipeline.process("nonexistent_doc_id")


@pytest.mark.slow
class TestProcessingPerformance:
    """处理性能测试"""

    @pytest.mark.integration
    def test_chunking_performance(self):
        """测试分块性能"""
        from app.processors.text_chunker import TextChunker
        from tests.utils import PerformanceHelper

        chunker = TextChunker(chunk_size=500, chunk_overlap=50)

        # 生成大文本（10000字）
        text = "这是测试文本。" * 2000

        # 测试性能
        _, duration = PerformanceHelper.measure_time(
            chunker.chunk,
            text
        )

        # 断言性能
        from tests.utils import AssertHelper
        AssertHelper.assert_performance(
            duration=duration,
            max_duration=1.0,
            operation="Text chunking (10k chars)"
        )

    @pytest.mark.integration
    def test_vector_generation_performance(self):
        """测试向量生成性能"""
        from app.processors.vector_generator import MockEmbedding
        from tests.utils import PerformanceHelper

        generator = MockEmbedding()

        # 生成100个文本
        texts = [f"Test text {i}" for i in range(100)]

        # 测试性能
        _, duration = PerformanceHelper.measure_time(
            generator.generate,
            texts
        )

        # 断言性能
        from tests.utils import AssertHelper
        AssertHelper.assert_performance(
            duration=duration,
            max_duration=2.0,
            operation="Vector generation (100 texts)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
