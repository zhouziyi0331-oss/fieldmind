"""
Agent 5: SynthesisAgent - 记忆综合与引用溯源
整合多层记忆系统，为最终报告生成提供上下文和引用支持
"""
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryLevel(str, Enum):
    """记忆层级"""
    SHORT_TERM = "short_term"    # 短期记忆（7天内）
    MID_TERM = "mid_term"        # 中期记忆（1个月内）
    LONG_TERM = "long_term"      # 长期记忆（持久化）


class SynthesisStrategy(str, Enum):
    """综合策略"""
    CONTEXT_AWARE = "context_aware"          # 上下文感知（适合对话）
    CITATION_FOCUSED = "citation_focused"    # 引用为中心（适合学术报告）
    MEMORY_ENHANCED = "memory_enhanced"      # 记忆增强（适合长期项目）
    COMPREHENSIVE = "comprehensive"          # 全面综合（使用所有内部服务）
    EXTERNAL_MEMORY_ENHANCED = "external_memory_enhanced"  # 外部记忆增强（Cognee/LightRAG/Mem0）
    FULL_STACK = "full_stack"               # 全栈模式（内部+外部所有服务）
    AUTO = "auto"                           # 自动选择策略


@dataclass
class MemoryFragment:
    """记忆片段"""
    content: str
    memory_type: str
    level: MemoryLevel
    relevance_score: float
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationInfo:
    """引用信息"""
    source_file: str
    document_type: str
    citation_text: str
    page_number: Optional[int] = None
    timestamp_range: Optional[str] = None
    speaker: Optional[str] = None
    chunk_index: Optional[int] = None
    relevance_score: float = 0.0


@dataclass
class SynthesisContext:
    """综合上下文"""
    project_id: int
    query: str
    memories: List[MemoryFragment] = field(default_factory=list)
    citations: List[CitationInfo] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    document_chunks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    """综合结果"""
    context: SynthesisContext
    system_prompt: str
    context_summary: str
    total_memories: int
    total_citations: int
    strategy_used: SynthesisStrategy
    processing_time: float = 0.0


class SynthesisAgent:
    """
    Agent 5: 记忆综合与引用溯源代理

    职责：
    1. 整合三层记忆系统（短期/中期/长期）
    2. 管理对话历史和上下文
    3. 提供精确的引用溯源信息
    4. 为报告生成准备完整的上下文

    集成服务：
    - MemoryService: 三层记忆管理
    - ConversationMemoryService: 对话上下文
    - LongMemoryService: 向量检索
    - MemoryInjector: 记忆注入系统提示词
    """

    def __init__(
        self,
        default_strategy: SynthesisStrategy = SynthesisStrategy.AUTO,
        max_memories: int = 20,
        max_citations: int = 10,
        relevance_threshold: float = 0.6,
        enable_conversation_history: bool = True
    ):
        self.default_strategy = default_strategy
        self.max_memories = max_memories
        self.max_citations = max_citations
        self.relevance_threshold = relevance_threshold
        self.enable_conversation_history = enable_conversation_history

        # 懒加载服务（内部）
        self._memory_service = None
        self._conversation_memory_service = None
        self._long_memory_service = None
        self._memory_injector = None

        # 懒加载服务（外部记忆平台）
        self._mem0_service = None
        self._cognee_service = None
        self._lightrag_service = None
        self._neo4j_service = None

        # 懒加载服务（Skill演化记忆）
        self._skill_evolution_integration = None

        # 懒加载服务（外部知识关联 - Phase 4）
        self._external_knowledge_integration = None

    def _get_memory_service(self, db_session, project_id: int):
        """获取三层记忆服务（需要db和project_id）"""
        from app.services.memory_service import MemoryService
        return MemoryService(db=db_session, project_id=project_id)

    def _get_conversation_memory_service(self, db_session):
        """获取对话记忆服务"""
        if self._conversation_memory_service is None:
            from app.services.conversation_memory_service import ConversationMemoryService
            self._conversation_memory_service = ConversationMemoryService(db=db_session)
        return self._conversation_memory_service

    def _get_long_memory_service(self):
        """获取长期记忆服务（单例）"""
        if self._long_memory_service is None:
            from app.services.long_memory_service import LongMemoryService
            self._long_memory_service = LongMemoryService()
        return self._long_memory_service

    def _get_memory_injector(self, db_session, project_id: int):
        """获取记忆注入器（需要db和project_id）"""
        from app.services.memory_injector import MemoryInjector
        return MemoryInjector(db=db_session, project_id=project_id)

    def _get_mem0_service(self):
        """获取Mem0长记忆服务"""
        if self._mem0_service is None:
            from app.services.mem0_service import Mem0Service
            self._mem0_service = Mem0Service()
            logger.info("Mem0服务已加载")
        return self._mem0_service

    def _get_cognee_service(self):
        """获取Cognee知识图谱服务"""
        if self._cognee_service is None:
            from app.services.cognee_service import get_cognee_service
            self._cognee_service = get_cognee_service()
            logger.info("Cognee服务已加载")
        return self._cognee_service

    def _get_lightrag_service(self):
        """获取LightRAG图谱检索服务"""
        if self._lightrag_service is None:
            from app.services.lightrag_service import get_lightrag_service
            self._lightrag_service = get_lightrag_service()
            logger.info("LightRAG服务已加载")
        return self._lightrag_service

    def _get_neo4j_service(self):
        """获取Neo4j驾驭工程集成服务"""
        if self._neo4j_service is None:
            from app.services.graph_database_integration_v2 import GraphDatabaseIntegrationV2
            self._neo4j_service = GraphDatabaseIntegrationV2()
            logger.info("Neo4j驾驭工程服务已加载")
        return self._neo4j_service

    def _get_skill_evolution_integration(self):
        """获取Skill演化集成服务"""
        if self._skill_evolution_integration is None:
            from app.agents.skill_evolution_integration import get_skill_evolution_integration
            self._skill_evolution_integration = get_skill_evolution_integration()
            logger.info("🎯 Skill演化集成服务已加载")
        return self._skill_evolution_integration

    def _get_external_knowledge_integration(self):
        """获取外部知识关联集成服务（Phase 4）"""
        if self._external_knowledge_integration is None:
            from app.agents.external_knowledge_integration import get_external_knowledge_integration
            self._external_knowledge_integration = get_external_knowledge_integration()
            logger.info("🌐 外部知识关联集成服务已加载")
        return self._external_knowledge_integration

    def _select_strategy(
        self,
        query: str,
        include_conversation: bool,
        include_citations: bool
    ) -> SynthesisStrategy:
        """自动选择最佳策略"""
        if self.default_strategy != SynthesisStrategy.AUTO:
            return self.default_strategy

        # 关键词检测
        citation_keywords = ['引用', '来源', '出处', '文献', '参考', 'citation', 'source', 'reference']
        memory_keywords = ['记住', '之前', '上次', '历史', '记忆', 'remember', 'previous', 'history']

        has_citation_intent = any(kw in query.lower() for kw in citation_keywords)
        has_memory_intent = any(kw in query.lower() for kw in memory_keywords)

        # 策略选择逻辑
        if include_citations and has_citation_intent:
            return SynthesisStrategy.CITATION_FOCUSED
        elif has_memory_intent:
            return SynthesisStrategy.MEMORY_ENHANCED
        elif include_conversation:
            return SynthesisStrategy.CONTEXT_AWARE
        else:
            return SynthesisStrategy.COMPREHENSIVE

    def prepare_synthesis_context(
        self,
        project_id: int,
        query: str,
        db_session,
        strategy: Optional[SynthesisStrategy] = None,
        include_documents: bool = True,
        include_conversation: bool = True,
        include_citations: bool = True
    ) -> SynthesisResult:
        """
        准备综合上下文（同步版本 - 仅支持内部服务）

        注意：此方法不支持外部记忆平台，如需使用外部记忆请调用 prepare_synthesis_context_async()

        Args:
            project_id: 项目ID
            query: 用户查询
            db_session: 数据库会话
            strategy: 综合策略（None则自动选择）
            include_documents: 是否包含文档chunks
            include_conversation: 是否包含对话历史
            include_citations: 是否包含引用信息

        Returns:
            SynthesisResult: 综合结果
        """
        import time
        start_time = time.time()

        # 选择策略
        selected_strategy = strategy or self._select_strategy(
            query, include_conversation, include_citations
        )

        # 如果选择了外部记忆策略，给出警告并降级
        if selected_strategy in [SynthesisStrategy.EXTERNAL_MEMORY_ENHANCED, SynthesisStrategy.FULL_STACK]:
            logger.warning(f"同步方法不支持{selected_strategy.value}策略，降级为COMPREHENSIVE")
            selected_strategy = SynthesisStrategy.COMPREHENSIVE

        logger.info(f"使用综合策略: {selected_strategy.value}")

        # 创建上下文对象
        context = SynthesisContext(
            project_id=project_id,
            query=query
        )

        # 根据策略执行
        if selected_strategy == SynthesisStrategy.CONTEXT_AWARE:
            self._prepare_context_aware(context, db_session)
        elif selected_strategy == SynthesisStrategy.CITATION_FOCUSED:
            self._prepare_citation_focused(context, db_session)
        elif selected_strategy == SynthesisStrategy.MEMORY_ENHANCED:
            self._prepare_memory_enhanced(context, db_session)
        elif selected_strategy == SynthesisStrategy.COMPREHENSIVE:
            self._prepare_comprehensive(context, db_session, include_documents, include_conversation, include_citations)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(context, db_session)

        # 生成上下文摘要
        context_summary = self._generate_context_summary(context)

        processing_time = time.time() - start_time

        return SynthesisResult(
            context=context,
            system_prompt=system_prompt,
            context_summary=context_summary,
            total_memories=len(context.memories),
            total_citations=len(context.citations),
            strategy_used=selected_strategy,
            processing_time=processing_time
        )

    async def prepare_synthesis_context_async(
        self,
        project_id: int,
        query: str,
        db_session,
        strategy: Optional[SynthesisStrategy] = None,
        include_documents: bool = True,
        include_conversation: bool = True,
        include_citations: bool = True
    ) -> SynthesisResult:
        """
        准备综合上下文（异步版本 - 支持外部记忆平台）

        Args:
            project_id: 项目ID
            query: 用户查询
            db_session: 数据库会话
            strategy: 综合策略（None则自动选择）
            include_documents: 是否包含文档chunks
            include_conversation: 是否包含对话历史
            include_citations: 是否包含引用信息

        Returns:
            SynthesisResult: 综合结果
        """
        import time
        start_time = time.time()

        # 选择策略
        selected_strategy = strategy or self._select_strategy(
            query, include_conversation, include_citations
        )
        logger.info(f"使用综合策略: {selected_strategy.value}")

        # 创建上下文对象
        context = SynthesisContext(
            project_id=project_id,
            query=query
        )

        # 根据策略执行（支持async）
        if selected_strategy == SynthesisStrategy.CONTEXT_AWARE:
            self._prepare_context_aware(context, db_session)
        elif selected_strategy == SynthesisStrategy.CITATION_FOCUSED:
            self._prepare_citation_focused(context, db_session)
        elif selected_strategy == SynthesisStrategy.MEMORY_ENHANCED:
            self._prepare_memory_enhanced(context, db_session)
        elif selected_strategy == SynthesisStrategy.COMPREHENSIVE:
            self._prepare_comprehensive(context, db_session, include_documents, include_conversation, include_citations)
        elif selected_strategy == SynthesisStrategy.EXTERNAL_MEMORY_ENHANCED:
            await self._prepare_external_memory_enhanced(context, db_session)
        elif selected_strategy == SynthesisStrategy.FULL_STACK:
            await self._prepare_full_stack(context, db_session, include_documents, include_conversation, include_citations)

        # 构建系统提示词
        system_prompt = self._build_system_prompt(context, db_session)

        # 生成上下文摘要
        context_summary = self._generate_context_summary(context)

        processing_time = time.time() - start_time

        return SynthesisResult(
            context=context,
            system_prompt=system_prompt,
            context_summary=context_summary,
            total_memories=len(context.memories),
            total_citations=len(context.citations),
            strategy_used=selected_strategy,
            processing_time=processing_time
        )

    def _prepare_context_aware(self, context: SynthesisContext, db_session):
        """上下文感知策略：重点对话历史和最近chunks"""
        logger.info("执行CONTEXT_AWARE策略")

        conv_service = self._get_conversation_memory_service(db_session)

        # 准备对话上下文
        conv_context = conv_service.prepare_context(
            project_id=context.project_id,
            query=context.query,
            include_documents=True,
            include_analyses=True,
            include_chunks=True
        )

        # 提取对话历史
        if 'conversation_history' in conv_context:
            context.conversation_history = conv_context['conversation_history']

        # 提取相关chunks
        if 'relevant_chunks' in conv_context:
            context.document_chunks = conv_context['relevant_chunks']

        # 收集短期记忆
        memory_service = self._get_memory_service(db_session, context.project_id)
        short_term_memories = memory_service.get_short_term_memories(
            limit=self.max_memories // 2
        )

        context.memories = [
            MemoryFragment(
                content=mem.content,
                memory_type=mem.memory_type,
                level=MemoryLevel.SHORT_TERM,
                relevance_score=0.8,
                source_type=mem.source_type,
                source_id=mem.source_id,
                timestamp=mem.created_at
            )
            for mem in short_term_memories
        ]

        logger.info(f"收集到 {len(context.memories)} 条短期记忆，{len(context.conversation_history)} 条对话历史")

    def _prepare_citation_focused(self, context: SynthesisContext, db_session):
        """引用为中心策略：重点提取引用信息"""
        logger.info("执行CITATION_FOCUSED策略")

        conv_service = self._get_conversation_memory_service(db_session)

        # 获取相关chunks（包含元数据）
        conv_context = conv_service.prepare_context(
            project_id=context.project_id,
            query=context.query,
            include_documents=True,
            include_analyses=False,
            include_chunks=True
        )

        if 'relevant_chunks' in conv_context:
            chunks = conv_context['relevant_chunks']
            context.document_chunks = chunks

            # 从chunks提取引用信息
            for chunk in chunks[:self.max_citations]:
                citation = self._extract_citation_from_chunk(chunk)
                if citation:
                    context.citations.append(citation)

        logger.info(f"收集到 {len(context.citations)} 条引用信息")

    def _prepare_memory_enhanced(self, context: SynthesisContext, db_session):
        """记忆增强策略：三层记忆全覆盖"""
        logger.info("执行MEMORY_ENHANCED策略")

        memory_service = self._get_memory_service(db_session, context.project_id)
        long_memory_service = self._get_long_memory_service()

        # 1. 短期记忆
        short_memories = memory_service.get_short_term_memories(
            limit=self.max_memories // 3
        )
        for mem in short_memories:
            context.memories.append(MemoryFragment(
                content=mem.content,
                memory_type=mem.memory_type,
                level=MemoryLevel.SHORT_TERM,
                relevance_score=0.8,
                source_type=mem.source_type,
                source_id=mem.source_id,
                timestamp=mem.created_at
            ))

        # 2. 中期记忆
        mid_memories = memory_service.get_mid_term_memories(
            limit=self.max_memories // 3
        )
        for mem in mid_memories:
            context.memories.append(MemoryFragment(
                content=mem.content,
                memory_type=mem.memory_type,
                level=MemoryLevel.MID_TERM,
                relevance_score=0.7,
                source_type=mem.source_type,
                source_id=mem.source_id,
                timestamp=mem.created_at
            ))

        # 3. 长期记忆（向量检索）
        long_memories = long_memory_service.search_long_term_memory(
            query=context.query,
            project_id=context.project_id,
            top_k=self.max_memories // 3,
            relevance_threshold=self.relevance_threshold
        )
        for mem in long_memories:
            context.memories.append(MemoryFragment(
                content=mem.get('content', ''),
                memory_type='long_term',
                level=MemoryLevel.LONG_TERM,
                relevance_score=mem.get('relevance_score', 0.6),
                metadata=mem
            ))

        logger.info(f"收集到三层记忆：短期{len(short_memories)}，中期{len(mid_memories)}，长期{len(long_memories)}")

    def _prepare_comprehensive(
        self,
        context: SynthesisContext,
        db_session,
        include_documents: bool,
        include_conversation: bool,
        include_citations: bool
    ):
        """全面综合策略：使用所有服务"""
        logger.info("执行COMPREHENSIVE策略 - 使用所有服务")

        # 1. 记忆增强部分
        self._prepare_memory_enhanced(context, db_session)

        # 2. 对话历史
        if include_conversation and self.enable_conversation_history:
            conv_service = self._get_conversation_memory_service(db_session)
            conv_context = conv_service.prepare_context(
                project_id=context.project_id,
                query=context.query,
                include_documents=include_documents,
                include_analyses=True,
                include_chunks=True
            )

            if 'conversation_history' in conv_context:
                context.conversation_history = conv_context['conversation_history']

            if 'relevant_chunks' in conv_context:
                context.document_chunks = conv_context['relevant_chunks']

        # 3. 引用信息
        if include_citations:
            for chunk in context.document_chunks[:self.max_citations]:
                citation = self._extract_citation_from_chunk(chunk)
                if citation:
                    context.citations.append(citation)

        logger.info(f"综合完成：{len(context.memories)}条记忆，{len(context.citations)}条引用，{len(context.conversation_history)}条对话")

    async def _prepare_external_memory_enhanced(
        self,
        context: SynthesisContext,
        db_session
    ):
        """外部记忆增强策略：调用Cognee/LightRAG/Mem0"""
        logger.info("执行EXTERNAL_MEMORY_ENHANCED策略 - 调用外部记忆平台")

        external_memories_count = {
            'mem0': 0,
            'cognee': 0,
            'lightrag': 0
        }

        # 1. Mem0长记忆检索
        try:
            mem0_service = self._get_mem0_service()
            if mem0_service and mem0_service.memory:
                mem0_results = mem0_service.search_memories(
                    project_id=context.project_id,
                    query=context.query,
                    limit=self.max_memories // 3
                )

                for mem in mem0_results:
                    memory_content = mem.get('memory', '') or mem.get('content', '')
                    if memory_content:
                        context.memories.append(MemoryFragment(
                            content=memory_content,
                            memory_type='external_mem0',
                            level=MemoryLevel.LONG_TERM,
                            relevance_score=mem.get('score', 0.7),
                            metadata={
                                'platform': 'mem0',
                                'mem0_id': mem.get('id'),
                                'source': mem.get('metadata', {})
                            }
                        ))
                        external_memories_count['mem0'] += 1

                logger.info(f"✅ Mem0检索: {external_memories_count['mem0']}条记忆")
        except Exception as e:
            logger.warning(f"⚠️ Mem0检索失败（非致命）: {e}")

        # 2. Cognee知识图谱检索
        try:
            cognee_service = self._get_cognee_service()
            cognee_results = await cognee_service.recall_context(
                query=context.query,
                project_id=str(context.project_id),
                search_type="insights",
                top_k=self.max_memories // 3
            )

            for insight in cognee_results:
                # Cognee返回的可能是对象或字符串
                insight_content = str(insight) if insight else ""
                if insight_content:
                    context.memories.append(MemoryFragment(
                        content=insight_content,
                        memory_type='external_cognee',
                        level=MemoryLevel.LONG_TERM,
                        relevance_score=0.8,
                        metadata={'platform': 'cognee', 'type': 'insight'}
                    ))
                    external_memories_count['cognee'] += 1

            logger.info(f"✅ Cognee检索: {external_memories_count['cognee']}条洞察")
        except Exception as e:
            logger.warning(f"⚠️ Cognee检索失败（非致命）: {e}")

        # 3. LightRAG图谱增强检索
        try:
            lightrag_service = self._get_lightrag_service()
            lightrag_context = await lightrag_service.query(
                query_text=context.query,
                project_id=str(context.project_id),
                mode="hybrid",
                only_need_context=True,
                top_k=5
            )

            if lightrag_context and len(lightrag_context.strip()) > 0:
                context.memories.append(MemoryFragment(
                    content=lightrag_context,
                    memory_type='external_lightrag',
                    level=MemoryLevel.LONG_TERM,
                    relevance_score=0.85,
                    metadata={
                        'platform': 'lightrag',
                        'mode': 'hybrid',
                        'length': len(lightrag_context)
                    }
                ))
                external_memories_count['lightrag'] += 1

            logger.info(f"✅ LightRAG检索: {external_memories_count['lightrag']}条上下文")
        except Exception as e:
            logger.warning(f"⚠️ LightRAG检索失败（非致命）: {e}")

        total_external = sum(external_memories_count.values())
        logger.info(f"🎉 外部记忆检索完成: 总计{total_external}条 (Mem0:{external_memories_count['mem0']}, Cognee:{external_memories_count['cognee']}, LightRAG:{external_memories_count['lightrag']})")

    async def _prepare_full_stack(
        self,
        context: SynthesisContext,
        db_session,
        include_documents: bool,
        include_conversation: bool,
        include_citations: bool
    ):
        """全栈策略：内部+外部所有服务"""
        logger.info("执行FULL_STACK策略 - 内部+外部所有服务")

        # 1. 先执行COMPREHENSIVE策略（内部所有服务）
        self._prepare_comprehensive(
            context, db_session,
            include_documents, include_conversation, include_citations
        )

        internal_count = len(context.memories)

        # 2. 再执行外部记忆增强
        await self._prepare_external_memory_enhanced(context, db_session)

        external_count = len(context.memories) - internal_count

        logger.info(f"🚀 全栈综合完成: 内部{internal_count}条 + 外部{external_count}条 = 总计{len(context.memories)}条记忆")

    def _extract_citation_from_chunk(self, chunk: Dict[str, Any]) -> Optional[CitationInfo]:
        """从chunk提取引用信息"""
        try:
            metadata = chunk.get('metadata', {})

            # 必须有source_file
            source_file = metadata.get('source_file') or metadata.get('file_name', '')
            if not source_file:
                return None

            document_type = metadata.get('document_type', 'unknown')

            # 构建引用文本
            citation_text = self._format_citation_text(metadata)

            return CitationInfo(
                source_file=source_file,
                document_type=document_type,
                citation_text=citation_text,
                page_number=metadata.get('page_number'),
                timestamp_range=metadata.get('timestamp_range'),
                speaker=metadata.get('speaker'),
                chunk_index=metadata.get('chunk_index'),
                relevance_score=chunk.get('score', 0.0)
            )
        except Exception as e:
            logger.warning(f"提取引用信息失败: {e}")
            return None

    def _format_citation_text(self, metadata: Dict[str, Any]) -> str:
        """格式化引用文本"""
        source_file = metadata.get('source_file', metadata.get('file_name', '未知来源'))
        doc_type = metadata.get('document_type', '')

        # PDF/DOCX格式
        if doc_type in ['pdf', 'docx']:
            page = metadata.get('page_number')
            if page:
                return f"[来源：{source_file} P{page}]"
            return f"[来源：{source_file}]"

        # 音频/视频格式
        elif doc_type in ['audio', 'video']:
            speaker = metadata.get('speaker', '')
            time_range = metadata.get('timestamp_range', '')
            if speaker and time_range:
                return f"[来源：{source_file} {speaker} {time_range}]"
            elif time_range:
                return f"[来源：{source_file} {time_range}]"
            return f"[来源：{source_file}]"

        # 默认格式
        return f"[来源：{source_file}]"

    def _build_system_prompt(self, context: SynthesisContext, db_session) -> str:
        """构建包含记忆的系统提示词"""
        try:
            # 使用MemoryInjector构建
            memory_injector = self._get_memory_injector(db_session, context.project_id)

            base_prompt = """你是FieldMind AI助手，专注于田野调查研究和数据分析。
你的回答应该：
1. 基于项目上下文和历史记忆
2. 引用具体的文档来源（使用提供的引用信息）
3. 保持学术严谨性和可溯源性
4. 结合短期、中期和长期记忆提供全面的答案"""

            system_prompt = memory_injector.build_system_prompt(
                base_prompt=base_prompt,
                user_query=context.query,
                include_short_term=True,
                include_mid_term=True,
                include_long_term=True,
                max_memories=self.max_memories
            )

            # 追加引用信息
            if context.citations:
                citation_section = "\n\n## 可用引用来源\n"
                for i, citation in enumerate(context.citations[:5], 1):
                    citation_section += f"{i}. {citation.citation_text}\n"
                system_prompt += citation_section

            return system_prompt

        except Exception as e:
            logger.error(f"构建系统提示词失败: {e}")
            return "你是FieldMind AI助手，专注于田野调查研究和数据分析。"

    def _generate_context_summary(self, context: SynthesisContext) -> str:
        """生成上下文摘要"""
        summary_parts = []

        summary_parts.append(f"项目ID: {context.project_id}")
        summary_parts.append(f"查询: {context.query}")

        if context.memories:
            memory_by_level = {}
            for mem in context.memories:
                level = mem.level.value
                memory_by_level[level] = memory_by_level.get(level, 0) + 1
            summary_parts.append(f"记忆: {dict(memory_by_level)}")

        if context.citations:
            summary_parts.append(f"引用: {len(context.citations)}条")

        if context.conversation_history:
            summary_parts.append(f"对话历史: {len(context.conversation_history)}轮")

        if context.document_chunks:
            summary_parts.append(f"文档片段: {len(context.document_chunks)}个")

        return " | ".join(summary_parts)

    def export_context_to_dict(self, result: SynthesisResult) -> Dict[str, Any]:
        """导出上下文为字典格式（供其他Agent使用）"""
        return {
            'project_id': result.context.project_id,
            'query': result.context.query,
            'system_prompt': result.system_prompt,
            'context_summary': result.context_summary,
            'memories': [
                {
                    'content': mem.content,
                    'type': mem.memory_type,
                    'level': mem.level.value,
                    'relevance': mem.relevance_score,
                    'timestamp': mem.timestamp.isoformat() if mem.timestamp else None
                }
                for mem in result.context.memories
            ],
            'citations': [
                {
                    'source': cit.source_file,
                    'type': cit.document_type,
                    'text': cit.citation_text,
                    'page': cit.page_number,
                    'timestamp': cit.timestamp_range,
                    'speaker': cit.speaker,
                    'relevance': cit.relevance_score
                }
                for cit in result.context.citations
            ],
            'conversation_history': result.context.conversation_history,
            'document_chunks': result.context.document_chunks,
            'strategy_used': result.strategy_used.value,
            'processing_time': result.processing_time,
            'stats': {
                'total_memories': result.total_memories,
                'total_citations': result.total_citations,
                'conversation_turns': len(result.context.conversation_history),
                'document_chunks': len(result.context.document_chunks)
            }
        }

    # ==================== Neo4j驾驭工程集成方法 ====================

    def _get_synthesis_neo4j_service(self):
        """获取SynthesisNeo4j服务（与驾驭工程集成）"""
        if not hasattr(self, '_synthesis_neo4j_service') or self._synthesis_neo4j_service is None:
            from app.services.synthesis_neo4j_service import get_synthesis_neo4j_service
            self._synthesis_neo4j_service = get_synthesis_neo4j_service()
            logger.info("🎯 SynthesisNeo4j驾驭工程服务已加载")
        return self._synthesis_neo4j_service

    async def build_knowledge_graph_from_context(
        self,
        project_id: int,
        context: SynthesisContext,
        enable_context_tree: bool = True,
        enable_timeline: bool = True,
        enable_theme_graph: bool = True,
        enable_keyword_network: bool = True
    ) -> Dict[str, Any]:
        """
        从综合上下文构建Neo4j知识图谱

        将记忆、引用、文档等信息转换为：
        1. 脉络树 (Context Tree)
        2. 时间线 (Timeline)
        3. 主题图谱 (Theme Graph)
        4. 关键词网络 (Keyword Network)

        Args:
            project_id: 项目ID
            context: 综合上下文
            enable_*: 各组件的开关

        Returns:
            构建结果统计
        """
        logger.info(f"🔨 开始从上下文构建Neo4j知识图谱: 项目{project_id}")

        neo4j_service = self._get_synthesis_neo4j_service()
        results = {
            'project_id': project_id,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }

        try:
            # 1. 构建脉络树
            if enable_context_tree and context.memories:
                from app.services.synthesis_neo4j_service import ContextNode

                # 提取根脉络（最高层级概念）
                root_context = ContextNode(
                    context_id=f"root_{project_id}_{datetime.utcnow().timestamp()}",
                    project_id=project_id,
                    title=context.query,  # 查询本身作为根脉络
                    description=f"根脉络：{context.query}",
                    level=0,
                    created_at=datetime.utcnow()
                )

                # 从记忆中提取子脉络
                sub_contexts = []
                for idx, mem in enumerate(context.memories[:10]):  # 取前10个记忆作为子脉络
                    sub_context = ContextNode(
                        context_id=f"sub_{project_id}_{idx}_{datetime.utcnow().timestamp()}",
                        project_id=project_id,
                        title=mem.content[:50],  # 记忆内容前50字作为标题
                        description=mem.content,
                        level=1,
                        parent_id=root_context.context_id,
                        created_at=mem.timestamp or datetime.utcnow(),
                        metadata={'memory_type': mem.memory_type, 'relevance': mem.relevance_score}
                    )
                    sub_contexts.append(sub_context)

                context_tree_result = neo4j_service.create_context_tree(
                    project_id=project_id,
                    root_context=root_context,
                    sub_contexts=sub_contexts
                )
                results['components']['context_tree'] = context_tree_result
                logger.info(f"  ✅ 脉络树构建完成: {context_tree_result}")

            # 2. 构建时间线
            if enable_timeline and (context.memories or context.citations):
                from app.services.synthesis_neo4j_service import TimelineEvent

                events = []

                # 从记忆创建事件
                for idx, mem in enumerate(context.memories):
                    if mem.timestamp:
                        event = TimelineEvent(
                            event_id=f"event_mem_{project_id}_{idx}",
                            project_id=project_id,
                            timestamp=mem.timestamp,
                            event_type="memory_created",
                            title=f"{mem.memory_type}记忆",
                            description=mem.content[:100],
                            metadata={'memory_type': mem.memory_type, 'source': mem.source_type}
                        )
                        events.append(event)

                # 从引用创建事件
                for idx, cit in enumerate(context.citations):
                    event = TimelineEvent(
                        event_id=f"event_cit_{project_id}_{idx}",
                        project_id=project_id,
                        timestamp=datetime.utcnow(),  # 引用发现时间
                        event_type="citation_found",
                        title=f"发现引用: {cit.source_file}",
                        description=cit.citation_text,
                        metadata={'document_type': cit.document_type, 'page': cit.page_number}
                    )
                    events.append(event)

                if events:
                    timeline_result = neo4j_service.create_timeline(
                        project_id=project_id,
                        events=events
                    )
                    results['components']['timeline'] = timeline_result
                    logger.info(f"  ✅ 时间线构建完成: {timeline_result}")

            # 3. 构建主题图谱
            if enable_theme_graph and context.memories:
                from app.services.synthesis_neo4j_service import ThemeNode

                # 从记忆类型提取主题
                theme_types = {}
                for mem in context.memories:
                    if mem.memory_type not in theme_types:
                        theme_types[mem.memory_type] = []
                    theme_types[mem.memory_type].append(mem)

                themes = []
                for theme_type, mems in theme_types.items():
                    theme = ThemeNode(
                        theme_id=f"theme_{project_id}_{theme_type}",
                        project_id=project_id,
                        name=theme_type,
                        description=f"{theme_type}类型的记忆集合",
                        importance=len(mems) / len(context.memories),  # 根据数量计算重要性
                        related_keywords=[],
                        metadata={'count': len(mems)}
                    )
                    themes.append(theme)

                # 构建主题间关系（相邻记忆类型视为相关）
                relationships = []
                theme_list = list(theme_types.keys())
                for i in range(len(theme_list) - 1):
                    relationships.append({
                        'from': f"theme_{project_id}_{theme_list[i]}",
                        'to': f"theme_{project_id}_{theme_list[i+1]}",
                        'type': 'RELATES_TO',
                        'weight': 0.5
                    })

                if themes:
                    theme_graph_result = neo4j_service.create_theme_graph(
                        project_id=project_id,
                        themes=themes,
                        relationships=relationships
                    )
                    results['components']['theme_graph'] = theme_graph_result
                    logger.info(f"  ✅ 主题图谱构建完成: {theme_graph_result}")

            # 4. 构建关键词网络
            if enable_keyword_network and context.document_chunks:
                from app.services.synthesis_neo4j_service import KeywordNode
                import re

                # 简单关键词提取（实际应用中可使用NLP工具）
                keyword_freq = {}
                for chunk in context.document_chunks:
                    text = chunk.get('text', '')
                    # 提取中文词（2-4字）和英文单词
                    words = re.findall(r'[一-龥]{2,4}|[a-zA-Z]{3,}', text)
                    for word in words:
                        keyword_freq[word] = keyword_freq.get(word, 0) + 1

                # 取频率最高的前20个关键词
                top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]

                keywords = []
                for kw, freq in top_keywords:
                    keyword_node = KeywordNode(
                        keyword=kw,
                        project_id=project_id,
                        frequency=freq,
                        context_ids=[],
                        metadata={'extracted_from': 'document_chunks'}
                    )
                    keywords.append(keyword_node)

                # 构建共现关系（简化版）
                co_occurrences = []
                for i in range(len(keywords) - 1):
                    co_occurrences.append({
                        'keyword1': keywords[i].keyword,
                        'keyword2': keywords[i+1].keyword,
                        'count': min(keywords[i].frequency, keywords[i+1].frequency)
                    })

                if keywords:
                    keyword_network_result = neo4j_service.create_keyword_network(
                        project_id=project_id,
                        keywords=keywords,
                        co_occurrences=co_occurrences
                    )
                    results['components']['keyword_network'] = keyword_network_result
                    logger.info(f"  ✅ 关键词网络构建完成: {keyword_network_result}")

            logger.info(f"🎉 Neo4j知识图谱构建完成: {len(results['components'])}个组件")
            results['success'] = True
            return results

        except Exception as e:
            logger.error(f"❌ Neo4j知识图谱构建失败: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
            return results

    async def query_knowledge_graph(
        self,
        project_id: int,
        query_type: str,  # 'context_tree', 'timeline', 'theme_graph', 'keyword_network', 'overview'
        **kwargs
    ) -> Dict[str, Any]:
        """
        查询Neo4j知识图谱

        Args:
            project_id: 项目ID
            query_type: 查询类型
            **kwargs: 查询参数

        Returns:
            查询结果
        """
        logger.info(f"🔍 查询Neo4j知识图谱: 项目{project_id}, 类型={query_type}")

        neo4j_service = self._get_synthesis_neo4j_service()

        try:
            if query_type == 'context_tree':
                root_id = kwargs.get('root_context_id')
                if not root_id:
                    return {'error': 'root_context_id is required for context_tree query'}
                return neo4j_service.query_context_tree(project_id, root_id)

            elif query_type == 'timeline':
                return neo4j_service.query_timeline(
                    project_id=project_id,
                    start_time=kwargs.get('start_time'),
                    end_time=kwargs.get('end_time'),
                    event_type=kwargs.get('event_type')
                )

            elif query_type == 'theme_graph':
                return neo4j_service.query_theme_graph(
                    project_id=project_id,
                    center_theme_id=kwargs.get('center_theme_id'),
                    max_depth=kwargs.get('max_depth', 2)
                )

            elif query_type == 'keyword_network':
                return neo4j_service.query_keyword_network(
                    project_id=project_id,
                    keyword=kwargs.get('keyword'),
                    min_frequency=kwargs.get('min_frequency', 1)
                )

            elif query_type == 'overview':
                return neo4j_service.get_project_knowledge_graph(project_id)

            else:
                return {'error': f'Unknown query_type: {query_type}'}

        except Exception as e:
            logger.error(f"❌ 知识图谱查询失败: {e}", exc_info=True)
            return {'error': str(e)}

    # ==================== Skill演化记忆集成 ====================

    async def track_skill_execution(
        self,
        db_session,
        skill_id: int,
        project_id: int,
        execution_result: Dict[str, Any]
    ) -> None:
        """
        追踪Skill执行并记录到演化记忆系统

        Args:
            db_session: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            execution_result: 执行结果
        """
        skill_evolution = self._get_skill_evolution_integration()
        await skill_evolution.track_skill_execution(
            db=db_session,
            skill_id=skill_id,
            project_id=project_id,
            execution_result=execution_result
        )

    async def detect_and_record_skill_changes(
        self,
        db_session,
        skill_id: int,
        project_id: int,
        current_content: str,
        change_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        检测Skill变更并自动创建新版本

        Args:
            db_session: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            current_content: 当前Skill内容
            change_context: 变更上下文

        Returns:
            Optional[Dict]: 如果创建了新版本，返回版本信息
        """
        skill_evolution = self._get_skill_evolution_integration()
        new_version = await skill_evolution.auto_detect_skill_changes(
            db=db_session,
            skill_id=skill_id,
            project_id=project_id,
            current_content=current_content,
            change_context=change_context
        )

        if new_version:
            logger.info(f"🎯 自动记录Skill变更: v{new_version.version_number}")
            return new_version.to_dict()
        return None

    async def get_skill_evolution_summary(
        self,
        db_session,
        skill_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取Skill的演化历史摘要

        Args:
            db_session: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            Dict: 演化摘要
        """
        skill_evolution = self._get_skill_evolution_integration()
        return await skill_evolution.get_skill_evolution_summary(
            db=db_session,
            skill_id=skill_id,
            project_id=project_id
        )

    async def suggest_skill_optimization(
        self,
        db_session,
        skill_id: int,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        基于使用统计生成Skill优化建议

        Args:
            db_session: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            List[Dict]: 优化建议列表
        """
        skill_evolution = self._get_skill_evolution_integration()
        return await skill_evolution.suggest_skill_optimization(
            db=db_session,
            skill_id=skill_id,
            project_id=project_id
        )

    async def export_skill_evolution_to_cognee(
        self,
        db_session,
        skill_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        将Skill演化历史导出到Cognee知识图谱

        Args:
            db_session: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            Dict: 导出结果
        """
        logger.info(f"📤 导出Skill演化历史到Cognee: skill_id={skill_id}")

        # 1. 获取演化历史数据
        skill_evolution = self._get_skill_evolution_integration()
        export_data = await skill_evolution.export_skill_evolution_to_cognee(
            db=db_session,
            skill_id=skill_id,
            project_id=project_id
        )

        if not export_data.get('success'):
            return export_data

        # 2. 存储到Cognee知识图谱
        try:
            cognee_service = self._get_cognee_service()
            knowledge_entries = export_data['knowledge_entries']

            # 将每个knowledge entry作为文本存储到Cognee
            for entry in knowledge_entries:
                entry_text = f"""
Skill Evolution Entry:
Type: {entry['type']}
ID: {entry['id']}
Name: {entry.get('name', entry.get('version_number', 'N/A'))}
Data: {entry}
"""
                await cognee_service.add_text(
                    text=entry_text,
                    metadata={
                        'type': entry['type'],
                        'skill_id': skill_id,
                        'project_id': project_id,
                        'entry_id': entry['id']
                    }
                )

            logger.info(f"✅ 成功导出 {len(knowledge_entries)} 个Skill演化条目到Cognee")

            return {
                'success': True,
                'skill_id': skill_id,
                'entries_exported': len(knowledge_entries),
                'cognee_storage': 'completed'
            }

        except Exception as e:
            logger.error(f"❌ 导出到Cognee失败: {e}")
            return {
                'success': False,
                'skill_id': skill_id,
                'error': str(e)
            }

    # ==================== Phase 4: 外部知识关联方法 ====================

    async def retrieve_thinking_patterns_cross_project(
        self,
        db_session,
        current_project_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        跨项目检索思维模式（不是记忆）

        Args:
            db_session: 数据库会话
            current_project_id: 当前项目ID
            context: 上下文信息

        Returns:
            Dict: 检索到的思维模式
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.retrieve_thinking_patterns_cross_project(
            db=db_session,
            current_project_id=current_project_id,
            context=context
        )

    async def find_applicable_patterns(
        self,
        db_session,
        project_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据当前上下文查找适用的思维模式

        Args:
            db_session: 数据库会话
            project_id: 项目ID
            context: 当前上下文

        Returns:
            Dict: 适用的思维模式
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.find_applicable_patterns_for_context(
            db=db_session,
            project_id=project_id,
            context=context
        )

    async def extract_and_update_skill_knowledge(
        self,
        db_session,
        project_id: int,
        skill_id: Optional[str],
        execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从项目执行中提取思维模式并更新到Skill知识库

        Args:
            db_session: 数据库会话
            project_id: 项目ID
            skill_id: Skill ID
            execution_data: 执行数据

        Returns:
            Dict: 更新结果
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.extract_and_update_skill_knowledge(
            db=db_session,
            project_id=project_id,
            skill_id=skill_id,
            execution_data=execution_data
        )

    async def sync_patterns_to_skill_knowledge(
        self,
        db_session,
        project_id: int
    ) -> Dict[str, Any]:
        """
        批量同步思维模式到Skill知识库

        Args:
            db_session: 数据库会话
            project_id: 项目ID

        Returns:
            Dict: 同步结果
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.sync_patterns_to_skill_knowledge_batch(
            db=db_session,
            project_id=project_id
        )

    async def get_skill_knowledge_base(
        self,
        db_session,
        project_id: int,
        skill_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取Skill知识库内容

        Args:
            db_session: 数据库会话
            project_id: 项目ID
            skill_id: Skill ID (optional)

        Returns:
            Dict: 知识库内容
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.get_skill_knowledge_base(
            db=db_session,
            project_id=project_id,
            skill_id=skill_id
        )

    async def add_domain_knowledge(
        self,
        db_session,
        domain: str,
        topic: str,
        knowledge_content: str,
        source_type: str = "manual_input",
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加领域知识作为常识背景（不影响决策/分析/报告）

        Args:
            db_session: 数据库会话
            domain: 领域
            topic: 主题
            knowledge_content: 知识内容
            source_type: 来源类型
            source_url: 来源URL

        Returns:
            Dict: 添加结果（包含使用约束警告）
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.add_domain_knowledge_as_background(
            db=db_session,
            domain=domain,
            topic=topic,
            knowledge_content=knowledge_content,
            source_type=source_type,
            source_url=source_url
        )

    async def query_domain_knowledge(
        self,
        db_session,
        domain: Optional[str],
        topic: Optional[str]
    ) -> Dict[str, Any]:
        """
        查询领域知识（仅用于显示，不影响决策）

        Args:
            db_session: 数据库会话
            domain: 领域
            topic: 主题

        Returns:
            Dict: 领域知识（带使用约束说明）
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.query_domain_knowledge_for_context(
            db=db_session,
            domain=domain,
            topic=topic
        )

    async def track_thinking_pattern_usage(
        self,
        db_session,
        pattern_id: int,
        usage_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        追踪思维模式的使用结果

        Args:
            db_session: 数据库会话
            pattern_id: 模式ID
            usage_result: 使用结果

        Returns:
            Dict: 追踪结果
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.track_pattern_usage(
            db=db_session,
            pattern_id=pattern_id,
            usage_result=usage_result
        )

    async def validate_thinking_pattern(
        self,
        db_session,
        pattern_id: int,
        validation_result: bool,
        validator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        验证思维模式

        Args:
            db_session: 数据库会话
            pattern_id: 模式ID
            validation_result: 验证结果
            validator_id: 验证者ID

        Returns:
            Dict: 验证结果
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.validate_pattern(
            db=db_session,
            pattern_id=pattern_id,
            validation_result=validation_result,
            validator_id=validator_id
        )

    async def get_external_knowledge_summary(
        self,
        db_session,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取外部知识关联的综合摘要

        Args:
            db_session: 数据库会话
            project_id: 项目ID

        Returns:
            Dict: 综合摘要（包含思维模式、Skill知识库、领域知识统计）
        """
        external_knowledge = self._get_external_knowledge_integration()
        return await external_knowledge.get_external_knowledge_summary(
            db=db_session,
            project_id=project_id
        )

    async def generate_synthesis_insights(
        self,
        project_id: str,
        db_session,
        query: Optional[str] = None,
        include_business_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Phase 5核心方法：生成综合洞察并存储到synthesis_results表

        这是SynthesisAgent在Phase 5的新增核心功能：
        1. 调用business_analysis Skill运行15个分析服务
        2. 整合记忆系统、知识图谱、外部知识
        3. 进行综合决策和洞察生成
        4. 将所有决策数据存储到synthesis_results表（可验证、可追溯）

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            query: 分析查询（可选，用于上下文检索）
            include_business_analysis: 是否包含商业分析（默认True）

        Returns:
            综合洞察结果，包含：
            - key_insights: 关键洞察列表
            - decision_factors: 决策依据
            - recommendations: 建议事项
            - thinking_patterns: 应用的思维模式
            - skill_knowledge: 使用的Skill知识
            - domain_knowledge: 领域知识引用
            - applied_skills: 应用的Skills列表
            - memory_fragments: 相关记忆片段
            - knowledge_nodes: 知识节点引用
            - citations: 来源引用
            - context_summary: 上下文摘要
            - confidence_score: 综合置信度
            - synthesis_result_id: 存储在数据库中的记录ID
        """
        from datetime import datetime
        from sqlalchemy import text
        import json

        logger.info(f"🎯 开始生成综合洞察 - 项目: {project_id}")

        # 1. 运行15个商业分析服务（如果需要）
        business_insights = None
        if include_business_analysis:
            try:
                from app.services.skills.business_analysis import get_business_analysis_skill
                business_skill = get_business_analysis_skill()
                business_insights = await business_skill.execute(
                    project_id=project_id,
                    db_session=db_session,
                    force_refresh=False  # 使用缓存
                )
                logger.info(f"✅ 商业分析完成: {business_insights.get('analyses_run', 0)}个分析")
            except Exception as e:
                logger.warning(f"⚠️ 商业分析失败（非致命）: {e}")
                business_insights = {'error': str(e)}

        # 2. 获取记忆系统上下文
        synthesis_context = SynthesisContext(
            project_id=int(project_id),
            query=query or "生成项目综合报告",
            metadata={'phase': 5, 'purpose': 'synthesis_insights'}
        )

        # 使用COMPREHENSIVE策略获取内部记忆
        try:
            synthesis_result = await self.synthesize(
                context=synthesis_context,
                db_session=db_session,
                strategy=SynthesisStrategy.COMPREHENSIVE
            )
            logger.info(f"✅ 记忆综合完成: {synthesis_result.total_memories}条记忆, {synthesis_result.total_citations}条引用")
        except Exception as e:
            logger.warning(f"⚠️ 记忆综合失败（非致命）: {e}")
            synthesis_result = None

        # 3. 获取外部知识关联摘要（思维模式、Skill知识、领域知识）
        external_knowledge_summary = None
        try:
            external_knowledge_summary = await self.get_external_knowledge_summary(
                db_session=db_session,
                project_id=int(project_id)
            )
            logger.info(f"✅ 外部知识获取完成")
        except Exception as e:
            logger.warning(f"⚠️ 外部知识获取失败（非致命）: {e}")

        # 4. 生成综合洞察
        key_insights = []
        decision_factors = []
        recommendations = []

        # 从商业分析中提取洞察
        if business_insights and 'synthesis' in business_insights:
            synthesis = business_insights['synthesis']

            # 关键发现
            for finding in synthesis.get('key_findings', []):
                key_insights.append({
                    'source': 'business_analysis',
                    'aspect': finding.get('aspect'),
                    'insight': finding.get('finding')
                })

            # 跨维度洞察
            for cross_insight in synthesis.get('cross_dimensional_insights', []):
                key_insights.append({
                    'source': 'cross_dimensional',
                    'pattern': cross_insight.get('pattern'),
                    'insight': cross_insight.get('description'),
                    'supporting_sources': cross_insight.get('sources', [])
                })

            # 注意点转为决策因素
            for attention in synthesis.get('attention_points', []):
                decision_factors.append({
                    'type': 'attention_required',
                    'urgency': attention.get('urgency'),
                    'factor': attention.get('point')
                })

        # 从recommendation分析中提取建议
        if business_insights and 'analysis_results' in business_insights:
            rec_analysis = business_insights['analysis_results'].get('recommendation')
            if rec_analysis:
                for rec in rec_analysis.get('recommendations', []):
                    recommendations.append({
                        'category': rec.get('category'),
                        'priority': rec.get('priority'),
                        'title': rec.get('title'),
                        'current_state': rec.get('current_state'),
                        'target_state': rec.get('target_state'),
                        'actions': rec.get('actions', []),
                        'expected_impact': rec.get('expected_impact')
                    })

        # 从记忆系统提取洞察
        if synthesis_result:
            for memory in synthesis_result.context.memories[:5]:  # 取前5个最相关的记忆
                decision_factors.append({
                    'type': 'memory_context',
                    'memory_type': memory.memory_type,
                    'level': memory.level.value,
                    'relevance': memory.relevance_score,
                    'content_preview': memory.content[:200] if len(memory.content) > 200 else memory.content
                })

        # 5. 整理思维模式、Skill知识、领域知识引用
        thinking_patterns = []
        skill_knowledge = []
        domain_knowledge = []

        if external_knowledge_summary:
            # 思维模式
            for pattern in external_knowledge_summary.get('thinking_patterns', [])[:5]:
                thinking_patterns.append({
                    'pattern_name': pattern.get('pattern_name'),
                    'application': pattern.get('description'),
                    'confidence': pattern.get('confidence_score', 0.8)
                })

            # Skill知识
            skill_stats = external_knowledge_summary.get('skill_knowledge', {})
            if skill_stats.get('total_skills', 0) > 0:
                skill_knowledge.append({
                    'total_skills': skill_stats.get('total_skills'),
                    'avg_effectiveness': skill_stats.get('avg_effectiveness'),
                    'top_skills': skill_stats.get('top_performing_skills', [])[:3]
                })

            # 领域知识
            domain_stats = external_knowledge_summary.get('domain_knowledge', {})
            if domain_stats.get('total_domains', 0) > 0:
                domain_knowledge.append({
                    'total_domains': domain_stats.get('total_domains'),
                    'active_domains': domain_stats.get('active_domains'),
                    'coverage': domain_stats.get('coverage_percentage')
                })

        # 6. 整理应用的Skills列表
        applied_skills = ['business_analysis']  # business_analysis Skill必然被应用
        if business_insights and 'analyses_run' in business_insights:
            applied_skills.append(f"{business_insights['analyses_run']}_analysis_services")

        # 7. 整理记忆片段和知识节点
        memory_fragments = []
        if synthesis_result:
            memory_fragments = [
                {
                    'memory_type': m.memory_type,
                    'level': m.level.value,
                    'relevance': m.relevance_score,
                    'source': m.source_type
                }
                for m in synthesis_result.context.memories
            ]

        knowledge_nodes = []
        if external_knowledge_summary:
            kn_stats = external_knowledge_summary.get('knowledge_nodes', {})
            knowledge_nodes.append({
                'total_nodes': kn_stats.get('total_nodes', 0),
                'node_types': kn_stats.get('node_types', 0)
            })

        # 8. 整理引用信息
        citations = []
        if synthesis_result:
            citations = [
                {
                    'source_file': c.source_file,
                    'document_type': c.document_type,
                    'relevance': c.relevance_score
                }
                for c in synthesis_result.context.citations[:10]
            ]

        # 9. 生成上下文摘要
        context_summary = f"项目{project_id}的综合分析基于{len(key_insights)}个关键洞察、" \
                         f"{len(decision_factors)}个决策因素和{len(recommendations)}个建议。" \
                         f"应用了{len(applied_skills)}个Skills，整合了{len(memory_fragments)}条记忆。"

        # 10. 计算综合置信度
        confidence_scores = []
        if business_insights and 'synthesis' in business_insights:
            conf_assessment = business_insights['synthesis'].get('confidence_assessment', {})
            if 'average_confidence' in conf_assessment:
                confidence_scores.append(conf_assessment['average_confidence'])

        if synthesis_result and synthesis_result.context.memories:
            avg_memory_relevance = sum(m.relevance_score for m in synthesis_result.context.memories) / len(synthesis_result.context.memories)
            confidence_scores.append(avg_memory_relevance)

        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.75

        # 11. 存储到synthesis_results表
        insert_query = text("""
            INSERT INTO synthesis_results (
                project_id,
                key_insights,
                decision_factors,
                recommendations,
                thinking_patterns,
                skill_knowledge,
                domain_knowledge,
                applied_skills,
                memory_fragments,
                knowledge_nodes,
                citations,
                context_summary,
                confidence_score,
                created_at
            ) VALUES (
                :project_id,
                :key_insights,
                :decision_factors,
                :recommendations,
                :thinking_patterns,
                :skill_knowledge,
                :domain_knowledge,
                :applied_skills,
                :memory_fragments,
                :knowledge_nodes,
                :citations,
                :context_summary,
                :confidence_score,
                :created_at
            )
        """)

        db_session.execute(insert_query, {
            'project_id': project_id,
            'key_insights': json.dumps(key_insights, ensure_ascii=False),
            'decision_factors': json.dumps(decision_factors, ensure_ascii=False),
            'recommendations': json.dumps(recommendations, ensure_ascii=False),
            'thinking_patterns': json.dumps(thinking_patterns, ensure_ascii=False),
            'skill_knowledge': json.dumps(skill_knowledge, ensure_ascii=False),
            'domain_knowledge': json.dumps(domain_knowledge, ensure_ascii=False),
            'applied_skills': json.dumps(applied_skills, ensure_ascii=False),
            'memory_fragments': json.dumps(memory_fragments, ensure_ascii=False),
            'knowledge_nodes': json.dumps(knowledge_nodes, ensure_ascii=False),
            'citations': json.dumps(citations, ensure_ascii=False),
            'context_summary': context_summary,
            'confidence_score': overall_confidence,
            'created_at': datetime.utcnow()
        })
        db_session.commit()

        # 获取刚插入的记录ID
        result = db_session.execute(text("SELECT last_insert_rowid()"))
        synthesis_result_id = result.fetchone()[0]

        logger.info(f"✅ 综合洞察已存储到数据库 - ID: {synthesis_result_id}")

        # 12. 返回完整结果
        return {
            'synthesis_result_id': synthesis_result_id,
            'key_insights': key_insights,
            'decision_factors': decision_factors,
            'recommendations': recommendations,
            'thinking_patterns': thinking_patterns,
            'skill_knowledge': skill_knowledge,
            'domain_knowledge': domain_knowledge,
            'applied_skills': applied_skills,
            'memory_fragments': memory_fragments,
            'knowledge_nodes': knowledge_nodes,
            'citations': citations,
            'context_summary': context_summary,
            'confidence_score': round(overall_confidence, 2),
            'metadata': {
                'business_analysis_included': include_business_analysis,
                'analyses_run': business_insights.get('analyses_run', 0) if business_insights else 0,
                'total_insights': len(key_insights),
                'total_recommendations': len(recommendations)
            }
        }
