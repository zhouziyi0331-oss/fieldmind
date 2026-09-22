"""工作流Schema定义"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowType(str, Enum):
    """工作流类型"""
    DOCUMENT = "document"
    AUDIO = "audio"
    CRAWLER = "crawler"
    RAG = "rag"
    REPORT = "report"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class WorkflowStatus(str, Enum):
    """工作流执行状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """工作流步骤"""
    order: int
    name: str
    task: str
    description: Optional[str] = None


class WorkflowExecutionSummary(BaseModel):
    """工作流执行摘要"""
    id: str
    executed_at: datetime
    project_name: Optional[str] = None
    status: WorkflowStatus
    duration_seconds: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: str
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    step_count: int
    usage_count: int  # total_executions
    avg_duration: str  # 格式化的平均时长
    is_active: bool
    created_at: datetime
    last_executed_at: Optional[datetime] = None
    execution_history: List[WorkflowExecutionSummary] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, workflow):
        """从ORM模型创建"""
        # 格式化平均时长
        avg_duration = "未知"
        if workflow.avg_duration_seconds:
            minutes = int(workflow.avg_duration_seconds / 60)
            seconds = int(workflow.avg_duration_seconds % 60)
            if minutes > 0:
                avg_duration = f"{minutes}分{seconds}秒"
            else:
                avg_duration = f"{seconds}秒"

        # 获取最近5次执行历史
        execution_history = []
        for exec in workflow.executions[:5]:
            execution_history.append(WorkflowExecutionSummary(
                id=exec.id,
                executed_at=exec.created_at,
                project_name=exec.project_name,
                status=exec.status,
                duration_seconds=exec.duration_seconds
            ))

        # 计算步骤数
        step_count = len(workflow.steps) if workflow.steps else 0

        return cls(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            workflow_type=workflow.workflow_type,
            step_count=step_count,
            usage_count=workflow.total_executions,
            avg_duration=avg_duration,
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            last_executed_at=workflow.last_executed_at,
            execution_history=execution_history
        )


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[WorkflowResponse]
    total: int


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    config: Optional[Dict[str, Any]] = None


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    project_id: Optional[int] = None
    input_data: Dict[str, Any]


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    message: str
