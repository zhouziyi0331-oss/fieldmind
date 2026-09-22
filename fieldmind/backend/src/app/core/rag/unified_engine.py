"""
统一RAG引擎 (Unified RAG Engine)

整合所有RAG提供者，提供统一的查询接口
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from app.core.rag.base_interface import (
    BaseRAGInterface, RAGQuery, RAGResult, RAGResponse, RAGMode,
    RAGProviderConfig, RAGProviderNotFoundError, RAGQueryError
)
from app.core.rag.router import RAGRouter, RoutingStrategy, get_rag_router
from app.core.rag.adapters.base_rag_adapter import BaseRAGAdapter
from app.core.rag.adapters.lightrag_adapter import LightRAGAdapter
from app.core.rag.adapters.graphrag_adapter import GraphRAGAdapter

logger = logging.getLogger(__name__)


class UnifiedRAGEngine:
    """统一RAG引擎"""

    def __init__(self):
        """初始化统一RAG引擎"""
        # RAG提供者注册表
        self._providers: Dict[str, BaseRAGInterface] = {}

        # 提供者配置
        self._provider_configs: Dict[str, RAGProviderConfig] = {}

        # 智能路由器
        self._router = get_rag_router()

        # 结果缓存（简单内存缓存）
        self._cache: Dict[str, RAGResponse] = {}
        self._cache_ttl = 300  # 5分钟

        # 统计信息
        self._stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'provider_usage': {}
        }

        logger.info("✅ 统一RAG引擎初始化")

    async def initialize(self):
        """初始化所有RAG提供者"""
        try:
            # 1. 初始化BaseRAG
            try:
                base_rag = BaseRAGAdapter()
                if await base_rag.initialize():
                    self._providers['base_rag'] = base_rag
                    self._provider_configs['base_rag'] = RAGProviderConfig(
                        enabled=True,
                        priority=1,
                        weight=0.8
                    )
                    logger.info("✅ BaseRAG 已注册")
            except Exception as e:
                logger.warning(f"⚠️ BaseRAG 注册失败: {e}")

            # 2. 初始化LightRAG
            try:
                lightrag = LightRAGAdapter()
                if await lightrag.initialize():
                    self._providers['lightrag'] = lightrag
                    self._provider_configs['lightrag'] = RAGProviderConfig(
                        enabled=True,
                        priority=3,
                        weight=0.95
                    )
                    logger.info("✅ LightRAG 已注册")
            except Exception as e:
                logger.warning(f"⚠️ LightRAG 注册失败: {e}")

            # 3. 初始化GraphRAG
            try:
                graphrag = GraphRAGAdapter()
                if await graphrag.initialize():
                    self._providers['graphrag'] = graphrag
                    self._provider_configs['graphrag'] = RAGProviderConfig(
                        enabled=True,
                        priority=2,
                        weight=0.9
                    )
                    logger.info("✅ GraphRAG 已注册")
            except Exception as e:
                logger.warning(f"⚠️ GraphRAG 注册失败: {e}")

            logger.info(
                f"✅ 统一RAG引擎初始化完成: "
                f"{len(self._providers)} 个提供者已注册"
            )

        except Exception as e:
            logger.error(f"❌ 统一RAG引擎初始化失败: {e}")

    # ==================== 核心查询接口 ====================

    async def query(
        self,
        query: str,
        mode: RAGMode = RAGMode.ADAPTIVE,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        routing_strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
        options: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        统一查询接口

        Args:
            query: 查询文本
            mode: 检索模式
            top_k: 返回结果数
            project_id: 项目ID
            filters: 过滤条件
            use_cache: 是否使用缓存
            routing_strategy: 路由策略
            options: 额外选项

        Returns:
            RAG响应
        """
        start_time = datetime.now()
        self._stats['total_queries'] += 1

        logger.info(
            f"🔍 统一RAG查询: query='{query[:50]}...', "
            f"mode={mode.value}, top_k={top_k}"
        )

        try:
            # 1. 检查缓存
            if use_cache:
                cache_key = self._build_cache_key(query, mode, top_k, project_id)
                cached = self._get_from_cache(cache_key)
                if cached:
                    self._stats['cache_hits'] += 1
                    logger.debug("✅ 缓存命中")
                    return cached

            # 2. 构建RAG查询
            rag_query = RAGQuery(
                query=query,
                mode=mode,
                top_k=top_k,
                project_id=project_id,
                filters=filters,
                options=options or {}
            )

            # 3. 选择提供者
            available_providers = self._get_available_providers()

            if not available_providers:
                raise RAGProviderNotFoundError("没有可用的RAG提供者")

            selected_providers = self._router.select_providers(
                rag_query=rag_query,
                available_providers=available_providers,
                strategy=routing_strategy
            )

            logger.debug(f"📌 选中提供者: {selected_providers}")

            # 4. 执行查询
            if len(selected_providers) == 1:
                # 单提供者查询
                results = await self._query_single_provider(
                    selected_providers[0],
                    rag_query
                )
            else:
                # 多提供者并行查询
                results = await self._query_multiple_providers(
                    selected_providers,
                    rag_query
                )

            # 5. 构建响应
            processing_time = (datetime.now() - start_time).total_seconds()

            response = RAGResponse(
                query=query,
                results=results,
                total_count=len(results),
                sources_used=selected_providers,
                processing_time=processing_time,
                metadata={
                    'mode': mode.value,
                    'routing_strategy': routing_strategy.value,
                    'cache_used': False
                }
            )

            # 6. 缓存结果
            if use_cache:
                self._put_to_cache(cache_key, response)

            logger.info(
                f"✅ 查询完成: {len(results)} 条结果, "
                f"time={processing_time:.2f}s"
            )

            return response

        except Exception as e:
            logger.error(f"❌ 查询失败: {e}", exc_info=True)

            # 返回空结果而不是抛出异常
            processing_time = (datetime.now() - start_time).total_seconds()
            return RAGResponse(
                query=query,
                results=[],
                total_count=0,
                sources_used=[],
                processing_time=processing_time,
                metadata={'error': str(e)}
            )

    async def _query_single_provider(
        self,
        provider_name: str,
        rag_query: RAGQuery
    ) -> List[RAGResult]:
        """单提供者查询"""
        provider = self._providers.get(provider_name)

        if not provider:
            raise RAGProviderNotFoundError(f"提供者 {provider_name} 未找到")

        # 调整模式
        if not provider.supports_mode(rag_query.mode):
            # 推荐模式
            rag_query.mode = self._router.recommend_mode(
                rag_query.query,
                provider_name
            )
            logger.debug(
                f"📌 {provider_name} 不支持原模式，"
                f"使用推荐模式: {rag_query.mode.value}"
            )

        # 执行查询
        results = await provider.query(rag_query)

        # 更新统计
        if provider_name not in self._stats['provider_usage']:
            self._stats['provider_usage'][provider_name] = 0
        self._stats['provider_usage'][provider_name] += 1

        return results

    async def _query_multiple_providers(
        self,
        provider_names: List[str],
        rag_query: RAGQuery
    ) -> List[RAGResult]:
        """多提供者并行查询"""
        tasks = []

        for provider_name in provider_names:
            task = self._query_single_provider(provider_name, rag_query)
            tasks.append(task)

        # 并行执行
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        all_results = []
        for provider_name, results in zip(provider_names, results_list):
            if isinstance(results, Exception):
                logger.warning(f"⚠️ {provider_name} 查询失败: {results}")
                continue

            all_results.extend(results)

        # 融合和排序
        merged_results = self._merge_and_rank_results(
            all_results,
            rag_query.top_k
        )

        return merged_results

    def _merge_and_rank_results(
        self,
        results: List[RAGResult],
        top_k: int
    ) -> List[RAGResult]:
        """
        合并和排序结果

        策略：
        1. 去重（基于内容相似度）
        2. 按分数排序
        3. 应用提供者权重
        4. 返回top_k
        """
        if not results:
            return []

        # 1. 应用提供者权重
        weighted_results = []
        for result in results:
            provider_config = self._provider_configs.get(result.source)
            if provider_config:
                # 调整分数
                weighted_score = result.score * provider_config.weight
                result.score = weighted_score

            weighted_results.append(result)

        # 2. 按分数排序
        sorted_results = sorted(
            weighted_results,
            key=lambda x: x.score,
            reverse=True
        )

        # 3. 简单去重（基于内容前100字符）
        seen_contents = set()
        unique_results = []

        for result in sorted_results:
            content_key = result.content[:100]

            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_results.append(result)

            if len(unique_results) >= top_k:
                break

        return unique_results

    # ==================== 文档管理 ====================

    async def ingest(
        self,
        content: str,
        document_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        target_providers: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        插入文档到所有或指定的RAG提供者

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据
            target_providers: 目标提供者（None=全部）

        Returns:
            每个提供者的插入结果
        """
        logger.info(
            f"📝 统一RAG索引: doc_id={document_id}, "
            f"length={len(content)}"
        )

        if target_providers is None:
            target_providers = list(self._providers.keys())

        tasks = []
        for provider_name in target_providers:
            if provider_name in self._providers:
                provider = self._providers[provider_name]
                task = provider.ingest(content, document_id, project_id, metadata)
                tasks.append((provider_name, task))

        # 并行执行
        results = {}
        for provider_name, task in tasks:
            try:
                success = await task
                results[provider_name] = success
            except Exception as e:
                logger.error(f"❌ {provider_name} 索引失败: {e}")
                results[provider_name] = False

        logger.info(
            f"✅ 文档索引完成: "
            f"{sum(results.values())}/{len(results)} 成功"
        )

        return results

    async def delete(
        self,
        document_id: str,
        project_id: Optional[str] = None,
        target_providers: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        从所有或指定的RAG提供者删除文档

        Args:
            document_id: 文档ID
            project_id: 项目ID
            target_providers: 目标提供者（None=全部）

        Returns:
            每个提供者的删除结果
        """
        logger.info(f"🗑️ 统一RAG删除: doc_id={document_id}")

        if target_providers is None:
            target_providers = list(self._providers.keys())

        tasks = []
        for provider_name in target_providers:
            if provider_name in self._providers:
                provider = self._providers[provider_name]
                task = provider.delete(document_id, project_id)
                tasks.append((provider_name, task))

        # 并行执行
        results = {}
        for provider_name, task in tasks:
            try:
                success = await task
                results[provider_name] = success
            except Exception as e:
                logger.error(f"❌ {provider_name} 删除失败: {e}")
                results[provider_name] = False

        logger.info(
            f"✅ 文档删除完成: "
            f"{sum(results.values())}/{len(results)} 成功"
        )

        return results

    # ==================== 辅助方法 ====================

    def _get_available_providers(self) -> List[str]:
        """获取可用的提供者列表"""
        available = []
        for name, config in self._provider_configs.items():
            if config.enabled and name in self._providers:
                available.append(name)

        # 按优先级排序
        available.sort(
            key=lambda x: self._provider_configs[x].priority,
            reverse=True
        )

        return available

    def _build_cache_key(
        self,
        query: str,
        mode: RAGMode,
        top_k: int,
        project_id: Optional[str]
    ) -> str:
        """构建缓存键"""
        return f"{query}:{mode.value}:{top_k}:{project_id or 'global'}"

    def _get_from_cache(self, cache_key: str) -> Optional[RAGResponse]:
        """从缓存获取"""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # 检查是否过期（简单实现）
            return cached
        return None

    def _put_to_cache(self, cache_key: str, response: RAGResponse):
        """放入缓存"""
        # 简单缓存，不考虑过期（生产环境应使用Redis）
        if len(self._cache) > 1000:
            # 清空一半缓存
            keys_to_remove = list(self._cache.keys())[:500]
            for key in keys_to_remove:
                del self._cache[key]

        self._cache[cache_key] = response

    # ==================== 管理接口 ====================

    def register_provider(
        self,
        provider_name: str,
        provider: BaseRAGInterface,
        config: Optional[RAGProviderConfig] = None
    ) -> bool:
        """注册自定义RAG提供者"""
        try:
            self._providers[provider_name] = provider
            self._provider_configs[provider_name] = config or RAGProviderConfig()

            logger.info(f"✅ 注册RAG提供者: {provider_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 注册RAG提供者失败: {e}")
            return False

    def get_provider_status(self) -> Dict[str, Any]:
        """获取所有提供者状态"""
        status = {}
        for name, provider in self._providers.items():
            try:
                health = asyncio.run(provider.health_check())
                status[name] = health
            except:
                status[name] = {'status': 'error'}

        return status

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_queries': self._stats['total_queries'],
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate': (
                self._stats['cache_hits'] / self._stats['total_queries']
                if self._stats['total_queries'] > 0 else 0
            ),
            'provider_usage': self._stats['provider_usage'],
            'registered_providers': len(self._providers),
            'available_providers': len(self._get_available_providers())
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("✅ 缓存已清空")


# 全局单例
_unified_rag_engine_instance = None


async def get_unified_rag_engine() -> UnifiedRAGEngine:
    """获取统一RAG引擎单例"""
    global _unified_rag_engine_instance
    if _unified_rag_engine_instance is None:
        _unified_rag_engine_instance = UnifiedRAGEngine()
        await _unified_rag_engine_instance.initialize()
    return _unified_rag_engine_instance
