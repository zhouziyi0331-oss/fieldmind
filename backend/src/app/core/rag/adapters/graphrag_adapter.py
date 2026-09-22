"""
GraphRAG适配器

适配graphrag_service.py到统一RAG接口
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio

from app.core.rag.base_interface import (
    BaseRAGInterface, RAGQuery, RAGResult, RAGMode,
    RAGIngestionError, RAGQueryError
)

logger = logging.getLogger(__name__)


class GraphRAGAdapter(BaseRAGInterface):
    """GraphRAG多尺度知识图谱适配器"""

    provider_name = "graphrag"
    provider_version = "1.0.0"
    supported_modes = [
        RAGMode.LOCAL,
        RAGMode.GLOBAL,
        RAGMode.HYBRID
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._graphrag_service = None

    async def initialize(self) -> bool:
        """初始化GraphRAG服务"""
        try:
            from app.services.graphrag_service import get_graphrag_service

            self._graphrag_service = get_graphrag_service()
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
        执行多尺度知识图谱检索

        Args:
            rag_query: RAG查询请求

        Returns:
            检索结果列表
        """
        if not self._initialized or not self._graphrag_service:
            raise RAGQueryError(f"{self.provider_name} 未初始化")

        try:
            logger.debug(
                f"🔍 {self.provider_name} 检索: "
                f"query='{rag_query.query[:50]}...', "
                f"mode={rag_query.mode.value}"
            )

            rag_results = []

            # 根据模式执行不同的检索
            if rag_query.mode == RAGMode.LOCAL:
                # 局部搜索
                result = await self._graphrag_service.local_search(
                    query=rag_query.query,
                    project_id=rag_query.project_id,
                    community_level=2
                )

                if result.get('status') == 'success':
                    rag_results.append(RAGResult(
                        content=result.get('response', ''),
                        score=0.88,
                        source=self.provider_name,
                        metadata={
                            'search_type': 'local',
                            'community_level': 2,
                            **result.get('metadata', {})
                        }
                    ))

            elif rag_query.mode == RAGMode.GLOBAL:
                # 全局搜索
                result = await self._graphrag_service.global_search(
                    query=rag_query.query,
                    project_id=rag_query.project_id,
                    community_level=2
                )

                if result.get('status') == 'success':
                    rag_results.append(RAGResult(
                        content=result.get('response', ''),
                        score=0.88,
                        source=self.provider_name,
                        metadata={
                            'search_type': 'global',
                            'community_level': 2,
                            **result.get('metadata', {})
                        }
                    ))

            else:  # HYBRID或默认
                # 同时执行局部和全局搜索
                local_task = self._graphrag_service.local_search(
                    query=rag_query.query,
                    project_id=rag_query.project_id,
                    community_level=2
                )

                global_task = self._graphrag_service.global_search(
                    query=rag_query.query,
                    project_id=rag_query.project_id,
                    community_level=2
                )

                local_result, global_result = await asyncio.gather(
                    local_task, global_task,
                    return_exceptions=True
                )

                # 处理局部结果
                if not isinstance(local_result, Exception) and local_result.get('status') == 'success':
                    rag_results.append(RAGResult(
                        content=local_result.get('response', ''),
                        score=0.88,
                        source=self.provider_name,
                        metadata={
                            'search_type': 'local',
                            'community_level': 2
                        }
                    ))

                # 处理全局结果
                if not isinstance(global_result, Exception) and global_result.get('status') == 'success':
                    rag_results.append(RAGResult(
                        content=global_result.get('response', ''),
                        score=0.87,  # 全局稍低一点
                        source=self.provider_name,
                        metadata={
                            'search_type': 'global',
                            'community_level': 2
                        }
                    ))

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
        插入文档到GraphRAG（如果支持）

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据

        Returns:
            是否成功
        """
        if not self._initialized or not self._graphrag_service:
            raise RAGIngestionError(f"{self.provider_name} 未初始化")

        try:
            logger.debug(
                f"📝 {self.provider_name} 索引文档: "
                f"id={document_id}, length={len(content)}"
            )

            # 检查GraphRAG服务是否有insert方法
            if hasattr(self._graphrag_service, 'insert_document'):
                success = await self._graphrag_service.insert_document(
                    content=content,
                    document_id=document_id,
                    project_id=project_id,
                    metadata=metadata
                )

                if success:
                    logger.debug(f"✅ {self.provider_name} 文档索引成功")
                else:
                    logger.warning(f"⚠️ {self.provider_name} 文档索引失败")

                return success
            else:
                logger.warning(
                    f"⚠️ {self.provider_name} 不支持直接插入文档，"
                    f"需要通过GraphRAG的索引管道处理"
                )
                return False

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 索引失败: {e}")
            raise RAGIngestionError(f"索引失败: {str(e)}")

    async def delete(
        self,
        document_id: str,
        project_id: Optional[str] = None
    ) -> bool:
        """
        删除文档（GraphRAG可能不支持删除，返回False）

        Args:
            document_id: 文档ID
            project_id: 项目ID

        Returns:
            是否成功
        """
        logger.warning(
            f"⚠️ {self.provider_name} 不支持文档删除: "
            f"document_id={document_id}"
        )
        return False

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = await super().health_check()

        if self._graphrag_service:
            health['service_available'] = True
            health['supported_modes'] = [m.value for m in self.supported_modes]

            # 检查服务健康状态
            try:
                service_health = self._graphrag_service.health_check()
                health['service_health'] = service_health
            except:
                health['service_health'] = {'available': False}
        else:
            health['service_available'] = False

        return health


# 工厂函数
async def create_graphrag_adapter(
    config: Optional[Dict[str, Any]] = None
) -> GraphRAGAdapter:
    """
    创建并初始化GraphRAG适配器

    Args:
        config: 配置

    Returns:
        初始化后的适配器
    """
    adapter = GraphRAGAdapter(config)
    await adapter.initialize()
    return adapter
