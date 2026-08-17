"""
v2 Agent系统 - 新的6Agent架构

这是从FieldMind-Rebuild迁移来的新Agent系统：
1. IngestionAgent - 文档摄入与预处理
2. ChunkingAgent - 智能分块
3. VectorizationAgent - 向量化
4. KnowledgeAgent - 知识图谱构建
5. SynthesisAgent - 记忆综合与引用
6. ReportAgent - 综合报告生成

核心特性：
- PipelineState持久化：所有阶段数据存储在数据库
- 断点恢复：任何阶段失败可以重新开始
- 数据流可追溯：每个阶段的输入输出清晰可查

使用方式：
    from app.agents.v2.coordinator import AgentCoordinator

    coordinator = AgentCoordinator()
    result = await coordinator.run_pipeline(
        project_id=1,
        mode=PipelineMode.FULL
    )
"""

from app.agents.v2.ingestion_agent import IngestionAgent
from app.agents.v2.chunking_agent import ChunkingAgent
from app.agents.v2.vectorization_agent import VectorizationAgent
from app.agents.v2.knowledge_agent import KnowledgeAgent
from app.agents.v2.synthesis_agent import SynthesisAgent
from app.agents.v2.report_agent import ReportAgent
from app.agents.v2.coordinator import AgentCoordinator, PipelineMode, PipelineStage

__all__ = [
    "IngestionAgent",
    "ChunkingAgent",
    "VectorizationAgent",
    "KnowledgeAgent",
    "SynthesisAgent",
    "ReportAgent",
    "AgentCoordinator",
    "PipelineMode",
    "PipelineStage",
]
