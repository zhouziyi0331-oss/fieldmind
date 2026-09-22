"""
RAG (Retrieval Augmented Generation) 引擎
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        from langchain.embeddings import HuggingFaceEmbeddings

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.documents import Document
except ImportError:
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import Document
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.services.semantic_embedding import load_embedding_backend
import logging

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG引擎 - 文档检索增强生成"""

    def __init__(self):
        # 初始化嵌入模型（优先使用本机缓存的中文语义模型）
        logger.info("🔄 初始化RAG嵌入模型: 本地中文语义模型 (bge-large-zh-v1.5)")

        self.embedding_backend = load_embedding_backend()
        if self.embedding_backend is None:
            raise RuntimeError("本地语义嵌入模型不可用，请检查 backend/src/models/bge-large-zh-v1.5")

        self.embeddings = self.embedding_backend
        self.embedding_dim = self._probe_embedding_dimension()
        logger.info(
            f"✅ 语义嵌入模型加载完成: {self.embedding_backend.model_name}，维度: {self.embedding_dim}"
        )

        self.chroma_enabled = False
        self.chroma_disabled_reason = None

        # 使用持久化的本地ChromaDB（不依赖服务器）
        try:
            chroma_db_path = Path(settings.chromadb.persist_dir)
            chroma_db_path.mkdir(parents=True, exist_ok=True)

            expected_dim = int(getattr(settings.chromadb, "expected_dimension", 0) or 0)
            enable_indexing = bool(getattr(settings.chromadb, "enable_indexing", False))
            if not enable_indexing:
                self.chroma_disabled_reason = "disabled_by_config"
                logger.info("ℹ️ Chroma索引已按配置关闭，SQLite为主结构化存储")
                self.chroma_client = None
                self.collection = None
            else:
                if expected_dim and self.embedding_dim != expected_dim:
                    logger.warning(
                        f"⚠️ Chroma维度配置与实际模型不一致：实际={self.embedding_dim}, 期望={expected_dim}，继续使用实际维度"
                    )
                self.chroma_client = chromadb.PersistentClient(
                    path=str(chroma_db_path),
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

                # 获取或创建集合
                self.collection = self.chroma_client.get_or_create_collection(
                    name=settings.chromadb.collection_name,
                    metadata={
                        "description": "FieldMind文档向量存储",
                        "embedding_dim": self.embedding_dim,
                    }
                )
                self.chroma_enabled = True
                logger.info(
                    f"✅ ChromaDB已初始化（持久化路径: {chroma_db_path}, 维度: {self.embedding_dim}）"
                )

        except Exception as e:
            logger.error(f"初始化ChromaDB失败: {e}")
            self.chroma_client = None
            self.collection = None
            self.chroma_disabled_reason = str(e)

        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # LLM
        self.llm = self._init_llm()

    def _probe_embedding_dimension(self) -> int:
        return self.embedding_backend.get_sentence_embedding_dimension()

    def _init_llm(self):
        """初始化LLM - 使用 P3 智能路由"""
        try:
            # 尝试使用 P3 LLM 适配器（智能路由 + 成本优化）
            from app.services.llm_adapter import get_llm_adapter

            logger.info("✅ 使用 P3 LLM 适配器（智能路由 + 成本优化）")
            return get_llm_adapter(strategy="cost_optimized")

        except ImportError:
            # 回退到原有方案
            logger.warning("P3 LLM 适配器不可用，使用传统方式")
            if settings.ai.anthropic_api_key:
                return ChatAnthropic(
                    anthropic_api_key=settings.ai.anthropic_api_key,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.7,
                )
            elif settings.ai.openai_api_key:
                return ChatOpenAI(
                    openai_api_key=settings.ai.openai_api_key,
                    model="gpt-4",
                    temperature=0.7,
                )
            else:
                logger.warning("未配置LLM API Key，RAG问答功能将不可用")
                return None

    def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        索引文档到向量数据库

        Args:
            documents: 文档列表，每个文档包含 {id, text, metadata}
            batch_size: 批处理大小

        Returns:
            索引结果统计
        """
        logger.info(f"开始索引 {len(documents)} 个文档")

        if not self.collection or not self.chroma_enabled:
            logger.info("ℹ️ Chroma未启用，跳过向量索引，保留SQLite结构化数据")
            return {
                "documents": len(documents),
                "chunks": 0,
                "status": "skipped",
                "reason": self.chroma_disabled_reason or "not_initialized"
            }

        total_chunks = 0
        for doc in documents:
            # 分割文档
            chunks = self.text_splitter.split_text(doc["text"])

            embeddings = self.embeddings.embed_documents(chunks)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['id']}_chunk_{i}"
                metadata = {
                    **doc.get("metadata", {}),
                    "document_id": doc["id"],
                    "chunk_index": i,
                }

                self.collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[metadata],
                    embeddings=[embeddings[i]],
                )

            total_chunks += len(chunks)

        logger.info(f"索引完成：{len(documents)} 个文档，{total_chunks} 个分块")

        return {
            "documents": len(documents),
            "chunks": total_chunks,
            "status": "success"
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        logger.info(f"执行语义搜索: {query}")

        if not self.collection or not self.chroma_enabled:
            logger.info("ℹ️ Chroma未启用，语义搜索返回空结果")
            return []

        # 查询ChromaDB
        results = self.collection.query(
            query_embeddings=[self.embeddings.embed_query(query)],
            n_results=top_k,
            where=filter_dict
        )

        # 格式化结果
        search_results = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                search_results.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        logger.info(f"找到 {len(search_results)} 个相关结果")
        return search_results

    def query(
        self,
        question: str,
        top_k: int = 5,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        RAG问答

        Args:
            question: 用户问题
            top_k: 检索文档数量
            return_sources: 是否返回来源

        Returns:
            问答结果，包含answer和sources
        """
        if not self.llm:
            return {
                "answer": "LLM未配置，无法回答问题",
                "sources": []
            }

        logger.info(f"RAG问答: {question}")

        # 1. 检索相关文档
        relevant_docs = self.search(question, top_k=top_k)

        # 2. 构建提示词
        context = "\n\n".join([doc["text"] for doc in relevant_docs])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是FieldMind田野调查助手。基于提供的上下文回答用户问题。

上下文信息：
{context}

要求：
1. 仅基于上下文回答，不要编造信息
2. 如果上下文中没有相关信息，明确说明
3. 回答要准确、简洁、有条理
4. 使用中文回答"""),
            ("human", "{question}")
        ])

        # 3. 生成回答
        chain = prompt | self.llm
        response = chain.invoke({
            "context": context,
            "question": question
        })

        answer = response.content if hasattr(response, "content") else str(response)

        # 4. 整理来源
        sources = []
        if return_sources:
            for doc in relevant_docs:
                sources.append({
                    "document_id": doc["metadata"].get("document_id"),
                    "text_snippet": doc["text"][:200] + "...",
                    "metadata": doc["metadata"]
                })

        logger.info("RAG问答完成")

        return {
            "answer": answer,
            "sources": sources,
            "question": question
        }

    def delete_document(self, document_id: str):
        """
        删除文档的所有分块

        Args:
            document_id: 文档ID
        """
        if not self.collection or not self.chroma_enabled:
            return

        # 查找该文档的所有分块
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"已删除文档 {document_id} 的 {len(results['ids'])} 个分块")


# 全局实例 - 延迟初始化以避免测试环境中的网络依赖
try:
    rag_engine = RAGEngine()
except Exception as e:
    logger.warning(f"RAG引擎初始化失败（可能在测试环境中）: {e}")
    rag_engine = None
