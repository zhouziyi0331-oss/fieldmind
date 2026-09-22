"""
测试向量存储抽象接口

验证基础数据类和接口定义的正确性
"""

import pytest
import numpy as np
from app.vector_store import Document, SearchResult, DistanceMetric, IndexType, VectorStore


class TestDocument:
    """测试 Document 数据类"""

    def test_create_valid_document(self):
        """测试创建有效文档"""
        embedding = np.array([0.1, 0.2, 0.3])
        doc = Document(
            id="doc1",
            content="test content",
            embedding=embedding,
            metadata={"source": "test"}
        )

        assert doc.id == "doc1"
        assert doc.content == "test content"
        assert np.array_equal(doc.embedding, embedding)
        assert doc.metadata["source"] == "test"

    def test_document_empty_id(self):
        """测试空ID应该抛出异常"""
        with pytest.raises(ValueError, match="id cannot be empty"):
            Document(
                id="",
                content="test",
                embedding=np.array([0.1, 0.2])
            )

    def test_document_invalid_embedding_type(self):
        """测试非numpy数组的embedding应该抛出异常"""
        with pytest.raises(TypeError, match="must be a numpy array"):
            Document(
                id="doc1",
                content="test",
                embedding=[0.1, 0.2]  # 应该是numpy数组
            )

    def test_document_multi_dimensional_embedding(self):
        """测试多维embedding应该抛出异常"""
        with pytest.raises(ValueError, match="must be 1-dimensional"):
            Document(
                id="doc1",
                content="test",
                embedding=np.array([[0.1, 0.2], [0.3, 0.4]])
            )

    def test_document_default_metadata(self):
        """测试默认空元数据"""
        doc = Document(
            id="doc1",
            content="test",
            embedding=np.array([0.1])
        )
        assert doc.metadata == {}


class TestSearchResult:
    """测试 SearchResult 数据类"""

    def test_create_search_result(self):
        """测试创建搜索结果"""
        doc = Document(
            id="doc1",
            content="test",
            embedding=np.array([0.1, 0.2])
        )
        result = SearchResult(
            document=doc,
            score=0.95,
            distance=0.05,
            rank=0
        )

        assert result.document == doc
        assert result.score == 0.95
        assert result.distance == 0.05
        assert result.rank == 0


class TestDistanceMetric:
    """测试距离度量枚举"""

    def test_metric_values(self):
        """测试所有度量类型的值"""
        assert DistanceMetric.COSINE.value == "cosine"
        assert DistanceMetric.EUCLIDEAN.value == "euclidean"
        assert DistanceMetric.DOT_PRODUCT.value == "dot_product"
        assert DistanceMetric.L2.value == "l2"


class TestIndexType:
    """测试索引类型枚举"""

    def test_index_values(self):
        """测试所有索引类型的值"""
        assert IndexType.FLAT.value == "flat"
        assert IndexType.IVF.value == "ivf"
        assert IndexType.HNSW.value == "hnsw"
        assert IndexType.LSH.value == "lsh"


class MockVectorStore(VectorStore):
    """用于测试的Mock实现"""

    def __init__(self, dimension: int):
        super().__init__(dimension)
        self._storage = {}

    def add(self, documents):
        for doc in documents:
            self._storage[doc.id] = doc
        return [doc.id for doc in documents]

    def search(self, query_embedding, top_k=10, filters=None):
        # 简单的线性搜索实现
        results = []
        for doc in self._storage.values():
            score = float(np.dot(query_embedding, doc.embedding))
            results.append(SearchResult(doc, score, 1-score, 0))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, doc_ids):
        count = 0
        for doc_id in doc_ids:
            if doc_id in self._storage:
                del self._storage[doc_id]
                count += 1
        return count

    def update(self, documents):
        count = 0
        for doc in documents:
            if doc.id in self._storage:
                self._storage[doc.id] = doc
                count += 1
        return count

    def get(self, doc_ids):
        return [self._storage.get(doc_id) for doc_id in doc_ids]

    def count(self):
        return len(self._storage)

    def clear(self):
        self._storage.clear()


class TestVectorStoreInterface:
    """测试 VectorStore 抽象接口"""

    @pytest.fixture
    def store(self):
        """创建测试用的向量存储实例"""
        return MockVectorStore(dimension=128)

    @pytest.fixture
    def sample_documents(self):
        """创建示例文档"""
        docs = []
        for i in range(5):
            embedding = np.random.rand(128).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"content {i}",
                embedding=embedding,
                metadata={"index": i}
            )
            docs.append(doc)
        return docs

    def test_add_documents(self, store, sample_documents):
        """测试添加文档"""
        ids = store.add(sample_documents)
        assert len(ids) == 5
        assert store.count() == 5

    def test_search(self, store, sample_documents):
        """测试搜索"""
        store.add(sample_documents)
        query = np.random.rand(128).astype(np.float32)
        results = store.search(query, top_k=3)

        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)

    def test_delete(self, store, sample_documents):
        """测试删除"""
        store.add(sample_documents)
        deleted = store.delete(["doc0", "doc1"])

        assert deleted == 2
        assert store.count() == 3

    def test_update(self, store, sample_documents):
        """测试更新"""
        store.add(sample_documents)

        # 更新第一个文档
        updated_doc = Document(
            id="doc0",
            content="updated content",
            embedding=sample_documents[0].embedding,
            metadata={"updated": True}
        )
        count = store.update([updated_doc])

        assert count == 1
        retrieved = store.get(["doc0"])[0]
        assert retrieved.content == "updated content"

    def test_get(self, store, sample_documents):
        """测试获取文档"""
        store.add(sample_documents)
        docs = store.get(["doc0", "doc2", "nonexistent"])

        assert len(docs) == 3
        assert docs[0].id == "doc0"
        assert docs[1].id == "doc2"
        assert docs[2] is None

    def test_exists(self, store, sample_documents):
        """测试文档存在性检查"""
        store.add(sample_documents)

        assert store.exists("doc0") is True
        assert store.exists("nonexistent") is False

    def test_clear(self, store, sample_documents):
        """测试清空"""
        store.add(sample_documents)
        store.clear()

        assert store.count() == 0

    def test_validate_embedding(self, store):
        """测试向量维度验证"""
        valid = np.random.rand(128)
        invalid = np.random.rand(64)

        store.validate_embedding(valid)  # 不应抛出异常

        with pytest.raises(ValueError, match="dimension mismatch"):
            store.validate_embedding(invalid)

    def test_len(self, store, sample_documents):
        """测试 len() 操作"""
        store.add(sample_documents)
        assert len(store) == 5

    def test_repr(self, store):
        """测试字符串表示"""
        repr_str = repr(store)
        assert "MockVectorStore" in repr_str
        assert "dimension=128" in repr_str

    def test_get_stats(self, store, sample_documents):
        """测试统计信息"""
        store.add(sample_documents)
        stats = store.get_stats()

        assert stats["count"] == 5
        assert stats["dimension"] == 128
        assert "distance_metric" in stats
        assert "index_type" in stats

    def test_batch_search(self, store, sample_documents):
        """测试批量搜索"""
        store.add(sample_documents)
        queries = [np.random.rand(128).astype(np.float32) for _ in range(3)]
        results = store.batch_search(queries, top_k=2)

        assert len(results) == 3
        assert all(len(r) == 2 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
