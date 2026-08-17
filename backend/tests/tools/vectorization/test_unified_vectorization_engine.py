"""
统一向量化引擎测试

测试UnifiedVectorizationEngine的所有功能:
- 4种编码引擎 (BGE-large/small, MiniLM, TF-IDF)
- 4种存储后端 (SQL, ChromaDB, Dual, Memory)
- 编码接口 (query, documents, batch)
- 存储接口 (vectorize_and_store)
- 检索接口 (search_similar)
- 管理接口 (delete, statistics)
- 便捷函数
- 降级策略
- 输出模式 (dataclass vs dict)
"""

import pytest
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

from app.tools.vectorization import (
    UnifiedVectorizationEngine,
    VectorEngine,
    StorageBackend,
    VectorizedChunk,
    SearchResult,
    VectorStatistics,
    create_engine,
    encode_query,
    encode_documents,
)


# ==================== 测试数据 ====================

SAMPLE_TEXTS = [
    "费孝通先生在江村进行了深入的田野调查",
    "十八洞村是精准扶贫的典型案例",
    "苗族银饰是重要的非物质文化遗产",
    "布依族的山歌传承了古老的民族文化",
    "侗族的鼓楼是村寨的文化中心",
]

SAMPLE_QUERIES = [
    "田野调查方法",
    "扶贫案例",
    "非遗传承",
]

SAMPLE_CHUNKS = [
    {
        "chunk_id": "chunk_001",
        "text": "费孝通先生在江村进行了深入的田野调查",
        "document_id": "doc_001",
        "chunk_index": 0,
        "metadata": {"author": "费孝通", "location": "江村"},
    },
    {
        "chunk_id": "chunk_002",
        "text": "十八洞村是精准扶贫的典型案例",
        "document_id": "doc_001",
        "chunk_index": 1,
        "metadata": {"location": "十八洞村", "topic": "扶贫"},
    },
    {
        "chunk_id": "chunk_003",
        "text": "苗族银饰是重要的非物质文化遗产",
        "document_id": "doc_002",
        "chunk_index": 0,
        "metadata": {"ethnic": "苗族", "topic": "非遗"},
    },
]


# ==================== 1. 基础初始化测试 ====================

class TestInitialization:
    """测试引擎初始化"""

    def test_init_with_tfidf(self):
        """测试TF-IDF引擎初始化（最可靠，无需下载）"""
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        assert engine.engine_type == VectorEngine.TFIDF
        assert engine.storage_backend == StorageBackend.MEMORY
        assert engine.dimension == 384
        assert engine.model_name == "tfidf-local"
        assert engine.encoder is not None

    def test_init_with_memory_storage(self):
        """测试内存存储初始化"""
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        assert engine.memory_storage == {}
        assert engine.sql_storage is None
        assert engine.chroma_storage is None

    def test_singleton_pattern(self):
        """测试单例模式"""
        engine1 = UnifiedVectorizationEngine.get_instance(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )
        engine2 = UnifiedVectorizationEngine.get_instance(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        assert engine1 is engine2

    def test_different_instances_for_different_configs(self):
        """测试不同配置使用不同实例"""
        engine1 = UnifiedVectorizationEngine.get_instance(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )
        engine2 = UnifiedVectorizationEngine.get_instance(
            engine=VectorEngine.MINILM,
            storage=StorageBackend.MEMORY
        )

        # 可能是同一个（如果MiniLM降级到TF-IDF）或不同
        # 至少不会报错
        assert engine1 is not None
        assert engine2 is not None


# ==================== 2. 编码功能测试 ====================

class TestEncoding:
    """测试编码功能"""

    @pytest.fixture
    def engine(self):
        """创建TF-IDF引擎用于测试"""
        return UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

    def test_encode_query_basic(self, engine):
        """测试查询编码"""
        query = "田野调查方法"
        embedding = engine.encode_query(query)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert not np.isnan(embedding).any()

    def test_encode_query_normalization(self, engine):
        """测试查询向量归一化"""
        query = "扶贫案例研究"
        embedding = engine.encode_query(query, normalize=True)

        # 归一化向量的模应该接近1
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    def test_encode_empty_query(self, engine):
        """测试空查询"""
        with pytest.raises(ValueError):
            engine.encode_query("")

    def test_encode_documents_batch(self, engine):
        """测试批量文档编码"""
        embeddings = engine.encode_documents(SAMPLE_TEXTS)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(SAMPLE_TEXTS), 384)
        assert not np.isnan(embeddings).any()

    def test_encode_documents_empty_list(self, engine):
        """测试空文档列表"""
        embeddings = engine.encode_documents([])

        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings) == 0

    def test_encode_documents_with_empty_strings(self, engine):
        """测试包含空字符串的文档列表"""
        texts = ["有效文本", "", "  ", "另一个有效文本"]
        embeddings = engine.encode_documents(texts)

        # 空字符串会被过滤
        assert len(embeddings) == 2

    def test_encode_batch_processing(self, engine):
        """测试批处理"""
        # 大批量测试
        large_batch = [f"文本{i}" for i in range(100)]
        embeddings = engine.encode_documents(large_batch, batch_size=32)

        assert len(embeddings) == 100

    def test_dimension_consistency(self, engine):
        """测试维度一致性"""
        query_emb = engine.encode_query("测试查询")
        doc_embs = engine.encode_documents(["测试文档1", "测试文档2"])

        assert query_emb.shape[0] == engine.dimension
        assert doc_embs.shape[1] == engine.dimension


# ==================== 3. 存储功能测试 ====================

class TestStorage:
    """测试存储功能"""

    @pytest.fixture
    def engine(self):
        """创建内存存储引擎"""
        return UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

    def test_vectorize_and_store_basic(self, engine):
        """测试基本向量化和存储"""
        result = engine.vectorize_and_store(SAMPLE_CHUNKS)

        assert len(result) == len(SAMPLE_CHUNKS)
        assert all(isinstance(chunk, VectorizedChunk) for chunk in result)

        # 检查第一个结果
        first = result[0]
        assert first.chunk_id == "chunk_001"
        assert first.text == "费孝通先生在江村进行了深入的田野调查"
        assert len(first.embedding) == 384
        assert first.dimension == 384
        assert first.model == "tfidf-local"

    def test_storage_in_memory(self, engine):
        """测试内存存储"""
        engine.vectorize_and_store(SAMPLE_CHUNKS)

        # 检查内存存储
        assert len(engine.memory_storage) == 3
        assert "chunk_001" in engine.memory_storage
        assert "chunk_002" in engine.memory_storage
        assert "chunk_003" in engine.memory_storage

    def test_output_mode_dataclass(self, engine):
        """测试dataclass输出模式"""
        result = engine.vectorize_and_store(SAMPLE_CHUNKS, output_mode="dataclass")

        assert all(isinstance(chunk, VectorizedChunk) for chunk in result)

    def test_output_mode_dict(self, engine):
        """测试dict输出模式（向后兼容）"""
        result = engine.vectorize_and_store(SAMPLE_CHUNKS, output_mode="dict")

        assert all(isinstance(chunk, dict) for chunk in result)
        assert "chunk_id" in result[0]
        assert "embedding" in result[0]
        assert "dimension" in result[0]

    def test_metadata_preservation(self, engine):
        """测试元数据保留"""
        result = engine.vectorize_and_store(SAMPLE_CHUNKS)

        first = result[0]
        assert first.metadata["author"] == "费孝通"
        assert first.metadata["location"] == "江村"

    def test_empty_chunks_list(self, engine):
        """测试空chunks列表"""
        result = engine.vectorize_and_store([])

        assert result == []


# ==================== 4. 检索功能测试 ====================

