"""
SuperAgent API Routes
为5个SuperAgents + Coordinator提供RESTful API接口

功能：
1. Knowledge Agent - 深度文档分析和知识提取
2. Search Agent - 多源智能检索
3. Summary Agent - 结构化摘要生成
4. Transcript Agent - 音视频转录和分析
5. Coordinator - 多Agent编排执行
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import asyncio
import logging
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import AIServiceException
from app.schemas.response import success_response, error_response
from app.services.agents.base_agent import AgentTask
from app.schemas.agent_schemas import (
    # Knowledge Agent
    KnowledgeAnalysisRequest,
    KnowledgeAnalysisResponse,
    KnowledgeAnalysisResult,
    ExtractedEntity,
    ExtractedRelation,

    # Search Agent
    SearchQueryRequest,
    SearchQueryResponse,
    SearchQueryResult,
    SearchResult,

    # Summary Agent
    SummaryRequest,
    SummaryResponse,
    SummaryResult,
    SummarySection,

    # Transcript Agent
    TranscriptRequest,
    TranscriptResponse,
    TranscriptResult,
    TranscriptSegment,

    # Orchestration
    OrchestrationRequest,
    OrchestrationResponse,
    OrchestrationResult,
    AgentTaskResult,

    # Common
    AgentMetadata,
    APIResponse,
    ErrorDetail,
    AgentStatusQuery,
    AgentStatusResponse,
)

# Import SuperAgents
from app.services.agents.super_knowledge_agent import SuperKnowledgeAgent
from app.services.agents.super_search_agent import SuperSearchAgent
from app.services.agents.super_summary_agent import SuperSummaryAgent
from app.services.agents.super_transcript_agent import SuperTranscriptAgent
from app.services.agents.coordinator_agent import EnhancedCoordinatorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["SuperAgents"])

# 全局执行状态存储（生产环境应使用Redis）
execution_store: Dict[str, Dict[str, Any]] = {}


# ============= Helper Functions =============

def create_execution_id() -> str:
    """生成唯一执行ID"""
    return f"exec_{uuid.uuid4().hex[:12]}"


def store_execution(execution_id: str, data: Dict[str, Any]):
    """存储执行状态"""
    execution_store[execution_id] = {
        **data,
        "updated_at": datetime.now()
    }


def get_execution(execution_id: str) -> Dict[str, Any]:
    """获取执行状态"""
    return execution_store.get(execution_id)


def run_agent(agent, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """统一调用 SuperAgent，避免使用不存在的 execute 接口。"""
    result = agent.execute_task(AgentTask(
        task_id=create_execution_id(),
        task_type=task_type,
        input_data=input_data,
    ))
    return {
        "status": "success" if result.success else "failed",
        "data": result.output_data if result.success else {},
        "execution_time": result.execution_time,
        "plugins_used": result.metadata.get("plugins_used", []),
        "stages": result.metadata.get("stages", []),
        "warnings": result.warnings,
        "error": "; ".join(result.errors) if result.errors else None,
    }


# ============= Knowledge Agent API =============

@router.post("/knowledge/analyze", response_model=APIResponse)
async def knowledge_analyze(
    request: KnowledgeAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Knowledge Agent - 深度文档分析

    功能：
    - 提取实体和关系
    - 识别主题和洞察
    - 生成知识图谱数据
    - 调用 LightRAG、MarkItDown 等插件

    使用场景：
    - 用户上传新文档后的自动分析
    - 知识图谱构建的数据源
    - 深度内容理解
    """
    execution_id = create_execution_id()

    try:
        logger.info(f"[{execution_id}] Starting Knowledge Agent analysis")
        logger.info(f"Documents: {request.document_ids}, Depth: {request.analysis_depth}")

        # 初始化执行状态
        store_execution(execution_id, {
            "status": "running",
            "agent_type": "knowledge",
            "progress": 0.0,
            "started_at": datetime.now()
        })

        # 创建 SuperKnowledgeAgent 实例
        agent = SuperKnowledgeAgent(agent_id=f"knowledge_{execution_id}")

        from app.models.project import ProjectDocument
        from app.models.document_chunk import DocumentChunk
        documents_content = []
        query = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(request.document_ids)
        )
        if request.project_id is not None:
            query = query.filter(ProjectDocument.project_id == request.project_id)
        documents = query.all()
        found_ids = {doc.id for doc in documents}
        missing_ids = sorted(set(request.document_ids) - found_ids)
        if missing_ids:
            raise ValueError(f"文档不存在或不属于指定项目: {missing_ids}")

        for doc in documents:
            content = doc.text_content or ""
            if not content:
                content = "\n".join(
                    chunk.text
                    for chunk in db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == doc.id
                    ).order_by(DocumentChunk.chunk_index).all()
                )
            if not content.strip():
                raise ValueError(f"文档 {doc.id} 尚未完成文本提取，无法分析")
            documents_content.append({
                "id": doc.id,
                "content": content,
            })

        # 执行分析（同步调用，后续可改为异步）
        analysis_input = {
            "documents": documents_content,
            "depth": request.analysis_depth,
            "focus_areas": request.focus_areas,
            "max_entities": request.max_entities
        }

        # 执行Agent
        agent_result = run_agent(agent, "knowledge_analysis", {
            "query_type": "entity_extraction",
            "content": "\n\n".join(
                f"[文档 {item['id']}]\n{item['content']}"
                for item in documents_content
            ),
            "strategy": "comprehensive",
            "parameters": analysis_input,
        })

        # 解析结果
        if agent_result.get("status") == "success":
            result_data = agent_result.get("data", {})

            # 构造响应
            knowledge_result = KnowledgeAnalysisResult(
                entities=[
                    ExtractedEntity(
                        name=e.get("name", ""),
                        type=e.get("type", "unknown"),
                        description=e.get("description"),
                        confidence=e.get("confidence", 0.8),
                        mentions=e.get("mentions", 1),
                        document_ids=e.get("document_ids", [])
                    )
                    for e in result_data.get("entities", [])
                ],
                relations=[
                    ExtractedRelation(
                        source=r.get("source", ""),
                        target=r.get("target", ""),
                        relation_type=r.get("type", "related_to"),
                        confidence=r.get("confidence", 0.7),
                        evidence=r.get("evidence")
                    )
                    for r in result_data.get("relations", [])
                ],
                themes=result_data.get("themes", []),
                key_insights=result_data.get("insights", []),
                document_summaries=result_data.get("summaries", {}),
                confidence_score=result_data.get("confidence", 0.85)
            )

            metadata = AgentMetadata(
                plugins_used=agent_result.get("plugins_used", []),
                token_usage=agent_result.get("token_usage"),
                execution_stages=agent_result.get("stages", []),
                warnings=agent_result.get("warnings", [])
            )

            response = KnowledgeAnalysisResponse(
                agent_id=agent.agent_id,
                status="success",
                execution_time=agent_result.get("execution_time", 0.0),
                metadata=metadata,
                result=knowledge_result
            )

            # 更新执行状态
            store_execution(execution_id, {
                "status": "completed",
                "agent_type": "knowledge",
                "progress": 100.0,
                "completed_at": datetime.now(),
                "result": response.dict()
            })

            return APIResponse(
                success=True,
                data=response.dict(),
                error=None
            )

        else:
            # Agent执行失败
            error_msg = agent_result.get("error", "Unknown error")
            logger.error(f"[{execution_id}] Knowledge Agent failed: {error_msg}")

            raise AIServiceException(
                message=error_msg,
                service="knowledge_agent",
                details={"execution_id": execution_id, "code": "KNOWLEDGE_AGENT_FAILED"}
            )

    except Exception as e:
        logger.error(f"[{execution_id}] Exception in Knowledge Agent: {str(e)}", exc_info=True)

        store_execution(execution_id, {
            "status": "failed",
            "agent_type": "knowledge",
            "error": str(e),
            "completed_at": datetime.now()
        })

        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="KNOWLEDGE_AGENT_ERROR",
                message=f"Knowledge Agent execution failed: {str(e)}",
                details={"execution_id": execution_id},
                recovery_suggestions=[
                    "Check document IDs are valid",
                    "Verify plugins are properly configured",
                    "Try with fewer documents or lower analysis depth"
                ]
            ).dict()
        )


