"""
工作流引擎API端点

提供工作流创建、执行、监控和管理接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.workflow_execution import WorkflowStatus, StepStatus
from app.services.workflow_service import WorkflowService
from app.services.workflow_handlers import register_default_handlers
from app.core.workflow_websocket import workflow_progress_manager, create_progress_callback


router = APIRouter()


# ==================== Pydantic 模型 ====================

class WorkflowExecutionCreate(BaseModel):
    """创建工作流执行请求"""
    project_id: int = Field(..., description="项目ID")
    workflow_type: str = Field(..., description="工作流类型")
    config: Dict[str, Any] = Field(..., description="工作流配置")
    template_id: Optional[int] = Field(None, description="使用的模板ID")


class WorkflowStepConfig(BaseModel):
    """工作流步骤配置"""
    step_name: str = Field(..., description="步骤名称")
    step_type: str = Field(..., description="步骤类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="步骤配置")
    dependencies: List[str] = Field(default_factory=list, description="依赖的步骤名称")


class WorkflowExecutionStart(BaseModel):
    """启动工作流执行请求"""
    steps: List[WorkflowStepConfig] = Field(..., description="步骤配置列表")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    id: int
    project_id: int
    workflow_type: str
    status: str
    config: Dict[str, Any]
    result: Dict[str, Any]
    template_id: Optional[int]
    triggered_by: Optional[int]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class WorkflowStepResponse(BaseModel):
    """工作流步骤响应"""
    id: int
    execution_id: int
    step_name: str
    step_type: str
    step_order: int
    status: str
    config: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    retry_count: int
    dependencies: List[str]
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True


class WorkflowProgressResponse(BaseModel):
    """工作流进度响应"""
    execution_id: int
    status: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    running_steps: int
    progress_percentage: float
    started_at: Optional[str]
    current_step: Optional[str]
    steps: List[Dict[str, Any]]


class WorkflowTemplateCreate(BaseModel):
    """创建工作流模板请求"""
    name: str = Field(..., description="模板名称")
    workflow_type: str = Field(..., description="工作流类型")
    description: Optional[str] = Field(None, description="模板描述")
    steps_definition: List[Dict[str, Any]] = Field(..., description="步骤定义")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="默认配置")


class WorkflowTemplateResponse(BaseModel):
    """工作流模板响应"""
    id: int
    name: str
    workflow_type: str
    description: Optional[str]
    steps_definition: List[Dict[str, Any]]
    default_config: Dict[str, Any]
    is_active: bool
    created_by: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ==================== 依赖项 ====================

async def get_workflow_service(db: AsyncSession = Depends(get_db)) -> WorkflowService:
    """获取工作流服务"""
    service = WorkflowService(db)
    # 注册默认处理器
    register_default_handlers(service)
    return service


# ==================== 工作流执行 ====================

@router.post("/executions", response_model=WorkflowExecutionResponse, summary="创建工作流执行")
async def create_workflow_execution(
    execution: WorkflowExecutionCreate,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    创建工作流执行实例

    - **project_id**: 项目ID
    - **workflow_type**: 工作流类型（document_analysis, data_processing等）
    - **config**: 工作流配置参数
    - **template_id**: 可选，使用的模板ID
    """
    result = await workflow_service.create_execution(
        project_id=execution.project_id,
        workflow_type=execution.workflow_type,
        config=execution.config,
        template_id=execution.template_id,
        triggered_by=current_user.id
    )

    return WorkflowExecutionResponse(
        id=result.id,
        project_id=result.project_id,
        workflow_type=result.workflow_type,
        status=result.status.value,
        config=result.config,
        result=result.result,
        template_id=result.template_id,
        triggered_by=result.triggered_by,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.post("/executions/{execution_id}/start", response_model=WorkflowExecutionResponse, summary="启动工作流执行")
async def start_workflow_execution(
    execution_id: int = Path(..., description="执行实例ID"),
    start_config: WorkflowExecutionStart = ...,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    启动工作流执行

    - **steps**: 步骤配置列表，每个步骤包含名称、类型、配置和依赖
    """
    # 转换步骤配置
    steps_config = [
        {
            "step_name": step.step_name,
            "step_type": step.step_type,
            "config": step.config,
            "dependencies": step.dependencies
        }
        for step in start_config.steps
    ]

    result = await workflow_service.start_execution(
        execution_id=execution_id,
        steps_config=steps_config
    )

    return WorkflowExecutionResponse(
        id=result.id,
        project_id=result.project_id,
        workflow_type=result.workflow_type,
        status=result.status.value,
        config=result.config,
        result=result.result,
        template_id=result.template_id,
        triggered_by=result.triggered_by,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.post("/executions/{execution_id}/execute", summary="执行工作流（后台任务）")
async def execute_workflow(
    execution_id: int = Path(..., description="执行实例ID"),
    background_tasks: BackgroundTasks = ...,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    执行工作流（异步后台任务）

    启动后台任务执行工作流，可通过WebSocket实时监听进度
    """
    # 创建进度回调
    progress_callback = create_progress_callback(execution_id)

    # 添加后台任务
    async def run_workflow():
        await workflow_service.execute_workflow(execution_id, progress_callback)

    background_tasks.add_task(run_workflow)

    return {
        "execution_id": execution_id,
        "message": "工作流已开始执行",
        "websocket_url": f"/api/v1/workflows/executions/{execution_id}/progress"
    }


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowExecutionResponse, summary="取消工作流执行")
async def cancel_workflow_execution(
    execution_id: int = Path(..., description="执行实例ID"),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """取消正在执行的工作流"""
    result = await workflow_service.cancel_execution(execution_id)

    return WorkflowExecutionResponse(
        id=result.id,
        project_id=result.project_id,
        workflow_type=result.workflow_type,
        status=result.status.value,
        config=result.config,
        result=result.result,
        template_id=result.template_id,
        triggered_by=result.triggered_by,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


# ==================== 工作流查询 ====================

@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse, summary="获取工作流执行详情")
async def get_workflow_execution(
    execution_id: int = Path(..., description="执行实例ID"),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流执行的详细信息"""
    result = await workflow_service.get_execution(execution_id, include_steps=False)

    if not result:
        raise HTTPException(status_code=404, detail="工作流执行不存在")

    return WorkflowExecutionResponse(
        id=result.id,
        project_id=result.project_id,
        workflow_type=result.workflow_type,
        status=result.status.value,
        config=result.config,
        result=result.result,
        template_id=result.template_id,
        triggered_by=result.triggered_by,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        created_at=result.created_at.isoformat()
    )


@router.get("/executions", response_model=List[WorkflowExecutionResponse], summary="查询工作流执行列表")
async def list_workflow_executions(
    project_id: Optional[int] = Query(None, description="筛选项目"),
    workflow_type: Optional[str] = Query(None, description="筛选工作流类型"),
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(50, description="返回数量", ge=1, le=100),
    offset: int = Query(0, description="分页偏移", ge=0),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """查询工作流执行列表"""
    # 转换状态枚举
    status_enum = None
    if status:
        try:
            status_enum = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")

    results = await workflow_service.list_executions(
        project_id=project_id,
        workflow_type=workflow_type,
        status=status_enum,
        limit=limit,
        offset=offset
    )

    return [
        WorkflowExecutionResponse(
            id=r.id,
            project_id=r.project_id,
            workflow_type=r.workflow_type,
            status=r.status.value,
            config=r.config,
            result=r.result,
            template_id=r.template_id,
            triggered_by=r.triggered_by,
            started_at=r.started_at.isoformat() if r.started_at else None,
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            created_at=r.created_at.isoformat()
        )
        for r in results
    ]


@router.get("/executions/{execution_id}/steps", response_model=List[WorkflowStepResponse], summary="获取工作流步骤列表")
async def get_workflow_steps(
    execution_id: int = Path(..., description="执行实例ID"),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流的所有步骤"""
    execution = await workflow_service.get_execution(execution_id, include_steps=True)

    if not execution:
        raise HTTPException(status_code=404, detail="工作流执行不存在")

    return [
        WorkflowStepResponse(
            id=step.id,
            execution_id=step.execution_id,
            step_name=step.step_name,
            step_type=step.step_type,
            step_order=step.step_order,
            status=step.status.value,
            config=step.config,
            output_data=step.output_data,
            error_message=step.error_message,
            retry_count=step.retry_count,
            dependencies=step.dependencies,
            started_at=step.started_at.isoformat() if step.started_at else None,
            completed_at=step.completed_at.isoformat() if step.completed_at else None
        )
        for step in sorted(execution.steps, key=lambda s: s.step_order)
    ]


@router.get("/executions/{execution_id}/progress", response_model=WorkflowProgressResponse, summary="获取工作流进度")
async def get_workflow_progress(
    execution_id: int = Path(..., description="执行实例ID"),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流执行的实时进度"""
    progress = await workflow_service.get_execution_progress(execution_id)

    if not progress:
        raise HTTPException(status_code=404, detail="工作流执行不存在")

    return WorkflowProgressResponse(**progress)


# ==================== WebSocket 实时进度 ====================

@router.websocket("/executions/{execution_id}/ws")
async def workflow_progress_websocket(
    websocket: WebSocket,
    execution_id: int
):
    """
    WebSocket端点：实时推送工作流执行进度

    连接后会实时接收以下类型的消息：
    - progress: 步骤进度更新
    - execution_status: 整体状态更新
    - step_output: 步骤输出数据
    - completion: 工作流完成
    """
    await workflow_progress_manager.connect(websocket, execution_id)

    try:
        # 保持连接
        while True:
            # 接收客户端ping消息（保持连接）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await workflow_progress_manager.disconnect(websocket, execution_id)


# ==================== 工作流模板 ====================

@router.post("/templates", response_model=WorkflowTemplateResponse, summary="创建工作流模板")
async def create_workflow_template(
    template: WorkflowTemplateCreate,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """
    创建工作流模板

    - **name**: 模板名称
    - **workflow_type**: 工作流类型
    - **description**: 模板描述
    - **steps_definition**: 步骤定义列表
    - **default_config**: 默认配置
    """
    result = await workflow_service.create_template(
        name=template.name,
        workflow_type=template.workflow_type,
        description=template.description,
        steps_definition=template.steps_definition,
        default_config=template.default_config,
        created_by=current_user.id
    )

    return WorkflowTemplateResponse(
        id=result.id,
        name=result.name,
        workflow_type=result.workflow_type,
        description=result.description,
        steps_definition=result.steps_definition,
        default_config=result.default_config,
        is_active=result.is_active,
        created_by=result.created_by,
        created_at=result.created_at.isoformat(),
        updated_at=result.updated_at.isoformat()
    )


@router.get("/templates", response_model=List[WorkflowTemplateResponse], summary="获取工作流模板列表")
async def list_workflow_templates(
    workflow_type: Optional[str] = Query(None, description="筛选工作流类型"),
    is_active: Optional[bool] = Query(True, description="筛选是否激活"),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """查询工作流模板列表"""
    results = await workflow_service.list_templates(
        workflow_type=workflow_type,
        is_active=is_active
    )

    return [
        WorkflowTemplateResponse(
            id=t.id,
            name=t.name,
            workflow_type=t.workflow_type,
            description=t.description,
            steps_definition=t.steps_definition,
            default_config=t.default_config,
            is_active=t.is_active,
            created_by=t.created_by,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat()
        )
        for t in results
    ]


# ==================== 步骤管理 ====================

@router.post("/steps/{step_id}/retry", response_model=WorkflowStepResponse, summary="重试失败的步骤")
async def retry_workflow_step(
    step_id: int = Path(..., description="步骤ID"),
    max_retries: int = Query(3, description="最大重试次数", ge=1, le=10),
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """重试失败的工作流步骤"""
    result = await workflow_service.retry_step(step_id, max_retries)

    return WorkflowStepResponse(
        id=result.id,
        execution_id=result.execution_id,
        step_name=result.step_name,
        step_type=result.step_type,
        step_order=result.step_order,
        status=result.status.value,
        config=result.config,
        output_data=result.output_data,
        error_message=result.error_message,
        retry_count=result.retry_count,
        dependencies=result.dependencies,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None
    )


@router.get("/handlers", summary="获取已注册的步骤处理器")
async def get_registered_handlers(
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """获取所有已注册的步骤处理器类型"""
    handlers = workflow_service.get_registered_handlers()

    return {
        "handlers": handlers,
        "count": len(handlers)
    }
