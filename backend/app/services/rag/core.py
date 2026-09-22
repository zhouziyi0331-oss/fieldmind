"""
RAG (Retrieval-Augmented Generation) 增强服务

提供检索增强生成的完整实现
"""
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    rank: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "rank": self.rank
        }


class VectorStore:
    """
    向量存储

    管理文档嵌入和向量搜索
    """

    def __init__(self, embedding_dim: int = 768):
        """
        初始化向量存储

        Args:
            embedding_dim: 嵌入维度
        """
        self.embedding_dim = embedding_dim
        self.documents: Dict[str, Document] = {}
        self.embeddings: List[np.ndarray] = []
        self.doc_ids: List[str] = []

    def add_document(self, document: Document, embedding: np.ndarray):
        """
        添加文档

        Args:
            document: 文档
            embedding: 嵌入向量
        """
        if embedding.shape[0] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embedding.shape[0]}")

        self.documents[document.doc_id] = document
        self.embeddings.append(embedding)
        self.doc_ids.append(document.doc_id)

        logger.info(f"Added document {document.doc_id} to vector store")

    def remove_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档 ID

        Returns:
            是否成功
        """
        if doc_id not in self.documents:
            return False

        # 找到索引
        index = self.doc_ids.index(doc_id)

        # 删除
        del self.documents[doc_id]
        del self.embeddings[index]
        del self.doc_ids[index]

        logger.info(f"Removed document {doc_id} from vector store")
        return True

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索相似文档

        Args:
            query_embedding: 查询嵌入
            top_k: 返回数量
            filter_metadata: 元数据过滤

        Returns:
            搜索结果列表
        """
        if len(self.embeddings) == 0:
            return []

        # 计算余弦相似度
        embeddings_array = np.array(self.embeddings)
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)

        similarities = np.dot(embeddings_norm, query_norm)

        # 应用元数据过滤
        if filter_metadata:
            valid_indices = []
            for i, doc_id in enumerate(self.doc_ids):
                doc = self.documents[doc_id]
                if all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    valid_indices.append(i)

            if not valid_indices:
                return []

            similarities = similarities[valid_indices]
            filtered_doc_ids = [self.doc_ids[i] for i in valid_indices]
        else:
            filtered_doc_ids = self.doc_ids

        # 获取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            doc_id = filtered_doc_ids[idx]
            document = self.documents[doc_id]
            score = float(similarities[idx])

            results.append(SearchResult(
                document=document,
                score=score,
                rank=rank
            ))

        return results

    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "embedding_dim": self.embedding_dim
        }


class EmbeddingService:
    """
    嵌入服务

    生成文本嵌入向量
    """

    def __init__(self, model_name: str = "sentence-transformers"):
        """
        初始化嵌入服务

        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.embedding_dim = 768  # 默认维度

    async def embed_text(self, text: str) -> np.ndarray:
        """
        生成文本嵌入

        Args:
            text: 文本

        Returns:
            嵌入向量
        """
        # 简单的模拟实现
        # 实际应该使用真实的嵌入模型（如 sentence-transformers）
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        seed = int.from_bytes(hash_obj.digest()[:4], 'big')
        np.random.seed(seed)
        embedding = np.random.randn(self.embedding_dim)
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量生成嵌入

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        return [await self.embed_text(text) for text in texts]


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) 服务

    结合检索和生成的完整流程
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        """
        初始化 RAG 服务

        Args:
            vector_store: 向量存储
            embedding_service: 嵌入服务
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        索引文档

        Args:
            doc_id: 文档 ID
            content: 文档内容
            metadata: 元数据

        Returns:
            文档对象
        """
        # 生成嵌入
        embedding = await self.embedding_service.embed_text(content)

        # 创建文档
        document = Document(
            doc_id=doc_id,
            content=content,
            metadata=metadata or {},
            embedding=embedding
        )

        # 添加到向量存储
        self.vector_store.add_document(document, embedding)

        logger.info(f"Indexed document {doc_id}")
        return document

    async def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Document]:
        """
        批量索引文档

        Args:
            documents: 文档列表 (dict with doc_id, content, metadata)

        Returns:
            文档对象列表
        """
        indexed_docs = []
        for doc_data in documents:
            doc = await self.index_document(
                doc_id=doc_data["doc_id"],
                content=doc_data["content"],
                metadata=doc_data.get("metadata")
            )
            indexed_docs.append(doc)

        return indexed_docs

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_metadata: 元数据过滤

        Returns:
            搜索结果列表
        """
        # 生成查询嵌入
        query_embedding = await self.embedding_service.embed_text(query)

        # 搜索
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        return results

    async def generate_with_context(
        self,
        query: str,
        top_k: int = 3,
        llm_provider: str = "openai",
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        检索增强生成

        Args:
            query: 查询
            top_k: 检索文档数
            llm_provider: LLM 提供商
            model: 模型名称

        Returns:
            生成结果
        """
        # 1. 检索相关文档
        search_results = await self.search(query, top_k=top_k)

        if not search_results:
            return {
                "query": query,
                "answer": "No relevant documents found.",
                "sources": [],
                "context_used": False
            }

        # 2. 构建上下文
        context_parts = []
        sources = []

        for result in search_results:
            context_parts.append(f"[Document {result.rank}]\n{result.document.content}")
            sources.append({
                "doc_id": result.document.doc_id,
                "score": result.score,
                "content": result.document.content[:200] + "..."
            })

        context = "\n\n".join(context_parts)

        # 3. 构建 prompt
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""

        # 4. 调用 LLM (这里是模拟)
        # 实际应该调用真实的 LLM 服务
        answer = f"Based on the provided context, here is the answer to '{query}'. (This is a simulated response. In production, this would be generated by an actual LLM.)"

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "context_used": True,
            "num_sources": len(sources)
        }

    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档 ID

        Returns:
            是否成功
        """
        return self.vector_store.remove_document(doc_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.vector_store.get_statistics()


class ChunkingService:
    """
    文档分块服务

    将长文档分割成合适的块
    """

    @staticmethod
    def chunk_by_tokens(
        text: str,
        max_tokens: int = 512,
        overlap: int = 50
    ) -> List[str]:
        """
        按 token 数分块

        Args:
            text: 文本
            max_tokens: 最大 token 数
            overlap: 重叠 token 数

        Returns:
            文本块列表
        """
        # 简单实现：按单词分块
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word.split())
            if current_length + word_length > max_tokens:
                # 保存当前块
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # 开始新块，包含重叠
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:]
                    current_length = overlap
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(word)
            current_length += word_length

        # 添加最后一块
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @staticmethod
    def chunk_by_paragraphs(text: str) -> List[str]:
        """
        按段落分块

        Args:
            text: 文本

        Returns:
            段落列表
        """
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    @staticmethod
    def chunk_by_sentences(
        text: str,
        sentences_per_chunk: int = 5
    ) -> List[str]:
        """
        按句子分块

        Args:
            text: 文本
            sentences_per_chunk: 每块句子数

        Returns:
            文本块列表
        """
        # 简单的句子分割
        sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|")
        chunks = []

        for i in range(0, len(sentences), sentences_per_chunk):
            chunk = " ".join(sentences[i:i + sentences_per_chunk])
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks
