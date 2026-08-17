"""
Agent Request/Response Schemas
SuperAgent API 的 Pydantic 模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ============= 基础模型 =============

class AgentMetadata(BaseModel):
    """Agent执行元数据"""
    plugins_used: List[str] = Field(default_factory=list, description="使用的插件列表")
    token_usage: Optional[int] = Field(None, description="Token消耗")
    execution_stages: List[str] = Field(default_factory=list, description="执行阶段")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class AgentExecutionResult(BaseModel):
    """Agent执行结果（通用）"""
    agent_id: str = Field(..., description="Agent唯一标识")
    status: Literal["success", "failed", "partial"] = Field(..., description="执行状态")
    execution_time: float = Field(..., description="执行耗时（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间戳")
    metadata: AgentMetadata = Field(default_factory=AgentMetadata, description="执行元数据")


# ============= Knowledge Agent =============

class KnowledgeAnalysisRequest(BaseModel):
    """Knowledge Agent 分析请求"""
    document_ids: List[int] = Field(..., description="要分析的文档ID列表", min_items=1)
    project_id: Optional[int] = Field(None, description="项目ID（可选）")
    analysis_depth: Literal["quick", "standard", "deep"] = Field(
        "standard",
        description="分析深度：quick=快速扫描, standard=标准分析, deep=深度挖掘"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="关注领域（如：人物、地点、事件、概念等）"
    )
    use_plugins: List[str] = Field(
        default_factory=lambda: ["lightrag", "markitdown"],
        description="启用的插件"
    )
    max_entities: int = Field(50, description="最大提取实体数", ge=10, le=500)


class ExtractedEntity(BaseModel):
    """提取的实体"""
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(None, description="实体描述")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    mentions: int = Field(..., description="出现次数")
    document_ids: List[int] = Field(default_factory=list, description="关联文档")


class ExtractedRelation(BaseModel):
    """提取的关系"""
    source: str = Field(..., description="源实体")
    target: str = Field(..., description="目标实体")
    relation_type: str = Field(..., description="关系类型")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    evidence: Optional[str] = Field(None, description="支持证据")


class KnowledgeAnalysisResult(BaseModel):
    """Knowledge Agent 分析结果"""
    entities: List[ExtractedEntity] = Field(..., description="提取的实体列表")
    relations: List[ExtractedRelation] = Field(..., description="提取的关系列表")
    themes: List[Dict[str, Any]] = Field(..., description="发现的主题")
    key_insights: List[str] = Field(..., description="关键洞察")
    document_summaries: Dict[int, str] = Field(..., description="文档级摘要")
    confidence_score: float = Field(..., description="整体置信度", ge=0.0, le=1.0)


class KnowledgeAnalysisResponse(AgentExecutionResult):
    """Knowledge Agent 响应"""
    result: KnowledgeAnalysisResult = Field(..., description="分析结果")
    error: Optional[str] = Field(None, description="错误信息")


# ============= Search Agent =============

class SearchQueryRequest(BaseModel):
    """Search Agent 搜索请求"""
    query: str = Field(..., description="搜索查询", min_length=1)
    project_id: Optional[int] = Field(None, description="限定项目范围")
    search_scope: Literal["documents", "knowledge_graph", "memory", "all"] = Field(
        "all",
        description="搜索范围"
    )
    search_modes: List[Literal["semantic", "keyword", "hybrid"]] = Field(
        default_factory=lambda: ["hybrid"],
        description="搜索模式"
    )
    max_results: int = Field(20, description="最大结果数", ge=1, le=100)
    include_context: bool = Field(True, description="是否包含上下文")
    use_plugins: List[str] = Field(
        default_factory=lambda: ["lightrag", "crawl4ai"],
        description="启用的插件"
    )


class SearchResult(BaseModel):
    """单个搜索结果"""
    content: str = Field(..., description="结果内容")
    source: str = Field(..., description="来源（文档/网页/记忆）")
    source_id: Optional[int] = Field(None, description="来源ID")
    relevance_score: float = Field(..., description="相关性分数", ge=0.0, le=1.0)
    context: Optional[str] = Field(None, description="上下文片段")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class SearchQueryResult(BaseModel):
    """Search Agent 搜索结果"""
    query: str = Field(..., description="原始查询")
    results: List[SearchResult] = Field(..., description="搜索结果列表")
    total_found: int = Field(..., description="总共找到的结果数")
    search_strategy: str = Field(..., description="使用的搜索策略")
    aggregated_answer: Optional[str] = Field(None, description="聚合回答（如果适用）")


class SearchQueryResponse(AgentExecutionResult):
    """Search Agent 响应"""
    result: SearchQueryResult = Field(..., description="搜索结果")
    error: Optional[str] = Field(None, description="错误信息")


# ============= Summary Agent =============

class SummaryRequest(BaseModel):
    """Summary Agent 摘要请求"""
    content_source: Literal["documents", "text", "conversation"] = Field(
        ...,
        description="内容来源类型"
    )
    document_ids: Optional[List[int]] = Field(None, description="文档ID列表（当source=documents）")
    text_content: Optional[str] = Field(None, description="直接文本内容（当source=text）")
    conversation_id: Optional[int] = Field(None, description="对话ID（当source=conversation）")

    summary_type: Literal["abstract", "structured", "bullet_points", "narrative"] = Field(
        "structured",
        description="摘要类型"
    )
    summary_length: Literal["brief", "moderate", "detailed"] = Field(
        "moderate",
        description="摘要长度"
    )
    focus_aspects: List[str] = Field(
        default_factory=list,
        description="关注方面（如：方法论、发现、结论等）"
    )
    use_plugins: List[str] = Field(
        default_factory=lambda: ["lightrag"],
        description="启用的插件"
    )


class SummarySection(BaseModel):
    """摘要章节"""
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    key_points: List[str] = Field(default_factory=list, description="关键点")


class SummaryResult(BaseModel):
    """Summary Agent 摘要结果"""
    summary_type: str = Field(..., description="摘要类型")
    sections: List[SummarySection] = Field(..., description="摘要章节")
    overall_summary: str = Field(..., description="总体摘要")
    key_takeaways: List[str] = Field(..., description="关键要点")
    word_count: int = Field(..., description="字数统计")
    compression_ratio: float = Field(..., description="压缩比", ge=0.0, le=1.0)


class SummaryResponse(AgentExecutionResult):
    """Summary Agent 响应"""
    result: SummaryResult = Field(..., description="摘要结果")
    error: Optional[str] = Field(None, description="错误信息")


# ============= Transcript Agent =============

class TranscriptRequest(BaseModel):
    """Transcript Agent 转录请求"""
    audio_file_path: Optional[str] = Field(None, description="音频文件路径")
    audio_url: Optional[str] = Field(None, description="音频URL")
    document_id: Optional[int] = Field(None, description="关联文档ID")

    language: str = Field("zh", description="语言代码（zh, en, etc.）")
    include_timestamps: bool = Field(True, description="是否包含时间戳")
    speaker_diarization: bool = Field(False, description="是否区分说话人")
    extract_entities: bool = Field(True, description="是否提取实体")
    generate_summary: bool = Field(True, description="是否生成摘要")

    use_plugins: List[str] = Field(
        default_factory=lambda: ["whisper", "lightrag"],
        description="启用的插件"
    )


class TranscriptSegment(BaseModel):
    """转录片段"""
    start_time: float = Field(..., description="开始时间（秒）")
    end_time: float = Field(..., description="结束时间（秒）")
    text: str = Field(..., description="转录文本")
    speaker: Optional[str] = Field(None, description="说话人标识")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)


class TranscriptResult(BaseModel):
    """Transcript Agent 转录结果"""
    full_text: str = Field(..., description="完整转录文本")
    segments: List[TranscriptSegment] = Field(..., description="转录片段列表")
    duration: float = Field(..., description="音频时长（秒）")
    language_detected: str = Field(..., description="检测到的语言")

    entities: Optional[List[ExtractedEntity]] = Field(None, description="提取的实体")
    summary: Optional[str] = Field(None, description="内容摘要")
    key_topics: List[str] = Field(default_factory=list, description="关键主题")


class TranscriptResponse(AgentExecutionResult):
    """Transcript Agent 响应"""
    result: TranscriptResult = Field(..., description="转录结果")
    error: Optional[str] = Field(None, description="错误信息")


# ============= Coordinator / Orchestration =============

class AgentTaskSpec(BaseModel):
    """单个Agent任务规格"""
    agent_type: Literal["knowledge", "search", "summary", "transcript"] = Field(
        ...,
        description="Agent类型"
    )
    task_id: str = Field(..., description="任务ID（用于依赖引用）")
    parameters: Dict[str, Any] = Field(..., description="Agent特定参数")
    depends_on: List[str] = Field(default_factory=list, description="依赖的任务ID列表")
    priority: int = Field(1, description="优先级（1-10）", ge=1, le=10)


class OrchestrationRequest(BaseModel):
    """多Agent编排请求"""
    tasks: List[AgentTaskSpec] = Field(..., description="任务列表", min_items=1)
    execution_mode: Literal["sequential", "parallel", "dag"] = Field(
        "dag",
        description="执行模式：sequential=顺序, parallel=并行, dag=根据依赖图"
    )
    project_id: Optional[int] = Field(None, description="项目ID")
    timeout: int = Field(300, description="总超时时间（秒）", ge=10, le=3600)
    stop_on_error: bool = Field(False, description="遇到错误是否停止")


class AgentTaskResult(BaseModel):
    """单个Agent任务结果"""
    task_id: str = Field(..., description="任务ID")
    agent_type: str = Field(..., description="Agent类型")
    status: Literal["success", "failed", "skipped", "timeout"] = Field(..., description="状态")
    result: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    execution_time: float = Field(..., description="执行时间（秒）")
    error: Optional[str] = Field(None, description="错误信息")


class OrchestrationResult(BaseModel):
    """编排执行结果"""
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="完成任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    task_results: List[AgentTaskResult] = Field(..., description="各任务结果")
    execution_graph: Optional[Dict[str, Any]] = Field(None, description="执行图（DAG模式）")
    aggregated_insights: Optional[str] = Field(None, description="聚合洞察（如果适用）")


class OrchestrationResponse(AgentExecutionResult):
    """Coordinator 响应"""
    result: OrchestrationResult = Field(..., description="编排结果")
    error: Optional[str] = Field(None, description="错误信息")


# ============= 通用响应包装 =============

class APIResponse(BaseModel):
    """API统一响应格式"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    recovery_suggestions: List[str] = Field(
        default_factory=list,
        description="恢复建议"
    )


# ============= WebSocket 消息 =============

class AgentProgressEvent(BaseModel):
    """Agent进度事件（WebSocket）"""
    event_type: Literal["started", "progress", "completed", "failed"] = Field(
        ...,
        description="事件类型"
    )
    agent_id: str = Field(..., description="Agent ID")
    task_id: Optional[str] = Field(None, description="任务ID（编排模式）")
    progress: float = Field(..., description="进度百分比", ge=0.0, le=100.0)
    current_stage: str = Field(..., description="当前阶段描述")
    partial_result: Optional[Dict[str, Any]] = Field(None, description="部分结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentStatusQuery(BaseModel):
    """Agent状态查询"""
    execution_id: str = Field(..., description="执行ID")


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    execution_id: str = Field(..., description="执行ID")
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(
        ...,
        description="执行状态"
    )
    progress: float = Field(..., description="进度", ge=0.0, le=100.0)
    current_stage: Optional[str] = Field(None, description="当前阶段")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    result: Optional[Dict[str, Any]] = Field(None, description="结果（如果完成）")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
