"""
RAG集成服务 - 统一管理所有RAG引擎对规范化内容的索引

功能：
1. 将规范化后的文档自动分发到所有启用的RAG引擎
2. 并行执行，避免阻塞
3. 错误处理和重试机制
4. 索引状态跟踪

集成的RAG引擎：
- Quivr (第二大脑RAG)
- LightRAG (图谱增强RAG)
- GraphRAG (微软多尺度RAG)
- Cognee (AI记忆图谱)
- Mem0 (长记忆系统)
- RAGFlow (高级文档处理)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class RAGIntegrationService:
    """RAG集成服务 - 统一索引协调器"""

    def __init__(self):
        """初始化所有RAG服务实例"""
        self.services_available = {}
        self._initialize_services()

    def _initialize_services(self):
        """初始化并检查各RAG服务可用性"""

        # 1. Quivr
        try:
            from app.services.quivr_service import get_quivr_service
            self.quivr = get_quivr_service()
            self.services_available['quivr'] = True
            logger.info("✅ Quivr服务已加载")
        except Exception as e:
            self.services_available['quivr'] = False
            logger.warning(f"⚠️ Quivr服务不可用: {e}")

        # 2. LightRAG
        try:
            from app.services.lightrag_service import get_lightrag_service
            self.lightrag = get_lightrag_service()
            self.services_available['lightrag'] = True
            logger.info("✅ LightRAG服务已加载")
        except Exception as e:
            self.services_available['lightrag'] = False
            logger.warning(f"⚠️ LightRAG服务不可用: {e}")

        # 3. GraphRAG
        try:
            from app.services.graphrag_service import get_graphrag_service
            self.graphrag = get_graphrag_service()
            self.services_available['graphrag'] = True
            logger.info("✅ GraphRAG服务已加载")
        except Exception as e:
            self.services_available['graphrag'] = False
            logger.warning(f"⚠️ GraphRAG服务不可用: {e}")

        # 4. Cognee
        try:
            from app.services.cognee_service import get_cognee_service
            self.cognee = get_cognee_service()
            self.services_available['cognee'] = True
            logger.info("✅ Cognee服务已加载")
        except Exception as e:
            self.services_available['cognee'] = False
            logger.warning(f"⚠️ Cognee服务不可用: {e}")

        # 5. Mem0
        try:
            from app.services.mem0_service import Mem0Service
            self.mem0 = Mem0Service()
            self.services_available['mem0'] = True
            logger.info("✅ Mem0服务已加载")
        except Exception as e:
            self.services_available['mem0'] = False
            logger.warning(f"⚠️ Mem0服务不可用: {e}")

        # 6. RAGFlow
        try:
            from app.services.ragflow_service import ragflow_service
            self.ragflow = ragflow_service
            self.services_available['ragflow'] = ragflow_service.is_available()
            if self.services_available['ragflow']:
                logger.info("✅ RAGFlow服务已加载")
            else:
                logger.warning("⚠️ RAGFlow服务未配置")
        except Exception as e:
            self.services_available['ragflow'] = False
            logger.warning(f"⚠️ RAGFlow服务不可用: {e}")

        available_count = sum(1 for v in self.services_available.values() if v)
        logger.info(f"📊 RAG集成服务初始化完成: {available_count}/{len(self.services_available)} 个引擎可用")

    async def index_normalized_document(
        self,
        document_id: int,
        normalized_text: str,
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        engines: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        将规范化后的文档索引到所有（或指定的）RAG引擎

        Args:
            document_id: 文档ID
            normalized_text: 规范化后的文本
            project_id: 项目ID（用于数据隔离）
            metadata: 文档元数据
            engines: 指定要索引的引擎列表，None表示全部

        Returns:
            Dict[engine_name, result]: 各引擎的索引结果
        """
        start_time = asyncio.get_event_loop().time()

        logger.info(f"{'='*60}")
        logger.info(f"🚀 开始RAG多引擎索引 - 文档 {document_id}")
        logger.info(f"   项目ID: {project_id}")
        logger.info(f"   文本长度: {len(normalized_text)} 字符")
        logger.info(f"   目标引擎: {engines or '全部'}")
        logger.info(f"{'='*60}")

        metadata = metadata or {}
        metadata.update({
            'document_id': document_id,
            'project_id': project_id,
            'indexed_at': datetime.utcnow().isoformat()
        })

        # 确定要索引的引擎
        target_engines = engines or list(self.services_available.keys())
        target_engines = [e for e in target_engines if self.services_available.get(e, False)]

        if not target_engines:
            logger.warning("⚠️ 没有可用的RAG引擎")
            return {}

        # 并行索引到所有引擎
        tasks = []
        engine_names = []

        for engine in target_engines:
            if engine == 'quivr':
                tasks.append(self._index_to_quivr(project_id, normalized_text, metadata))
            elif engine == 'lightrag':
                tasks.append(self._index_to_lightrag(project_id, document_id, normalized_text, metadata))
            elif engine == 'graphrag':
                tasks.append(self._index_to_graphrag(project_id, document_id, normalized_text, metadata))
            elif engine == 'cognee':
                tasks.append(self._index_to_cognee(project_id, document_id, normalized_text, metadata))
            elif engine == 'mem0':
                tasks.append(self._index_to_mem0(project_id, document_id, normalized_text, metadata))
            elif engine == 'ragflow':
                tasks.append(self._index_to_ragflow(project_id, document_id, normalized_text, metadata))

            engine_names.append(engine)

        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        final_results = {}
        success_count = 0

        for engine_name, result in zip(engine_names, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {engine_name} 索引失败: {result}")
                final_results[engine_name] = {
                    'status': 'error',
                    'error': str(result),
                    'traceback': traceback.format_exc()
                }
            else:
                final_results[engine_name] = result
                if result.get('status') == 'success':
                    success_count += 1
                    logger.info(f"✅ {engine_name} 索引成功")
                else:
                    logger.warning(f"⚠️ {engine_name} 索引失败: {result.get('error')}")

        elapsed_time = asyncio.get_event_loop().time() - start_time

        logger.info(f"{'='*60}")
        logger.info(f"✅ RAG多引擎索引完成 - 文档 {document_id}")
        logger.info(f"   成功: {success_count}/{len(target_engines)}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info(f"{'='*60}")

        return {
            'success': success_count > 0,
            'total_engines': len(target_engines),
            'success_count': success_count,
            'elapsed_time': round(elapsed_time, 2),
            'results': final_results
        }

    async def search_all_engines(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
        engines: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        在所有RAG引擎中搜索

        Args:
            query: 查询文本
            project_id: 项目ID
            top_k: 每个引擎返回的结果数
            engines: 指定搜索的引擎，None表示全部

        Returns:
            Dict[engine_name, results]: 各引擎的搜索结果
        """
        logger.info(f"🔍 跨RAG引擎搜索: {query[:50]}...")

        target_engines = engines or [e for e in self.services_available.keys() if self.services_available[e]]

        tasks = []
        engine_names = []

        for engine in target_engines:
            if engine == 'quivr':
                tasks.append(self._search_quivr(project_id, query, top_k))
            elif engine == 'lightrag':
                tasks.append(self._search_lightrag(project_id, query, top_k))
            elif engine == 'graphrag':
                tasks.append(self._search_graphrag(project_id, query))
            elif engine == 'cognee':
                tasks.append(self._search_cognee(project_id, query, top_k))
            elif engine == 'mem0':
                tasks.append(self._search_mem0(project_id, query, top_k))

            engine_names.append(engine)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = {}
        for engine_name, result in zip(engine_names, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {engine_name} 搜索失败: {result}")
                final_results[engine_name] = {'status': 'error', 'error': str(result)}
            else:
                final_results[engine_name] = result

        return final_results

    # ========== 索引方法 ==========

    async def _index_to_quivr(self, project_id: str, content: str, metadata: Dict) -> Dict:
        """索引到Quivr"""
        try:
            result = await self.quivr.index_document(
                project_id=project_id,
                content=content,
                metadata=metadata
            )
            return result
        except Exception as e:
            logger.error(f"Quivr索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _index_to_lightrag(self, project_id: str, document_id: int, content: str, metadata: Dict) -> Dict:
        """索引到LightRAG"""
        try:
            success = await self.lightrag.insert_document(
                content=content,
                document_id=str(document_id),
                project_id=project_id,
                metadata=metadata
            )
            return {
                'status': 'success' if success else 'failed',
                'indexed': success
            }
        except Exception as e:
            logger.error(f"LightRAG索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _index_to_graphrag(self, project_id: str, document_id: int, content: str, metadata: Dict) -> Dict:
        """索引到GraphRAG"""
        try:
            result = await self.graphrag.index_document(
                content=content,
                project_id=project_id,
                document_id=document_id,
                metadata=metadata
            )
            return result
        except Exception as e:
            logger.error(f"GraphRAG索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _index_to_cognee(self, project_id: str, document_id: int, content: str, metadata: Dict) -> Dict:
        """索引到Cognee"""
        try:
            result = await self.cognee.remember_document(
                content=content,
                document_id=str(document_id),
                project_id=project_id,
                metadata=metadata
            )
            return {
                'status': 'success',
                'result': str(result) if result else None
            }
        except Exception as e:
            logger.error(f"Cognee索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _index_to_mem0(self, project_id: str, document_id: int, content: str, metadata: Dict) -> Dict:
        """索引到Mem0"""
        try:
            result = self.mem0.add_document_memory(
                project_id=int(project_id),
                document_id=document_id,
                content=content,
                metadata=metadata
            )
            return {
                'status': 'success' if result else 'failed',
                'result': result
            }
        except Exception as e:
            logger.error(f"Mem0索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _index_to_ragflow(self, project_id: str, document_id: int, content: str, metadata: Dict) -> Dict:
        """索引到RAGFlow"""
        try:
            # RAGFlow需要文件路径，这里跳过直接文本索引
            return {
                'status': 'skipped',
                'message': 'RAGFlow需要文件路径，暂不支持直接文本索引'
            }
        except Exception as e:
            logger.error(f"RAGFlow索引异常: {e}")
            return {'status': 'error', 'error': str(e)}

    # ========== 搜索方法 ==========

    async def _search_quivr(self, project_id: str, query: str, top_k: int) -> Dict:
        """在Quivr中搜索"""
        try:
            result = await self.quivr.search(
                project_id=project_id,
                query=query,
                n_results=top_k
            )
            return result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _search_lightrag(self, project_id: str, query: str, top_k: int) -> Dict:
        """在LightRAG中搜索"""
        try:
            result = await self.lightrag.query(
                query_text=query,
                project_id=project_id,
                mode='hybrid',
                top_k=top_k
            )
            return {
                'status': 'success',
                'results': [{'content': result}] if result else []
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _search_graphrag(self, project_id: str, query: str) -> Dict:
        """在GraphRAG中搜索"""
        try:
            # 使用local搜索
            result = await self.graphrag.local_search(
                query=query,
                project_id=project_id
            )
            return result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _search_cognee(self, project_id: str, query: str, top_k: int) -> Dict:
        """在Cognee中搜索"""
        try:
            results = await self.cognee.recall_context(
                query=query,
                project_id=project_id,
                top_k=top_k
            )
            return {
                'status': 'success',
                'results': results
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _search_mem0(self, project_id: str, query: str, top_k: int) -> Dict:
        """在Mem0中搜索"""
        try:
            results = self.mem0.search_memories(
                project_id=int(project_id),
                query=query,
                limit=top_k
            )
            return {
                'status': 'success',
                'results': results
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_engines_status(self) -> Dict[str, Any]:
        """获取所有引擎的状态"""
        return {
            'available_engines': self.services_available,
            'total_engines': len(self.services_available),
            'available_count': sum(1 for v in self.services_available.values() if v)
        }


# ========== 全局单例 ==========

_rag_integration_service: Optional[RAGIntegrationService] = None


def get_rag_integration_service() -> RAGIntegrationService:
    """获取RAG集成服务单例"""
    global _rag_integration_service
    if _rag_integration_service is None:
        _rag_integration_service = RAGIntegrationService()
    return _rag_integration_service
