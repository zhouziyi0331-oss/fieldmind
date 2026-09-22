"""
BaseRAG适配器

适配现有的rag_engine.py到统一RAG接口
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio

from app.core.rag.base_interface import (
    BaseRAGInterface, RAGQuery, RAGResult, RAGMode,
    RAGIngestionError, RAGQueryError
)

logger = logging.getLogger(__name__)


class BaseRAGAdapter(BaseRAGInterface):
    """基础RAG引擎适配器"""

    provider_name = "base_rag"
    provider_version = "1.0.0"
    supported_modes = [RAGMode.VECTOR]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._rag_engine = None

    async def initialize(self) -> bool:
        """初始化BaseRAG引擎"""
        try:
            from app.core.rag_engine import rag_engine

            if rag_engine is None:
                logger.error("❌ RAG引擎未初始化")
                return False

            self._rag_engine = rag_engine
            self._initialized = True

            logger.info(f"✅ {self.provider_name} 初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 初始化失败: {e}")
            return False

    async def query(
        self,
        rag_query: RAGQuery
    ) -> List[RAGResult]:
        """
        执行向量检索

        Args:
            rag_query: RAG查询请求

        Returns:
            检索结果列表
        """
        if not self._initialized or not self._rag_engine:
            raise RAGQueryError(f"{self.provider_name} 未初始化")

        try:
            logger.debug(
                f"🔍 {self.provider_name} 检索: "
                f"query='{rag_query.query[:50]}...', "
                f"top_k={rag_query.top_k}"
            )

            # 调用原始RAG引擎的search方法
            # 需要在同步上下文中运行
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                self._rag_engine.search,
                rag_query.query,
                rag_query.top_k,
                rag_query.filters
            )

            # 转换为统一格式
            rag_results = []
            for idx, result in enumerate(search_results):
                # 计算归一化分数（距离越小越相关）
                distance = result.get('distance', 0)
                # 假设距离在0-2之间，转换为0-1的分数
                score = max(0, 1 - (distance / 2)) if distance else 0.8

                rag_result = RAGResult(
                    content=result.get('text', ''),
                    score=score,
                    source=self.provider_name,
                    metadata=result.get('metadata', {}),
                    document_id=result.get('metadata', {}).get('document_id'),
                    chunk_id=result.get('metadata', {}).get('chunk_id')
                )

                rag_results.append(rag_result)

            logger.debug(
                f"✅ {self.provider_name} 返回 {len(rag_results)} 条结果"
            )

            return rag_results

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 查询失败: {e}")
            raise RAGQueryError(f"查询失败: {str(e)}")

    async def ingest(
        self,
        content: str,
        document_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        插入文档到向量数据库

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据

        Returns:
            是否成功
        """
        if not self._initialized or not self._rag_engine:
            raise RAGIngestionError(f"{self.provider_name} 未初始化")

        try:
            logger.debug(
                f"📝 {self.provider_name} 索引文档: "
                f"id={document_id}, length={len(content)}"
            )

            # 构建文档
            doc = {
                'id': document_id,
                'text': content,
                'metadata': metadata or {}
            }

            # 添加项目ID到元数据
            if project_id:
                doc['metadata']['project_id'] = project_id

            # 调用原始RAG引擎的ingest方法
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._rag_engine.ingest_documents,
                [doc]
            )

            success = result.get('status') == 'success' or result.get('status') == 'skipped'

            if success:
                logger.debug(f"✅ {self.provider_name} 文档索引成功")
            else:
                logger.warning(f"⚠️ {self.provider_name} 文档索引失败")

            return success

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 索引失败: {e}")
            raise RAGIngestionError(f"索引失败: {str(e)}")

    async def delete(
        self,
        document_id: str,
        project_id: Optional[str] = None
    ) -> bool:
        """
        删除文档

        Args:
            document_id: 文档ID
            project_id: 项目ID

        Returns:
            是否成功
        """
        if not self._initialized or not self._rag_engine:
            return False

        try:
            logger.debug(f"🗑️ {self.provider_name} 删除文档: id={document_id}")

            # 调用原始RAG引擎的delete方法
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._rag_engine.delete_document,
                document_id
            )

            logger.debug(f"✅ {self.provider_name} 文档删除成功")
            return True

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 删除失败: {e}")
            return False

    async def query_with_answer(
        self,
        question: str,
        top_k: int = 5,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        RAG问答（保留原有功能）

        Args:
            question: 问题
            top_k: 检索文档数
            return_sources: 是否返回来源

        Returns:
            包含答案和来源的字典
        """
        if not self._initialized or not self._rag_engine:
            return {
                "answer": "RAG引擎未初始化",
                "sources": []
            }

        try:
            logger.debug(f"💬 {self.provider_name} RAG问答: {question[:50]}...")

            # 调用原始RAG引擎的query方法
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._rag_engine.query,
                question,
                top_k,
                return_sources
            )

            logger.debug(f"✅ {self.provider_name} 问答完成")
            return result

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 问答失败: {e}")
            return {
                "answer": f"问答失败: {str(e)}",
                "sources": []
            }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = await super().health_check()

        if self._rag_engine:
            health['chroma_enabled'] = getattr(self._rag_engine, 'chroma_enabled', False)
            health['embedding_dim'] = getattr(self._rag_engine, 'embedding_dim', None)
            health['llm_available'] = self._rag_engine.llm is not None

        return health


# 工厂函数
async def create_base_rag_adapter(
    config: Optional[Dict[str, Any]] = None
) -> BaseRAGAdapter:
    """
    创建并初始化BaseRAG适配器

    Args:
        config: 配置

    Returns:
        初始化后的适配器
    """
    adapter = BaseRAGAdapter(config)
    await adapter.initialize()
    return adapter