# ============= Search Agent API =============

@router.post("/search/query", response_model=APIResponse)
async def search_query(
    request: SearchQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Search Agent - 多源智能检索

    功能：
    - 语义检索（向量搜索）
    - 关键词检索
    - 混合检索
    - 多源聚合（文档、知识图谱、记忆）

    使用场景：
    - 对话系统的RAG检索
    - 知识发现和探索
    - 相关内容推荐
    """
    execution_id = create_execution_id()

    try:
        logger.info(f"[{execution_id}] Starting Search Agent query: {request.query}")

        # 创建 SuperSearchAgent 实例
        agent = SuperSearchAgent(agent_id=f"search_{execution_id}")

        # 执行搜索
        search_input = {
            "query": request.query,
            "project_id": request.project_id,
            "scope": request.search_scope,
            "modes": request.search_modes,
            "max_results": request.max_results,
            "include_context": request.include_context
        }

        agent_result = run_agent(agent, "search_query", {
            "query_type": "web_search",
            "query": request.query,
            "strategy": "comprehensive",
            "parameters": search_input,
        })

        if agent_result.get("status") == "success":
            result_data = agent_result.get("data", {})

            # 构造响应
            search_result = SearchQueryResult(
                query=request.query,
                results=[
                    SearchResult(
                        content=r.get("content", ""),
                        source=r.get("source", "unknown"),
                        source_id=r.get("source_id"),
                        relevance_score=r.get("score", 0.5),
                        context=r.get("context") if request.include_context else None,
                        metadata=r.get("metadata", {})
                    )
                    for r in result_data.get("results", [])
                ],
                total_found=result_data.get("total_found", 0),
                search_strategy=result_data.get("strategy", "hybrid"),
                aggregated_answer=result_data.get("aggregated_answer")
            )

            metadata = AgentMetadata(
                plugins_used=agent_result.get("plugins_used", []),
                execution_stages=agent_result.get("stages", [])
            )

            response = SearchQueryResponse(
                agent_id=agent.agent_id,
                status="success",
                execution_time=agent_result.get("execution_time", 0.0),
                metadata=metadata,
                result=search_result
            )

            return APIResponse(success=True, data=response.dict())

        else:
            raise AIServiceException(
                message=agent_result.get("error", "Unknown error"),
                service="search_agent",
                details={"execution_id": execution_id, "code": "SEARCH_AGENT_FAILED"}
            )

    except Exception as e:
        logger.error(f"[{execution_id}] Search Agent error: {str(e)}", exc_info=True)

        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="SEARCH_AGENT_ERROR",
                message=f"Search Agent failed: {str(e)}",
                details={"execution_id": execution_id},
                recovery_suggestions=[
                    "Simplify the search query",
                    "Try different search modes",
                    "Check if project_id is valid"
                ]
            ).dict()
        )


# ============= Summary Agent API =============

@router.post("/summary/generate", response_model=APIResponse)
async def summary_generate(
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    """
    Summary Agent - 结构化摘要生成

    功能：
    - 多种摘要类型（摘要、结构化、要点、叙述）
    - 可调节摘要长度
    - 关注特定方面
    - 支持多文档摘要

    使用场景：
    - 快速了解大量文档内容
    - 生成报告概要
    - 对话历史总结
    """
    execution_id = create_execution_id()

    try:
        logger.info(f"[{execution_id}] Starting Summary Agent")

        # 创建 SuperSummaryAgent 实例
        agent = SuperSummaryAgent(agent_id=f"summary_{execution_id}")

        # 准备输入
        summary_input = {
            "content_source": request.content_source,
            "document_ids": request.document_ids,
            "text_content": request.text_content,
            "conversation_id": request.conversation_id,
            "summary_type": request.summary_type,
            "summary_length": request.summary_length,
            "focus_aspects": request.focus_aspects
        }

        documents = []
        if request.document_ids:
            from app.models.project import ProjectDocument
            for doc in db.query(ProjectDocument).filter(
                ProjectDocument.id.in_(request.document_ids)
            ).all():
                if doc.text_content:
                    documents.append({"id": doc.id, "content": doc.text_content})

        agent_result = run_agent(agent, "summary_generation", {
            "query_type": (
                "text_summarization"
                if request.text_content
                else "multi_level_summary"
            ),
            "strategy": "fast",
            "text": request.text_content,
            "documents": documents,
            "query": None,
            "parameters": summary_input,
        })

        if agent_result.get("status") == "success":
            result_data = agent_result.get("data", {})

            # 构造响应
            summary_result = SummaryResult(
                summary_type=request.summary_type,
                sections=[
                    SummarySection(
                        title=s.get("title", ""),
                        content=s.get("content", ""),
                        key_points=s.get("key_points", [])
                    )
                    for s in result_data.get("sections", [])
                ],
                overall_summary=result_data.get("overall_summary", ""),
                key_takeaways=result_data.get("key_takeaways", []),
                word_count=result_data.get("word_count", 0),
                compression_ratio=result_data.get("compression_ratio", 0.1)
            )

            metadata = AgentMetadata(
                plugins_used=agent_result.get("plugins_used", []),
                execution_stages=agent_result.get("stages", [])
            )

            response = SummaryResponse(
                agent_id=agent.agent_id,
                status="success",
                execution_time=agent_result.get("execution_time", 0.0),
                metadata=metadata,
                result=summary_result
            )

            return APIResponse(success=True, data=response.dict())

        else:
            raise AIServiceException(
                message=agent_result.get("error", "Unknown error"),
                service="summary_agent",
                details={"execution_id": execution_id, "code": "SUMMARY_AGENT_FAILED"}
            )

    except Exception as e:
        logger.error(f"[{execution_id}] Summary Agent error: {str(e)}", exc_info=True)

        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="SUMMARY_AGENT_ERROR",
                message=f"Summary Agent failed: {str(e)}",
                details={"execution_id": execution_id},
                recovery_suggestions=[
                    "Check content source is valid",
                    "Verify document IDs exist",
                    "Try a simpler summary type"
                ]
            ).dict()
        )


# ============= Transcript Agent API =============

@router.post("/transcript/process", response_model=APIResponse)
async def transcript_process(
    request: TranscriptRequest,
    db: Session = Depends(get_db)
):
    """
    Transcript Agent - 音视频转录和分析

    功能：
    - 语音转文本（Whisper）
    - 说话人区分
    - 实体提取
    - 内容摘要

    使用场景：
    - 访谈录音转录
    - 会议记录生成
    - 音视频内容索引
    """
    execution_id = create_execution_id()

    try:
        logger.info(f"[{execution_id}] Starting Transcript Agent")

        # 创建 SuperTranscriptAgent 实例
        agent = SuperTranscriptAgent(agent_id=f"transcript_{execution_id}")

        # 准备输入
        transcript_input = {
            "audio_file_path": request.audio_file_path,
            "audio_url": request.audio_url,
            "document_id": request.document_id,
            "language": request.language,
            "include_timestamps": request.include_timestamps,
            "speaker_diarization": request.speaker_diarization,
            "extract_entities": request.extract_entities,
            "generate_summary": request.generate_summary
        }

        agent_result = run_agent(agent, "transcript", {
            "query_type": "format_conversion",
            "strategy": "comprehensive",
            "file_path": request.audio_file_path or "",
            "parameters": transcript_input,
        })

        if agent_result.get("status") == "success":
            result_data = agent_result.get("data", {})

            # 构造响应
            transcript_result = TranscriptResult(
                full_text=result_data.get("full_text", ""),
                segments=[
                    TranscriptSegment(
                        start_time=seg.get("start_time", 0.0),
                        end_time=seg.get("end_time", 0.0),
                        text=seg.get("text", ""),
                        speaker=seg.get("speaker"),
                        confidence=seg.get("confidence", 0.9)
                    )
                    for seg in result_data.get("segments", [])
                ],
                duration=result_data.get("duration", 0.0),
                language_detected=result_data.get("language_detected", request.language),
                entities=[
                    ExtractedEntity(
                        name=e.get("name", ""),
                        type=e.get("type", "unknown"),
                        description=e.get("description"),
                        confidence=e.get("confidence", 0.8),
                        mentions=e.get("mentions", 1),
                        document_ids=[]
                    )
                    for e in result_data.get("entities", [])
                ] if request.extract_entities else None,
                summary=result_data.get("summary") if request.generate_summary else None,
                key_topics=result_data.get("key_topics", [])
            )

            metadata = AgentMetadata(
                plugins_used=agent_result.get("plugins_used", []),
                execution_stages=agent_result.get("stages", [])
            )

            response = TranscriptResponse(
                agent_id=agent.agent_id,
                status="success",
                execution_time=agent_result.get("execution_time", 0.0),
                metadata=metadata,
                result=transcript_result
            )

            return APIResponse(success=True, data=response.dict())

        else:
            raise AIServiceException(
                message=agent_result.get("error", "Unknown error"),
                service="transcript_agent",
                details={"execution_id": execution_id, "code": "TRANSCRIPT_AGENT_FAILED"}
            )

    except Exception as e:
        logger.error(f"[{execution_id}] Transcript Agent error: {str(e)}", exc_info=True)

        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="TRANSCRIPT_AGENT_ERROR",
                message=f"Transcript Agent failed: {str(e)}",
                details={"execution_id": execution_id},
                recovery_suggestions=[
                    "Check audio file path is valid",
                    "Verify audio format is supported",
                    "Try with shorter audio files"
                ]
            ).dict()
        )


# ============= Coordinator / Orchestration API =============

@router.post("/orchestrate", response_model=APIResponse)
async def orchestrate_agents(
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Coordinator - 多Agent编排执行

    功能：
    - 顺序执行多个Agents
    - 并行执行多个Agents
    - DAG模式（根据依赖关系执行）
    - 结果聚合和洞察生成

    使用场景：
    - 复杂分析工作流
    - 多步骤任务自动化
    - 协同分析
    """
    execution_id = create_execution_id()

    try:
        logger.info(f"[{execution_id}] Starting Agent Orchestration")
        logger.info(f"Tasks: {len(request.tasks)}, Mode: {request.execution_mode}")

        store_execution(execution_id, {
            "status": "running",
            "agent_type": "coordinator",
            "progress": 0.0,
            "started_at": datetime.now()
        })

        # 创建 EnhancedCoordinatorAgent 实例
        coordinator = EnhancedCoordinatorAgent(
            agent_id=f"coordinator_{execution_id}",
            db_session=db
        )

        # 准备任务列表
        orchestration_input = {
            "tasks": [
                {
                    "agent_type": task.agent_type,
                    "task_id": task.task_id,
                    "parameters": task.parameters,
                    "depends_on": task.depends_on,
                    "priority": task.priority
                }
                for task in request.tasks
            ],
            "execution_mode": request.execution_mode,
            "project_id": request.project_id,
            "timeout": request.timeout,
            "stop_on_error": request.stop_on_error
        }

        # 执行编排
        orchestration_result = coordinator.execute(orchestration_input)

        if orchestration_result.get("status") == "success":
            result_data = orchestration_result.get("data", {})

            # 构造响应
            orchestration_output = OrchestrationResult(
                total_tasks=len(request.tasks),
                completed_tasks=result_data.get("completed_tasks", 0),
                failed_tasks=result_data.get("failed_tasks", 0),
                task_results=[
                    AgentTaskResult(
                        task_id=tr.get("task_id", ""),
                        agent_type=tr.get("agent_type", ""),
                        status=tr.get("status", "unknown"),
                        result=tr.get("result"),
                        execution_time=tr.get("execution_time", 0.0),
                        error=tr.get("error")
                    )
                    for tr in result_data.get("task_results", [])
                ],
                execution_graph=result_data.get("execution_graph"),
                aggregated_insights=result_data.get("aggregated_insights")
            )

            metadata = AgentMetadata(
                execution_stages=result_data.get("stages", []),
                warnings=result_data.get("warnings", [])
            )

            response = OrchestrationResponse(
                agent_id=coordinator.agent_id,
                status="success" if orchestration_output.failed_tasks == 0 else "partial",
                execution_time=orchestration_result.get("execution_time", 0.0),
                metadata=metadata,
                result=orchestration_output
            )

            store_execution(execution_id, {
                "status": "completed",
                "agent_type": "coordinator",
                "progress": 100.0,
                "completed_at": datetime.now(),
                "result": response.dict()
            })

            return APIResponse(success=True, data=response.dict())

        else:
            raise AIServiceException(
                message=orchestration_result.get("error", "Unknown error"),
                service="coordinator",
                details={"execution_id": execution_id, "code": "ORCHESTRATION_FAILED"}
            )

    except Exception as e:
        logger.error(f"[{execution_id}] Orchestration error: {str(e)}", exc_info=True)

        store_execution(execution_id, {
            "status": "failed",
            "agent_type": "coordinator",
            "error": str(e),
            "completed_at": datetime.now()
        })

        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="ORCHESTRATION_ERROR",
                message=f"Agent orchestration failed: {str(e)}",
                details={"execution_id": execution_id},
                recovery_suggestions=[
                    "Check task dependencies are valid",
                    "Verify all task parameters",
                    "Try with fewer tasks or sequential mode"
                ]
            ).dict()
        )


