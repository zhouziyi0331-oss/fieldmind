"""
测试 ChromaDB 向量存储后端

验证 Chroma 特性和功能
"""

import warnings
# 在导入任何内容之前禁用所有警告
warnings.filterwarnings("ignore")

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from app.vector_store import Document, DistanceMetric, IndexType
from app.vector_store.backends import ChromaVectorStore


class TestChromaVectorStoreBasic:
    """测试基本功能"""

    @pytest.fixture
    def dimension(self):
        """向量维度"""
        return 128

    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_documents(self, dimension):
        """创建示例文档"""
        docs = []
        for i in range(10):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"This is document {i}",
                embedding=embedding,
                metadata={"index": i, "category": f"cat{i % 3}"}
            )
            docs.append(doc)
        return docs

    def test_create_ephemeral_store(self, dimension):
        """测试创建内存存储"""
        store = ChromaVectorStore(
            dimension=dimension,
            collection_name="test_collection"
        )
        assert store.dimension == dimension
        assert store.count() == 0
        assert store.persist_directory is None

    def test_create_persistent_store(self, dimension, temp_dir):
        """测试创建持久化存储"""
        store = ChromaVectorStore(
            dimension=dimension,
            collection_name="test_collection",
            persist_directory=temp_dir
        )
        assert store.dimension == dimension
        assert store.persist_directory == temp_dir
        assert Path(temp_dir).exists()

    def test_add_documents(self, dimension, sample_documents):
        """测试添加文档"""
        store = ChromaVectorStore(
            dimension=dimension,
            collection_name="test_add"
        )
        ids = store.add(sample_documents)

        assert len(ids) == 10
        assert store.count() == 10

    def test_add_empty_list(self, dimension):
        """测试添加空列表"""
        store = ChromaVectorStore(dimension=dimension)
        ids = store.add([])
        assert ids == []

    def test_search_basic(self, dimension, sample_documents):
        """测试基本搜索"""
        store = ChromaVectorStore(
            dimension=dimension,
            collection_name="test_search"
        )
        store.add(sample_documents)

        # 使用第一个文档的向量搜索
        query = sample_documents[0].embedding
        results = store.search(query, top_k=5)

        assert len(results) <= 5
        assert all(hasattr(r, 'document') for r in results)
        assert all(hasattr(r, 'score') for r in results)
        # 第一个结果应该是自己
        assert results[0].document.id == "doc0"

    def test_search_empty_store(self, dimension):
        """测试空存储搜索"""
        store = ChromaVectorStore(dimension=dimension)
        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=5)

        assert results == []

    def test_get_documents(self, dimension, sample_documents):
        """测试获取文档"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(sample_documents)

        docs = store.get(["doc0", "doc5", "nonexistent"])

        assert len(docs) == 3
        assert docs[0] is not None
        assert docs[0].id == "doc0"
        assert docs[1] is not None
        assert docs[1].id == "doc5"
        assert docs[2] is None

    def test_delete_documents(self, dimension, sample_documents):
        """测试删除文档"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(sample_documents)

        deleted = store.delete(["doc0", "doc1", "nonexistent"])

        # 应该删除了2个（nonexistent不存在）
        assert deleted == 2
        assert store.count() == 8

        # 验证已删除
        docs = store.get(["doc0", "doc1"])
        assert docs[0] is None
        assert docs[1] is None

    def test_update_documents(self, dimension, sample_documents):
        """测试更新文档"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(sample_documents)

        # 更新第一个文档
        updated_doc = Document(
            id="doc0",
            content="Updated content",
            embedding=np.random.rand(dimension).astype(np.float32),
            metadata={"updated": True}
        )

        count = store.update([updated_doc])
        assert count == 1

        # 验证更新
        retrieved = store.get(["doc0"])[0]
        assert retrieved is not None
        assert retrieved.content == "Updated content"

    def test_clear(self, dimension, sample_documents):
        """测试清空"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(sample_documents)
        store.clear()

        assert store.count() == 0


class TestChromaFilters:
    """测试元数据过滤功能"""

    @pytest.fixture
    def dimension(self):
        return 64

    @pytest.fixture
    def documents(self, dimension):
        """创建带元数据的文档"""
        docs = []
        for i in range(20):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding,
                metadata={
                    "category": f"cat{i % 3}",
                    "year": 2020 + (i % 5),
                    "score": i * 10,
                }
            )
            docs.append(doc)
        return docs

    def test_filter_equal(self, dimension, documents):
        """测试等于过滤"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(
            query,
            top_k=20,
            filters={"category": "cat0"}
        )

        # 只返回 category="cat0" 的文档
        for r in results:
            assert r.document.metadata["category"] == "cat0"

    def test_filter_greater_than(self, dimension, documents):
        """测试大于过滤"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(
            query,
            top_k=20,
            filters={"year": {"$gt": 2022}}
        )

        # 只返回 year > 2022 的文档
        for r in results:
            assert r.document.metadata["year"] > 2022

    def test_filter_less_than_equal(self, dimension, documents):
        """测试小于等于过滤"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(
            query,
            top_k=20,
            filters={"score": {"$lte": 100}}
        )

        # 只返回 score <= 100 的文档
        for r in results:
            assert r.document.metadata["score"] <= 100

    def test_filter_in(self, dimension, documents):
        """测试 in 过滤"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(
            query,
            top_k=20,
            filters={"category": {"$in": ["cat0", "cat1"]}}
        )

        # 只返回 category 在 ["cat0", "cat1"] 中的文档
        for r in results:
            assert r.document.metadata["category"] in ["cat0", "cat1"]

    def test_filter_and(self, dimension, documents):
        """测试逻辑与过滤"""
        store = ChromaVectorStore(dimension=dimension)
        store.add(documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(
            query,
            top_k=20,
            filters={
                "$and": [
                    {"category": "cat0"},
                    {"year": {"$gte": 2021}}
                ]
            }
        )

        # 同时满足两个条件
        for r in results:
            assert r.document.metadata["category"] == "cat0"
            assert r.document.metadata["year"] >= 2021


class TestChromaDistanceMetrics:
    """测试不同距离度量"""

    @pytest.fixture
    def dimension(self):
        return 64

    @pytest.fixture
    def documents(self, dimension):
        docs = []
        for i in range(5):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding
            )
            docs.append(doc)
        return docs

    def test_cosine_similarity(self, dimension, documents):
        """测试余弦相似度"""
        store = ChromaVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.COSINE
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0
        assert all(0 <= r.score <= 1 for r in results)

    def test_l2_distance(self, dimension, documents):
        """测试 L2 距离"""
        store = ChromaVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.L2
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0
        assert all(r.distance >= 0 for r in results)

    def test_dot_product(self, dimension, documents):
        """测试点积"""
        store = ChromaVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.DOT_PRODUCT
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0


