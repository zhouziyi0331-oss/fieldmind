"""
多源记忆整合器 (Multi-Source Memory Aggregator)

整合6大记忆源：
1. long_memory - 基础向量记忆
2. Cognee - AI驱动的认知记忆
3. LightRAG - 轻量级知识图谱RAG
4. Mem0 - 长期记忆系统
5. Graphiti - 时态知识图谱
6. GraphRAG - 微软多尺度知识图谱

提供统一的记忆检索和存储接口
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryAggregator:
    """多源记忆整合器"""

    def __init__(self):
        """初始化记忆整合器"""
        self._long_memory_service = None
        self._cognee_service = None
        self._lightrag_service = None
        self._mem0_service = None
        self._graphiti_service = None
        self._graphrag_service = None
        self._khoj_service = None
        self._quivr_service = None

        # 记忆源权重配置（可根据场景调整）
        self.source_weights = {
            'long_memory': 1.0,      # 基础记忆，始终可用
            'cognee': 0.9,           # AI认知记忆，高质量
            'lightrag': 0.85,        # 知识图谱，结构化
            'mem0': 0.8,             # 长期记忆，持久化
            'graphiti': 0.75,        # 时态图谱，时间敏感
            'graphrag': 0.95,        # 多尺度图谱，全局+局部
            'khoj': 0.7,             # 个人知识库
            'quivr': 0.7             # 第二大脑RAG
        }

        logger.info("✅ 多源记忆整合器初始化")

    # ==================== 延迟加载服务 ====================

    @property
    def long_memory(self):
        """长记忆服务（延迟加载）"""
        if self._long_memory_service is None:
            try:
                from app.services.long_memory_service import long_memory_service
                self._long_memory_service = long_memory_service
                logger.debug("✅ long_memory服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ long_memory服务加载失败: {e}")
        return self._long_memory_service

    @property
    def cognee(self):
        """Cognee服务（延迟加载）"""
        if self._cognee_service is None:
            try:
                from app.services.cognee_service import get_cognee_service
                self._cognee_service = get_cognee_service()
                logger.debug("✅ Cognee服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ Cognee服务加载失败: {e}")
        return self._cognee_service

    @property
    def lightrag(self):
        """LightRAG服务（延迟加载）"""
        if self._lightrag_service is None:
            try:
                from app.services.lightrag_service import get_lightrag_service
                self._lightrag_service = get_lightrag_service()
                logger.debug("✅ LightRAG服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ LightRAG服务加载失败: {e}")
        return self._lightrag_service

    @property
    def mem0(self):
        """Mem0服务（延迟加载）"""
        if self._mem0_service is None:
            try:
                from app.services.mem0_service import Mem0Service
                self._mem0_service = Mem0Service()
                logger.debug("✅ Mem0服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ Mem0服务加载失败: {e}")
        return self._mem0_service

    @property
    def graphiti(self):
        """Graphiti服务（延迟加载）"""
        if self._graphiti_service is None:
            try:
                from app.services.graphiti_service import get_graphiti_service
                self._graphiti_service = get_graphiti_service()
                logger.debug("✅ Graphiti服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ Graphiti服务加载失败: {e}")
        return self._graphiti_service

    @property
    def graphrag(self):
        """GraphRAG服务（延迟加载）"""
        if self._graphrag_service is None:
            try:
                from app.services.graphrag_service import get_graphrag_service
                self._graphrag_service = get_graphrag_service()
                logger.debug("✅ GraphRAG服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ GraphRAG服务加载失败: {e}")
        return self._graphrag_service

    @property
    def khoj(self):
        """Khoj服务（延迟加载）"""
        if self._khoj_service is None:
            try:
                from app.services.khoj_service import get_khoj_service
                self._khoj_service = get_khoj_service()
                logger.debug("✅ Khoj服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ Khoj服务加载失败: {e}")
        return self._khoj_service

    @property
    def quivr(self):
        """Quivr服务（延迟加载）"""
        if self._quivr_service is None:
            try:
                from app.services.quivr_service import get_quivr_service
                self._quivr_service = get_quivr_service()
                logger.debug("✅ Quivr服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ Quivr服务加载失败: {e}")
        return self._quivr_service

    # ==================== 核心检索方法 ====================

    def aggregate_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        project_id: Optional[int] = None,
        memory_config: Optional[Dict[str, Any]] = None,
        enabled_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        聚合多源记忆

        Args:
            query: 查询文本
            session_id: 会话ID（用于会话级记忆）
            project_id: 项目ID（用于项目级记忆）
            memory_config: 记忆配置
            enabled_sources: 启用的记忆源列表（None=全部）

        Returns:
            整合后的记忆上下文
        """
        start_time = datetime.now()

        config = memory_config or {}
        top_k = config.get('search_depth', 5)
        relevance_threshold = config.get('relevance_threshold', 0.7)
        max_context_tokens = config.get('max_context_tokens', 8000)

        # 确定启用的记忆源
        if enabled_sources is None:
            enabled_sources = ['long_memory', 'cognee', 'lightrag', 'mem0',
                             'graphiti', 'graphrag', 'khoj', 'quivr']

        logger.info(f"🔍 开始聚合记忆: query='{query[:50]}...', sources={enabled_sources}")

        # 并行检索所有记忆源
        memory_results = {}

        if 'long_memory' in enabled_sources:
            memory_results['long_memory'] = self._retrieve_long_memory(
                query, session_id, project_id, top_k
            )

        if 'cognee' in enabled_sources:
            memory_results['cognee'] = self._retrieve_cognee(
                query, session_id, project_id, top_k
            )

        if 'lightrag' in enabled_sources:
            memory_results['lightrag'] = self._retrieve_lightrag(
                query, project_id, top_k
            )

        if 'mem0' in enabled_sources:
            memory_results['mem0'] = self._retrieve_mem0(
                query, project_id, top_k
            )

        if 'graphiti' in enabled_sources:
            memory_results['graphiti'] = self._retrieve_graphiti(
                query, project_id, top_k
            )

        if 'graphrag' in enabled_sources:
            memory_results['graphrag'] = self._retrieve_graphrag(
                query, project_id
            )

        if 'khoj' in enabled_sources:
            memory_results['khoj'] = self._retrieve_khoj(
                query, project_id, top_k
            )

        if 'quivr' in enabled_sources:
            memory_results['quivr'] = self._retrieve_quivr(
                query, project_id
            )

        # 构建整合上下文
        aggregated_context = self._build_aggregated_context(
            memory_results,
            max_tokens=max_context_tokens
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            'context': aggregated_context,
            'sources_used': list(memory_results.keys()),
            'source_results': {
                k: len(v.get('results', [])) if v else 0
                for k, v in memory_results.items()
            },
            'processing_time': processing_time,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(
            f"✅ 记忆聚合完成: "
            f"sources={len(memory_results)}, "
            f"time={processing_time:.2f}s"
        )

        return result

    # ==================== 各记忆源检索方法 ====================

    def _retrieve_long_memory(
        self,
        query: str,
        session_id: Optional[str],
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索基础长记忆"""
        try:
            if not self.long_memory:
                return None

            context = self.long_memory.build_memory_context(
                query=query,
                session_id=session_id,
                project_id=project_id,
                config={'search_depth': top_k}
            )

            if context:
                return {
                    'results': [{'content': context}],
                    'source': 'long_memory'
                }
            return None

        except Exception as e:
            logger.warning(f"⚠️ long_memory检索失败: {e}")
            return None

    def _retrieve_cognee(
        self,
        query: str,
        session_id: Optional[str],
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索Cognee认知记忆"""
        try:
            if not self.cognee:
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    self.cognee.recall_context(
                        query=query,
                        project_id=str(project_id) if project_id else None,
                        session_id=session_id,
                        search_type="insights",
                        top_k=top_k
                    )
                )

                if results:
                    return {
                        'results': [{'content': r} for r in results],
                        'source': 'cognee'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Cognee检索失败: {e}")
            return None

    def _retrieve_lightrag(
        self,
        query: str,
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索LightRAG知识图谱"""
        try:
            if not self.lightrag:
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.lightrag.query(
                        query_text=query,
                        project_id=str(project_id) if project_id else None,
                        mode="hybrid",
                        only_need_context=True,
                        top_k=top_k
                    )
                )

                if result:
                    return {
                        'results': [{'content': result}],
                        'source': 'lightrag'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ LightRAG检索失败: {e}")
            return None

    def _retrieve_mem0(
        self,
        query: str,
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索Mem0长记忆"""
        try:
            if not self.mem0:
                return None

            results = self.mem0.search_memories(
                project_id=project_id if project_id else 0,
                query=query,
                limit=top_k
            )

            if results:
                return {
                    'results': [
                        {'content': r.get('memory', r.get('text', str(r)))}
                        for r in results
                    ],
                    'source': 'mem0'
                }
            return None

        except Exception as e:
            logger.warning(f"⚠️ Mem0检索失败: {e}")
            return None

    def _retrieve_graphiti(
        self,
        query: str,
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索Graphiti时态知识图谱"""
        try:
            if not self.graphiti:
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    self.graphiti.search(
                        query=query,
                        project_id=str(project_id) if project_id else None,
                        num_results=top_k
                    )
                )

                if results:
                    return {
                        'results': [
                            {
                                'content': f"[{r.get('name', 'Unknown')}] {r.get('content', '')}",
                                'timestamp': r.get('created_at')
                            }
                            for r in results
                        ],
                        'source': 'graphiti'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Graphiti检索失败: {e}")
            return None

    def _retrieve_graphrag(
        self,
        query: str,
        project_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """检索GraphRAG多尺度知识图谱"""
        try:
            if not self.graphrag:
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 并行执行局部和全局搜索
                local_results = loop.run_until_complete(
                    self.graphrag.local_search(
                        query=query,
                        project_id=str(project_id) if project_id else None,
                        community_level=2
                    )
                )

                global_results = loop.run_until_complete(
                    self.graphrag.global_search(
                        query=query,
                        project_id=str(project_id) if project_id else None,
                        community_level=2
                    )
                )

                results = []

                if local_results.get('status') == 'success':
                    results.append({
                        'content': f"[局部视角] {local_results.get('response', '')}",
                        'type': 'local'
                    })

                if global_results.get('status') == 'success':
                    results.append({
                        'content': f"[全局视角] {global_results.get('response', '')}",
                        'type': 'global'
                    })

                if results:
                    return {
                        'results': results,
                        'source': 'graphrag'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ GraphRAG检索失败: {e}")
            return None

    def _retrieve_khoj(
        self,
        query: str,
        project_id: Optional[int],
        top_k: int
    ) -> Optional[Dict[str, Any]]:
        """检索Khoj个人知识库"""
        try:
            if not self.khoj:
                return None

            # 健康检查
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                health = loop.run_until_complete(self.khoj.health_check())

                if not health.get('available'):
                    return None

                search_results = loop.run_until_complete(
                    self.khoj.search(
                        query=query,
                        n=top_k,
                        project_id=str(project_id) if project_id else None
                    )
                )

                if search_results.get('status') == 'success' and search_results.get('results'):
                    results = search_results['results']
                    return {
                        'results': [
                            {
                                'content': r.get('content', r.get('entry', ''))[:500],
                                'score': r.get('score', 0)
                            }
                            for r in results
                        ],
                        'source': 'khoj'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Khoj检索失败: {e}")
            return None

    def _retrieve_quivr(
        self,
        query: str,
        project_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """检索Quivr第二大脑RAG"""
        try:
            if not self.quivr:
                return None

            # 健康检查
            health = self.quivr.health_check()

            if not health.get('available'):
                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.quivr.ask(
                        project_id=str(project_id) if project_id else 'default',
                        question=query
                    )
                )

                if result.get('status') == 'success' and result.get('answer'):
                    return {
                        'results': [
                            {
                                'content': result['answer'][:800],
                                'sources': result.get('sources', [])[:2]
                            }
                        ],
                        'source': 'quivr'
                    }
                return None
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Quivr检索失败: {e}")
            return None

    # ==================== 上下文构建 ====================

    def _build_aggregated_context(
        self,
        memory_results: Dict[str, Optional[Dict]],
        max_tokens: int = 8000
    ) -> str:
        """
        构建整合的记忆上下文

        策略：
        1. 按权重排序记忆源
        2. 逐源添加内容直到达到token限制
        3. 保持上下文结构清晰
        """
        context_parts = []
        estimated_tokens = 0

        # 按权重排序记忆源
        sorted_sources = sorted(
            memory_results.items(),
            key=lambda x: self.source_weights.get(x[0], 0.5),
            reverse=True
        )

        for source_name, source_data in sorted_sources:
            if not source_data or not source_data.get('results'):
                continue

            # 构建该记忆源的上下文
            source_context = self._format_source_context(
                source_name,
                source_data['results']
            )

            # 估算tokens（简单估算：1 token ≈ 4字符）
            source_tokens = len(source_context) // 4

            # 检查是否超过限制
            if estimated_tokens + source_tokens > max_tokens:
                # 截断内容
                remaining_tokens = max_tokens - estimated_tokens
                truncated_context = source_context[:remaining_tokens * 4]
                context_parts.append(truncated_context)
                break

            context_parts.append(source_context)
            estimated_tokens += source_tokens

        if not context_parts:
            return ""

        return "\n\n".join(context_parts)

    def _format_source_context(
        self,
        source_name: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """格式化单个记忆源的上下文"""
        source_titles = {
            'long_memory': '基础记忆',
            'cognee': 'Cognee AI认知记忆',
            'lightrag': 'LightRAG知识图谱',
            'mem0': 'Mem0长期记忆',
            'graphiti': 'Graphiti时态图谱',
            'graphrag': 'GraphRAG多尺度图谱',
            'khoj': 'Khoj个人知识库',
            'quivr': 'Quivr第二大脑'
        }

        title = source_titles.get(source_name, source_name)

        parts = [f"=== {title} ==="]

        for idx, result in enumerate(results[:5], 1):  # 最多5条
            content = result.get('content', '')
            if content:
                # 特殊处理不同类型的结果
                if 'score' in result:
                    parts.append(f"{idx}. (相关度: {result['score']:.2f}) {content}")
                elif 'timestamp' in result:
                    parts.append(f"{idx}. [{result['timestamp']}] {content}")
                else:
                    parts.append(f"{idx}. {content}")

        return "\n".join(parts)

    # ==================== 记忆存储 ====================

    def save_to_memory(
        self,
        content: str,
        session_id: Optional[str] = None,
        project_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        target_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        保存内容到多个记忆源

        Args:
            content: 要保存的内容
            session_id: 会话ID
            project_id: 项目ID
            metadata: 元数据
            target_sources: 目标记忆源（None=全部）

        Returns:
            保存结果
        """
        if target_sources is None:
            target_sources = ['long_memory', 'cognee', 'mem0']

        logger.info(f"💾 保存内容到记忆: targets={target_sources}")

        save_results = {}

        if 'long_memory' in target_sources:
            save_results['long_memory'] = self._save_to_long_memory(
                content, session_id, project_id, metadata
            )

        if 'cognee' in target_sources:
            save_results['cognee'] = self._save_to_cognee(
                content, session_id, project_id, metadata
            )

        if 'mem0' in target_sources:
            save_results['mem0'] = self._save_to_mem0(
                content, project_id, metadata
            )

        successful = sum(1 for v in save_results.values() if v)

        logger.info(f"✅ 记忆保存完成: {successful}/{len(target_sources)} 成功")

        return {
            'success': successful > 0,
            'saved_to': [k for k, v in save_results.items() if v],
            'results': save_results
        }

    def _save_to_long_memory(
        self,
        content: str,
        session_id: Optional[str],
        project_id: Optional[int],
        metadata: Optional[Dict]
    ) -> bool:
        """保存到基础长记忆"""
        try:
            if not self.long_memory:
                return False

            self.long_memory.save_conversation_to_memory(
                session_id=session_id,
                messages=[{"role": "assistant", "content": content}],
                project_id=project_id
            )
            return True

        except Exception as e:
            logger.warning(f"⚠️ long_memory保存失败: {e}")
            return False

    def _save_to_cognee(
        self,
        content: str,
        session_id: Optional[str],
        project_id: Optional[int],
        metadata: Optional[Dict]
    ) -> bool:
        """保存到Cognee"""
        try:
            if not self.cognee:
                return False

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.cognee.remember_conversation(
                        messages=[{"role": "assistant", "content": content}],
                        session_id=session_id,
                        project_id=str(project_id) if project_id else None
                    )
                )
                return True
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Cognee保存失败: {e}")
            return False

    def _save_to_mem0(
        self,
        content: str,
        project_id: Optional[int],
        metadata: Optional[Dict]
    ) -> bool:
        """保存到Mem0"""
        try:
            if not self.mem0:
                return False

            self.mem0.add_memory(
                project_id=project_id if project_id else 0,
                content=content,
                metadata=metadata or {}
            )
            return True

        except Exception as e:
            logger.warning(f"⚠️ Mem0保存失败: {e}")
            return False

    # ==================== 统计与管理 ====================

    def get_memory_statistics(
        self,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            'sources': {},
            'total_memories': 0,
            'timestamp': datetime.utcnow().isoformat()
        }

        # 收集各源统计
        if self.long_memory:
            try:
                long_stats = self.long_memory.get_memory_statistics(project_id)
                stats['sources']['long_memory'] = long_stats
                stats['total_memories'] += long_stats.get('total_memories', 0)
            except:
                pass

        # TODO: 其他记忆源的统计

        return stats


# 全局单例
_memory_aggregator_instance = None


def get_memory_aggregator() -> MemoryAggregator:
    """获取记忆整合器单例"""
    global _memory_aggregator_instance
    if _memory_aggregator_instance is None:
        _memory_aggregator_instance = MemoryAggregator()
    return _memory_aggregator_instance
