"""
工具注册表 - Agent服务映射

定义每个Agent可使用的服务工具，不移动文件位置，仅记录归属关系。
"""

from typing import Dict, List

# Agent工具映射
AGENT_TOOLS: Dict[str, List[str]] = {
    # 1️⃣ IngestionAgent - 文档摄取
    "ingestion": [
        "document_converter",           # 基础转换器
        "document_converter_v2",        # 升级版转换器
        "document_parser",              # 文档解析
        "multimodal_processor",         # 多模态处理
        "video_processor",              # 视频处理
        "text_processor",               # 文本处理
        "table_processor",              # 表格处理
        "data_curation",                # 数据清洗
        "data_quality_checker",         # 质量检查
    ],

    # 2️⃣ ChunkingAgent - 分块
    "chunking": [
        "document_chunker",             # 基础分块器
        "document_chunker_v2",          # 升级版分块器
        "semantic_chunker",             # 语义分块
        "audio_chunker",                # 音频分块
    ],

    # 3️⃣ VectorizationAgent - 向量化与实体提取
    "vectorization": [
        "entity_extraction",            # 基础实体提取
        "entity_extractor",             # 实体提取器
        "entity_categorizer",           # 实体分类
        "llm_enhanced_extractor",       # LLM增强提取
        "structured_extractor",         # 结构化提取
        "temporal_extractor",           # 时序提取
        "cross_document_entity_resolver", # 跨文档实体解析
        "multimodal_alignment",         # 多模态对齐
    ],

    # 4️⃣ KnowledgeAgent - 知识图谱构建
    "knowledge": [
        "knowledge_graph",              # 基础图谱
        "knowledge_graph_v2",           # 升级版图谱
        "knowledge_graph_service",      # 图谱服务
        "knowledge_graph_improved",     # 改进版图谱
        "knowledge_graph_builder",      # 图谱构建器
        "knowledge_graph_builder_optimized", # 优化版构建器
        "relation_discovery",           # 关系发现
        "document_relation_discovery",  # 文档关系发现
        "document_network_builder",     # 文档网络构建
        "neo4j_adapter",                # Neo4j适配器
        "dynamic_discovery",            # 动态发现
        "correlation_recommender",      # 关联推荐
    ],

    # 5️⃣ SynthesisAgent - 综合与记忆
    "synthesis": [
        "memory_service",               # 记忆服务
        "mem0_service",                 # Mem0集成
        "long_memory_service",          # 长期记忆
        "conversation_memory_service",  # 对话记忆
        "memory_injector",              # 记忆注入
        "evidence_extractor",           # 证据提取
        "facts_anchor",                 # 事实锚定
        "fact_statement_populator",     # 事实填充
        "source_traceback_service",     # 源追溯
        "anti_hallucination_report",    # 反幻觉报告
    ],

    # 6️⃣ ReportAgent - 报告生成
    "report": [
        "dynamic_report_generator",     # 动态报告生成
        "llm_report_generator",         # LLM报告生成
        "business_analysis_service",    # 商业分析
        "creative_analysis_service",    # 创意分析
        "cultural_classifier",          # 文化分类
        "proposal_generator_service",   # 提案生成
        "adaptive_analyzer",            # 自适应分析
    ],
}


# 工作流编排服务（供Coordinator使用）
COORDINATOR_TOOLS: List[str] = [
    "workflow_chain",                   # 工作流链
    "workflow_engine",                  # 工作流引擎
    "workflow_templates",               # 工作流模板
    "document_processing_pipeline",     # 文档处理流水线
    "document_processing_pipeline_v2",  # 升级版流水线
    "document_processing_pipeline_complete", # 完整版流水线
    "batch_processor",                  # 批处理器
    "auto_processing_trigger",          # 自动触发器
    "background_tasks",                 # 后台任务
]


# 独立服务（不整合到Agent系统）
STANDALONE_SERVICES: List[str] = [
    "chat_service",                     # 聊天服务
    "enhanced_chat_service",            # 增强聊天服务
    "conversation_history_manager",     # 对话历史管理
    "hierarchical_retriever",           # 层次检索
    "keyword_search_service",           # 关键词搜索
    "ragflow_service",                  # RAGFlow集成
    "intelligent_agent",                # 智能代理
    "skill_sandbox",                    # 技能沙箱
    "data_federation_service",          # 数据联邦
]


# 工具加载器
def get_agent_tools(agent_name: str) -> List[str]:
    """
    获取指定Agent的工具列表

    Args:
        agent_name: Agent名称 (ingestion/chunking/vectorization/knowledge/synthesis/report)

    Returns:
        工具名称列表
    """
    return AGENT_TOOLS.get(agent_name, [])


def get_all_tools() -> Dict[str, List[str]]:
    """
    获取所有Agent的工具映射

    Returns:
        完整的工具注册表
    """
    return AGENT_TOOLS.copy()


def is_tool_registered(tool_name: str) -> bool:
    """
    检查工具是否已注册

    Args:
        tool_name: 工具名称

    Returns:
        是否已注册
    """
    for tools in AGENT_TOOLS.values():
        if tool_name in tools:
            return True
    return tool_name in COORDINATOR_TOOLS or tool_name in STANDALONE_SERVICES


def get_tool_agent(tool_name: str) -> str:
    """
    查找工具所属的Agent

    Args:
        tool_name: 工具名称

    Returns:
        Agent名称，如果未找到返回None
    """
    for agent_name, tools in AGENT_TOOLS.items():
        if tool_name in tools:
            return agent_name

    if tool_name in COORDINATOR_TOOLS:
        return "coordinator"

    if tool_name in STANDALONE_SERVICES:
        return "standalone"

    return None


# 工具统计
def get_tool_stats() -> Dict[str, int]:
    """
    获取工具统计信息

    Returns:
        各Agent的工具数量
    """
    stats = {agent: len(tools) for agent, tools in AGENT_TOOLS.items()}
    stats["coordinator"] = len(COORDINATOR_TOOLS)
    stats["standalone"] = len(STANDALONE_SERVICES)
    stats["total"] = sum(stats.values())
    return stats
