"""向量化服务 - 封装ChromaDB操作"""
from typing import List, Dict, Any, Optional
import logging

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

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class VectorizationService:
    """向量化服务"""

    def __init__(self):
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # 文档集合
        self.collection = self.chroma_client.get_or_create_collection(
            name="fieldmind_documents",
            metadata={"description": "FieldMind文档向量存储"}
        )

        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

    def vectorize_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        向量化单个文档

        Args:
            document_id: 文档ID
            text: 文档文本
            metadata: 文档元数据

        Returns:
            向量化结果
        """
        logger.info(f"开始向量化文档: {document_id}")

        # 1. 分割文本
        chunks = self.text_splitter.split_text(text)
        logger.info(f"文档分块: {len(chunks)} 个chunk")

        if not chunks:
            return {
                'document_id': document_id,
                'chunk_count': 0,
                'status': 'empty'
            }

        # 2. 准备元数据
        base_metadata = metadata or {}

        # 3. 向量化并存储
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_metadata = {
                **base_metadata,
                "document_id": document_id,
                "chunk_index": i,
                "chunk_total": len(chunks),
                "text_length": len(chunk)
            }

            # 使用upsert避免重复ID警告（如果chunk_id已存在则更新，否则插入）
            self.collection.upsert(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[chunk_metadata]
            )

            chunk_ids.append(chunk_id)

        logger.info(f"向量化完成: {len(chunk_ids)} 个chunk")

        return {
            'document_id': document_id,
            'chunk_count': len(chunk_ids),
            'chunk_ids': chunk_ids,
            'status': 'success'
        }

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
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
        logger.info(f"执行语义搜索: {query[:50]}...")

        # 查询ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_dict
        )

        # 格式化结果
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                result = {
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "relevance_score": 1 - results["distances"][0][i] if results.get("distances") else 1.0
                }
                search_results.append(result)

        logger.info(f"找到 {len(search_results)} 个相关结果")
        return search_results

    def search_by_document(
        self,
        document_ids: List[str],
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定文档中搜索

        Args:
            document_ids: 文档ID列表
            query: 查询文本
            top_k: 每个文档返回的结果数量

        Returns:
            搜索结果
        """
        results = []

        for doc_id in document_ids:
            doc_results = self.search_similar(
                query=query,
                top_k=top_k,
                filter_dict={"document_id": doc_id}
            )
            results.extend(doc_results)

        # 按相关性排序
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return results[:top_k * len(document_ids)]

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID

        Returns:
            删除结果
        """
        logger.info(f"删除文档向量: {document_id}")

        # 查找该文档的所有chunk
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"已删除 {len(results['ids'])} 个chunk")

            return {
                'document_id': document_id,
                'deleted_count': len(results['ids']),
                'status': 'success'
            }
        else:
            return {
                'document_id': document_id,
                'deleted_count': 0,
                'status': 'not_found'
            }

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        获取文档的所有chunk

        Args:
            document_id: 文档ID

        Returns:
            Chunk列表
        """
        results = self.collection.get(
            where={"document_id": document_id}
        )

        chunks = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                chunks.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })

        return chunks

    def update_document_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新文档元数据

        Args:
            document_id: 文档ID
            metadata: 新的元数据

        Returns:
            更新结果
        """
        # 获取所有chunk
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if not results["ids"]:
            return {
                'document_id': document_id,
                'status': 'not_found'
            }

        # 更新每个chunk的元数据
        for i, chunk_id in enumerate(results["ids"]):
            old_metadata = results["metadatas"][i]
            new_metadata = {**old_metadata, **metadata}

            self.collection.update(
                ids=[chunk_id],
                metadatas=[new_metadata]
            )

        logger.info(f"更新了 {len(results['ids'])} 个chunk的元数据")

        return {
            'document_id': document_id,
            'updated_count': len(results['ids']),
            'status': 'success'
        }


# 全局实例 - 延迟初始化以避免测试环境中的网络依赖
try:
    vectorization_service = VectorizationService()
except Exception as e:
    logger.warning(f"向量化服务初始化失败（可能在测试环境中）: {e}")
    vectorization_service = None
