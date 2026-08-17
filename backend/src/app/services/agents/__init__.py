"""
Agents模块 - 专业Agent集合

包含6个专业Agent：
1. TranscriptAgent - 音频/视频转文字
2. EntityAgent - 命名实体识别
3. RelationAgent - 关系抽取
4. SearchAgent - 互联网搜索
5. SummaryAgent - 总结报告生成
6. CoordinatorAgent - 任务协调

Agent Mesh架构组件：
- AgentMessageBus - 消息总线
- SharedContextPool - 共享上下文池
- AgentMesh - Agent网格管理器

SuperAgents (Phase 2):
- SuperKnowledgeAgent - 知识图谱超级Agent (graphrag + graphiti + cognee)
- SuperSearchAgent - 搜索爬虫超级Agent (crawl4ai + firecrawl + browser-use)
- SuperSummaryAgent - 总结记忆超级Agent (ragflow + LightRAG + mem0)
- SuperTranscriptAgent - 文档转换超级Agent (markitdown + PDF-Guru)
- EnhancedCoordinatorAgent - 增强协调代理 (整合所有SuperAgents)
"""

from .base_agent import (
    AgentBase,
    AgentRole,
    AgentStatus,
    AgentTask,
    AgentResult
)

from .agent_message_bus import AgentMessageBus, MessagePriority
from .shared_context_pool import SharedContextPool, ContextScope
from .agent_mesh import AgentMesh

from .super_knowledge_agent import (
    SuperKnowledgeAgent,
    KnowledgeGraphStrategy,
    KnowledgeQueryType,
    KnowledgeGraphResult
)

from .super_search_agent import (
    SuperSearchAgent,
    SearchStrategy,
    SearchQueryType,
    SearchResult
)

from .super_summary_agent import (
    SuperSummaryAgent,
    SummaryStrategy,
    SummaryQueryType,
    SummaryResult
)

from .super_transcript_agent import (
    SuperTranscriptAgent,
    TranscriptStrategy,
    TranscriptQueryType,
    TranscriptResult
)

from .coordinator_agent import (
    EnhancedCoordinatorAgent,
    TaskCategory,
    CoordinationStrategy,
    AgentAllocation,
    CoordinationResult,
)

__all__ = [
    # Base
    'AgentBase',
    'AgentRole',
    'AgentStatus',
    'AgentTask',
    'AgentResult',

    # Agent Mesh
    'AgentMessageBus',
    'MessagePriority',
    'SharedContextPool',
    'ContextScope',
    'AgentMesh',

    # SuperAgents - Knowledge
    'SuperKnowledgeAgent',
    'KnowledgeGraphStrategy',
    'KnowledgeQueryType',
    'KnowledgeGraphResult',

    # SuperAgents - Search
    'SuperSearchAgent',
    'SearchStrategy',
    'SearchQueryType',
    'SearchResult',

    # SuperAgents - Summary
    'SuperSummaryAgent',
    'SummaryStrategy',
    'SummaryQueryType',
    'SummaryResult',

    # SuperAgents - Transcript
    'SuperTranscriptAgent',
    'TranscriptStrategy',
    'TranscriptQueryType',
    'TranscriptResult',

    # Enhanced Coordinator
    'EnhancedCoordinatorAgent',
    'TaskCategory',
    'CoordinationStrategy',
    'AgentAllocation',
    'CoordinationResult',
]
