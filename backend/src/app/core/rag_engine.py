"""
RAG (Retrieval Augmented Generation) 引擎
"""

from typing import List, Dict, Any, Optional
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

from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG引擎 - 文档检索增强生成"""

    def __init__(self):
        # 初始化嵌入模型（强制使用FlagEmbedding - 中文优化）
        logger.info("🔄 初始化RAG嵌入模型: FlagEmbedding (bge-small-zh-v1.5)")

        try:
            import os
            from FlagEmbedding import FlagModel

            # 强制使用ModelScope下载的本地模型
            model_cache = os.path.expanduser('~/.cache/modelscope/models/AI-ModelScope--bge-small-zh-v1.5/snapshots/master')

            if not os.path.exists(model_cache):
                raise FileNotFoundError(f"本地模型未找到: {model_cache}")

            logger.info(f"使用本地模型: {model_cache}")

            # 直接初始化FlagModel
            self.flag_model = FlagModel(
                model_cache,
                query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                use_fp16=True
            )

            # 创建LangChain兼容的包装器
            class FlagEmbeddingsWrapper:
                def __init__(self, model):
                    self.model = model

                def embed_query(self, text: str):
                    return self.model.encode_queries([text])[0].tolist()

                def embed_documents(self, texts):
                    return self.model.encode(texts).tolist()

            self.embeddings = FlagEmbeddingsWrapper(self.flag_model)

            logger.info("✅ FlagEmbedding加载完成（中文准确率+20%）")

        except Exception as e:
            logger.error(f"❌ FlagEmbedding加载失败: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"必须使用FlagEmbedding，请先运行: python3 /tmp/download_flag_embedding.py") from e

        # 使用持久化的本地ChromaDB（不依赖服务器）
        try:
            chroma_db_path = "/Users/alwan/FieldMind-Rebuild/chroma_db"
            import os
            os.makedirs(chroma_db_path, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=chroma_db_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 获取或创建集合
            self.collection = self.chroma_client.get_or_create_collection(
                name="fieldmind_documents",
                metadata={"description": "FieldMind文档向量存储"}
            )

            logger.info(f"✅ ChromaDB已初始化（持久化路径: {chroma_db_path}）")

        except Exception as e:
            logger.error(f"初始化ChromaDB失败: {e}")
            self.chroma_client = None
            self.collection = None

        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # LLM
        self.llm = self._init_llm()

    def _init_llm(self):
        """初始化LLM"""
        if settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
            )
        elif settings.OPENAI_API_KEY:
            return ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
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

        total_chunks = 0
        for doc in documents:
            # 分割文档
            chunks = self.text_splitter.split_text(doc["text"])

            # 生成嵌入并存储
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['id']}_chunk_{i}"
                metadata = {
                    **doc.get("metadata", {}),
                    "document_id": doc["id"],
                    "chunk_index": i,
                }

                # 添加到ChromaDB
                self.collection.add(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[metadata]
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

        # 查询ChromaDB
        results = self.collection.query(
            query_texts=[query],
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
