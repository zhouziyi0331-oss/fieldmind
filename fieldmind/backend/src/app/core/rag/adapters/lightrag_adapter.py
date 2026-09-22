"""
LightRAG适配器

适配lightrag_service.py到统一RAG接口
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio

from app.core.rag.base_interface import (
    BaseRAGInterface, RAGQuery, RAGResult, RAGMode,
    RAGIngestionError, RAGQueryError
)

logger = logging.getLogger(__name__)


class LightRAGAdapter(BaseRAGInterface):
    """LightRAG知识图谱适配器"""

    provider_name = "lightrag"
    provider_version = "1.0.0"
    supported_modes = [
        RAGMode.VECTOR,
        RAGMode.KNOWLEDGE_GRAPH,
        RAGMode.LOCAL,
        RAGMode.GLOBAL,
        RAGMode.HYBRID,
        RAGMode.ADAPTIVE
    ]

    # 模式映射
    MODE_MAPPING = {
        RAGMode.VECTOR: "naive",
        RAGMode.KNOWLEDGE_GRAPH: "local",
        RAGMode.LOCAL: "local",
        RAGMode.GLOBAL: "global",
        RAGMode.HYBRID: "hybrid",
        RAGMode.ADAPTIVE: "mix"
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._lightrag_service = None

    async def initialize(self) -> bool:
        """初始化LightRAG服务"""
        try:
            from app.services.lightrag_service import LightRAGService

            self._lightrag_service = LightRAGService()
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
        执行知识图谱检索

        Args:
            rag_query: RAG查询请求

        Returns:
            检索结果列表
        """
        if not self._initialized or not self._lightrag_service:
            raise RAGQueryError(f"{self.provider_name} 未初始化")

        try:
            # 转换模式
            lightrag_mode = self.MODE_MAPPING.get(
                rag_query.mode,
                "hybrid"  # 默认混合模式
            )

            logger.debug(
                f"🔍 {self.provider_name} 检索: "
                f"query='{rag_query.query[:50]}...', "
                f"mode={lightrag_mode}, "
                f"top_k={rag_query.top_k}"
            )

            # 调用LightRAG服务
            result = await self._lightrag_service.query(
                query_text=rag_query.query,
                project_id=rag_query.project_id,
                mode=lightrag_mode,
                only_need_context=True,
                top_k=rag_query.top_k
            )

            # 解析结果
            rag_results = []

            if isinstance(result, str):
                # 简单字符串结果，转换为单个RAGResult
                rag_results.append(RAGResult(
                    content=result,
                    score=0.85,  # LightRAG不返回具体分数，给一个高分
                    source=self.provider_name,
                    metadata={'mode': lightrag_mode}
                ))
            elif isinstance(result, dict):
                # 字典结果，可能包含更多信息
                content = result.get('response') or result.get('context') or str(result)

                rag_results.append(RAGResult(
                    content=content,
                    score=0.85,
                    source=self.provider_name,
                    metadata={
                        'mode': lightrag_mode,
                        **result.get('metadata', {})
                    },
                    entities=result.get('entities'),
                    relations=result.get('relations')
                ))
            elif isinstance(result, list):
                # 列表结果
                for idx, item in enumerate(result[:rag_query.top_k]):
                    if isinstance(item, str):
                        content = item
                        metadata = {'mode': lightrag_mode, 'index': idx}
                    else:
                        content = item.get('content') or item.get('text') or str(item)
                        metadata = {
                            'mode': lightrag_mode,
                            'index': idx,
                            **item.get('metadata', {})
                        }

                    # 根据位置计算分数
                    score = 0.9 - (idx * 0.05)  # 递减分数

                    rag_results.append(RAGResult(
                        content=content,
                        score=max(score, 0.5),
                        source=self.provider_name,
                        metadata=metadata,
                        entities=item.get('entities') if isinstance(item, dict) else None,
                        relations=item.get('relations') if isinstance(item, dict) else None
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
        插入文档到LightRAG知识图谱

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据

        Returns:
            是否成功
        """
        if not self._initialized or not self._lightrag_service:
            raise RAGIngestionError(f"{self.provider_name} 未初始化")

        try:
            logger.debug(
                f"📝 {self.provider_name} 索引文档: "
                f"id={document_id}, length={len(content)}"
            )

            # 调用LightRAG服务插入文档
            success = await self._lightrag_service.insert_document(
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

        except Exception as e:
            logger.error(f"❌ {self.provider_name} 索引失败: {e}")
            raise RAGIngestionError(f"索引失败: {str(e)}")

    async def delete(
        self,
        document_id: str,
        project_id: Optional[str] = None
    ) -> bool:
        """
        删除文档（LightRAG可能不支持删除，返回False）

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

        if self._lightrag_service:
            health['service_available'] = True
            health['supported_modes'] = [m.value for m in self.supported_modes]
        else:
            health['service_available'] = False

        return health


# 工厂函数
async def create_lightrag_adapter(
    config: Optional[Dict[str, Any]] = None
) -> LightRAGAdapter:
    """
    创建并初始化LightRAG适配器

    Args:
        config: 配置

    Returns:
        初始化后的适配器
    """
    adapter = LightRAGAdapter(config)
    await adapter.initialize()
    return adapter
