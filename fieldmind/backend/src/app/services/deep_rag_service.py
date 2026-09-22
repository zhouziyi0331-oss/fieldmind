"""
深度RAG对话系统 - Phase 3.6
Deep RAG Chat Service with Multi-Source Retrieval and Citation Tracing

功能特性：
1. 多路检索（向量+全文+图谱+关键词）
2. 引用溯源（答案标注来源文档和位置）
3. 多轮对话上下文记忆
4. 置信度评分
5. 多文档综合分析
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import asyncio
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class DeepRAGService:
    """深度RAG对话服务 - 统一多源检索"""

    def __init__(self):
        self.retrieval_sources = {}
        self.conversation_history = defaultdict(list)  # session_id -> messages
        self._init_retrieval_sources()

    def _init_retrieval_sources(self):
        """初始化所有检索源"""

        # 1. ChromaDB向量检索
        try:
            from app.core.rag_engine import rag_engine
            self.retrieval_sources['vector'] = rag_engine
            logger.info("✅ 向量检索源已加载 (ChromaDB + FlagEmbedding)")
        except Exception as e:
            logger.warning(f"⚠️ 向量检索源加载失败: {e}")

        # 2. Cognee记忆检索
        try:
            from app.services.cognee_service import get_cognee_service
            self.retrieval_sources['cognee'] = get_cognee_service()
            logger.info("✅ Cognee记忆检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Cognee检索源加载失败: {e}")

        # 3. LightRAG知识图谱检索
        try:
            from app.services.lightrag_service import get_lightrag_service
            self.retrieval_sources['lightrag'] = get_lightrag_service()
            logger.info("✅ LightRAG知识图谱检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ LightRAG检索源加载失败: {e}")

        # 4. Mem0长记忆检索
        try:
            from app.services.mem0_service import Mem0Service
            self.retrieval_sources['mem0'] = Mem0Service()
            logger.info("✅ Mem0长记忆检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Mem0检索源加载失败: {e}")

        # 5. Graphiti时态图谱检索
        try:
            from app.services.graphiti_service import get_graphiti_service
            self.retrieval_sources['graphiti'] = get_graphiti_service()
            logger.info("✅ Graphiti时态图谱检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Graphiti检索源加载失败: {e}")

        # 6. GraphRAG社区检索
        try:
            from app.services.graphrag_service import get_graphrag_service
            self.retrieval_sources['graphrag'] = get_graphrag_service()
            logger.info("✅ GraphRAG社区检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ GraphRAG检索源加载失败: {e}")

        # 7. Khoj增量检索
        try:
            from app.services.khoj_service import get_khoj_service
            self.retrieval_sources['khoj'] = get_khoj_service()
            logger.info("✅ Khoj增量检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Khoj检索源加载失败: {e}")

        # 8. Quivr第二大脑检索
        try:
            from app.services.quivr_service import get_quivr_service
            self.retrieval_sources['quivr'] = get_quivr_service()
            logger.info("✅ Quivr第二大脑检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Quivr检索源加载失败: {e}")

        # 9. Neo4j原生图谱检索
        try:
            from app.services.knowledge_graph_service import knowledge_graph_service
            self.retrieval_sources['neo4j'] = knowledge_graph_service
            logger.info("✅ Neo4j知识图谱检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j检索源加载失败: {e}")

        # 10. 关键词全文检索
        try:
            from app.services.keyword_search_service import keyword_search_service
            self.retrieval_sources['keyword'] = keyword_search_service
            logger.info("✅ 关键词全文检索源已加载")
        except Exception as e:
            logger.warning(f"⚠️ 关键词检索源加载失败: {e}")

        logger.info(f"📊 检索源初始化完成，共 {len(self.retrieval_sources)} 个可用源")

    async def multi_source_retrieve(
        self,
        query: str,
        project_id: Optional[int] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
        enabled_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        多源并行检索

        Args:
            query: 查询问题
            project_id: 项目ID
            session_id: 会话ID
            top_k: 每个源返回的Top K结果
            enabled_sources: 启用的检索源列表，None则启用所有

        Returns:
            {
                'results': {source_name: results},
                'metadata': {统计信息},
                'citations': [引用列表]
            }
        """
        logger.info(f"🔍 开始多源检索: query='{query[:50]}...', sources={len(self.retrieval_sources)}")

        results = {}
        citations = []

        # 确定要使用的检索源
        sources_to_use = enabled_sources if enabled_sources else list(self.retrieval_sources.keys())

        # 并行检索所有源
        tasks = []
        for source_name in sources_to_use:
            if source_name in self.retrieval_sources:
                task = self._retrieve_from_source(
                    source_name=source_name,
                    query=query,
                    project_id=project_id,
                    session_id=session_id,
                    top_k=top_k
                )
                tasks.append((source_name, task))

        # 等待所有检索完成
        for source_name, task in tasks:
            try:
                source_results = await task
                if source_results:
                    results[source_name] = source_results
                    # 提取引用
                    source_citations = self._extract_citations(source_name, source_results)
                    citations.extend(source_citations)
            except Exception as e:
                logger.error(f"❌ 从 {source_name} 检索失败: {e}")
                results[source_name] = {'error': str(e)}

        # 统计信息
        metadata = {
            'total_sources': len(sources_to_use),
            'successful_sources': len([r for r in results.values() if 'error' not in r]),
            'total_results': sum(len(r.get('results', [])) for r in results.values() if isinstance(r, dict)),
            'total_citations': len(citations),
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"✅ 多源检索完成: {metadata['successful_sources']}/{metadata['total_sources']} 成功")

        return {
            'results': results,
            'metadata': metadata,
            'citations': citations
        }

    async def _retrieve_from_source(
        self,
        source_name: str,
        query: str,
        project_id: Optional[int],
        session_id: Optional[str],
        top_k: int
    ) -> Dict[str, Any]:
        """从单个检索源获取结果"""

        source = self.retrieval_sources.get(source_name)
        if not source:
            return {'error': 'Source not available'}

        try:
            # 1. ChromaDB向量检索
            if source_name == 'vector':
                result = source.retrieve_documents(
                    query=query,
                    top_k=top_k,
                    project_id=project_id
                )
                return {
                    'results': result.get('documents', []),
                    'scores': result.get('distances', []),
                    'type': 'vector'
                }

            # 2. Cognee记忆检索
            elif source_name == 'cognee':
                memories = await source.recall_context(
                    query=query,
                    project_id=str(project_id) if project_id else None,
                    session_id=session_id,
                    search_type="insights",
                    top_k=top_k
                )
                return {
                    'results': [{'text': m, 'source': 'cognee'} for m in memories],
                    'type': 'memory'
                }

            # 3. LightRAG知识图谱检索
            elif source_name == 'lightrag':
                result = await source.query(
                    query_text=query,
                    project_id=str(project_id) if project_id else None,
                    mode="hybrid",
                    only_need_context=False,
                    top_k=top_k
                )
                return {
                    'results': [{'text': result, 'source': 'lightrag'}],
                    'type': 'knowledge_graph'
                }

            # 4. Mem0长记忆检索
            elif source_name == 'mem0':
                memories = source.search_memories(
                    project_id=project_id if project_id else 0,
                    query=query,
                    limit=top_k
                )
                return {
                    'results': [{'text': m.get('memory', str(m)), 'source': 'mem0'} for m in memories],
                    'type': 'long_memory'
                }

            # 5. Graphiti时态图谱检索
            elif source_name == 'graphiti':
                results = await source.search(
                    query=query,
                    project_id=str(project_id) if project_id else None,
                    num_results=top_k
                )
                return {
                    'results': [
                        {
                            'text': f"[{r.get('name', 'Unknown')}] {r.get('content', '')}",
                            'source': 'graphiti',
                            'metadata': r
                        }
                        for r in results
                    ],
                    'type': 'temporal_graph'
                }

            # 6. GraphRAG社区检索
            elif source_name == 'graphrag':
                result = await source.query(
                    query=query,
                    project_id=str(project_id) if project_id else None,
                    mode="global"
                )
                return {
                    'results': [{'text': result, 'source': 'graphrag'}],
                    'type': 'community_graph'
                }

            # 7. Khoj增量检索
            elif source_name == 'khoj':
                result = await source.search(
                    query=query,
                    project_id=str(project_id) if project_id else None,
                    limit=top_k
                )
                return {
                    'results': result.get('results', []),
                    'type': 'incremental'
                }

            # 8. Quivr第二大脑检索
            elif source_name == 'quivr':
                result = await source.ask(
                    question=query,
                    project_id=str(project_id) if project_id else None,
                    return_citations=True
                )
                return {
                    'results': [{'text': result.get('answer', ''), 'citations': result.get('citations', [])}],
                    'type': 'second_brain'
                }

            # 9. Neo4j原生图谱检索
            elif source_name == 'neo4j':
                # 搜索相关实体和关系
                entities = source.search_entities(query, limit=top_k)
                return {
                    'results': [
                        {
                            'text': f"{e.get('name', '')} ({e.get('type', '')}): {e.get('properties', {})}",
                            'source': 'neo4j',
                            'entity': e
                        }
                        for e in entities
                    ],
                    'type': 'native_graph'
                }

            # 10. 关键词全文检索
            elif source_name == 'keyword':
                results = source.search(
                    query=query,
                    project_id=project_id,
                    limit=top_k
                )
                return {
                    'results': results,
                    'type': 'fulltext'
                }

            else:
                return {'error': f'Unknown source: {source_name}'}

        except Exception as e:
            logger.error(f"❌ {source_name} 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def _extract_citations(self, source_name: str, source_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从检索结果中提取引用信息"""
        citations = []

        results = source_results.get('results', [])
        for idx, result in enumerate(results):
            if isinstance(result, dict):
                citation = {
                    'source': source_name,
                    'index': idx,
                    'text': result.get('text', str(result)),
                    'confidence': result.get('score', result.get('distance', 0.0)),
                    'metadata': result.get('metadata', {}),
                }

                # 添加文档来源信息
                if 'document_id' in result:
                    citation['document_id'] = result['document_id']
                if 'document_name' in result:
                    citation['document_name'] = result['document_name']
                if 'page' in result:
                    citation['page'] = result['page']
                if 'chunk_id' in result:
                    citation['chunk_id'] = result['chunk_id']

                citations.append(citation)

        return citations

    def rank_and_fuse(
        self,
        multi_source_results: Dict[str, Any],
        fusion_method: str = 'rrf',
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        融合多源检索结果并重排序

        Args:
            multi_source_results: 多源检索结果
            fusion_method: 融合方法 ('rrf', 'weighted', 'simple')
            top_k: 返回Top K结果

        Returns:
            排序后的结果列表
        """
        all_results = []

        # 收集所有结果
        for source_name, source_data in multi_source_results['results'].items():
            if 'error' in source_data:
                continue

            results = source_data.get('results', [])
            for idx, result in enumerate(results):
                if isinstance(result, dict):
                    all_results.append({
                        'source': source_name,
                        'source_rank': idx,
                        'text': result.get('text', str(result)),
                        'metadata': result.get('metadata', {}),
                        'original': result
                    })

        # RRF (Reciprocal Rank Fusion) 融合
        if fusion_method == 'rrf':
            k = 60  # RRF常数
            result_scores = defaultdict(float)
            result_data = {}

            for result in all_results:
                # 生成唯一标识（基于文本内容）
                result_id = hash(result['text'][:200])

                # RRF评分
                score = 1.0 / (k + result['source_rank'] + 1)
                result_scores[result_id] += score

                if result_id not in result_data:
                    result_data[result_id] = result

            # 排序
            sorted_results = sorted(
                result_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]

            return [
                {
                    **result_data[result_id],
                    'fusion_score': score
                }
                for result_id, score in sorted_results
            ]

        # 简单合并（按源排名）
        elif fusion_method == 'simple':
            return all_results[:top_k]

        else:
            logger.warning(f"⚠️ 未知融合方法: {fusion_method}，使用simple")
            return all_results[:top_k]

    async def deep_chat(
        self,
        query: str,
        session_id: str,
        project_id: Optional[int] = None,
        use_context: bool = True,
        top_k: int = 5,
        enabled_sources: Optional[List[str]] = None,
        llm_provider: str = 'anthropic'
    ) -> Dict[str, Any]:
        """
        深度RAG对话 - 主接口

        Args:
            query: 用户问题
            session_id: 会话ID
            project_id: 项目ID
            use_context: 是否使用对话历史上下文
            top_k: 检索Top K结果
            enabled_sources: 启用的检索源
            llm_provider: LLM提供商 ('anthropic', 'openai', 'ollama')

        Returns:
            {
                'answer': '回答',
                'citations': [引用列表],
                'confidence': 置信度,
                'sources_used': [使用的源],
                'context': '检索上下文'
            }
        """
        logger.info(f"💬 深度RAG对话: session={session_id}, query='{query[:50]}...'")

        # 1. 多源检索
        retrieval_result = await self.multi_source_retrieve(
            query=query,
            project_id=project_id,
            session_id=session_id,
            top_k=top_k,
            enabled_sources=enabled_sources
        )

        # 2. 融合排序
        fused_results = self.rank_and_fuse(
            multi_source_results=retrieval_result,
            fusion_method='rrf',
            top_k=top_k
        )

        # 3. 构建上下文
        context = self._build_context(fused_results, retrieval_result['citations'])

        # 4. 获取对话历史
        conversation_context = ""
        if use_context and session_id in self.conversation_history:
            recent_messages = self.conversation_history[session_id][-6:]  # 最近3轮
            conversation_context = "\n\n".join([
                f"{'用户' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
                for msg in recent_messages
            ])

        # 5. 生成回答
        answer_result = await self._generate_answer(
            query=query,
            context=context,
            conversation_context=conversation_context,
            llm_provider=llm_provider
        )

        # 6. 保存对话历史
        self.conversation_history[session_id].append({
            'role': 'user',
            'content': query,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.conversation_history[session_id].append({
            'role': 'assistant',
            'content': answer_result['answer'],
            'timestamp': datetime.utcnow().isoformat()
        })

        # 7. 计算置信度
        confidence = self._calculate_confidence(
            answer=answer_result['answer'],
            context=context,
            num_sources=retrieval_result['metadata']['successful_sources']
        )

        result = {
            'answer': answer_result['answer'],
            'citations': retrieval_result['citations'],
            'confidence': confidence,
            'sources_used': list(retrieval_result['results'].keys()),
            'context': context,
            'metadata': {
                'retrieval_stats': retrieval_result['metadata'],
                'fused_results_count': len(fused_results),
                'conversation_turns': len(self.conversation_history[session_id]) // 2
            }
        }

        logger.info(f"✅ 深度RAG对话完成: confidence={confidence:.2f}, sources={len(result['sources_used'])}")

        return result

    def _build_context(self, fused_results: List[Dict[str, Any]], citations: List[Dict[str, Any]]) -> str:
        """构建检索上下文"""
        context_parts = []

        for idx, result in enumerate(fused_results, 1):
            source = result.get('source', 'unknown')
            text = result.get('text', '')
            score = result.get('fusion_score', 0.0)

            context_parts.append(
                f"[来源{idx}: {source}, 相关度={score:.3f}]\n{text}\n"
            )

        return "\n---\n".join(context_parts)

    async def _generate_answer(
        self,
        query: str,
        context: str,
        conversation_context: str,
        llm_provider: str
    ) -> Dict[str, Any]:
        """生成回答"""

        # 构建提示词
        system_prompt = """你是FieldMind田野调查助手，基于用户上传的文档回答问题。

重要规则：
1. 仅基于提供的检索上下文回答
2. 明确引用来源（如"根据来源1..."）
3. 如果上下文不足以回答，明确说明
4. 保持学术严谨性
5. 对于民族学、人类学问题，提供深度分析"""

        user_prompt = f"""检索上下文：
{context}

对话历史：
{conversation_context if conversation_context else '(无历史对话)'}

用户问题：
{query}

请基于上述上下文回答问题，并明确引用来源编号。"""

        try:
            # Anthropic Claude
            if llm_provider == 'anthropic':
                import os
                from anthropic import Anthropic

                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not configured")

                client = Anthropic(api_key=api_key)

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                answer = response.content[0].text

            # OpenAI GPT
            elif llm_provider == 'openai':
                import os
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not configured")

                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=4096,
                    temperature=0.7
                )

                answer = response.choices[0].message.content

            # Ollama本地
            elif llm_provider == 'ollama':
                import httpx

                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "qwen2.5:14b",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "stream": False
                        }
                    )

                    result = response.json()
                    answer = result.get('message', {}).get('content', '')

            else:
                raise ValueError(f"Unknown LLM provider: {llm_provider}")

            return {'answer': answer, 'provider': llm_provider}

        except Exception as e:
            logger.error(f"❌ LLM生成失败: {e}")
            return {
                'answer': f"抱歉，生成回答时出错：{str(e)}",
                'provider': llm_provider,
                'error': str(e)
            }

    def _calculate_confidence(self, answer: str, context: str, num_sources: int) -> float:
        """计算置信度评分"""

        confidence = 0.0

        # 1. 基于检索源数量（最多0.3分）
        confidence += min(num_sources / 10.0, 0.3)

        # 2. 基于上下文长度（最多0.2分）
        confidence += min(len(context) / 10000.0, 0.2)

        # 3. 基于回答长度（最多0.2分）
        confidence += min(len(answer) / 1000.0, 0.2)

        # 4. 基于引用标记（最多0.3分）
        citation_markers = ['来源', '根据', '参考', '引用', '[', '【']
        citation_count = sum(1 for marker in citation_markers if marker in answer)
        confidence += min(citation_count / 10.0, 0.3)

        return min(confidence, 1.0)

    def clear_conversation(self, session_id: str):
        """清除对话历史"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"🗑️ 已清除会话 {session_id} 的对话历史")

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history.get(session_id, [])

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'service': 'DeepRAGService',
            'available_sources': list(self.retrieval_sources.keys()),
            'total_sources': len(self.retrieval_sources),
            'active_conversations': len(self.conversation_history),
            'status': 'healthy'
        }


# 全局单例
_deep_rag_service = None


def get_deep_rag_service() -> DeepRAGService:
    """获取深度RAG服务单例"""
    global _deep_rag_service
    if _deep_rag_service is None:
        _deep_rag_service = DeepRAGService()
    return _deep_rag_service