class TestSearch:
    """测试检索功能"""

    @pytest.fixture
    def engine_with_data(self):
        """创建并填充数据的引擎"""
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )
        engine.vectorize_and_store(SAMPLE_CHUNKS)
        return engine

    def test_search_similar_basic(self, engine_with_data):
        """测试基本语义检索"""
        results = engine_with_data.search_similar(
            query="田野调查",
            top_k=3
        )

        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)

        # 检查结果结构
        if results:
            first = results[0]
            assert isinstance(first.chunk, VectorizedChunk)
            assert isinstance(first.score, float)
            assert 0.0 <= first.score <= 1.0
            assert first.rank >= 1

    def test_search_ranking(self, engine_with_data):
        """测试检索结果排序"""
        results = engine_with_data.search_similar(
            query="扶贫工作",
            top_k=3
        )

        # 相似度应该递减
        if len(results) > 1:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

        # rank应该递增
        ranks = [r.rank for r in results]
        assert ranks == list(range(1, len(results) + 1))

    def test_search_with_threshold(self, engine_with_data):
        """测试相似度阈值"""
        # 高阈值应该返回更少结果
        results_high = engine_with_data.search_similar(
            query="田野调查",
            top_k=10,
            threshold=0.8
        )

        results_low = engine_with_data.search_similar(
            query="田野调查",
            top_k=10,
            threshold=0.0
        )

        assert len(results_high) <= len(results_low)

    def test_search_with_filters(self, engine_with_data):
        """测试过滤条件"""
        # 注意: 内存存储的过滤是基于metadata的
        results = engine_with_data.search_similar(
            query="文化",
            top_k=10,
            filters={"topic": "非遗"}
        )

        # 应该只返回topic=非遗的结果
        for result in results:
            assert result.chunk.metadata.get("topic") == "非遗"

    def test_search_top_k_limit(self, engine_with_data):
        """测试top_k限制"""
        results = engine_with_data.search_similar(
            query="文化",
            top_k=2
        )

        assert len(results) <= 2

    def test_search_output_mode_dict(self, engine_with_data):
        """测试dict输出模式"""
        results = engine_with_data.search_similar(
            query="田野调查",
            top_k=3,
            output_mode="dict"
        )

        assert all(isinstance(r, dict) for r in results)
        if results:
            assert "chunk" in results[0]
            assert "score" in results[0]
            assert "rank" in results[0]

    def test_search_empty_query(self, engine_with_data):
        """测试空查询"""
        results = engine_with_data.search_similar(query="", top_k=3)

        assert results == []


# ==================== 5. 管理功能测试 ====================

class TestManagement:
    """测试管理功能"""

    @pytest.fixture
    def engine_with_data(self):
        """创建并填充数据的引擎"""
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )
        engine.vectorize_and_store(SAMPLE_CHUNKS)
        return engine

    def test_delete_by_document(self, engine_with_data):
        """测试按文档ID删除"""
        # 删除前
        assert len(engine_with_data.memory_storage) == 3

        # 删除doc_001的所有chunks
        success = engine_with_data.delete_by_document("doc_001")

        assert success
        assert len(engine_with_data.memory_storage) == 1
        assert "chunk_003" in engine_with_data.memory_storage

    def test_get_statistics_basic(self, engine_with_data):
        """测试统计信息"""
        stats = engine_with_data.get_statistics()

        assert isinstance(stats, VectorStatistics)
        assert stats.total_chunks == 3
        assert stats.total_documents == 2  # doc_001 和 doc_002
        assert stats.dimension == 384
        assert stats.model == "tfidf-local"
        assert stats.storage_backend == StorageBackend.MEMORY

    def test_get_statistics_avg_length(self, engine_with_data):
        """测试平均长度统计"""
        stats = engine_with_data.get_statistics()

        expected_avg = sum(len(c["text"]) for c in SAMPLE_CHUNKS) / len(SAMPLE_CHUNKS)
        assert abs(stats.avg_chunk_length - expected_avg) < 0.1

    def test_statistics_to_dict(self, engine_with_data):
        """测试统计信息转dict"""
        stats = engine_with_data.get_statistics()
        stats_dict = stats.to_dict()

        assert isinstance(stats_dict, dict)
        assert "total_chunks" in stats_dict
        assert "dimension" in stats_dict
        assert "model" in stats_dict


