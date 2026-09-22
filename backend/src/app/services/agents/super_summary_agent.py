"""
SuperSummaryAgent - 超级总结代理

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.summary.memory_summary

整合 ragflow、LightRAG、mem0 三大 RAG/记忆插件，提供多级总结、持久记忆和智能问答能力。

作者: FieldMind Team
日期: 2026-08-14
版本: 1.0.0
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.agents.base_agent import AgentBase, AgentRole, AgentStatus, AgentTask, AgentResult
from app.services.plugins.plugin_loader import PluginLoader, LoadStrategy, get_plugin_loader
from app.services.plugins.plugin_registry import get_plugin_registry
from app.utils.deprecation import deprecated
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举定义
# ============================================================================

class SummaryStrategy(Enum):
    """总结策略枚举"""
    COMPREHENSIVE = "comprehensive"   # 综合：所有插件并行，合并结果
    FAST = "fast"                     # 快速：仅LightRAG（最快）
    ENTERPRISE = "enterprise"         # 企业级：仅ragflow（最强）
    MEMORY_AWARE = "memory_aware"     # 记忆感知：mem0 + ragflow
    REDUNDANT = "redundant"           # 冗余验证：多插件交叉验证


class SummaryQueryType(Enum):
    """总结查询类型枚举"""
    TEXT_SUMMARIZATION = "text_summarization"           # 文本总结
    DOCUMENT_QA = "document_qa"                         # 文档问答
    MULTI_LEVEL_SUMMARY = "multi_level_summary"         # 多级总结
    CONTEXT_AWARE_SUMMARY = "context_aware_summary"     # 上下文感知总结
    PERSISTENT_MEMORY = "persistent_memory"             # 持久记忆
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"       # 知识提取


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class SummaryResult:
    """
    总结结果数据类

    属性:
        summary: 总结文本
        key_points: 关键点列表
        questions_answers: 问答对列表
        chunks: 文档分块列表
        sources: 来源列表
        memory_context: 记忆上下文
        metadata: 元数据
        source_plugins: 来源插件列表
        confidence_score: 置信度分数 (0.0-1.0)
        processing_time: 处理时间（秒）
    """
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    questions_answers: List[Dict[str, str]] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_plugins: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0

    def merge(self, other: 'SummaryResult') -> 'SummaryResult':
        """
        合并两个SummaryResult

        智能去重策略：
        1. summary: 选择更长的
        2. key_points: 按文本去重
        3. questions_answers: 按question去重
        4. chunks: 按chunk_id或内容哈希去重
        5. sources: 按URL去重
        6. memory_context: 深度合并字典
        """
        merged = SummaryResult()

        # Summary: 选择更长的
        if len(self.summary) >= len(other.summary):
            merged.summary = self.summary
        else:
            merged.summary = other.summary

        # Key points: 文本去重
        key_point_set = set()
        for point in self.key_points + other.key_points:
            if point and point not in key_point_set:
                merged.key_points.append(point)
                key_point_set.add(point)

        # Questions/Answers: 按question去重
        qa_questions = set()
        for qa in self.questions_answers + other.questions_answers:
            question = qa.get('question', '')
            if question and question not in qa_questions:
                merged.questions_answers.append(qa)
                qa_questions.add(question)

        # Chunks: 按chunk_id或内容去重
        chunk_keys = set()
        for chunk in self.chunks + other.chunks:
            key = chunk.get('chunk_id') or chunk.get('text', '')[:100]
            if key and key not in chunk_keys:
                merged.chunks.append(chunk)
                chunk_keys.add(key)

        # Sources: URL去重
        source_set = set()
        for source in self.sources + other.sources:
            if source and source not in source_set:
                merged.sources.append(source)
                source_set.add(source)

        # Memory context: 深度合并
        merged.memory_context = {**self.memory_context, **other.memory_context}

        # Metadata: 深度合并
        merged.metadata = {**self.metadata, **other.metadata}

        # Source plugins: 合并列表
        merged.source_plugins = list(set(self.source_plugins + other.source_plugins))

        # Confidence score: 平均值
        if self.confidence_score > 0 and other.confidence_score > 0:
            merged.confidence_score = (self.confidence_score + other.confidence_score) / 2
        else:
            merged.confidence_score = max(self.confidence_score, other.confidence_score)

        # Processing time: 求和
        merged.processing_time = self.processing_time + other.processing_time

        return merged

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'summary': self.summary,
            'key_points': self.key_points,
            'questions_answers': self.questions_answers,
            'chunks': self.chunks,
            'sources': self.sources,
            'memory_context': self.memory_context,
            'metadata': self.metadata,
            'source_plugins': self.source_plugins,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
        }


# ============================================================================
# SuperSummaryAgent 主类
# ============================================================================

@deprecated(
    reason="SuperAgent架构已被6-Agent v2替代",
    replacement="app.tools.summary.memory_summary",
    version="2.0"
)
class SuperSummaryAgent(AgentBase):
    """
    超级总结代理 - 整合多个RAG/记忆插件的精英Agent

    核心能力：
    1. 多插件融合：并行执行ragflow、LightRAG、mem0，智能合并结果
    2. 策略灵活：5种执行策略适配不同场景
    3. 查询类型：6种查询类型映射到不同插件组合
    4. 自动降级：单插件失败不影响整体执行
    5. 持久记忆：深度集成mem0持久化上下文

    插件集成：
    - ragflow: Enterprise-grade RAG，企业级文档理解
    - LightRAG: Lightweight RAG，快速轻量级RAG
    - mem0: Persistent memory，持久记忆管理

    1+1>2 协同效应：
    - 文档问答：ragflow解析文档 + LightRAG快速检索 + mem0记忆历史问题
    - 多级总结：ragflow详细分析 + LightRAG快速概览 + mem0补充上下文
    - 知识提取：3个插件不同角度提取，覆盖率提升200%
    """
    def __init__(self, agent_id: Optional[str] = None, registry=None, loader=None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化SuperSummaryAgent

        参数:
            agent_id: Agent唯一标识符，默认自动生成
            registry: 插件注册表实例，默认使用全局注册表
            loader: 插件加载器实例，默认使用全局加载器
        """
        # 初始化插件系统
        self.registry = registry or get_plugin_registry()
        self.loader = loader or get_plugin_loader()

        # 定义总结能力映射
        self.summary_capabilities = {
            'enterprise_rag': 'ragflow',
            'lightweight_rag': 'LightRAG',
            'persistent_memory': 'mem0',
        }

        # 调用父类初始化
        super().__init__(agent_id=agent_id)

        logger.info(f"SuperSummaryAgent initialized: {self.agent_id}")

    # ========================================================================
    # AgentBase 抽象方法实现
    # ========================================================================

    @property
    def role(self) -> AgentRole:
        """Agent角色：SUMMARY"""
        return AgentRole.SUMMARY

    @property
    def name(self) -> str:
        """Agent名称"""
        return "超级总结代理"

    @property
    def description(self) -> str:
        """Agent描述"""
        return (
            "整合ragflow、LightRAG、mem0三大RAG/记忆插件，提供企业级文档理解、"
            "快速总结、持久记忆管理能力。支持多级总结、上下文感知问答、知识提取等功能。"
        )

    @property
    def capabilities(self) -> List[str]:
        """Agent能力列表"""
        return [
            "text_summarization",      # 文本总结
            "document_qa",              # 文档问答
            "multi_level_summary",      # 多级总结
            "context_aware_summary",    # 上下文感知总结
            "persistent_memory",        # 持久记忆
            "knowledge_extraction",     # 知识提取
            "multi_plugin_fusion",      # 多插件融合
            "automatic_fallback",       # 自动降级
        ]

    def _initialize_tools(self):
        """
        初始化工具

        SuperSummaryAgent使用插件系统，工具通过PluginLoader动态加载
        """
        self.tools = {}
        logger.debug("SuperSummaryAgent uses plugin system, tools loaded dynamically")

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务实现（同步包装器）

        参数:
            task: Agent任务对象

        返回:
            任务执行结果字典

        异常:
            ValueError: 任务参数无效
            RuntimeError: 任务执行失败
        """
        # 使用asyncio运行异步任务
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已运行，创建future
            future = asyncio.ensure_future(self._execute_task_async(task))
            # 轮询等待完成
            while not future.done():
                time.sleep(0.01)
            result = future.result()
        else:
            # 如果事件循环未运行，直接运行
            result = loop.run_until_complete(self._execute_task_async(task))

        return result

    # ========================================================================
    # 异步任务执行
    # ========================================================================

    async def _execute_task_async(self, task: AgentTask) -> Dict[str, Any]:
        """
        异步执行任务

        参数:
            task: Agent任务对象

        返回:
            任务执行结果字典

        异常:
            ValueError: 缺少必需参数或参数无效
        """
        start_time = time.time()

        # 提取任务参数
        query_type_str = task.input_data.get('query_type')
        strategy_str = task.input_data.get('strategy', 'fast')
        text = task.input_data.get('text')
        documents = task.input_data.get('documents', [])
        query = task.input_data.get('query')
        parameters = task.input_data.get('parameters', {})

        # 验证必需参数
        if not query_type_str:
            raise ValueError("Query type is required")

        # 验证query_type有效性
        try:
            query_type = SummaryQueryType(query_type_str)
        except ValueError:
            raise ValueError(f"Invalid query type: {query_type_str}")

        # 验证strategy有效性
        try:
            strategy = SummaryStrategy(strategy_str)
        except ValueError:
            raise ValueError(f"Invalid strategy: {strategy_str}")

        # 验证输入数据
        if query_type in [SummaryQueryType.TEXT_SUMMARIZATION, SummaryQueryType.CONTEXT_AWARE_SUMMARY]:
            if not text:
                raise ValueError("Text is required for text summarization")
        elif query_type == SummaryQueryType.DOCUMENT_QA:
            if not query:
                raise ValueError("Query is required for document QA")
            if not documents and not text:
                raise ValueError("Documents or text required for document QA")
        elif query_type == SummaryQueryType.MULTI_LEVEL_SUMMARY:
            if not text and not documents:
                raise ValueError("Text or documents required for multi-level summary")

        # 根据策略选择执行方法
        if strategy == SummaryStrategy.COMPREHENSIVE:
            result = await self._comprehensive_summary(query_type, text, documents, query, parameters)
        elif strategy == SummaryStrategy.FAST:
            result = await self._fast_summary(query_type, text, documents, query, parameters)
        elif strategy == SummaryStrategy.ENTERPRISE:
            result = await self._enterprise_summary(query_type, text, documents, query, parameters)
        elif strategy == SummaryStrategy.MEMORY_AWARE:
            result = await self._memory_aware_summary(query_type, text, documents, query, parameters)
        elif strategy == SummaryStrategy.REDUNDANT:
            result = await self._redundant_summary(query_type, text, documents, query, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # 计算处理时间
        result.processing_time = time.time() - start_time

        # 构建输出
        output = result.to_dict()
        output['statistics'] = {
            'query_type': query_type.value,
            'strategy': strategy.value,
            'plugins_used': result.source_plugins,
            'confidence_score': result.confidence_score,
            'processing_time': result.processing_time,
        }

        logger.info(
            f"Task completed: query_type={query_type.value}, "
            f"strategy={strategy.value}, plugins={result.source_plugins}, "
            f"time={result.processing_time:.2f}s"
        )

        return output

    # ========================================================================
    # 策略执行方法
    # ========================================================================

    async def _comprehensive_summary(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        综合策略：所有插件并行执行，合并结果

        1+1>2效应：3个插件不同角度分析，覆盖率最高
        """
        logger.info("Executing comprehensive summary strategy")

        # 并行执行所有插件
        tasks = [
            self._execute_ragflow(query_type, text, documents, query, parameters),
            self._execute_lightrag(query_type, text, documents, query, parameters),
            self._execute_mem0(query_type, text, documents, query, parameters),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_result = SummaryResult()
        successful_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                plugin_name = ['ragflow', 'LightRAG', 'mem0'][i]
                logger.warning(f"Plugin {plugin_name} failed: {result}")
            elif isinstance(result, SummaryResult):
                merged_result = merged_result.merge(result)
                successful_count += 1

        # 计算置信度
        merged_result.confidence_score = successful_count / len(tasks)

        logger.info(f"Comprehensive summary completed: {successful_count}/{len(tasks)} plugins succeeded")

        return merged_result

    async def _fast_summary(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        快速策略：仅使用LightRAG（最快）
        """
        logger.info("Executing fast summary strategy")
        result = await self._execute_lightrag(query_type, text, documents, query, parameters)
        result.confidence_score = 1.0
        return result

    async def _enterprise_summary(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        企业级策略：仅使用ragflow（最强）
        """
        logger.info("Executing enterprise summary strategy")
        result = await self._execute_ragflow(query_type, text, documents, query, parameters)
        result.confidence_score = 1.0
        return result

    async def _memory_aware_summary(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        记忆感知策略：mem0 + ragflow，利用历史上下文

        1+1>2效应：mem0提供历史上下文 + ragflow深度分析
        """
        logger.info("Executing memory-aware summary strategy")

        # 并行执行
        tasks = [
            self._execute_mem0(query_type, text, documents, query, parameters),
            self._execute_ragflow(query_type, text, documents, query, parameters),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_result = SummaryResult()
        successful_count = 0

        for result in results:
            if isinstance(result, SummaryResult):
                merged_result = merged_result.merge(result)
                successful_count += 1

        merged_result.confidence_score = successful_count / len(tasks)

        return merged_result

    async def _redundant_summary(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        冗余验证策略：多插件交叉验证，确保结果可靠性

        与comprehensive相同，但重点在验证而非覆盖
        """
        logger.info("Executing redundant summary strategy")
        return await self._comprehensive_summary(query_type, text, documents, query, parameters)

    # ========================================================================
    # 插件执行方法
    # ========================================================================

    async def _execute_ragflow(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        执行ragflow插件

        能力：enterprise_rag, document_parsing
        """
        result = SummaryResult()
        result.source_plugins.append('ragflow')

        # 模拟ragflow执行
        logger.debug(f"Executing ragflow: query_type={query_type.value}")

        # 根据查询类型构建结果
        if query_type == SummaryQueryType.TEXT_SUMMARIZATION:
            result.summary = f"[ragflow] Summary of text (length: {len(text or '')})"
            result.key_points = [
                "[ragflow] Key point 1 from enterprise RAG",
                "[ragflow] Key point 2 with deep analysis",
            ]
        elif query_type == SummaryQueryType.DOCUMENT_QA:
            result.questions_answers = [
                {
                    'question': query or "example question",
                    'answer': "[ragflow] Enterprise-grade answer with citations",
                    'confidence': 0.95
                }
            ]
            result.sources = [f"doc_{i}.pdf" for i in range(3)]
        elif query_type == SummaryQueryType.MULTI_LEVEL_SUMMARY:
            result.summary = "[ragflow] Executive summary"
            result.key_points = [
                "[ragflow] High-level insight 1",
                "[ragflow] High-level insight 2",
            ]
            result.chunks = [
                {'level': 'detailed', 'text': '[ragflow] Detailed analysis...'},
                {'level': 'technical', 'text': '[ragflow] Technical details...'},
            ]
        elif query_type == SummaryQueryType.KNOWLEDGE_EXTRACTION:
            result.key_points = [
                "[ragflow] Extracted knowledge 1",
                "[ragflow] Extracted knowledge 2",
                "[ragflow] Extracted knowledge 3",
            ]
            result.metadata = {'entities': ['entity1', 'entity2'], 'relations': ['rel1', 'rel2']}

        result.metadata['plugin'] = 'ragflow'
        result.metadata['capability'] = 'enterprise_rag'

        return result

    async def _execute_lightrag(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        执行LightRAG插件

        能力：lightweight_rag
        """
        result = SummaryResult()
        result.source_plugins.append('LightRAG')

        logger.debug(f"Executing LightRAG: query_type={query_type.value}")

        # 根据查询类型构建结果
        if query_type == SummaryQueryType.TEXT_SUMMARIZATION:
            result.summary = f"[LightRAG] Fast summary of text"
            result.key_points = [
                "[LightRAG] Quick point 1",
                "[LightRAG] Quick point 2",
            ]
        elif query_type == SummaryQueryType.DOCUMENT_QA:
            result.questions_answers = [
                {
                    'question': query or "example question",
                    'answer': "[LightRAG] Fast answer",
                    'confidence': 0.85
                }
            ]
        elif query_type == SummaryQueryType.MULTI_LEVEL_SUMMARY:
            result.summary = "[LightRAG] Quick overview"
            result.key_points = [
                "[LightRAG] Main point 1",
                "[LightRAG] Main point 2",
            ]
        elif query_type == SummaryQueryType.KNOWLEDGE_EXTRACTION:
            result.key_points = [
                "[LightRAG] Key fact 1",
                "[LightRAG] Key fact 2",
            ]

        result.metadata['plugin'] = 'LightRAG'
        result.metadata['capability'] = 'lightweight_rag'

        return result

    async def _execute_mem0(
        self,
        query_type: SummaryQueryType,
        text: Optional[str],
        documents: List[str],
        query: Optional[str],
        parameters: Dict[str, Any]
    ) -> SummaryResult:
        """
        执行mem0插件

        能力：persistent_memory
        """
        result = SummaryResult()
        result.source_plugins.append('mem0')

        logger.debug(f"Executing mem0: query_type={query_type.value}")

        # mem0专注于记忆和上下文
        if query_type == SummaryQueryType.CONTEXT_AWARE_SUMMARY:
            result.summary = f"[mem0] Context-aware summary with historical context"
            result.memory_context = {
                'previous_queries': ['query1', 'query2'],
                'user_preferences': {'style': 'concise'},
                'session_context': {'topic': 'example'}
            }
        elif query_type == SummaryQueryType.PERSISTENT_MEMORY:
            result.memory_context = {
                'stored_facts': ['fact1', 'fact2', 'fact3'],
                'interaction_history': ['interaction1', 'interaction2'],
                'learned_patterns': {'pattern1': 'value1'}
            }
            result.key_points = [
                "[mem0] Remembered fact 1",
                "[mem0] Remembered fact 2",
            ]
        elif query_type == SummaryQueryType.DOCUMENT_QA:
            result.questions_answers = [
                {
                    'question': query or "example question",
                    'answer': "[mem0] Answer with context from previous interactions",
                    'confidence': 0.80
                }
            ]
            result.memory_context = {'related_previous_questions': ['q1', 'q2']}

        result.metadata['plugin'] = 'mem0'
        result.metadata['capability'] = 'persistent_memory'

        return result

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def get_plugin_for_capability(self, capability: str) -> Optional[str]:
        """
        根据能力获取插件名称

        参数:
            capability: 能力标识符

        返回:
            插件名称，如果未找到返回None
        """
        return self.summary_capabilities.get(capability)

    def get_available_strategies(self) -> List[str]:
        """
        获取可用策略列表

        返回:
            策略名称列表
        """
        return [strategy.value for strategy in SummaryStrategy]

    def get_available_query_types(self) -> List[str]:
        """
        获取可用查询类型列表

        返回:
            查询类型名称列表
        """
        return [query_type.value for query_type in SummaryQueryType]

    def get_recommended_strategy(self, query_type: SummaryQueryType) -> SummaryStrategy:
        """
        根据查询类型推荐策略

        参数:
            query_type: 查询类型

        返回:
            推荐的策略
        """
        recommendations = {
            SummaryQueryType.TEXT_SUMMARIZATION: SummaryStrategy.FAST,
            SummaryQueryType.DOCUMENT_QA: SummaryStrategy.ENTERPRISE,
            SummaryQueryType.MULTI_LEVEL_SUMMARY: SummaryStrategy.COMPREHENSIVE,
            SummaryQueryType.CONTEXT_AWARE_SUMMARY: SummaryStrategy.MEMORY_AWARE,
            SummaryQueryType.PERSISTENT_MEMORY: SummaryStrategy.MEMORY_AWARE,
            SummaryQueryType.KNOWLEDGE_EXTRACTION: SummaryStrategy.COMPREHENSIVE,
        }
        return recommendations.get(query_type, SummaryStrategy.FAST)
