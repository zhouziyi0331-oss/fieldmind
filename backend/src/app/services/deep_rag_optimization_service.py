"""
Deep RAG查询优化服务 - Module 6
Enhanced Deep RAG Service with Query Optimization, Caching, and Event Integration

优化特性：
1. 查询缓存与智能失效
2. 查询重写与扩展
3. 自适应检索源选择
4. 结果质量评估与反馈
5. 查询性能监控
6. WebSocket实时进度推送
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
from sqlalchemy.orm import Session
from collections import defaultdict

from app.services.deep_rag_service import DeepRAGService
from app.services.event_emitter import get_event_emitter

logger = logging.getLogger(__name__)


class QueryCache:
    """查询缓存管理器"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _generate_key(self, query: str, project_id: Optional[int], sources: Optional[List[str]]) -> str:
        """生成缓存键"""
        key_data = f"{query}|{project_id}|{sorted(sources) if sources else 'all'}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, project_id: Optional[int], sources: Optional[List[str]]) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        key = self._generate_key(query, project_id, sources)

        if key in self.cache:
            entry = self.cache[key]

            # 检查是否过期
            if datetime.utcnow() - entry['timestamp'] > timedelta(seconds=self.ttl_seconds):
                del self.cache[key]
                logger.info(f"🗑️ 缓存过期删除: {key[:8]}")
                return None

            self.access_count[key] += 1
            logger.info(f"✅ 缓存命中: {key[:8]} (访问次数: {self.access_count[key]})")
            return entry['result']

        return None

    def set(self, query: str, project_id: Optional[int], sources: Optional[List[str]], result: Dict[str, Any]):
        """设置缓存"""
        key = self._generate_key(query, project_id, sources)

        # LRU淘汰
        if len(self.cache) >= self.max_size:
            # 删除访问次数最少的
            lru_key = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[lru_key]
            del self.access_count[lru_key]
            logger.info(f"🗑️ LRU淘汰: {lru_key[:8]}")

        self.cache[key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }
        self.access_count[key] = 0
        logger.info(f"💾 缓存已保存: {key[:8]}")

    def invalidate(self, project_id: Optional[int] = None):
        """失效缓存"""
        if project_id is None:
            # 清空所有
            self.cache.clear()
            self.access_count.clear()
            logger.info("🗑️ 已清空所有缓存")
        else:
            # 清空特定项目
            keys_to_delete = [
                key for key, entry in self.cache.items()
                if f"|{project_id}|" in key
            ]
            for key in keys_to_delete:
                del self.cache[key]
                if key in self.access_count:
                    del self.access_count[key]
            logger.info(f"🗑️ 已清空项目 {project_id} 的 {len(keys_to_delete)} 个缓存")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': sum(self.access_count.values()) / len(self.cache) if self.cache else 0,
            'total_accesses': sum(self.access_count.values())
        }


class QueryOptimizer:
    """查询优化器"""

    @staticmethod
    async def expand_query(query: str) -> List[str]:
        """查询扩展 - 生成相关查询变体"""
        expanded = [query]

        # 1. 同义词扩展
        synonyms_map = {
            '民族': ['族群', '种族', '民系'],
            '文化': ['习俗', '传统', '风俗'],
            '仪式': ['典礼', '礼仪', '祭祀'],
            '信仰': ['宗教', '信念', '崇拜'],
        }

        for word, synonyms in synonyms_map.items():
            if word in query:
                for synonym in synonyms:
                    expanded.append(query.replace(word, synonym))

        return expanded[:3]  # 最多返回3个变体

    @staticmethod
    def rewrite_query(query: str) -> str:
        """查询重写 - 优化查询表达"""
        # 去除冗余词
        stop_words = ['请问', '能否', '可以', '帮我', '我想']
        rewritten = query
        for word in stop_words:
            rewritten = rewritten.replace(word, '')

        return rewritten.strip()

    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """提取关键词"""
        # 简单实现：按空格和标点分词
        import re
        words = re.findall(r'\w+', query)
        # 过滤短词和常见词
        common_words = {'的', '了', '是', '在', '有', '和', '与', '对', '等', '个', '中'}
        keywords = [w for w in words if len(w) > 1 and w not in common_words]
        return keywords[:10]