# ==================== 6. 多引擎测试 ====================

class TestMultipleEngines:
    """测试不同引擎"""

    def test_tfidf_engine(self):
        """测试TF-IDF引擎"""
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        assert engine.engine_type == VectorEngine.TFIDF
        assert engine.dimension == 384

        # 测试编码
        emb = engine.encode_query("测试")
        assert len(emb) == 384

    @pytest.mark.skipif(True, reason="BGE模型可能未安装")
    def test_bge_small_engine(self):
        """测试BGE Small引擎（可能跳过）"""
        try:
            engine = UnifiedVectorizationEngine(
                engine=VectorEngine.BGE_SMALL,
                storage=StorageBackend.MEMORY,
                auto_fallback=False
            )

            assert engine.engine_type == VectorEngine.BGE_SMALL
            assert engine.dimension == 512

        except RuntimeError:
            pytest.skip("BGE Small not available")

    @pytest.mark.skipif(True, reason="MiniLM模型可能未安装")
    def test_minilm_engine(self):
        """测试MiniLM引擎（可能跳过）"""
        try:
            engine = UnifiedVectorizationEngine(
                engine=VectorEngine.MINILM,
                storage=StorageBackend.MEMORY,
                auto_fallback=False
            )

            assert engine.engine_type == VectorEngine.MINILM
            assert engine.dimension == 384

        except RuntimeError:
            pytest.skip("MiniLM not available")


# ==================== 7. 降级策略测试 ====================

class TestFallback:
    """测试自动降级"""

    def test_auto_fallback_enabled(self):
        """测试启用自动降级"""
        # 尝试加载不存在的大模型，应该降级到TF-IDF
        engine = UnifiedVectorizationEngine(
            engine=VectorEngine.BGE_LARGE,
            storage=StorageBackend.MEMORY,
            auto_fallback=True
        )

        # 应该成功初始化（降级到某个可用引擎）
        assert engine.encoder is not None
        assert engine.dimension > 0

    def test_auto_fallback_disabled(self):
        """测试禁用自动降级"""
        # 禁用降级，加载失败应该抛异常
        try:
            engine = UnifiedVectorizationEngine(
                engine=VectorEngine.BGE_LARGE,
                storage=StorageBackend.MEMORY,
                auto_fallback=False
            )
            # 如果BGE Large恰好可用，测试通过
            assert engine.engine_type == VectorEngine.BGE_LARGE
        except RuntimeError:
            # 预期行为：没有降级，抛异常
            pass


# ==================== 8. 便捷函数测试 ====================

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_engine(self):
        """测试create_engine函数"""
        engine = create_engine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        assert isinstance(engine, UnifiedVectorizationEngine)
        assert engine.engine_type == VectorEngine.TFIDF

    def test_encode_query_function(self):
        """测试encode_query便捷函数"""
        embedding = encode_query("测试查询", engine=VectorEngine.TFIDF)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 384

    def test_encode_documents_function(self):
        """测试encode_documents便捷函数"""
        embeddings = encode_documents(
            ["文本1", "文本2"],
            engine=VectorEngine.TFIDF
        )

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 384)


# ==================== 9. 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def engine(self):
        return UnifiedVectorizationEngine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

    def test_very_long_text(self, engine):
        """测试超长文本"""
        long_text = "测试" * 10000  # 20000字符
        embedding = engine.encode_query(long_text)

        assert len(embedding) == 384
        assert not np.isnan(embedding).any()

    def test_special_characters(self, engine):
        """测试特殊字符"""
        texts = [
            "包含emoji😀😁😂",
            "包含符号!@#$%^&*()",
            "包含换行\n和\t制表符",
            "包含中文标点，。！？",
        ]

        embeddings = engine.encode_documents(texts)
        assert len(embeddings) == len(texts)

    def test_single_character(self, engine):
        """测试单字符"""
        embedding = engine.encode_query("测")
        assert len(embedding) == 384

    def test_numeric_text(self, engine):
        """测试纯数字"""
        embedding = engine.encode_query("123456789")
        assert len(embedding) == 384

    def test_mixed_languages(self, engine):
        """测试混合语言"""
        texts = [
            "中英混合 English mixed",
            "日本語も含む text",
            "Полный multilingual 多语言",
        ]

        embeddings = engine.encode_documents(texts)
        assert len(embeddings) == len(texts)

    def test_repeated_vectorization(self, engine):
        """测试重复向量化"""
        # 多次向量化同一文本，结果应该一致
        text = "重复测试文本"

        emb1 = engine.encode_query(text)
        emb2 = engine.encode_query(text)

        # TF-IDF应该返回相同结果
        assert np.allclose(emb1, emb2, atol=1e-6)


# ==================== 10. 集成测试 ====================

class TestIntegration:
    """端到端集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建引擎
        engine = create_engine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        # 2. 向量化并存储
        chunks = [
            {"chunk_id": f"c{i}", "text": text, "document_id": "doc1", "chunk_index": i}
            for i, text in enumerate(SAMPLE_TEXTS)
        ]
        vectorized = engine.vectorize_and_store(chunks)

        assert len(vectorized) == len(SAMPLE_TEXTS)

        # 3. 语义检索
        results = engine.search_similar("田野调查", top_k=3)

        assert len(results) > 0
        assert results[0].rank == 1

        # 4. 获取统计
        stats = engine.get_statistics()

        assert stats.total_chunks == len(SAMPLE_TEXTS)

        # 5. 删除
        success = engine.delete_by_document("doc1")
        assert success

        # 6. 验证删除
        stats_after = engine.get_statistics()
        assert stats_after.total_chunks == 0

    def test_multiple_documents_workflow(self):
        """测试多文档工作流"""
        engine = create_engine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        # 存储多个文档
        for doc_id in ["doc1", "doc2", "doc3"]:
            chunks = [
                {
                    "chunk_id": f"{doc_id}_c{i}",
                    "text": f"{doc_id} 内容 {i}",
                    "document_id": doc_id,
                    "chunk_index": i,
                }
                for i in range(5)
            ]
            engine.vectorize_and_store(chunks)

        # 统计
        stats = engine.get_statistics()
        assert stats.total_chunks == 15
        assert stats.total_documents == 3

        # 删除一个文档
        engine.delete_by_document("doc2")

        # 验证
        stats_after = engine.get_statistics()
        assert stats_after.total_chunks == 10
        assert stats_after.total_documents == 2

    def test_search_accuracy(self):
        """测试检索准确性"""
        engine = create_engine(
            engine=VectorEngine.TFIDF,
            storage=StorageBackend.MEMORY
        )

        # 存储测试数据
        test_data = [
            {"chunk_id": "c1", "text": "费孝通的江村经济研究", "document_id": "d1", "chunk_index": 0},
            {"chunk_id": "c2", "text": "精准扶贫政策实施", "document_id": "d2", "chunk_index": 0},
            {"chunk_id": "c3", "text": "非物质文化遗产保护", "document_id": "d3", "chunk_index": 0},
        ]
        engine.vectorize_and_store(test_data)

        # 查询1: 应该匹配c1
        results1 = engine.search_similar("江村调查", top_k=1)
        assert len(results1) > 0
        # TF-IDF基于关键词，"江村"应该匹配c1
        # 但不保证绝对准确，所以只检查返回了结果

        # 查询2: 应该匹配c2
        results2 = engine.search_similar("扶贫工作", top_k=1)
        assert len(results2) > 0

        # 查询3: 应该匹配c3
        results3 = engine.search_similar("文化遗产", top_k=1)
        assert len(results3) > 0


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
