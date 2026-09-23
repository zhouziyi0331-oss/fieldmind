"""
RAG生成服务

检索增强生成（Retrieval-Augmented Generation）

核心功能：
- 智能检索相关内容
- 上下文组装和优化
- LLM生成有根据的答案
- 引用追踪和验证
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import json

from app.services.hybrid_retriever import HybridRetriever
from app.models.knowledge_graph import RAGSession, RAGQuery

logger = logging.getLogger(__name__)


class RAGGenerator:
    """
    RAG生成服务

    完整的检索-生成流程
    """

    def __init__(
        self,
        db: Session,
        retriever: HybridRetriever,
        llm_client
    ):
        self.db = db
        self.retriever = retriever
        self.llm = llm_client

    async def generate_answer(
        self,
        query: str,
        session_id: Optional[str] = None,
        retrieval_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成答案

        完整流程：
        1. 检索相关内容
        2. 组装上下文
        3. 生成答案
        4. 提取引用
        5. 保存记录
        """
        start_time = datetime.utcnow()

        # 1. 加载会话上下文
        session = None
        if session_id:
            session = self._get_or_create_session(session_id)

        # 2. 检索相关内容
        retrieval_start = datetime.utcnow()

        config = retrieval_config or {}
        retrieved = await self.retriever.retrieve(
            query,
            strategy=config.get('strategy', 'hybrid'),
            top_k=config.get('top_k', 10)
        )

        retrieval_time = (datetime.utcnow() - retrieval_start).total_seconds() * 1000

        logger.info(f"检索到 {len(retrieved)} 个相关内容，耗时 {retrieval_time:.0f}ms")

        # 3. 组装上下文
        context = self._assemble_context(retrieved, max_tokens=2000)

        # 4. 构建提示词
        prompt = self._build_prompt(query, context, session)

        # 5. LLM生成答案
        generation_start = datetime.utcnow()

        response = await self.llm.chat.completions.create(
            model=config.get('model', 'gpt-4'),
            messages=prompt,
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 1000)
        )

        answer = response.choices[0].message.content
        generation_time = (datetime.utcnow() - generation_start).total_seconds() * 1000

        # 6. 提取引用
        citations = self._extract_citations(answer, retrieved)

        # 7. 计算评估指标
        relevance_score = self._calculate_relevance(query, answer, retrieved)
        groundedness_score = self._calculate_groundedness(answer, retrieved)

        # 8. 保存查询记录
        query_record = self._save_query_record(
            query=query,
            retrieved=retrieved,
            answer=answer,
            citations=citations,
            session_id=session.id if session else None,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            relevance_score=relevance_score,
            groundedness_score=groundedness_score,
            model=config.get('model', 'gpt-4'),
            temperature=config.get('temperature', 0.7),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens
        )

        # 9. 更新会话
        if session:
            self._update_session(session, query, answer)

        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "answer": answer,
            "sources": citations,
            "retrieved_count": len(retrieved),
            "query_id": query_record.query_id,
            "metrics": {
                "retrieval_time_ms": retrieval_time,
                "generation_time_ms": generation_time,
                "total_time_ms": total_time,
                "relevance_score": relevance_score,
                "groundedness_score": groundedness_score
            },
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def _get_or_create_session(self, session_id: str) -> RAGSession:
        """获取或创建会话"""
        session = self.db.query(RAGSession).filter(
            RAGSession.session_id == session_id
        ).first()

        if not session:
            session = RAGSession(
                session_id=session_id,
                session_name=f"会话 {session_id[:8]}",
                context_window=[],
                retrieval_config={}
            )
            self.db.add(session)
            self.db.commit()

        return session

    def _assemble_context(self, retrieved: List[Dict], max_tokens: int = 2000) -> str:
        """
        组装上下文

        将检索结果组织成连贯的上下文，控制token数量
        """
        context_parts = []
        total_length = 0
        max_chars = max_tokens * 4  # 粗略估计

        for i, result in enumerate(retrieved, 1):
            content = result.get('content', '')
            source_info = ""

            # 添加来源信息
            if result.get('method') == 'graph':
                source_info = f"[实体: {result.get('entity_id', 'unknown')}]"
            else:
                source_info = f"[文档块: {i}]"

            part = f"{source_info}\n{content}\n"

            if total_length + len(part) > max_chars:
                break

            context_parts.append(part)
            total_length += len(part)

        return "\n".join(context_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        session: Optional[RAGSession]
    ) -> List[Dict[str, str]]:
        """构建LLM提示词"""
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的知识问答助手。基于提供的上下文回答用户的问题。

要求：
1. 只使用上下文中的信息回答
2. 如果上下文中没有相关信息，明确说"根据现有信息，我无法回答这个问题"
3. 在答案中标注信息来源，格式：[文档块: N] 或 [实体: XXX]
4. 回答要清晰、准确、有条理
5. 如果需要，可以引用多个来源综合回答"""
            }
        ]

        # 添加会话历史（如果有）
        if session and session.context_window:
            for turn in session.context_window[-5:]:  # 最近5轮对话
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })

        # 添加当前查询
        messages.append({
            "role": "user",
            "content": f"""上下文信息：
{context}