class TestChromaPersistence:
    """测试持久化功能"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def dimension(self):
        return 64

    @pytest.fixture
    def documents(self, dimension):
        docs = []
        for i in range(10):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding
            )
            docs.append(doc)
        return docs

    def test_persistence(self, temp_dir, dimension, documents):
        """测试数据持久化"""
        # 创建并添加数据
        store1 = ChromaVectorStore(
            dimension=dimension,
            collection_name="persist_test",
            persist_directory=temp_dir
        )
        store1.add(documents)

        # 创建新实例（自动加载）
        store2 = ChromaVectorStore(
            dimension=dimension,
            collection_name="persist_test",
            persist_directory=temp_dir
        )

        # 验证数据已持久化
        assert store2.count() == 10

        docs = store2.get([f"doc{i}" for i in range(10)])
        assert all(d is not None for d in docs)

    def test_search_after_reload(self, temp_dir, dimension, documents):
        """测试重新加载后搜索"""
        # 创建并添加数据
        store1 = ChromaVectorStore(
            dimension=dimension,
            collection_name="search_test",
            persist_directory=temp_dir
        )
        store1.add(documents)

        # 重新加载
        store2 = ChromaVectorStore(
            dimension=dimension,
            collection_name="search_test",
            persist_directory=temp_dir
        )

        # 搜索
        query = documents[0].embedding
        results = store2.search(query, top_k=3)

        assert len(results) > 0
        assert results[0].document.id == "doc0"


class TestChromaUtilities:
    """测试工具方法"""

    def test_from_documents(self):
        """测试 from_documents 便捷方法"""
        dimension = 64
        docs = []
        for i in range(5):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding
            )
            docs.append(doc)

        store = ChromaVectorStore.from_documents(
            documents=docs,
            dimension=dimension,
            collection_name="from_docs_test"
        )

        assert store.count() == 5

    def test_get_stats(self):
        """测试获取统计信息"""
        store = ChromaVectorStore(
            dimension=128,
            collection_name="stats_test"
        )

        docs = []
        for i in range(5):
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=np.random.rand(128).astype(np.float32)
            )
            docs.append(doc)
        store.add(docs)

        stats = store.get_stats()

        assert stats["count"] == 5
        assert stats["dimension"] == 128
        assert stats["collection_name"] == "stats_test"

    def test_peek(self):
        """测试预览功能"""
        store = ChromaVectorStore(dimension=64)

        docs = []
        for i in range(10):
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=np.random.rand(64).astype(np.float32)
            )
            docs.append(doc)
        store.add(docs)

        preview = store.peek(limit=5)

        assert "ids" in preview
        assert len(preview["ids"]) <= 5


class TestChromaEdgeCases:
    """测试边界情况"""

    def test_dimension_mismatch(self):
        """测试维度不匹配"""
        store = ChromaVectorStore(dimension=128)

        with pytest.raises(ValueError, match="dimension mismatch"):
            doc = Document(
                id="doc1",
                content="test",
                embedding=np.random.rand(64).astype(np.float32)
            )
            store.add([doc])

    def test_search_top_k_larger_than_count(self):
        """测试 top_k 大于文档数量"""
        store = ChromaVectorStore(dimension=64)

        docs = []
        for i in range(3):
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=np.random.rand(64).astype(np.float32)
            )
            docs.append(doc)
        store.add(docs)

        query = np.random.rand(64).astype(np.float32)
        results = store.search(query, top_k=10)

        assert len(results) == 3

    def test_update_nonexistent_document(self):
        """测试更新不存在的文档"""
        store = ChromaVectorStore(dimension=64)

        doc = Document(
            id="nonexistent",
            content="test",
            embedding=np.random.rand(64).astype(np.float32)
        )

        count = store.update([doc])
        assert count == 0

    def test_metadata_sanitization(self):
        """测试元数据清理"""
        store = ChromaVectorStore(dimension=64)

        # 包含复杂类型的元数据
        doc = Document(
            id="doc1",
            content="test",
            embedding=np.random.rand(64).astype(np.float32),
            metadata={
                "string": "value",
                "int": 42,
                "float": 3.14,
                "bool": True,
                "list": [1, 2, 3],  # 将被转换为字符串
                "dict": {"key": "value"}  # 将被转换为字符串
            }
        )

        ids = store.add([doc])
        assert len(ids) == 1

        # 验证可以检索
        retrieved = store.get(["doc1"])[0]
        assert retrieved is not None
        assert retrieved.metadata["string"] == "value"
        assert retrieved.metadata["int"] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