class SourceSelector:
    """自适应检索源选择器"""

    def __init__(self):
        self.source_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'avg_latency': 0.0,
            'success_rate': 1.0,
            'quality_score': 0.5,
            'total_queries': 0
        })

    def select_sources(
        self,
        query: str,
        available_sources: List[str],
        max_sources: int = 5
    ) -> List[str]:
        """基于性能和查询类型选择最优检索源"""

        # 1. 根据查询类型推荐源
        query_lower = query.lower()
        recommended = set()

        # 知识图谱相关
        if any(word in query_lower for word in ['关系', '连接', '网络', '社会']):
            recommended.update(['lightrag', 'graphiti', 'graphrag', 'neo4j'])

        # 记忆和历史相关
        if any(word in query_lower for word in ['之前', '历史', '过去', '记得']):
            recommended.update(['cognee', 'mem0', 'khoj'])

        # 文档搜索
        if any(word in query_lower for word in ['文档', '资料', '文本', '内容']):
            recommended.update(['vector', 'keyword', 'quivr'])

        # 如果没有特定推荐，使用性能最好的
        if not recommended:
            # 按综合得分排序
            sorted_sources = sorted(
                available_sources,
                key=lambda s: self._calculate_source_score(s),
                reverse=True
            )
            return sorted_sources[:max_sources]

        # 补充到max_sources
        result = list(recommended & set(available_sources))
        if len(result) < max_sources:
            remaining = [s for s in available_sources if s not in result]
            sorted_remaining = sorted(
                remaining,
                key=lambda s: self._calculate_source_score(s),
                reverse=True
            )
            result.extend(sorted_remaining[:max_sources - len(result)])

        return result[:max_sources]

    def _calculate_source_score(self, source: str) -> float:
        """计算源的综合得分"""
        perf = self.source_performance[source]

        # 综合考虑延迟、成功率和质量
        latency_score = max(0, 1 - perf['avg_latency'] / 10.0)  # 10秒归一化
        success_score = perf['success_rate']
        quality_score = perf['quality_score']

        return (latency_score * 0.3 + success_score * 0.4 + quality_score * 0.3)

    def update_performance(
        self,
        source: str,
        latency: float,
        success: bool,
        quality_score: Optional[float] = None
    ):
        """更新源性能指标"""
        perf = self.source_performance[source]
        total = perf['total_queries']

        # 移动平均
        perf['avg_latency'] = (perf['avg_latency'] * total + latency) / (total + 1)
        perf['success_rate'] = (perf['success_rate'] * total + (1.0 if success else 0.0)) / (total + 1)

        if quality_score is not None:
            perf['quality_score'] = (perf['quality_score'] * total + quality_score) / (total + 1)

        perf['total_queries'] = total + 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return dict(self.source_performance)


