"""
测试 FAISS 向量存储后端

验证所有索引类型和功能
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from app.vector_store import Document, DistanceMetric, IndexType
from app.vector_store.backends import FaissVectorStore


class TestFaissVectorStoreBasic:
    """测试基本功能"""

    @pytest.fixture
    def dimension(self):
        """向量维度"""
        return 128

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

    def test_create_flat_index(self, dimension):
        """测试创建 Flat 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.FLAT
        )
        assert store.dimension == dimension
        assert store.count() == 0

    def test_create_ivf_index(self, dimension):
        """测试创建 IVF 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.IVF,
            ivf_nlist=10,
            ivf_nprobe=5
        )
        assert store.dimension == dimension
        assert store.ivf_nlist == 10
        assert store.ivf_nprobe == 5

    def test_create_hnsw_index(self, dimension):
        """测试创建 HNSW 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.HNSW,
            hnsw_m=16,
            hnsw_ef_construction=100
        )
        assert store.dimension == dimension
        assert store.hnsw_m == 16

    def test_add_documents(self, dimension, sample_documents):
        """测试添加文档"""
        store = FaissVectorStore(dimension=dimension)
        ids = store.add(sample_documents)

        assert len(ids) == 10
        assert store.count() == 10
        assert all(doc.id in ids for doc in sample_documents)

    def test_add_empty_list(self, dimension):
        """测试添加空列表"""
        store = FaissVectorStore(dimension=dimension)
        ids = store.add([])
        assert ids == []
        assert store.count() == 0

    def test_search_basic(self, dimension, sample_documents):
        """测试基本搜索"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)

        # 使用第一个文档的向量搜索
        query = sample_documents[0].embedding
        results = store.search(query, top_k=5)

        assert len(results) <= 5
        assert all(hasattr(r, 'document') for r in results)
        assert all(hasattr(r, 'score') for r in results)
        # 第一个结果应该是自己（最相似）
        assert results[0].document.id == "doc0"

    def test_search_with_filters(self, dimension, sample_documents):
        """测试带过滤的搜索"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=10, filters={"category": "cat0"})

        # 只返回 category="cat0" 的文档
        assert all(r.document.metadata["category"] == "cat0" for r in results)

    def test_search_empty_store(self, dimension):
        """测试在空存储中搜索"""
        store = FaissVectorStore(dimension=dimension)
        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=5)

        assert results == []

    def test_get_documents(self, dimension, sample_documents):
        """测试获取文档"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)

        docs = store.get(["doc0", "doc5", "nonexistent"])

        assert len(docs) == 3
        assert docs[0].id == "doc0"
        assert docs[1].id == "doc5"
        assert docs[2] is None

    def test_delete_documents(self, dimension, sample_documents):
        """测试删除文档"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)

        deleted = store.delete(["doc0", "doc1", "nonexistent"])

        assert deleted == 2
        assert store.count() == 8
        assert not store.exists("doc0")
        assert not store.exists("doc1")
        assert store.exists("doc2")

    def test_update_documents(self, dimension, sample_documents):
        """测试更新文档"""
        store = FaissVectorStore(dimension=dimension)
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
        retrieved = store.get(["doc0"])[0]
        assert retrieved.content == "Updated content"
        assert retrieved.metadata["updated"] is True

    def test_clear(self, dimension, sample_documents):
        """测试清空"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)
        store.clear()

        assert store.count() == 0
        assert len(store._documents) == 0

    def test_rebuild_index(self, dimension, sample_documents):
        """测试重建索引"""
        store = FaissVectorStore(dimension=dimension)
        store.add(sample_documents)

        # 删除一些文档
        store.delete(["doc0", "doc1"])

        # 重建索引
        store.rebuild_index()

        assert store.count() == 8
        # 确保搜索仍然有效
        query = sample_documents[2].embedding
        results = store.search(query, top_k=3)
        assert len(results) > 0


class TestFaissDistanceMetrics:
    """测试不同的距离度量"""

    @pytest.fixture
    def dimension(self):
        return 64

    @pytest.fixture
    def documents(self, dimension):
        """创建测试文档"""
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
        store = FaissVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.COSINE
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0
        # 余弦相似度应该在 [0, 1]
        assert all(0 <= r.score <= 1 for r in results)

    def test_l2_distance(self, dimension, documents):
        """测试 L2 距离"""
        store = FaissVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.L2
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0
        # 距离应该 >= 0
        assert all(r.distance >= 0 for r in results)

    def test_dot_product(self, dimension, documents):
        """测试点积"""
        store = FaissVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.DOT_PRODUCT
        )
        store.add(documents)

        query = documents[0].embedding
        results = store.search(query, top_k=3)

        assert len(results) > 0


class TestFaissIndexTypes:
    """测试不同的索引类型"""

    @pytest.fixture
    def dimension(self):
        return 128

    @pytest.fixture
    def large_documents(self, dimension):
        """创建更多文档（用于 IVF）"""
        docs = []
        for i in range(200):
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding
            )
            docs.append(doc)
        return docs

    def test_flat_index(self, dimension, large_documents):
        """测试 Flat 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.FLAT
        )
        store.add(large_documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=10)

        assert len(results) == 10

    def test_ivf_index(self, dimension, large_documents):
        """测试 IVF 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.IVF,
            ivf_nlist=20,
            ivf_nprobe=5
        )
        store.add(large_documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=10)

        assert len(results) == 10

    def test_hnsw_index(self, dimension, large_documents):
        """测试 HNSW 索引"""
        store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.HNSW,
            hnsw_m=16,
            hnsw_ef_construction=100,
            hnsw_ef_search=64
        )
        store.add(large_documents)

        query = np.random.rand(dimension).astype(np.float32)
        results = store.search(query, top_k=10)

        assert len(results) == 10


class TestFaissPersistence:
    """测试持久化功能"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
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

    def test_save_and_load(self, temp_dir, dimension, documents):
        """测试保存和加载"""
        # 创建并保存
        store1 = FaissVectorStore(dimension=dimension)
        store1.add(documents)
        save_path = store1.save(temp_dir)

        assert Path(save_path, "index.faiss").exists()
        assert Path(save_path, "metadata.pkl").exists()

        # 加载
        store2 = FaissVectorStore.load(temp_dir)

        assert store2.count() == 10
        assert store2.dimension == dimension

        # 验证文档内容
        docs = store2.get([f"doc{i}" for i in range(10)])
        assert all(d is not None for d in docs)
        assert all(d.content == f"content {i}" for i, d in enumerate(docs))

    def test_save_with_persist_dir(self, temp_dir, dimension, documents):
        """测试使用 persist_dir 保存"""
        store = FaissVectorStore(
            dimension=dimension,
            persist_dir=temp_dir
        )
        store.add(documents)
        store.save()  # 不指定路径

        assert Path(temp_dir, "index.faiss").exists()

    def test_search_after_load(self, temp_dir, dimension, documents):
        """测试加载后搜索功能"""
        # 创建并保存
        store1 = FaissVectorStore(dimension=dimension)
        store1.add(documents)
        store1.save(temp_dir)

        # 加载
        store2 = FaissVectorStore.load(temp_dir)

        # 搜索
        query = documents[0].embedding
        results = store2.search(query, top_k=3)

        assert len(results) > 0
        assert results[0].document.id == "doc0"


