"""
RAG 服务测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np
from app.services.rag import (
    Document,
    VectorStore,
    EmbeddingService,
    RAGService,
    ChunkingService
)


class TestVectorStore:
    """测试向量存储"""

    def test_add_document(self):
        """测试添加文档"""
        store = VectorStore(embedding_dim=768)

        doc = Document(
            doc_id="doc1",
            content="This is a test document"
        )
        embedding = np.random.randn(768)

        store.add_document(doc, embedding)
        assert len(store.documents) == 1
        assert "doc1" in store.documents

    def test_remove_document(self):
        """测试删除文档"""
        store = VectorStore(embedding_dim=768)

        doc = Document(doc_id="doc1", content="Test")
        embedding = np.random.randn(768)
        store.add_document(doc, embedding)

        success = store.remove_document("doc1")
        assert success == True
        assert len(store.documents) == 0

    def test_search(self):
        """测试搜索"""
        store = VectorStore(embedding_dim=768)

        # 添加多个文档
        for i in range(5):
            doc = Document(
                doc_id=f"doc{i}",
                content=f"Document {i}"
            )
            embedding = np.random.randn(768)
            store.add_document(doc, embedding)

        # 搜索
        query_embedding = np.random.randn(768)
        results = store.search(query_embedding, top_k=3)

        assert len(results) == 3
        assert results[0].rank == 1
        assert results[1].rank == 2

    def test_search_with_filter(self):
        """测试带过滤的搜索"""
        store = VectorStore(embedding_dim=768)

        # 添加文档
        doc1 = Document(
            doc_id="doc1",
            content="Python programming",
            metadata={"category": "programming"}
        )
        doc2 = Document(
            doc_id="doc2",
            content="JavaScript tutorial",
            metadata={"category": "programming"}
        )
        doc3 = Document(
            doc_id="doc3",
            content="Cooking recipe",
            metadata={"category": "cooking"}
        )

        for doc in [doc1, doc2, doc3]:
            embedding = np.random.randn(768)
            store.add_document(doc, embedding)

        # 搜索（过滤）
        query_embedding = np.random.randn(768)
        results = store.search(
            query_embedding,
            top_k=10,
            filter_metadata={"category": "programming"}
        )

        assert len(results) == 2

    def test_statistics(self):
        """测试统计信息"""
        store = VectorStore(embedding_dim=768)

        for i in range(3):
            doc = Document(doc_id=f"doc{i}", content=f"Doc {i}")
            embedding = np.random.randn(768)
            store.add_document(doc, embedding)

        stats = store.get_statistics()
        assert stats["total_documents"] == 3
        assert stats["embedding_dim"] == 768


class TestEmbeddingService:
    """测试嵌入服务"""

    async def test_embed_text(self):
        """测试文本嵌入"""
        service = EmbeddingService()

        embedding = await service.embed_text("This is a test")

        assert embedding.shape == (768,)
        assert np.linalg.norm(embedding) > 0

    async def test_embed_batch(self):
        """测试批量嵌入"""
        service = EmbeddingService()

        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = await service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(e.shape == (768,) for e in embeddings)

    async def test_consistency(self):
        """测试嵌入一致性"""
        service = EmbeddingService()

        text = "Consistent text"
        emb1 = await service.embed_text(text)
        emb2 = await service.embed_text(text)

        # 相同文本应该产生相同嵌入
        assert np.allclose(emb1, emb2)


class TestRAGService:
    """测试 RAG 服务"""

    async def test_index_document(self):
        """测试索引文档"""
        store = VectorStore(embedding_dim=768)
        embedding_service = EmbeddingService()
        rag = RAGService(store, embedding_service)

        doc = await rag.index_document(
            doc_id="doc1",
            content="This is a test document",
            metadata={"type": "test"}
        )

        assert doc.doc_id == "doc1"
        assert len(store.documents) == 1

    async def test_index_documents(self):
        """测试批量索引"""
        store = VectorStore(embedding_dim=768)
        embedding_service = EmbeddingService()
        rag = RAGService(store, embedding_service)

        documents = [
            {"doc_id": "doc1", "content": "Document 1"},
            {"doc_id": "doc2", "content": "Document 2"},
            {"doc_id": "doc3", "content": "Document 3"}
        ]

        indexed = await rag.index_documents(documents)

        assert len(indexed) == 3
        assert len(store.documents) == 3

    async def test_search(self):
        """测试搜索"""
        store = VectorStore(embedding_dim=768)
        embedding_service = EmbeddingService()
        rag = RAGService(store, embedding_service)

        # 索引文档
        await rag.index_document("doc1", "Python programming language")
        await rag.index_document("doc2", "JavaScript web development")
        await rag.index_document("doc3", "Machine learning algorithms")

        # 搜索
        results = await rag.search("programming", top_k=2)

        assert len(results) <= 2
        assert all(r.score >= -1 and r.score <= 1 for r in results)

    async def test_generate_with_context(self):
        """测试检索增强生成"""
        store = VectorStore(embedding_dim=768)
        embedding_service = EmbeddingService()
        rag = RAGService(store, embedding_service)

        # 索引文档
        await rag.index_document(
            "doc1",
            "Python is a high-level programming language"
        )
        await rag.index_document(
            "doc2",
            "Python supports multiple programming paradigms"
        )

        # 生成
        result = await rag.generate_with_context(
            query="What is Python?",
            top_k=2
        )

        assert "query" in result
        assert "answer" in result
        assert "sources" in result
        assert len(result["sources"]) > 0

    async def test_delete_document(self):
        """测试删除文档"""
        store = VectorStore(embedding_dim=768)
        embedding_service = EmbeddingService()
        rag = RAGService(store, embedding_service)

        await rag.index_document("doc1", "Test document")

        success = await rag.delete_document("doc1")
        assert success == True
        assert len(store.documents) == 0


class TestChunkingService:
    """测试分块服务"""

    def test_chunk_by_tokens(self):
        """测试按 token 分块"""
        text = " ".join([f"word{i}" for i in range(100)])

        chunks = ChunkingService.chunk_by_tokens(text, max_tokens=20, overlap=5)

        assert len(chunks) > 1
        assert all(len(chunk.split()) <= 20 for chunk in chunks)

    def test_chunk_by_paragraphs(self):
        """测试按段落分块"""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"

        chunks = ChunkingService.chunk_by_paragraphs(text)

        assert len(chunks) == 3
        assert chunks[0] == "Paragraph 1"

    def test_chunk_by_sentences(self):
        """测试按句子分块"""
        text = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5."

        chunks = ChunkingService.chunk_by_sentences(text, sentences_per_chunk=2)

        assert len(chunks) == 3


async def test_integration_rag_pipeline():
    """集成测试：完整 RAG 流程"""
    # 创建服务
    store = VectorStore(embedding_dim=768)
    embedding_service = EmbeddingService()
    rag = RAGService(store, embedding_service)

    # 准备文档
    documents = [
        {
            "doc_id": "py_intro",
            "content": "Python is a versatile programming language known for its simplicity and readability.",
            "metadata": {"topic": "python", "type": "intro"}
        },
        {
            "doc_id": "py_features",
            "content": "Python supports object-oriented, functional, and procedural programming paradigms.",
            "metadata": {"topic": "python", "type": "features"}
        },
        {
            "doc_id": "js_intro",
            "content": "JavaScript is the programming language of the web, running in browsers.",
            "metadata": {"topic": "javascript", "type": "intro"}
        }
    ]

    # 索引文档
    await rag.index_documents(documents)
    assert len(store.documents) == 3

    # 搜索
    results = await rag.search("Python programming", top_k=2)
    assert len(results) == 2

    # 带过滤的搜索
    filtered_results = await rag.search(
        "programming language",
        top_k=10,
        filter_metadata={"topic": "python"}
    )
    assert len(filtered_results) == 2

    # 生成回答
    answer = await rag.generate_with_context(
        query="What is Python?",
        top_k=2
    )
    assert answer["context_used"] == True
    assert len(answer["sources"]) > 0


def run_async_test(coro):
    """运行异步测试"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running RAG service tests...")

    print("\n=== Testing VectorStore ===")
    test_store = TestVectorStore()
    test_store.test_add_document()
    test_store.test_remove_document()
    test_store.test_search()
    test_store.test_search_with_filter()
    test_store.test_statistics()
    print("✓ VectorStore tests passed")

    print("\n=== Testing EmbeddingService ===")
    test_embedding = TestEmbeddingService()
    run_async_test(test_embedding.test_embed_text())
    run_async_test(test_embedding.test_embed_batch())
    run_async_test(test_embedding.test_consistency())
    print("✓ EmbeddingService tests passed")

    print("\n=== Testing RAGService ===")
    test_rag = TestRAGService()
    run_async_test(test_rag.test_index_document())
    run_async_test(test_rag.test_index_documents())
    run_async_test(test_rag.test_search())
    run_async_test(test_rag.test_generate_with_context())
    run_async_test(test_rag.test_delete_document())
    print("✓ RAGService tests passed")

    print("\n=== Testing ChunkingService ===")
    test_chunking = TestChunkingService()
    test_chunking.test_chunk_by_tokens()
    test_chunking.test_chunk_by_paragraphs()
    test_chunking.test_chunk_by_sentences()
    print("✓ ChunkingService tests passed")

    print("\n=== Running Integration Tests ===")
    run_async_test(test_integration_rag_pipeline())
    print("✓ Integration tests passed")

    print("\n✅ All RAG service tests passed successfully!")
