"""轻量级Agent Mesh管理器。"""

from enum import Enum
from typing import Dict, Optional

from .agent_message_bus import AgentMessageBus
from .base_agent import AgentBase, AgentResult, AgentTask
from .shared_context_pool import SharedContextPool


class AgentState(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class AgentMesh:
    """管理Agent注册与任务派发。"""

    def __init__(self,
        message_bus: Optional[AgentMessageBus] = None,
        shared_context: Optional[SharedContextPool] = None,
        use_workflow_engine: bool = True):
        self.message_bus = message_bus or AgentMessageBus()
        self.shared_context = shared_context or SharedContextPool()
        self.agents: Dict[str, AgentBase] = {}
        self.use_workflow_engine = use_workflow_engine

    def register_agent(self, agent: AgentBase) -> AgentBase:
        agent.message_bus = self.message_bus
        agent.shared_context = self.shared_context
        self.agents[agent.agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        return self.agents.get(agent_id)

    def dispatch(self, agent_id: str, task: AgentTask) -> AgentResult:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent不存在: {agent_id}")
        return agent.execute_task(task)




        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

