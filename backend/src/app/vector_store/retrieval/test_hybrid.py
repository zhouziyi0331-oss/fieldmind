"""
测试混合检索功能

验证 BM25 和混合检索器
"""

import pytest
import numpy as np

from app.vector_store import Document, DistanceMetric, IndexType
from app.vector_store.backends import FaissVectorStore
from app.vector_store.retrieval import BM25Retriever, HybridRetriever, FusionMethod


class TestBM25Retriever:
    """测试 BM25 检索器"""

    @pytest.fixture
    def retriever(self):
        """创建 BM25 检索器"""
        return BM25Retriever(k1=1.5, b=0.75, language="zh")

    @pytest.fixture
    def sample_docs(self):
        """创建示例文档"""
        docs = [
            ("doc1", "机器学习是人工智能的一个分支"),
            ("doc2", "深度学习是机器学习的一种方法"),
            ("doc3", "神经网络是深度学习的基础"),
            ("doc4", "自然语言处理用于理解人类语言"),
            ("doc5", "计算机视觉用于图像识别"),
        ]
        return docs

    def test_create_retriever(self):
        """测试创建检索器"""
        retriever = BM25Retriever()
        assert retriever.k1 == 1.5
        assert retriever.b == 0.75
        assert len(retriever) == 0

    def test_add_documents(self, retriever, sample_docs):
        """测试添加文档"""
        doc_ids = [doc[0] for doc in sample_docs]
        contents = [doc[1] for doc in sample_docs]

        retriever.add_documents(contents, doc_ids)

        assert len(retriever) == 5
        assert len(retriever.vocab) > 0

    def test_search_basic(self, retriever, sample_docs):
        """测试基本搜索"""
        doc_ids = [doc[0] for doc in sample_docs]
        contents = [doc[1] for doc in sample_docs]
        retriever.add_documents(contents, doc_ids)

        # 搜索"机器学习"
        results = retriever.search("机器学习", top_k=3)

        assert len(results) <= 3
        assert all(isinstance(r, tuple) for r in results)
        assert all(len(r) == 2 for r in results)  # (doc_id, score)

        # 第一个结果应该相关
        assert results[0][0] in ["doc1", "doc2"]

    def test_search_exact_match(self, retriever, sample_docs):
        """测试精确匹配"""
        doc_ids = [doc[0] for doc in sample_docs]
        contents = [doc[1] for doc in sample_docs]
        retriever.add_documents(contents, doc_ids)

        # 搜索"深度学习"
        results = retriever.search("深度学习", top_k=5)

        # doc2 和 doc3 应该排前面
        top_ids = [r[0] for r in results[:2]]
        assert "doc2" in top_ids or "doc3" in top_ids

    def test_empty_query(self, retriever, sample_docs):
        """测试空查询"""
        doc_ids = [doc[0] for doc in sample_docs]
        contents = [doc[1] for doc in sample_docs]
        retriever.add_documents(contents, doc_ids)

        results = retriever.search("", top_k=5)
        assert results == []

    def test_clear(self, retriever, sample_docs):
        """测试清空"""
        doc_ids = [doc[0] for doc in sample_docs]
        contents = [doc[1] for doc in sample_docs]
        retriever.add_documents(contents, doc_ids)

        retriever.clear()

        assert len(retriever) == 0
        assert len(retriever.vocab) == 0


