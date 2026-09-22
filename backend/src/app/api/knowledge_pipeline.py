"""
知识流水线 API 路由
Knowledge Pipeline API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.knowledge import PipelineExecution
from app.services.knowledge_pipeline.orchestrator import KnowledgePipelineOrchestrator
from pydantic import BaseModel, Field

router = APIRouter(prefix="/knowledge-pipeline", tags=["Knowledge Pipeline"])


# ==================== Schemas ====================

class PipelineStartRequest(BaseModel):
    """启动流水线请求"""
    document_id: str = Field(..., description="文档ID")
    project_id: str = Field(..., description="项目ID")
    enable_statistical_cleaning: bool = Field(True, description="启用统计清洗")
    enable_llm_cleaning: bool = Field(False, description="启用LLM清洗")
    max_retries: int = Field(3, ge=1, le=10, description="最大重试次数")


class PipelineStatusResponse(BaseModel):
    """流水线状态响应"""
    execution_id: str
    status: str
    current_step: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    duration: Optional[float]
    completed_steps: List[str]
    errors: dict


class PipelineResultResponse(BaseModel):
    """流水线结果响应"""
    execution_id: str
    status: str
    duration: Optional[float]
    results: dict
    errors: dict


# ==================== 背景任务存储 ====================
# 用于跟踪后台执行的流水线
active_pipelines = {}


# ==================== API 端点 ====================

@router.post("/start", response_model=dict)
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启动知识构建流水线（后台任务）

    九步流程：
    1. 文本校刊（三层清洗）
    2. 结构分析
    3. 实体构建（NER + 消歧 + 共指）
    4. 事件提取（5W1H）
    5. 关系发现
    6. 本体构建（核心步骤）
    7. 逻辑推理
    8. 知识单元化
    9. 阅读器生成
    """
    # 验证文档存在
    from app.models.document import Document
    from sqlalchemy import select

    stmt = select(Document).where(
        Document.id == request.document_id,
        Document.project_id == request.project_id
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 检查权限（用户是否属于该项目）
    from app.models.project import Project
    stmt = select(Project).where(Project.id == request.project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取文档文本
    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no content")

    text = document.content

    # 创建流水线编排器
    orchestrator = KnowledgePipelineOrchestrator(
        document_id=request.document_id,
        project_id=request.project_id,
        user_id=current_user.id,
        db_session=db,
        llm_service=None  # TODO: 注入 LLM 服务
    )

    # 保存到活动流水线字典
    execution_id = f"exec_{request.document_id}_{int(datetime.utcnow().timestamp())}"
    active_pipelines[execution_id] = orchestrator

    # 添加后台任务
    async def run_pipeline():
        try:
            await orchestrator.execute(
                text=text,
                enable_statistical_cleaning=request.enable_statistical_cleaning,
                enable_llm_cleaning=request.enable_llm_cleaning,
                max_retries=request.max_retries
            )
        except Exception as e:
            print(f"Pipeline execution error: {e}")
        finally:
            # 执行完成后从活动字典中移除
            active_pipelines.pop(execution_id, None)

    background_tasks.add_task(run_pipeline)

    return {
        "execution_id": execution_id,
        "status": "running",
        "message": "知识构建流水线已在后台启动"
    }


@router.get("/status/{execution_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取流水线执行状态
    """
    # 先检查活动流水线
    if execution_id in active_pipelines:
        orchestrator = active_pipelines[execution_id]
        status = orchestrator.get_status()
        return PipelineStatusResponse(**status)

    # 检查数据库
    from sqlalchemy import select
    stmt = select(PipelineExecution).where(PipelineExecution.id == execution_id)
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")

    # 计算时长
    duration = None
    if execution.end_time and execution.start_time:
        duration = (execution.end_time - execution.start_time).total_seconds()

    return PipelineStatusResponse(
        execution_id=execution.id,
        status=execution.status,
        current_step=execution.current_step,
        start_time=execution.start_time.isoformat() if execution.start_time else None,
        end_time=execution.end_time.isoformat() if execution.end_time else None,
        duration=duration,
        completed_steps=list(execution.results.keys()) if execution.results else [],
        errors=execution.errors or {}
    )


@router.get("/results/{execution_id}", response_model=PipelineResultResponse)
async def get_pipeline_results(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取流水线执行结果
    """
    from sqlalchemy import select
    stmt = select(PipelineExecution).where(PipelineExecution.id == execution_id)
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")

    if execution.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline execution is not completed yet. Current status: {execution.status}"
        )

    # 计算时长
    duration = None
    if execution.end_time and execution.start_time:
        duration = (execution.end_time - execution.start_time).total_seconds()

    return PipelineResultResponse(
        execution_id=execution.id,
        status=execution.status,
        duration=duration,
        results=execution.results or {},
        errors=execution.errors or {}
    )


@router.post("/retry/{execution_id}", response_model=dict)
async def retry_pipeline(
    execution_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重试失败的流水线执行
    """
    from sqlalchemy import select
    stmt = select(PipelineExecution).where(PipelineExecution.id == execution_id)
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")

    if execution.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed executions. Current status: {execution.status}"
        )

    # 获取原始文档
    from app.models.document import Document
    stmt = select(Document).where(Document.id == execution.document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Original document not found")

    # 创建新的流水线编排器
    new_execution_id = f"exec_{execution.document_id}_{int(datetime.utcnow().timestamp())}_retry"

    orchestrator = KnowledgePipelineOrchestrator(
        document_id=execution.document_id,
        project_id=execution.project_id,
        user_id=current_user.id,
        db_session=db,
        llm_service=None
    )

    active_pipelines[new_execution_id] = orchestrator

    # 添加后台任务
    async def run_pipeline():
        try:
            await orchestrator.execute(
                text=document.content,
                enable_statistical_cleaning=True,
                enable_llm_cleaning=False,
                max_retries=3
            )
        except Exception as e:
            print(f"Pipeline retry error: {e}")
        finally:
            active_pipelines.pop(new_execution_id, None)

    background_tasks.add_task(run_pipeline)

    return {
        "execution_id": new_execution_id,
        "status": "running",
        "message": "流水线重试已启动"
    }


@router.delete("/cancel/{execution_id}")
async def cancel_pipeline(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消正在运行的流水线
    """
    if execution_id not in active_pipelines:
        raise HTTPException(
            status_code=404,
            detail="Pipeline execution not found or already completed"
        )

    orchestrator = active_pipelines[execution_id]
    orchestrator.status = "cancelled"

    # 从活动字典中移除
    active_pipelines.pop(execution_id, None)

    return {
        "execution_id": execution_id,
        "status": "cancelled",
        "message": "流水线已取消"
    }


@router.get("/list", response_model=List[dict])
async def list_pipeline_executions(
    project_id: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出流水线执行记录
    """
    from sqlalchemy import select, desc

    stmt = select(PipelineExecution).where(PipelineExecution.user_id == current_user.id)

    if project_id:
        stmt = stmt.where(PipelineExecution.project_id == project_id)

    if document_id:
        stmt = stmt.where(PipelineExecution.document_id == document_id)

    if status:
        stmt = stmt.where(PipelineExecution.status == status)

    stmt = stmt.order_by(desc(PipelineExecution.created_at))
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    executions = result.scalars().all()

    return [
        {
            "execution_id": exec.id,
            "document_id": exec.document_id,
            "project_id": exec.project_id,
            "status": exec.status,
            "current_step": exec.current_step,
            "start_time": exec.start_time.isoformat() if exec.start_time else None,
            "end_time": exec.end_time.isoformat() if exec.end_time else None,
            "created_at": exec.created_at.isoformat() if exec.created_at else None
        }
        for exec in executions
    ]


@router.get("/statistics/{project_id}")
async def get_pipeline_statistics(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目的流水线统计信息
    """
    from sqlalchemy import select, func
    from app.models.knowledge import (
        KnowledgeEntity,
        KnowledgeRelation,
        KnowledgeEvent,
        KnowledgeUnit
    )

    # 统计实体数量
    stmt = select(func.count(KnowledgeEntity.id)).where(
        KnowledgeEntity.project_id == project_id
    )
    result = await db.execute(stmt)
    entity_count = result.scalar() or 0

    # 统计关系数量
    stmt = select(func.count(KnowledgeRelation.id)).where(
        KnowledgeRelation.project_id == project_id
    )
    result = await db.execute(stmt)
    relation_count = result.scalar() or 0

    # 统计事件数量
    stmt = select(func.count(KnowledgeEvent.id)).where(
        KnowledgeEvent.project_id == project_id
    )
    result = await db.execute(stmt)
    event_count = result.scalar() or 0

    # 统计知识单元数量
    stmt = select(func.count(KnowledgeUnit.id)).where(
        KnowledgeUnit.project_id == project_id
    )
    result = await db.execute(stmt)
    knowledge_unit_count = result.scalar() or 0

    # 统计流水线执行次数
    stmt = select(func.count(PipelineExecution.id)).where(
        PipelineExecution.project_id == project_id
    )
    result = await db.execute(stmt)
    execution_count = result.scalar() or 0

    # 统计成功率
    stmt = select(func.count(PipelineExecution.id)).where(
        PipelineExecution.project_id == project_id,
        PipelineExecution.status == "completed"
    )
    result = await db.execute(stmt)
    success_count = result.scalar() or 0

    success_rate = (success_count / execution_count * 100) if execution_count > 0 else 0

    return {
        "project_id": project_id,
        "entity_count": entity_count,
        "relation_count": relation_count,
        "event_count": event_count,
        "knowledge_unit_count": knowledge_unit_count,
        "execution_count": execution_count,
        "success_count": success_count,
        "success_rate": round(success_rate, 2)
    }
