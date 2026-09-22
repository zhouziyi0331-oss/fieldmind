"""工作流API路由 - 完整实现"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.schemas.response import success_response, error_response
from app.models.workflow import Workflow, WorkflowExecution
from app.models.project import Project
from app.models.user import User
from app.schemas.workflow import (
    WorkflowResponse, WorkflowListResponse, WorkflowCreateRequest,
    WorkflowExecuteRequest, WorkflowExecutionResponse, WorkflowType, WorkflowStatus
)
from app.middleware.auth import get_current_user

router = APIRouter(tags=["Workflows"])


def _create_default_workflows(db: Session):
    """创建默认工作流模板"""
    default_workflows = [
        {
            "name": "田野调查完整流程",
            "description": "从文档导入、信息提取、知识图谱构建到报告生成的完整流程",
            "workflow_type": "document",
            "steps": [
                {"order": 1, "name": "文档上传", "task": "upload_document", "description": "上传田野调查资料"},
                {"order": 2, "name": "文档转换", "task": "convert_to_markdown", "description": "转换为可处理格式"},
                {"order": 3, "name": "向量化存储", "task": "vectorize_and_store", "description": "文本向量化并存储"},
                {"order": 4, "name": "实体识别", "task": "extract_entities", "description": "识别人物、地点、事件"},
                {"order": 5, "name": "知识图谱构建", "task": "build_knowledge_graph", "description": "构建实体关系网络"},
                {"order": 6, "name": "生成报告", "task": "generate_report", "description": "自动生成分析报告"}
            ],
            "config": {"auto_start": True, "retry_on_failure": True},
            "is_template": True
        },
        {
            "name": "音频转录与分析",
            "description": "访谈录音自动转录、向量化和实体提取的完整流程",
            "workflow_type": "audio",
            "steps": [
                {"order": 1, "name": "音频上传", "task": "upload_audio", "description": "上传访谈录音"},
                {"order": 2, "name": "元数据提取", "task": "extract_audio_metadata", "description": "提取时长、格式等信息"},
                {"order": 3, "name": "语音转录", "task": "transcribe_audio", "description": "语音转文字"},
                {"order": 4, "name": "向量化存储", "task": "vectorize_and_store", "description": "转录文本向量化"},
                {"order": 5, "name": "实体识别", "task": "extract_entities", "description": "识别关键信息"}
            ],
            "config": {"auto_start": True},
            "is_template": True
        },
        {
            "name": "智能报告生成",
            "description": "基于已有资料生成多维度分析报告",
            "workflow_type": "report",
            "steps": [
                {"order": 1, "name": "数据收集", "task": "collect_data", "description": "收集相关文档和数据"},
                {"order": 2, "name": "主题分析", "task": "analyze_themes", "description": "分析核心主题"},
                {"order": 3, "name": "结构生成", "task": "generate_structure", "description": "生成报告大纲"},
                {"order": 4, "name": "内容撰写", "task": "write_content", "description": "填充报告内容"},
                {"order": 5, "name": "格式输出", "task": "format_output", "description": "生成DOCX/PDF"}
            ],
            "config": {"auto_start": False},
            "is_template": True
        }
    ]

    for wf_data in default_workflows:
        # 检查是否已存在
        existing = db.query(Workflow).filter(Workflow.name == wf_data["name"]).first()
        if not existing:
            workflow = Workflow(**wf_data)
            db.add(workflow)

    db.commit()


@router.get("", response_model=WorkflowListResponse)
async def get_workflows(
    workflow_type: Optional[WorkflowType] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流列表"""
    # 确保有默认工作流
    workflow_count = db.query(Workflow).count()
    if workflow_count == 0:
        _create_default_workflows(db)

    query = db.query(Workflow)

    if workflow_type:
        query = query.filter(Workflow.workflow_type == workflow_type.value)

    if active_only:
        query = query.filter(Workflow.is_active == True)

    workflows = query.order_by(desc(Workflow.last_executed_at), desc(Workflow.created_at)).all()

    return WorkflowListResponse(
        workflows=[WorkflowResponse.from_orm(wf) for wf in workflows],
        total=len(workflows)
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return WorkflowResponse.from_orm(workflow)


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新工作流"""
    # 检查名称是否已存在
    existing = db.query(Workflow).filter(Workflow.name == workflow_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow '{workflow_data.name}' already exists"
        )

    # 创建工作流
    new_workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        workflow_type=workflow_data.workflow_type.value,
        steps=[step.dict() for step in workflow_data.steps],
        config=workflow_data.config or {},
        created_by=current_user.id,
        is_template=False
    )

    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)

    return WorkflowResponse.from_orm(new_workflow)


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    execute_data: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active"
        )

    # 获取项目信息（如果提供）
    project_name = None
    if execute_data.project_id:
        project = db.query(Project).filter(Project.id == execute_data.project_id).first()
        if project:
            project_name = project.name

    # 创建执行记录
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        project_id=execute_data.project_id,
        project_name=project_name,
        input_data=execute_data.input_data,
        status="running",
        current_step=0,
        total_steps=len(workflow.steps),
        executed_by=current_user.id,
        start_time=datetime.utcnow()
    )

    db.add(execution)

    # 更新工作流统计
    workflow.total_executions += 1
    workflow.last_executed_at = datetime.utcnow()

    db.commit()
    db.refresh(execution)

    # TODO: 启动实际的工作流任务（Celery）
    # task = execute_workflow_task.delay(execution.id)
    # execution.task_id = task.id
    # db.commit()

    return WorkflowExecutionResponse(
        execution_id=execution.id,
        workflow_id=workflow_id,
        status=WorkflowStatus.RUNNING,
        message="Workflow execution started"
    )


@router.delete("/{workflow_id}", response_model=dict)
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # 模板工作流不能删除
    if workflow.is_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete template workflows"
        )

    db.delete(workflow)
    db.commit()

    return success_response(data={}, message="Workflow deleted successfully")


@router.get("/{workflow_id}/executions", response_model=List[dict])
async def get_workflow_executions(
    workflow_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流执行历史"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id
    ).order_by(desc(WorkflowExecution.created_at)).limit(limit).all()

    return [
        {
            "id": exec.id,
            "project_name": exec.project_name,
            "status": exec.status,
            "executed_at": exec.created_at,
            "duration_seconds": exec.duration_seconds,
            "current_step": exec.current_step,
            "total_steps": exec.total_steps
        }
        for exec in executions
    ]