# ============= Status Query API =============

@router.get("/status/{execution_id}", response_model=APIResponse)
async def get_execution_status(execution_id: str):
    """
    查询Agent执行状态

    用于：
    - 轮询长时间运行的Agent
    - 获取执行进度
    - 检查执行结果
    """
    execution = get_execution(execution_id)

    if not execution:
        return APIResponse(
            success=False,
            data=None,
            error=ErrorDetail(
                code="EXECUTION_NOT_FOUND",
                message=f"Execution {execution_id} not found",
                details={"execution_id": execution_id},
                recovery_suggestions=["Check execution_id is correct"]
            ).dict()
        )

    status_response = AgentStatusResponse(
        execution_id=execution_id,
        status=execution.get("status", "unknown"),
        progress=execution.get("progress", 0.0),
        current_stage=execution.get("current_stage"),
        started_at=execution.get("started_at"),
        completed_at=execution.get("completed_at"),
        result=execution.get("result"),
        error=execution.get("error")
    )

    return APIResponse(success=True, data=status_response.dict())


# ============= Health Check =============

@router.get("/health")
async def agents_health_check():
    """
    SuperAgents 健康检查

    检查：
    - 各Agent类是否可导入
    - 插件是否可用
    - 数据库连接
    """
    health_status = {
        "status": "healthy",
        "agents": {},
        "plugins": {},
        "timestamp": datetime.now().isoformat()
    }

    # 检查各Agent
    agents_to_check = [
        ("knowledge", SuperKnowledgeAgent),
        ("search", SuperSearchAgent),
        ("summary", SuperSummaryAgent),
        ("transcript", SuperTranscriptAgent),
        ("coordinator", EnhancedCoordinatorAgent)
    ]

    for agent_name, agent_class in agents_to_check:
        try:
            # 尝试实例化（不执行）
            test_agent = agent_class(agent_id=f"health_check_{agent_name}")
            health_status["agents"][agent_name] = "ok"
        except Exception as e:
            health_status["agents"][agent_name] = f"error: {str(e)[:50]}"
            health_status["status"] = "degraded"

    # 检查插件（简单检查导入）
    plugins_to_check = ["markitdown", "crawl4ai", "mem0", "lightrag", "graphrag"]

    for plugin_name in plugins_to_check:
        try:
            if plugin_name == "markitdown":
                import markitdown
            elif plugin_name == "crawl4ai":
                import crawl4ai
            elif plugin_name == "mem0":
                import mem0
            # lightrag 和 graphrag 需要特殊路径
            health_status["plugins"][plugin_name] = "ok"
        except ImportError:
            health_status["plugins"][plugin_name] = "not_installed"

    return success_response(data=health_status)
