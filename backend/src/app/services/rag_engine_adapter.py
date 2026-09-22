"""
RAG Engine 适配器

将 RAGRetrievalService 与现有的 rag_engine 连接
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RAGEngineAdapter:
    """RAG Engine 适配器 - 兼容向量存储接口"""
    def __init__(self, rag_engine, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化适配器

        Args:
            rag_engine: 现有的 RAGEngine 实例
        """
        self.rag_engine = rag_engine
        self.embedding_dim = getattr(rag_engine, 'embedding_dim', 768)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        collection: str = "documents"
    ) -> List[Dict[str, Any]]:
        """
        向量检索（适配 RAGRetrievalService 接口）

        Args:
            query: 查询文本
            top_k: 返回数量
            filter: 过滤条件
            collection: 集合名称

        Returns:
            检索结果列表: [{"id": "", "text": "", "score": 0.0, "metadata": {}}]
        """
        try:
            # 检查 ChromaDB 是否可用
            if not self.rag_engine.chroma_enabled:
                logger.warning("ChromaDB 未启用，返回空结果")
                return []

            # 生成查询向量
            query_vector = self.rag_engine.embeddings.embed_query(query)

            # 使用 ChromaDB 查询
            results = self.rag_engine.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=filter  # ChromaDB 的过滤语法
            )

            # 转换为标准格式
            formatted_results = []

            if results and results['ids']:
                ids = results['ids'][0]
                documents = results['documents'][0]
                distances = results['distances'][0]
                metadatas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(ids)

                for i in range(len(ids)):
                    # 将距离转换为相似度分数（距离越小，分数越高）
                    # ChromaDB 使用 L2 距离，转换为 0-1 的分数
                    score = 1.0 / (1.0 + distances[i])

                    formatted_results.append({
                        "id": ids[i],
                        "text": documents[i],
                        "score": score,
                        "metadata": metadatas[i]
                    })

            logger.info(f"   向量检索返回 {len(formatted_results)} 个结果")

            return formatted_results

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> bool:
        """添加文档到向量存储"""
        try:
            if not self.rag_engine.chroma_enabled:
                logger.warning("ChromaDB 未启用")
                return False

            # 生成向量
            embeddings = self.rag_engine.embeddings.embed_documents(texts)

            # 生成 ID
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]

            # 添加到 ChromaDB
            self.rag_engine.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas or [{}] * len(texts)
            )

            logger.info(f"✅ 添加 {len(texts)} 个文档到向量存储")

            return True

        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            return False


def create_rag_adapter():
    """创建 RAG Engine 适配器"""
    from app.core.rag_engine import rag_engine

    return RAGEngineAdapter(rag_engine)
