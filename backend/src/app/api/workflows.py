"""
工作流API - 链路十二：工作流编排与执行
提供工作流创建、执行、监控等功能
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.workflow_engine import workflow_engine, WorkflowStatus, TaskStatus
from app.services.workflow_templates import (
    WorkflowTemplates,
    run_document_workflow,
    run_knowledge_graph_workflow,
    run_full_analysis_workflow
)

router = APIRouter(tags=["workflows"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    workflow_type: str  # document_processing, knowledge_graph, full_analysis
    project_id: int
    document_ids: Optional[List[int]] = None
    params: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    workflow_id: str
    workflow_name: str
    status: str
    message: str


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_id: str
    workflow_name: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    task_results: Dict[str, Any]
    metadata: Dict[str, Any]


# ==================== API接口 ====================

@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行工作流

    支持的工作流类型：
    - document_processing: 文档处理（向量化+实体提取+关键词）
    - knowledge_graph: 知识图谱构建（实体+关系+时间线）
    - full_analysis: 完整分析（文档处理+知识图谱+报告）
    """
    try:
        logger.info(f"🚀 执行工作流: {request.workflow_type}, project_id={request.project_id}")

        if request.workflow_type == "document_processing":
            # 文档处理工作流
            if not request.document_ids or len(request.document_ids) == 0:
                raise HTTPException(status_code=400, detail="document_ids不能为空")

            document_id = request.document_ids[0]
            workflow = WorkflowTemplates.create_document_processing_workflow(
                workflow_engine,
                document_id,
                request.project_id
            )

        elif request.workflow_type == "knowledge_graph":
            # 知识图谱构建工作流
            workflow = WorkflowTemplates.create_knowledge_graph_workflow(
                workflow_engine,
                request.project_id,
                request.document_ids
            )

        elif request.workflow_type == "full_analysis":
            # 完整分析工作流
            workflow = WorkflowTemplates.create_full_analysis_workflow(
                workflow_engine,
                request.project_id
            )

        else:
            raise HTTPException(status_code=400, detail=f"不支持的工作流类型: {request.workflow_type}")

        # 执行工作流
        execution = workflow_engine.execute_workflow(workflow)

        return WorkflowExecutionResponse(
            workflow_id=execution.workflow_id,
            workflow_name=execution.workflow_name,
            status=execution.status.value,
            message=f"工作流 {execution.workflow_name} 执行{'成功' if execution.status == WorkflowStatus.COMPLETED else '失败'}"
        )

    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    获取工作流执行状态

    返回工作流的详细执行信息，包括每个任务的状态和结果
    """
    execution = workflow_engine.get_execution(workflow_id)

    if not execution:
        raise HTTPException(status_code=404, detail="工作流不存在")

    return WorkflowStatusResponse(
        workflow_id=execution.workflow_id,
        workflow_name=execution.workflow_name,
        status=execution.status.value,
        start_time=execution.start_time.isoformat() if execution.start_time else None,
        end_time=execution.end_time.isoformat() if execution.end_time else None,
        task_results={
            name: {
                "status": result.status.value,
                "result": result.result,
                "error": result.error,
                "duration": result.duration_seconds
            }
            for name, result in execution.task_results.items()
        },
        metadata=execution.metadata
    )


@router.get("/")
async def list_workflows(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    列出所有工作流执行记录

    - status: 过滤状态（running, completed, failed）
    - limit: 返回数量
    """
    executions = workflow_engine.list_executions()

    # 状态过滤
    if status:
        try:
            status_enum = WorkflowStatus(status)
            executions = [e for e in executions if e.status == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")

    # 排序：最新的在前
    executions.sort(key=lambda x: x.created_at, reverse=True)

    # 限制数量
    executions = executions[:limit]

    return {
        "total": len(executions),
        "workflows": [
            {
                "workflow_id": e.workflow_id,
                "workflow_name": e.workflow_name,
                "status": e.status.value,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "created_at": e.created_at.isoformat(),
                "task_count": len(e.task_results),
                "completed_tasks": sum(1 for t in e.task_results.values() if t.status == TaskStatus.COMPLETED),
                "failed_tasks": sum(1 for t in e.task_results.values() if t.status == TaskStatus.FAILED)
            }
            for e in executions
        ]
    }


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    取消正在执行的工作流

    注意：仅标记为已取消，无法中断正在执行的任务
    """
    success = workflow_engine.cancel_workflow(workflow_id)

    if not success:
        raise HTTPException(status_code=400, detail="无法取消工作流（不存在或已完成）")

    return {"message": f"工作流 {workflow_id} 已取消"}


@router.get("/templates/list")
async def list_workflow_templates():
    """
    列出所有可用的工作流模板

    返回预定义的工作流模板列表及其描述
    """
    return {
        "templates": [
            {
                "type": "document_processing",
                "name": "文档处理工作流",
                "description": "对单个文档进行完整处理：提取文本 → 向量化 → 实体提取 → 关键词提取 → 更新状态",
                "required_params": ["project_id", "document_ids"],
                "steps": [
                    "提取文本内容",
                    "向量化存储",
                    "实体识别",
                    "关键词提取",
                    "更新文档状态"
                ]
            },
            {
                "type": "knowledge_graph",
                "name": "知识图谱构建工作流",
                "description": "从文档构建知识图谱：获取文档 → 提取实体 → 提取关系 → 构建时间线",
                "required_params": ["project_id"],
                "optional_params": ["document_ids"],
                "steps": [
                    "获取文档列表",
                    "批量提取实体",
                    "提取实体关系",
                    "构建时间线"
                ]
            },
            {
                "type": "full_analysis",
                "name": "完整分析工作流",
                "description": "项目完整分析：文档处理 → 知识图谱构建 → 生成分析报告",
                "required_params": ["project_id"],
                "steps": [
                    "获取项目文档",
                    "批量处理文档",
                    "构建知识图谱",
                    "生成分析报告"
                ]
            }
        ]
    }


@router.get("/stats")
async def get_workflow_stats(db: Session = Depends(get_db)):
    """
    获取工作流系统统计信息

    返回总执行次数、成功率、平均执行时间等
    """
    executions = workflow_engine.list_executions()

    total = len(executions)
    if total == 0:
        return {
            "total_executions": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "success_rate": 0.0
        }

    running = sum(1 for e in executions if e.status == WorkflowStatus.RUNNING)
    completed = sum(1 for e in executions if e.status == WorkflowStatus.COMPLETED)
    failed = sum(1 for e in executions if e.status == WorkflowStatus.FAILED)
    cancelled = sum(1 for e in executions if e.status == WorkflowStatus.CANCELLED)

    success_rate = (completed / total * 100) if total > 0 else 0.0

    # 计算平均执行时间
    durations = []
    for e in executions:
        if e.start_time and e.end_time:
            duration = (e.end_time - e.start_time).total_seconds()
            durations.append(duration)

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return {
        "total_executions": total,
        "running": running,
        "completed": completed,
        "failed": failed,
        "cancelled": cancelled,
        "success_rate": round(success_rate, 2),
        "average_duration_seconds": round(avg_duration, 2)
    }


# ==================== 快捷接口（简化调用） ====================

@router.post("/quick/document/{document_id}")
async def quick_process_document(
    document_id: int,
    project_id: int,
    background_tasks: BackgroundTasks
):
    """
    快捷接口：处理单个文档

    自动执行完整的文档处理流程
    """
    try:
        result = run_document_workflow(document_id, project_id)
        return {
            "message": "文档处理工作流已完成",
            "workflow_id": result["workflow_id"],
            "status": result["status"]
        }
    except Exception as e:
        logger.error(f"快捷文档处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick/knowledge-graph")
async def quick_build_knowledge_graph(
    project_id: int,
    document_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = None
):
    """
    快捷接口：构建知识图谱

    自动执行知识图谱构建流程
    """
    try:
        result = run_knowledge_graph_workflow(project_id, document_ids)
        return {
            "message": "知识图谱构建工作流已完成",
            "workflow_id": result["workflow_id"],
            "status": result["status"]
        }
    except Exception as e:
        logger.error(f"快捷知识图谱构建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick/full-analysis")
async def quick_full_analysis(
    project_id: int,
    background_tasks: BackgroundTasks
):
    """
    快捷接口：完整项目分析

    自动执行完整分析流程：文档处理 + 知识图谱 + 报告生成
    """
    try:
        result = run_full_analysis_workflow(project_id)
        return {
            "message": "完整分析工作流已完成",
            "workflow_id": result["workflow_id"],
            "status": result["status"],
            "summary": result.get("task_results", {}).get("generate_report", {})
        }
    except Exception as e:
        logger.error(f"快捷完整分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