class DeepRAGOptimizationService:
    """Deep RAG查询优化服务"""

    def __init__(self, db: Session):
        self.db = db
        self.deep_rag_service = DeepRAGService()
        self.query_cache = QueryCache(max_size=1000, ttl_seconds=3600)
        self.query_optimizer = QueryOptimizer()
        self.source_selector = SourceSelector()
        self.event_emitter = get_event_emitter()

        logger.info("✅ Deep RAG优化服务初始化完成")

    async def optimized_query(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int] = None,
        use_cache: bool = True,
        use_optimization: bool = True,
        max_sources: int = 5,
        top_k: int = 5,
        llm_provider: str = 'anthropic'
    ) -> Dict[str, Any]:
        """
        优化的深度RAG查询

        Args:
            query: 用户查询
            session_id: 会话ID
            project_id: 项目ID
            use_cache: 是否使用缓存
            use_optimization: 是否使用查询优化
            max_sources: 最多使用的检索源数量
            top_k: 每源返回结果数
            llm_provider: LLM提供商

        Returns:
            查询结果字典
        """
        start_time = datetime.utcnow()

        # 发送查询开始事件
        await self.event_emitter.emit("rag.query.start", {
            "session_id": session_id,
            "project_id": project_id,
            "query": query[:100],
            "timestamp": start_time.isoformat()
        })

        try:
            # 1. 查询优化
            optimized_query = query
            expanded_queries = [query]
            keywords = []

            if use_optimization:
                optimized_query = self.query_optimizer.rewrite_query(query)
                expanded_queries = await self.query_optimizer.expand_query(optimized_query)
                keywords = self.query_optimizer.extract_keywords(optimized_query)

                logger.info(f"📝 查询优化: '{query}' -> '{optimized_query}'")
                logger.info(f"🔍 扩展查询: {expanded_queries}")
                logger.info(f"🏷️ 关键词: {keywords}")

            # 2. 智能源选择
            available_sources = list(self.deep_rag_service.retrieval_sources.keys())
            selected_sources = self.source_selector.select_sources(
                query=optimized_query,
                available_sources=available_sources,
                max_sources=max_sources
            )

            logger.info(f"📡 选择检索源: {selected_sources}")

            # 发送检索进度事件
            await self.event_emitter.emit("rag.retrieval.progress", {
                "session_id": session_id,
                "project_id": project_id,
                "phase": "source_selection",
                "selected_sources": selected_sources,
                "timestamp": datetime.utcnow().isoformat()
            })

            # 3. 缓存检查
            cached_result = None
            if use_cache:
                cached_result = self.query_cache.get(
                    query=optimized_query,
                    project_id=project_id,
                    sources=selected_sources
                )

            if cached_result:
                logger.info("✅ 使用缓存结果")

                await self.event_emitter.emit("rag.query.complete", {
                    "session_id": session_id,
                    "project_id": project_id,
                    "cached": True,
                    "latency": (datetime.utcnow() - start_time).total_seconds(),
                    "timestamp": datetime.utcnow().isoformat()
                })

                return {
                    **cached_result,
                    'cached': True,
                    'optimized_query': optimized_query,
                    'keywords': keywords
                }

            # 4. 执行检索
            await self.event_emitter.emit("rag.retrieval.progress", {
                "session_id": session_id,
                "project_id": project_id,
                "phase": "retrieving",
                "timestamp": datetime.utcnow().isoformat()
            })

            # 对所有扩展查询并行检索
            retrieval_tasks = []
            for eq in expanded_queries[:2]:  # 最多2个扩展查询
                task = self.deep_rag_service.multi_source_retrieve(
                    query=eq,
                    project_id=project_id,
                    session_id=session_id,
                    top_k=top_k,
                    enabled_sources=selected_sources
                )
                retrieval_tasks.append(task)

            # 等待所有检索完成
            all_retrievals = await asyncio.gather(*retrieval_tasks)

            # 合并结果
            merged_results = self._merge_retrieval_results(all_retrievals)

            # 5. 融合排序
            await self.event_emitter.emit("rag.retrieval.progress", {
                "session_id": session_id,
                "project_id": project_id,
                "phase": "ranking",
                "timestamp": datetime.utcnow().isoformat()
            })

            fused_results = self.deep_rag_service.rank_and_fuse(
                multi_source_results=merged_results,
                fusion_method='rrf',
                top_k=top_k * 2  # 融合后取更多结果
            )

            # 6. 生成回答
            await self.event_emitter.emit("rag.retrieval.progress", {
                "session_id": session_id,
                "project_id": project_id,
                "phase": "generating",
                "timestamp": datetime.utcnow().isoformat()
            })

            result = await self.deep_rag_service.deep_chat(
                query=query,  # 使用原始查询
                session_id=session_id,
                project_id=project_id,
                use_context=True,
                top_k=top_k,
                enabled_sources=selected_sources,
                llm_provider=llm_provider
            )

            # 7. 质量评估
            quality_score = self._evaluate_result_quality(
                result=result,
                query=query,
                fused_results=fused_results
            )

            result['quality_score'] = quality_score
            result['optimized_query'] = optimized_query
            result['expanded_queries'] = expanded_queries
            result['keywords'] = keywords
            result['selected_sources'] = selected_sources
            result['cached'] = False

            # 8. 更新源性能
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()

            for source in selected_sources:
                self.source_selector.update_performance(
                    source=source,
                    latency=latency / len(selected_sources),
                    success=True,
                    quality_score=quality_score
                )

            # 9. 缓存结果
            if use_cache:
                self.query_cache.set(
                    query=optimized_query,
                    project_id=project_id,
                    sources=selected_sources,
                    result=result
                )

            # 10. 保存查询记录到数据库
            await self._save_query_record(
                query=query,
                session_id=session_id,
                project_id=project_id,
                result=result,
                latency=latency
            )

            # 发送完成事件
            await self.event_emitter.emit("rag.query.complete", {
                "session_id": session_id,
                "project_id": project_id,
                "cached": False,
                "latency": latency,
                "quality_score": quality_score,
                "timestamp": end_time.isoformat()
            })

            logger.info(f"✅ 优化查询完成: latency={latency:.2f}s, quality={quality_score:.2f}")

            return result

        except Exception as e:
            logger.error(f"❌ 优化查询失败: {e}")
            import traceback
            traceback.print_exc()

            # 发送错误事件
            await self.event_emitter.emit("rag.query.error", {
                "session_id": session_id,
                "project_id": project_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

            # 更新源失败率
            for source in selected_sources:
                self.source_selector.update_performance(
                    source=source,
                    latency=10.0,
                    success=False
                )

            raise

    def _merge_retrieval_results(self, all_retrievals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个检索结果"""
        merged = {
            'results': {},
            'metadata': {
                'total_sources': 0,
                'successful_sources': 0,
                'total_results': 0,
                'total_citations': 0
            },
            'citations': []
        }

        # 合并所有源的结果
        for retrieval in all_retrievals:
            for source_name, source_data in retrieval['results'].items():
                if source_name not in merged['results']:
                    merged['results'][source_name] = source_data
                else:
                    # 合并同一源的多个结果
                    existing = merged['results'][source_name]
                    if 'results' in existing and 'results' in source_data:
                        existing['results'].extend(source_data['results'])

            merged['citations'].extend(retrieval.get('citations', []))

        # 更新统计
        merged['metadata']['total_sources'] = len(merged['results'])
        merged['metadata']['successful_sources'] = len([
            r for r in merged['results'].values() if 'error' not in r
        ])
        merged['metadata']['total_results'] = sum(
            len(r.get('results', [])) for r in merged['results'].values() if isinstance(r, dict)
        )
        merged['metadata']['total_citations'] = len(merged['citations'])

        return merged

    def _evaluate_result_quality(
        self,
        result: Dict[str, Any],
        query: str,
        fused_results: List[Dict[str, Any]]
    ) -> float:
        """评估结果质量"""
        score = 0.0

        # 1. 答案长度（最多0.2分）
        answer = result.get('answer', '')
        score += min(len(answer) / 500.0, 0.2)

        # 2. 引用数量（最多0.3分）
        citations = result.get('citations', [])
        score += min(len(citations) / 10.0, 0.3)

        # 3. 检索源多样性（最多0.2分）
        sources_used = result.get('sources_used', [])
        score += min(len(sources_used) / 5.0, 0.2)

        # 4. 置信度（最多0.3分）
        confidence = result.get('confidence', 0.0)
        score += confidence * 0.3

        return min(score, 1.0)

    async def _save_query_record(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int],
        result: Dict[str, Any],
        latency: float
    ):
        """保存查询记录到数据库"""
        try:
            from app.models.rag_query import RAGQuery

            query_record = RAGQuery(
                project_id=project_id,
                session_id=session_id,
                query_text=query,
                optimized_query=result.get('optimized_query', query),
                answer=result.get('answer', ''),
                sources_used=json.dumps(result.get('sources_used', [])),
                citations_count=len(result.get('citations', [])),
                confidence=result.get('confidence', 0.0),
                quality_score=result.get('quality_score', 0.0),
                latency=latency,
                cached=result.get('cached', False),
                created_at=datetime.utcnow()
            )

            self.db.add(query_record)
            self.db.commit()

            logger.info(f"💾 查询记录已保存: id={query_record.id}")

        except Exception as e:
            logger.error(f"❌ 保存查询记录失败: {e}")
            self.db.rollback()

    def invalidate_cache(self, project_id: Optional[int] = None):
        """失效缓存"""
        self.query_cache.invalidate(project_id)

    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        return {
            'cache_stats': self.query_cache.get_stats(),
            'source_performance': self.source_selector.get_performance_stats(),
            'service': 'deep_rag_optimization'
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        base_health = self.deep_rag_service.health_check()
        return {
            **base_health,
            'optimization_enabled': True,
            'cache_size': len(self.query_cache.cache),
            'tracked_sources': len(self.source_selector.source_performance)
        }


# 全局单例
_optimization_service = None


def get_deep_rag_optimization_service(db: Session) -> DeepRAGOptimizationService:
    """获取优化服务单例"""
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = DeepRAGOptimizationService(db)
    return _optimization_service