问题：{query}

请基于上下文回答问题。"""
        })

        return messages

    def _extract_citations(self, answer: str, retrieved: List[Dict]) -> List[Dict]:
        """
        提取引用

        从答案中识别引用标记，关联到检索结果
        """
        citations = []

        # 查找 [文档块: N] 格式的引用
        import re
        doc_refs = re.findall(r'\[文档块:\s*(\d+)\]', answer)

        for ref in doc_refs:
            idx = int(ref) - 1
            if 0 <= idx < len(retrieved):
                citations.append({
                    "type": "document",
                    "index": idx,
                    "chunk_id": retrieved[idx].get('chunk_id'),
                    "content": retrieved[idx].get('content', '')[:200]
                })

        # 查找 [实体: XXX] 格式的引用
        entity_refs = re.findall(r'\[实体:\s*([^\]]+)\]', answer)

        for ref in entity_refs:
            citations.append({
                "type": "entity",
                "entity_name": ref.strip()
            })

        return citations

    def _calculate_relevance(self, query: str, answer: str, retrieved: List[Dict]) -> float:
        """
        计算答案相关性

        简化版：检查答案是否直接回答了问题
        """
        # TODO: 实现更复杂的相关性评估
        if "无法回答" in answer or "不知道" in answer:
            return 0.3

        if len(answer) < 50:
            return 0.5

        return 0.8

    def _calculate_groundedness(self, answer: str, retrieved: List[Dict]) -> float:
        """
        计算答案基于事实的程度

        检查答案内容是否来源于检索结果
        """
        # 简化版：检查答案中有多少内容在检索结果中出现
        if not retrieved:
            return 0.0

        answer_words = set(answer.split())
        retrieved_words = set()

        for result in retrieved:
            retrieved_words.update(result.get('content', '').split())

        if not answer_words:
            return 0.0

        overlap = len(answer_words & retrieved_words)
        return min(overlap / len(answer_words), 1.0)

    def _save_query_record(
        self,
        query: str,
        retrieved: List[Dict],
        answer: str,
        citations: List[Dict],
        session_id: Optional[int],
        retrieval_time: float,
        generation_time: float,
        relevance_score: float,
        groundedness_score: float,
        model: str,
        temperature: float,
        prompt_tokens: int,
        completion_tokens: int
    ) -> RAGQuery:
        """保存查询记录"""
        query_record = RAGQuery(
            session_id=session_id,
            query_text=query,
            retrieved_chunks=[{
                "chunk_id": r.get('chunk_id'),
                "score": r.get('similarity', r.get('rrf_score', 0)),
                "method": r.get('method')
            } for r in retrieved],
            generated_answer=answer,
            answer_sources=citations,
            llm_model=model,
            llm_temperature=temperature,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            relevance_score=relevance_score,
            groundedness_score=groundedness_score,
            retrieval_time_ms=int(retrieval_time),
            generation_time_ms=int(generation_time),
            total_time_ms=int(retrieval_time + generation_time)
        )

        self.db.add(query_record)
        self.db.commit()

        return query_record

    def _update_session(self, session: RAGSession, query: str, answer: str):
        """更新会话上下文"""
        if not session.context_window:
            session.context_window = []

        # 添加新对话
        session.context_window.append({
            "role": "user",
            "content": query
        })
        session.context_window.append({
            "role": "assistant",
            "content": answer
        })

        # 限制窗口大小
        if len(session.context_window) > session.max_context_turns * 2:
            session.context_window = session.context_window[-session.max_context_turns * 2:]

        session.query_count += 1
        session.last_activity = datetime.utcnow()

        self.db.commit()

    async def stream_answer(
        self,
        query: str,
        session_id: Optional[str] = None,
        retrieval_config: Optional[Dict] = None
    ):
        """
        流式生成答案

        逐步返回答案内容
        """
        # 1. 检索（同步）
        config = retrieval_config or {}
        retrieved = await self.retriever.retrieve(
            query,
            strategy=config.get('strategy', 'hybrid'),
            top_k=config.get('top_k', 10)
        )

        # 2. 组装上下文
        session = None
        if session_id:
            session = self._get_or_create_session(session_id)

        context = self._assemble_context(retrieved)
        prompt = self._build_prompt(query, context, session)

        # 3. 流式生成
        stream = await self.llm.chat.completions.create(
            model=config.get('model', 'gpt-4'),
            messages=prompt,
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 1000),
            stream=True
        )

        # 收集完整答案用于保存
        full_answer = ""

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_answer += content
                yield {
                    "type": "content",
                    "content": content
                }

        # 4. 发送引用
        citations = self._extract_citations(full_answer, retrieved)
        yield {
            "type": "citations",
            "citations": citations
        }

        # 5. 保存记录
        # TODO: 保存流式生成的记录
