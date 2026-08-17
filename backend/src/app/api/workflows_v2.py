"""
工作流API v2 - 使用6-Agent v2架构的真正v2 workflow
提供基于WorkflowV2Adapter的完整文档处理pipeline

完整6-Agent流程：
1. IngestionAgent - 文档加载
2. ChunkingAgent - 智能分块
3. VectorizationAgent - 向量化
4. KnowledgeAgent - 知识图谱构建 + Skills自动分析
5. SynthesisAgent - 综合洞察
6. ReportAgent - 报告生成
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import time

from app.core.database import get_db
from app.services.workflows.v2_adapter import get_v2_adapter, V2AgentResult

router = APIRouter(prefix="/api/v2/workflows", tags=["workflows-v2"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class V2WorkflowRequest(BaseModel):
    """v2 workflow执行请求"""
    project_id: int = Field(..., description="项目ID")
    document_ids: Optional[List[int]] = Field(None, description="文档ID列表（可选，不指定则处理项目所有文档）")

    # Pipeline配置
    enable_chunking: bool = Field(True, description="是否执行分块")
    enable_vectorization: bool = Field(True, description="是否执行向量化")
    enable_knowledge_graph: bool = Field(True, description="是否构建知识图谱")
    enable_skills_analysis: bool = Field(True, description="是否启用Skills分析（通过KnowledgeAgent自动执行）")
    enable_synthesis: bool = Field(True, description="是否生成综合洞察")
    enable_report: bool = Field(False, description="是否生成报告（耗时，可选）")

    # 报告配置
    report_type: str = Field("three_layer", description="报告类型：three_layer或traditional")
    report_level: Optional[str] = Field(None, description="报告详细度：brief/standard/detailed/comprehensive/dynamic")

    # 执行模式
    async_mode: bool = Field(False, description="是否异步执行（后台任务）")


class V2WorkflowStepResult(BaseModel):
    """v2 workflow单步执行结果"""
    step_name: str
    agent_type: str
    success: bool
    execution_time: float
    output_summary: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class V2WorkflowResponse(BaseModel):
    """v2 workflow执行响应"""
    success: bool
    message: str
    project_id: int
    workflow_id: str
    total_execution_time: float

    # 各步骤结果
    steps: List[V2WorkflowStepResult]

    # 最终输出摘要
    final_output: Dict[str, Any]


class V2AgentExecuteRequest(BaseModel):
    """单个v2 Agent执行请求（用于测试或手动调用）"""
    agent_type: str = Field(..., description="Agent类型：ingestion/chunking/vectorization/knowledge/synthesis/report")
    project_id: int = Field(..., description="项目ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class V2AgentExecuteResponse(BaseModel):
    """单个v2 Agent执行响应"""
    success: bool
    agent_type: str
    execution_time: float
    output_data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


# ==================== API接口 ====================

@router.post("/execute", response_model=V2WorkflowResponse)
async def execute_v2_workflow(
    request: V2WorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行完整的v2 workflow（6-Agent编排）

    与旧workflow的区别：
    - 旧版：使用UnifiedDocumentPipeline + workflow_engine
    - v2版：使用WorkflowV2Adapter + 6个v2 Agent
    - v2优势：Skills自动集成、真实数据流通、无防御性检查

    执行流程：
    1. IngestionAgent加载文档
    2. ChunkingAgent智能分块（支持表格、代码、图片）
    3. VectorizationAgent向量化
    4. KnowledgeAgent构建知识图谱 + 自动执行Skills分析
    5. SynthesisAgent生成综合洞察
    6. ReportAgent生成三层报告（可选）
    """
    if request.async_mode:
        # 异步模式：添加后台任务
        workflow_id = f"v2_workflow_{request.project_id}_{int(time.time())}"
        background_tasks.add_task(
            _execute_v2_workflow_background,
            workflow_id=workflow_id,
            request=request,
            db_session=db
        )

        return V2WorkflowResponse(
            success=True,
            message="v2 workflow已提交到后台执行",
            project_id=request.project_id,
            workflow_id=workflow_id,
            total_execution_time=0.0,
            steps=[],
            final_output={"status": "submitted", "workflow_id": workflow_id}
        )

    # 同步模式：立即执行
    workflow_id = f"v2_workflow_{request.project_id}_{int(time.time())}"

    try:
        result = await _execute_v2_workflow_sync(
            workflow_id=workflow_id,
            request=request,
            db_session=db
        )
        return result

    except Exception as e:
        logger.error(f"❌ v2 workflow执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"v2 workflow执行失败: {str(e)}")


@router.post("/execute_agent", response_model=V2AgentExecuteResponse)
async def execute_single_agent(
    request: V2AgentExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    执行单个v2 Agent（用于测试或手动编排）

    支持的agent_type：
    - ingestion: 文档加载
    - chunking: 智能分块
    - vectorization: 向量化
    - knowledge: 知识图谱构建（自动包含Skills分析）
    - synthesis: 综合洞察生成
    - report: 报告生成
    """
    try:
        adapter = get_v2_adapter()

        # 验证agent_type
        if not adapter.supports_agent_type(request.agent_type):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的agent_type: {request.agent_type}。支持的类型: ingestion, chunking, vectorization, knowledge, synthesis, report"
            )

        # 执行Agent
        result: V2AgentResult = adapter.execute_v2_agent(
            agent_type=request.agent_type,
            input_data={**request.input_data, 'project_id': request.project_id},
            db_session=db,
            metadata=request.metadata
        )

        return V2AgentExecuteResponse(
            success=result.success,
            agent_type=result.agent_type,
            execution_time=result.execution_time,
            output_data=result.output_data,
            errors=result.errors,
            warnings=result.warnings
        )

    except Exception as e:
        logger.error(f"❌ v2 Agent {request.agent_type} 执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent执行失败: {str(e)}")


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    获取v2 workflow执行状态（用于异步模式）

    TODO: 需要实现workflow状态持久化和查询
    当前返回placeholder
    """
    # TODO: 从数据库或缓存中查询workflow状态
    return {
        "workflow_id": workflow_id,
        "status": "unknown",
        "message": "状态查询功能待实现（需要workflow状态表）"
    }


@router.get("/agents")
async def list_available_agents():
    """
    列出所有可用的v2 Agent
    """
    adapter = get_v2_adapter()

    agents_info = {
        "ingestion": {
            "name": "IngestionAgent",
            "description": "文档加载Agent",
            "input": "project_id",
            "output": "documents列表"
        },
        "chunking": {
            "name": "ChunkingAgent",
            "description": "智能分块Agent（支持表格、代码、图片）",
            "input": "documents列表",
            "output": "chunks列表 + chunk_ids"
        },
        "vectorization": {
            "name": "VectorizationAgent",
            "description": "向量化Agent",
            "input": "chunk_ids",
            "output": "vectorized_count"
        },
        "knowledge": {
            "name": "KnowledgeAgent",
            "description": "知识图谱构建Agent（自动包含Skills分析）",
            "input": "project_id, documents",
            "output": "knowledge_graph + skills_result",
            "features": ["自动Skills分析", "实体关系提取", "时间线构建"]
        },
        "synthesis": {
            "name": "SynthesisAgent",
            "description": "综合洞察生成Agent",
            "input": "project_id",
            "output": "synthesis_insights"
        },
        "report": {
            "name": "ReportAgent",
            "description": "报告生成Agent（支持三层报告和传统报告）",
            "input": "project_id, report_type",
            "output": "report_id + report_structure"
        }
    }

    return {
        "total_agents": len(agents_info),
        "agents": agents_info,
        "note": "所有Agent通过WorkflowV2Adapter统一编排"
    }


# ==================== 内部执行函数 ====================

async def _execute_v2_workflow_sync(
    workflow_id: str,
    request: V2WorkflowRequest,
    db_session: Session
) -> V2WorkflowResponse:
    """
    同步执行完整v2 workflow
    真实完整执行，不跳过任何步骤
    """
    adapter = get_v2_adapter()
    steps_results = []
    overall_start_time = time.time()

    # 用于在步骤间传递数据
    pipeline_data = {
        'project_id': request.project_id,
        'document_ids': request.document_ids
    }

    try:
        # ==================== 步骤1: IngestionAgent ====================
        logger.info(f"🚀 [v2 Workflow] 步骤1/6: IngestionAgent - 加载文档")

        ingestion_result = adapter.execute_v2_agent(
            agent_type='ingestion',
            input_data={'project_id': request.project_id},
            db_session=db_session
        )

        steps_results.append(V2WorkflowStepResult(
            step_name="文档加载",
            agent_type="ingestion",
            success=ingestion_result.success,
            execution_time=ingestion_result.execution_time,
            output_summary={
                'document_count': ingestion_result.output_data.get('document_count', 0)
            },
            errors=ingestion_result.errors,
            warnings=ingestion_result.warnings
        ))

        if not ingestion_result.success:
            raise RuntimeError(f"IngestionAgent失败: {ingestion_result.errors}")

        # 获取文档列表
        documents = ingestion_result.output_data.get('documents', [])
        if not documents:
            raise ValueError(f"项目 {request.project_id} 没有文档")

        pipeline_data['documents'] = documents
        logger.info(f"✅ IngestionAgent完成，加载了 {len(documents)} 个文档")

        # ==================== 步骤2: ChunkingAgent ====================
        if request.enable_chunking:
            logger.info(f"🚀 [v2 Workflow] 步骤2/6: ChunkingAgent - 智能分块")

            chunking_result = adapter.execute_v2_agent(
                agent_type='chunking',
                input_data={
                    'project_id': request.project_id,
                    'documents': documents
                },
                db_session=db_session
            )

            steps_results.append(V2WorkflowStepResult(
                step_name="智能分块",
                agent_type="chunking",
                success=chunking_result.success,
                execution_time=chunking_result.execution_time,
                output_summary={
                    'total_chunks': chunking_result.output_data.get('total_chunks', 0),
                    'failed_docs': len(chunking_result.output_data.get('failed_docs', []))
                },
                errors=chunking_result.errors,
                warnings=chunking_result.warnings
            ))

            if not chunking_result.success:
                raise RuntimeError(f"ChunkingAgent失败: {chunking_result.errors}")

            # 获取chunk_ids
            chunk_ids = chunking_result.output_data.get('chunk_ids', [])
            if not chunk_ids:
                raise ValueError("ChunkingAgent没有返回chunk_ids")

            pipeline_data['chunk_ids'] = chunk_ids
            logger.info(f"✅ ChunkingAgent完成，生成了 {len(chunk_ids)} 个chunks")
        else:
            logger.info(f"⏭️  跳过ChunkingAgent（enable_chunking=False）")

        # ==================== 步骤3: VectorizationAgent ====================
        if request.enable_vectorization and request.enable_chunking:
            logger.info(f"🚀 [v2 Workflow] 步骤3/6: VectorizationAgent - 向量化")

            vectorization_result = adapter.execute_v2_agent(
                agent_type='vectorization',
                input_data={
                    'project_id': request.project_id,
                    'chunk_ids': pipeline_data.get('chunk_ids', [])
                },
                db_session=db_session
            )

            steps_results.append(V2WorkflowStepResult(
                step_name="向量化",
                agent_type="vectorization",
                success=vectorization_result.success,
                execution_time=vectorization_result.execution_time,
                output_summary={
                    'vectorized_count': vectorization_result.output_data.get('vectorized_count', 0)
                },
                errors=vectorization_result.errors,
                warnings=vectorization_result.warnings
            ))

            if not vectorization_result.success:
                raise RuntimeError(f"VectorizationAgent失败: {vectorization_result.errors}")

            logger.info(f"✅ VectorizationAgent完成，向量化了 {vectorization_result.output_data.get('vectorized_count', 0)} 个chunks")
        else:
            logger.info(f"⏭️  跳过VectorizationAgent（enable_vectorization={request.enable_vectorization}）")

        # ==================== 步骤4: KnowledgeAgent ====================
        if request.enable_knowledge_graph:
            logger.info(f"🚀 [v2 Workflow] 步骤4/6: KnowledgeAgent - 知识图谱构建 + Skills分析")

            knowledge_result = adapter.execute_v2_agent(
                agent_type='knowledge',
                input_data={
                    'project_id': request.project_id,
                    'documents': pipeline_data.get('documents', []),
                    'enable_skills_analysis': request.enable_skills_analysis  # 传递Skills开关
                },
                db_session=db_session
            )

            steps_results.append(V2WorkflowStepResult(
                step_name="知识图谱构建",
                agent_type="knowledge",
                success=knowledge_result.success,
                execution_time=knowledge_result.execution_time,
                output_summary={
                    'entity_count': knowledge_result.output_data.get('entity_count', 0),
                    'relation_count': knowledge_result.output_data.get('relation_count', 0),
                    'skills_executed': knowledge_result.output_data.get('skills_executed', []) if request.enable_skills_analysis else []
                },
                errors=knowledge_result.errors,
                warnings=knowledge_result.warnings
            ))

            if not knowledge_result.success:
                raise RuntimeError(f"KnowledgeAgent失败: {knowledge_result.errors}")

            pipeline_data['knowledge_graph'] = knowledge_result.output_data
            logger.info(f"✅ KnowledgeAgent完成，构建了 {knowledge_result.output_data.get('entity_count', 0)} 个实体")

            if request.enable_skills_analysis:
                skills_count = len(knowledge_result.output_data.get('skills_executed', []))
                logger.info(f"✅ Skills分析完成，执行了 {skills_count} 个Skills")
        else:
            logger.info(f"⏭️  跳过KnowledgeAgent（enable_knowledge_graph=False）")

        # ==================== 步骤5: SynthesisAgent ====================
        if request.enable_synthesis:
            logger.info(f"🚀 [v2 Workflow] 步骤5/6: SynthesisAgent - 综合洞察生成")

            synthesis_result = adapter.execute_v2_agent(
                agent_type='synthesis',
                input_data={
                    'project_id': request.project_id
                },
                db_session=db_session,
                metadata=pipeline_data
            )

            steps_results.append(V2WorkflowStepResult(
                step_name="综合洞察生成",
                agent_type="synthesis",
                success=synthesis_result.success,
                execution_time=synthesis_result.execution_time,
                output_summary={
                    'synthesis_id': synthesis_result.output_data.get('synthesis_id'),
                    'insight_count': synthesis_result.output_data.get('insight_count', 0)
                },
                errors=synthesis_result.errors,
                warnings=synthesis_result.warnings
            ))

            if not synthesis_result.success:
                raise RuntimeError(f"SynthesisAgent失败: {synthesis_result.errors}")

            pipeline_data['synthesis_result'] = synthesis_result.output_data
            logger.info(f"✅ SynthesisAgent完成，生成了综合洞察")
        else:
            logger.info(f"⏭️  跳过SynthesisAgent（enable_synthesis=False）")

        # ==================== 步骤6: ReportAgent ====================
        if request.enable_report:
            logger.info(f"🚀 [v2 Workflow] 步骤6/6: ReportAgent - 报告生成")

            report_result = adapter.execute_v2_agent(
                agent_type='report',
                input_data={
                    'project_id': request.project_id,
                    'report_type': request.report_type,
                    'report_level': request.report_level,
                    'synthesis_result_id': pipeline_data.get('synthesis_result', {}).get('synthesis_id')
                },
                db_session=db_session,
                metadata=pipeline_data
            )

            steps_results.append(V2WorkflowStepResult(
                step_name="报告生成",
                agent_type="report",
                success=report_result.success,
                execution_time=report_result.execution_time,
                output_summary={
                    'report_type': report_result.output_data.get('report_type'),
                    'total_words': report_result.output_data.get('total_words', 0)
                },
                errors=report_result.errors,
                warnings=report_result.warnings
            ))

            if not report_result.success:
                raise RuntimeError(f"ReportAgent失败: {report_result.errors}")

            pipeline_data['report'] = report_result.output_data
            logger.info(f"✅ ReportAgent完成，生成了报告")
        else:
            logger.info(f"⏭️  跳过ReportAgent（enable_report=False）")

        # ==================== 完成 ====================
        total_time = time.time() - overall_start_time

        logger.info(f"🎉 [v2 Workflow] 完整pipeline执行完成，总耗时 {total_time:.2f}秒")

        return V2WorkflowResponse(
            success=True,
            message=f"v2 workflow执行成功，共执行 {len(steps_results)} 个步骤",
            project_id=request.project_id,
            workflow_id=workflow_id,
            total_execution_time=total_time,
            steps=steps_results,
            final_output={
                'document_count': len(pipeline_data.get('documents', [])),
                'chunk_count': len(pipeline_data.get('chunk_ids', [])),
                'knowledge_graph': pipeline_data.get('knowledge_graph', {}).get('entity_count', 0) if request.enable_knowledge_graph else None,
                'synthesis_generated': request.enable_synthesis,
                'report_generated': request.enable_report
            }
        )

    except Exception as e:
        total_time = time.time() - overall_start_time
        logger.error(f"❌ [v2 Workflow] 执行失败: {e}", exc_info=True)

        return V2WorkflowResponse(
            success=False,
            message=f"v2 workflow执行失败: {str(e)}",
            project_id=request.project_id,
            workflow_id=workflow_id,
            total_execution_time=total_time,
            steps=steps_results,
            final_output={'error': str(e)}
        )


def _execute_v2_workflow_background(
    workflow_id: str,
    request: V2WorkflowRequest,
    db_session: Session
):
    """
    后台异步执行v2 workflow

    TODO:
    1. 需要持久化workflow状态到数据库
    2. 需要实现进度更新机制
    3. 需要实现结果通知机制
    """
    import asyncio

    logger.info(f"🔄 [后台任务] 开始执行v2 workflow: {workflow_id}")

    try:
        # 在后台执行同步函数
        result = asyncio.run(_execute_v2_workflow_sync(
            workflow_id=workflow_id,
            request=request,
            db_session=db_session
        ))

        logger.info(f"✅ [后台任务] v2 workflow完成: {workflow_id}")

        # TODO: 将结果存储到数据库或缓存

    except Exception as e:
        logger.error(f"❌ [后台任务] v2 workflow失败: {workflow_id}, error: {e}", exc_info=True)
        # TODO: 记录失败状态到数据库