class TestHybridRetriever:
    """测试混合检索器"""

    @pytest.fixture
    def dimension(self):
        return 128

    @pytest.fixture
    def vector_store(self, dimension):
        """创建向量存储"""
        return FaissVectorStore(
            dimension=dimension,
            distance_metric=DistanceMetric.COSINE,
            index_type=IndexType.FLAT
        )

    @pytest.fixture
    def sample_documents(self, dimension):
        """创建示例文档"""
        docs = []
        contents = [
            "机器学习是人工智能的一个分支",
            "深度学习是机器学习的一种方法",
            "神经网络是深度学习的基础",
            "自然语言处理用于理解人类语言",
            "计算机视觉用于图像识别",
        ]

        for i, content in enumerate(contents):
            # 创建随机向量
            embedding = np.random.rand(dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=content,
                embedding=embedding,
                metadata={"index": i}
            )
            docs.append(doc)

        return docs

    def test_create_retriever(self, vector_store):
        """测试创建混合检索器"""
        retriever = HybridRetriever(
            vector_store=vector_store,
            fusion_method=FusionMethod.RRF
        )

        assert retriever.fusion_method == FusionMethod.RRF
        assert retriever.dense_weight > 0
        assert retriever.sparse_weight > 0

    def test_add_documents(self, vector_store, sample_documents):
        """测试添加文档"""
        retriever = HybridRetriever(vector_store=vector_store)
        retriever.add_documents(sample_documents)

        assert vector_store.count() == 5
        assert len(retriever.bm25) == 5

    def test_rrf_fusion(self, vector_store, sample_documents):
        """测试 RRF 融合"""
        retriever = HybridRetriever(
            vector_store=vector_store,
            fusion_method=FusionMethod.RRF
        )
        retriever.add_documents(sample_documents)

        # 使用第一个文档的向量搜索
        query_embedding = sample_documents[0].embedding
        query_text = sample_documents[0].content

        results = retriever.search(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=3
        )

        assert len(results) <= 3
        assert all(hasattr(r, 'document') for r in results)
        assert all(hasattr(r, 'score') for r in results)

    def test_linear_fusion(self, vector_store, sample_documents):
        """测试线性融合"""
        retriever = HybridRetriever(
            vector_store=vector_store,
            fusion_method=FusionMethod.LINEAR,
            dense_weight=0.6,
            sparse_weight=0.4
        )
        retriever.add_documents(sample_documents)

        query_embedding = sample_documents[0].embedding
        query_text = sample_documents[0].content

        results = retriever.search(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=3
        )

        assert len(results) <= 3

    def test_max_fusion(self, vector_store, sample_documents):
        """测试最大值融合"""
        retriever = HybridRetriever(
            vector_store=vector_store,
            fusion_method=FusionMethod.MAX
        )
        retriever.add_documents(sample_documents)

        query_embedding = sample_documents[0].embedding
        query_text = sample_documents[0].content

        results = retriever.search(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=3
        )

        assert len(results) <= 3

    def test_custom_top_k(self, vector_store, sample_documents):
        """测试自定义召回数"""
        retriever = HybridRetriever(vector_store=vector_store)
        retriever.add_documents(sample_documents)

        query_embedding = sample_documents[0].embedding
        query_text = sample_documents[0].content

        results = retriever.search(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=2,
            dense_top_k=5,
            sparse_top_k=5
        )

        assert len(results) <= 2

    def test_clear(self, vector_store, sample_documents):
        """测试清空"""
        retriever = HybridRetriever(vector_store=vector_store)
        retriever.add_documents(sample_documents)

        retriever.clear()

        assert vector_store.count() == 0
        assert len(retriever.bm25) == 0

    def test_get_stats(self, vector_store, sample_documents):
        """测试获取统计信息"""
        retriever = HybridRetriever(vector_store=vector_store)
        retriever.add_documents(sample_documents)

        stats = retriever.get_stats()

        assert "vector_store" in stats
        assert "bm25_docs" in stats
        assert "fusion_method" in stats
        assert stats["bm25_docs"] == 5


class TestBM25English:
    """测试英文 BM25"""

    @pytest.fixture
    def retriever(self):
        return BM25Retriever(language="en")

    @pytest.fixture
    def english_docs(self):
        docs = [
            ("doc1", "Machine learning is a branch of artificial intelligence"),
            ("doc2", "Deep learning is a method of machine learning"),
            ("doc3", "Neural networks are the foundation of deep learning"),
            ("doc4", "Natural language processing is used to understand human language"),
            ("doc5", "Computer vision is used for image recognition"),
        ]
        return docs

    def test_english_search(self, retriever, english_docs):
        """测试英文搜索"""
        doc_ids = [doc[0] for doc in english_docs]
        contents = [doc[1] for doc in english_docs]
        retriever.add_documents(contents, doc_ids)

        results = retriever.search("machine learning", top_k=3)

        assert len(results) > 0
        # doc1 或 doc2 应该排前面
        top_ids = [r[0] for r in results[:2]]
        assert "doc1" in top_ids or "doc2" in top_ids


class TestFusionMethods:
    """测试不同融合方法的对比"""

    @pytest.fixture
    def setup_retriever(self):
        """设置检索器的辅助函数"""
        def _setup(fusion_method):
            dimension = 64
            store = FaissVectorStore(dimension=dimension)
            retriever = HybridRetriever(
                vector_store=store,
                fusion_method=fusion_method
            )

            # 添加文档
            docs = []
            for i in range(10):
                doc = Document(
                    id=f"doc{i}",
                    content=f"这是第{i}个文档的内容",
                    embedding=np.random.rand(dimension).astype(np.float32)
                )
                docs.append(doc)

            retriever.add_documents(docs)
            return retriever, docs

        return _setup

    def test_compare_fusion_methods(self, setup_retriever):
        """对比不同融合方法"""
        methods = [FusionMethod.RRF, FusionMethod.LINEAR, FusionMethod.MAX]
        results_map = {}

        for method in methods:
            retriever, docs = setup_retriever(method)

            query_embedding = docs[0].embedding
            query_text = docs[0].content

            results = retriever.search(
                query_text=query_text,
                query_embedding=query_embedding,
                top_k=5
            )

            results_map[method] = results

        # 验证所有方法都返回结果
        for method, results in results_map.items():
            assert len(results) > 0, f"{method} should return results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
