"""
Agent 系统 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.agents import (
    Agent,
    ReasoningAgent,
    AgentManager,
    AgentOrchestrator,
    AgentType,
    AgentStatus,
    ToolFactory
)

router = APIRouter(prefix="/agents", tags=["agents"])

# 全局管理器实例
_agent_manager = AgentManager()
_agent_orchestrator = AgentOrchestrator(_agent_manager)


# Request/Response Models
class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent 名称")
    agent_type: str = Field("task", description="Agent 类型")
    description: str = Field("", description="描述")
    tools: List[str] = Field(default_factory=list, description="工具列表")
    max_iterations: int = Field(10, ge=1, le=100, description="最大迭代次数")


class ExecuteAgentRequest(BaseModel):
    task: str = Field(..., description="任务描述")
    context: dict = Field(default_factory=dict, description="上下文")
    background: bool = Field(False, description="是否后台运行")


class CoordinateAgentsRequest(BaseModel):
    agent_ids: List[str] = Field(..., description="Agent ID 列表")
    task: str = Field(..., description="任务描述")
    strategy: str = Field("sequential", description="协调策略")


class CreateWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="工作流 ID")
    name: str = Field(..., description="工作流名称")
    steps: List[dict] = Field(..., description="步骤列表")


@router.post("/create")
async def create_agent(
    request: CreateAgentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建 Agent

    支持的 Agent 类型：
    - task: 任务型
    - reactive: 反应型
    - proactive: 主动型
    - collaborative: 协作型
    """
    try:
        # 创建工具
        all_tools = {
            "search": ToolFactory.create_search_tool(),
            "calculator": ToolFactory.create_calculator_tool(),
            "code_executor": ToolFactory.create_code_executor_tool(),
            "file_reader": ToolFactory.create_file_reader_tool(),
            "api_call": ToolFactory.create_api_call_tool(),
            "llm": ToolFactory.create_llm_tool()
        }

        tools = [all_tools[name] for name in request.tools if name in all_tools]

        # 创建 Agent
        if request.agent_type == "task":
            agent = ReasoningAgent(
                agent_id=request.agent_id,
                name=request.name,
                description=request.description,
                tools=tools,
                max_iterations=request.max_iterations
            )
        else:
            agent = Agent(
                agent_id=request.agent_id,
                name=request.name,
                agent_type=AgentType(request.agent_type),
                description=request.description,
                tools=tools,
                max_iterations=request.max_iterations
            )

        # 注册
        success = _agent_manager.register_agent(agent)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {request.agent_id} already exists"
            )

        return {"agent": agent.to_dict()}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取 Agent 信息"""
    agent = _agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return {"agent": agent.to_dict()}


@router.get("/")
async def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    列出所有 Agent

    可以按类型和状态过滤
    """
    type_filter = AgentType(agent_type) if agent_type else None
    status_filter = AgentStatus(status) if status else None

    agents = _agent_manager.list_agents(type_filter, status_filter)

    return {
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents)
    }


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除 Agent"""
    success = _agent_manager.unregister_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    执行 Agent

    可以选择同步或异步执行
    """
    result = await _agent_manager.execute_agent(
        agent_id=agent_id,
        task=request.task,
        context=request.context,
        background=request.background
    )

    return result


@router.post("/{agent_id}/pause")
async def pause_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """暂停 Agent"""
    success = _agent_manager.pause_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return {"message": "Agent paused"}


@router.post("/{agent_id}/resume")
async def resume_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """恢复 Agent"""
    success = _agent_manager.resume_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return {"message": "Agent resumed"}


@router.post("/{agent_id}/cancel")
async def cancel_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """取消 Agent"""
    success = _agent_manager.cancel_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return {"message": "Agent cancelled"}


@router.get("/{agent_id}/result")
async def get_agent_result(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取 Agent 执行结果"""
    result = _agent_manager.get_agent_result(agent_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No result found for agent {agent_id}"
        )

    return {"result": result}


@router.get("/{agent_id}/statistics")
async def get_agent_statistics(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取 Agent 统计信息"""
    agent = _agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent.get_statistics()


@router.post("/coordinate")
async def coordinate_agents(
    request: CoordinateAgentsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    协调多个 Agent

    策略：
    - sequential: 顺序执行
    - parallel: 并行执行
    - pipeline: 流水线执行
    """
    result = await _agent_manager.coordinate_agents(
        agent_ids=request.agent_ids,
        task=request.task,
        strategy=request.strategy
    )

    return result


@router.get("/manager/statistics")
async def get_manager_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取管理器统计信息"""
    return _agent_manager.get_statistics()


@router.post("/workflows/create")
async def create_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """创建工作流"""
    _agent_orchestrator.create_workflow(
        workflow_id=request.workflow_id,
        name=request.name,
        steps=request.steps
    )

    return {
        "workflow_id": request.workflow_id,
        "message": "Workflow created successfully"
    }


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    context: dict = {},
    current_user: User = Depends(get_current_user)
):
    """执行工作流"""
    result = await _agent_orchestrator.execute_workflow(
        workflow_id=workflow_id,
        initial_context=context
    )

    return result


@router.get("/tools")
async def list_tools(current_user: User = Depends(get_current_user)):
    """列出所有可用工具"""
    tools = ToolFactory.create_all_tools()
    return {
        "tools": [tool.to_dict() for tool in tools],
        "count": len(tools)
    }
