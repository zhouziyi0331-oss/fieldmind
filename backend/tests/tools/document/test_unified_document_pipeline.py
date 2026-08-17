"""
统一文档处理流水线测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from app.tools.document import (
    UnifiedDocumentPipeline,
    create_document_pipeline,
    process_single_document,
    DocumentProcessingError,
    ExtractionError,
    ChunkingError,
    VectorizationError,
    StorageError
)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock()
    db.query = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.execute = Mock()
    db.bulk_save_objects = Mock()
    return db


@pytest.fixture
def pipeline(mock_db):
    """创建测试用的pipeline实例"""
    return UnifiedDocumentPipeline(
        db=mock_db,
        max_retries=2,
        retry_delay=0.1,
        enable_checkpoints=False,  # 测试时禁用检查点
        enable_knowledge_graph=False,  # 测试时禁用可选功能
        enable_fact_extraction=False,
        enable_data_curation=False,
        enable_temporal_extraction=False
    )


class TestUnifiedDocumentPipeline:
    """测试统一文档处理流水线"""

    def test_initialization(self, mock_db):
        """测试初始化"""
        pipeline = UnifiedDocumentPipeline(
            db=mock_db,
            max_retries=5,
            retry_delay=2.0,
            enable_checkpoints=True
        )

        assert pipeline.db == mock_db
        assert pipeline.max_retries == 5
        assert pipeline.retry_delay == 2.0
        assert pipeline.enable_checkpoints is True

        # 服务应该是延迟加载的
        assert pipeline._converter is None
        assert pipeline._chunker is None
        assert pipeline._vectorizer is None

    def test_clean_text(self, pipeline):
        """测试文本清洗"""
        # 测试数据
        dirty_text = "这是一段测试文本\r\n\r\n\r\n多余的空白    字符\t\t\t和换行"
        metadata = {"source": "test"}

        cleaned_text, clean_metadata = pipeline._clean_text(dirty_text, metadata)

        # 验证清洗结果
        assert "\r" not in cleaned_text
        assert "    " not in cleaned_text  # 多余空格被压缩
        assert "\n\n\n" not in cleaned_text  # 多余换行被压缩
        assert clean_metadata["cleaned"] is True
        assert "original_length" in clean_metadata
        assert "cleaned_length" in clean_metadata

    def test_process_document_with_text_content(self, pipeline, mock_db):
        """测试直接提供文本内容的处理"""
        # Mock服务
        with patch.object(pipeline, '_get_chunker') as mock_chunker_getter, \
             patch.object(pipeline, '_get_vectorizer') as mock_vectorizer_getter, \
             patch('app.core.rag_engine.rag_engine') as mock_rag:

            # 设置mock chunker
            mock_chunker = Mock()
            mock_chunker.chunk_document = Mock(return_value=[
                {"text": "第一段", "metadata": {"chunk_index": 0}},
                {"text": "第二段", "metadata": {"chunk_index": 1}}
            ])
            mock_chunker_getter.return_value = mock_chunker

            # 设置mock vectorizer
            mock_vectorizer = Mock()
            mock_vectorizer.model_name = "test-model"
            mock_vectorizer.embedding_dim = 384
            mock_vectorizer.vectorize_chunks = Mock(return_value=[
                {"text": "第一段", "embedding": [0.1] * 384, "metadata": {"chunk_index": 0}},
                {"text": "第二段", "embedding": [0.2] * 384, "metadata": {"chunk_index": 1}}
            ])
            mock_vectorizer_getter.return_value = mock_vectorizer

            # 设置mock RAG engine
            mock_collection = Mock()
            mock_collection.add = Mock()
            mock_rag.collection = mock_collection

            # Mock文档记录
            mock_doc = Mock()
            mock_doc.extra_data = {}
            mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

            # 执行处理
            result = pipeline.process_document(
                document_id=1,
                project_id=10,
                text_content="这是一段测试文本。\n包含多个句子。",
                filename="test.txt",
                file_type="txt"
            )

            # 验证结果
            assert result["success"] is True
            assert result["document_id"] == 1
            assert result["project_id"] == 10
            assert "stages" in result
            assert "extraction" in result["stages"]
            assert "cleaning" in result["stages"]
            assert "chunking" in result["stages"]
            assert "vectorization" in result["stages"]
            assert "storage" in result["stages"]

            # 验证统计
            assert "statistics" in result
            assert result["statistics"]["total_chunks"] == 2
            assert result["statistics"]["stored_chunks"] == 2

            # 验证调用
            mock_chunker.chunk_document.assert_called_once()
            mock_vectorizer.vectorize_chunks.assert_called_once()
            mock_collection.add.assert_called_once()

    def test_extraction_error_handling(self, pipeline):
        """测试内容提取错误处理"""
        # 不提供file_path和text_content
        with pytest.raises(ExtractionError) as exc_info:
            pipeline._extract_content_with_retry(
                file_path=None,
                text_content=None,
                file_type=None,
                document_id=1
            )

        assert "必须提供" in str(exc_info.value)

    def test_chunking_with_retry(self, pipeline):
        """测试带重试的切分"""
        text = "这是测试文本。" * 100
        metadata = {"document_id": 1, "filename": "test.txt", "file_type": "txt"}

        # Mock chunker第一次失败，第二次成功
        mock_chunker = Mock()
        call_count = [0]

        def chunk_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("第一次失败")
            else:
                from app.services.document_chunker import DocumentChunker
                chunker = DocumentChunker()
                return chunker.chunk_document(text, metadata)

        mock_chunker.chunk_document = Mock(side_effect=chunk_side_effect)

        with patch.object(pipeline, '_get_chunker', return_value=mock_chunker):
            # 第一次调用应该重试并成功
            chunks = pipeline._chunk_with_retry(text, metadata)
            assert len(chunks) > 0
            assert call_count[0] == 2  # 第一次失败，第二次成功

    def test_chunking_retry_exhausted(self, pipeline):
        """测试重试次数耗尽"""
        text = "测试文本"
        metadata = {}

        # Mock chunker始终失败
        mock_chunker = Mock()
        mock_chunker.chunk_document = Mock(side_effect=Exception("持续失败"))

        with patch.object(pipeline, '_get_chunker', return_value=mock_chunker):
            with pytest.raises(ChunkingError) as exc_info:
                pipeline._chunk_with_retry(text, metadata)

            assert "重试" in str(exc_info.value)

    def test_vectorization_with_retry(self, pipeline):
        """测试带重试的向量化"""
        chunks = [
            {"text": "测试文本1", "metadata": {}},
            {"text": "测试文本2", "metadata": {}}
        ]

        # Mock vectorizer
        mock_vectorizer = Mock()
        mock_vectorizer.vectorize_chunks = Mock(return_value=[
            {"text": "测试文本1", "embedding": [0.1] * 384},
            {"text": "测试文本2", "embedding": [0.2] * 384}
        ])

        with patch.object(pipeline, '_get_vectorizer', return_value=mock_vectorizer):
            result = pipeline._vectorize_with_retry(chunks)

            assert len(result) == 2
            assert "embedding" in result[0]
            assert len(result[0]["embedding"]) == 384

    def test_storage_with_retry(self, pipeline, mock_db):
        """测试带重试的存储"""
        chunks = [
            {"text": "文本1", "embedding": [0.1] * 384},
            {"text": "文本2", "embedding": [0.2] * 384}
        ]

        # Mock RAG engine
        with patch('app.core.rag_engine.rag_engine') as mock_rag:
            mock_collection = Mock()
            mock_collection.add = Mock()
            mock_rag.collection = mock_collection

            stored_count = pipeline._store_with_retry(
                chunks=chunks,
                document_id=1,
                project_id=10,
                metadata={"source": "test"}
            )

            assert stored_count == 2
            mock_collection.add.assert_called_once()

            # 验证传递给ChromaDB的参数
            call_args = mock_collection.add.call_args
            assert len(call_args.kwargs['ids']) == 2
            assert len(call_args.kwargs['documents']) == 2
            assert len(call_args.kwargs['metadatas']) == 2
            assert len(call_args.kwargs['embeddings']) == 2

    def test_checkpoint_management(self, mock_db):
        """测试检查点管理"""
        pipeline = UnifiedDocumentPipeline(
            db=mock_db,
            enable_checkpoints=True
        )

        # 保存检查点
        pipeline._save_checkpoint(
            document_id=123,
            stage="chunked",
            data={"chunks": [{"text": "测试"}]}
        )

        # 加载检查点
        checkpoint = pipeline._load_checkpoint(123)
        assert checkpoint is not None
        assert checkpoint["document_id"] == 123
        assert checkpoint["stage"] == "chunked"
        assert "chunks" in checkpoint["data"]

        # 清除检查点
        pipeline._clear_checkpoint(123)
        checkpoint = pipeline._load_checkpoint(123)
        assert checkpoint is None

    def test_fact_statements_extraction(self, pipeline):
        """测试事实陈述提取"""
        text = "这是第一个事实陈述。这是第二个事实陈述。这是第三个事实陈述。"

        # Mock数据库执行
        pipeline.db.execute = Mock()
        pipeline.db.commit = Mock()

        count = pipeline._insert_fact_statements(
            text=text,
            document_id=1,
            project_id=10,
            source_file="test.txt"
        )

        assert count == 3
        pipeline.db.execute.assert_called_once()
        pipeline.db.commit.assert_called_once()

    def test_fact_statements_from_segments(self, pipeline):
        """测试从segments提取事实陈述"""
        segments = [
            {"text": "第一段音频文本", "start": 0.0, "end": 5.0},
            {"text": "第二段音频文本", "start": 5.0, "end": 10.0},
            {"text": "第三段音频文本", "start": 10.0, "end": 15.0}
        ]

        # Mock数据库执行
        pipeline.db.execute = Mock()
        pipeline.db.commit = Mock()

        count = pipeline._insert_fact_statements_from_segments(
            segments=segments,
            document_id=1,
            project_id=10,
            source_file="audio.mp3"
        )

        assert count == 3
        pipeline.db.execute.assert_called_once()
        pipeline.db.commit.assert_called_once()

    def test_batch_processing(self, pipeline, mock_db):
        """测试批处理"""
        documents = [
            {
                "document_id": 1,
                "project_id": 10,
                "text_content": "文档1内容"
            },
            {
                "document_id": 2,
                "project_id": 10,
                "text_content": "文档2内容"
            },
            {
                "document_id": 3,
                "project_id": 10,
                "text_content": "文档3内容"
            }
        ]

        # Mock process_document
        with patch.object(pipeline, 'process_document') as mock_process:
            mock_process.return_value = {"success": True, "document_id": 1}

            results = pipeline.batch_process_documents(documents)

            assert len(results) == 3
            assert mock_process.call_count == 3

    def test_convenience_functions(self, mock_db):
        """测试便捷函数"""
        # 测试 create_document_pipeline
        pipeline = create_document_pipeline(mock_db, max_retries=5)
        assert isinstance(pipeline, UnifiedDocumentPipeline)
        assert pipeline.max_retries == 5

        # 测试 process_single_document
        with patch.object(UnifiedDocumentPipeline, 'process_document') as mock_process:
            mock_process.return_value = {"success": True}

            result = process_single_document(
                db=mock_db,
                document_id=1,
                project_id=10,
                text_content="测试文本"
            )

            assert result["success"] is True
            mock_process.assert_called_once()


class TestErrorHandling:
    """测试错误处理"""

    def test_extraction_error(self):
        """测试提取错误"""
        error = ExtractionError("提取失败")
        assert isinstance(error, DocumentProcessingError)
        assert str(error) == "提取失败"

    def test_chunking_error(self):
        """测试切分错误"""
        error = ChunkingError("切分失败")
        assert isinstance(error, DocumentProcessingError)

    def test_vectorization_error(self):
        """测试向量化错误"""
        error = VectorizationError("向量化失败")
        assert isinstance(error, DocumentProcessingError)

    def test_storage_error(self):
        """测试存储错误"""
        error = StorageError("存储失败")
        assert isinstance(error, DocumentProcessingError)


class TestIntegration:
    """集成测试"""

    def test_full_pipeline_flow(self, mock_db):
        """测试完整流程（模拟）"""
        pipeline = UnifiedDocumentPipeline(
            db=mock_db,
            enable_checkpoints=False,
            enable_knowledge_graph=False,
            enable_fact_extraction=False,
            enable_data_curation=False,
            enable_temporal_extraction=False
        )

        # Mock所有服务
        with patch.object(pipeline, '_get_chunker') as mock_chunker_getter, \
             patch.object(pipeline, '_get_vectorizer') as mock_vectorizer_getter, \
             patch('app.core.rag_engine.rag_engine') as mock_rag:

            # 设置mocks
            mock_chunker = Mock()
            mock_chunker.chunk_document = Mock(return_value=[
                {"text": "Chunk 1", "metadata": {}},
                {"text": "Chunk 2", "metadata": {}}
            ])
            mock_chunker_getter.return_value = mock_chunker

            mock_vectorizer = Mock()
            mock_vectorizer.model_name = "test-model"
            mock_vectorizer.embedding_dim = 384
            mock_vectorizer.vectorize_chunks = Mock(return_value=[
                {"text": "Chunk 1", "embedding": [0.1] * 384},
                {"text": "Chunk 2", "embedding": [0.2] * 384}
            ])
            mock_vectorizer_getter.return_value = mock_vectorizer

            mock_collection = Mock()
            mock_rag.collection = mock_collection

            mock_doc = Mock()
            mock_doc.extra_data = {}
            mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

            # 执行
            result = pipeline.process_document(
                document_id=1,
                project_id=10,
                text_content="完整的测试文档内容。包含多个句子。"
            )

            # 验证
            assert result["success"] is True
            assert "stages" in result
            assert "statistics" in result
            assert result["statistics"]["total_chunks"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