class TestFaissStats:
    """测试统计信息"""

    def test_get_stats(self):
        """测试获取统计信息"""
        store = FaissVectorStore(
            dimension=128,
            index_type=IndexType.HNSW,
            hnsw_m=16
        )

        # 添加一些文档
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
        assert stats["index_type"] == "hnsw"
        assert "hnsw_m" in stats


class TestFaissEdgeCases:
    """测试边界情况"""

    def test_dimension_mismatch(self):
        """测试维度不匹配"""
        store = FaissVectorStore(dimension=128)

        # 尝试添加错误维度的文档
        with pytest.raises(ValueError, match="dimension mismatch"):
            doc = Document(
                id="doc1",
                content="test",
                embedding=np.random.rand(64).astype(np.float32)  # 错误维度
            )
            store.add([doc])

    def test_search_top_k_larger_than_count(self):
        """测试 top_k 大于文档数量"""
        store = FaissVectorStore(dimension=64)

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

        # 只返回实际存在的文档数量
        assert len(results) == 3

    def test_update_nonexistent_document(self):
        """测试更新不存在的文档"""
        store = FaissVectorStore(dimension=64)

        doc = Document(
            id="nonexistent",
            content="test",
            embedding=np.random.rand(64).astype(np.float32)
        )

        count = store.update([doc])
        assert count == 0

    def test_delete_nonexistent_document(self):
        """测试删除不存在的文档"""
        store = FaissVectorStore(dimension=64)

        count = store.delete(["nonexistent"])
        assert count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
