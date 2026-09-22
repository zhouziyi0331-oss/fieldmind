"""
Agent 管理器

管理多个 Agent 的生命周期和协作
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncio

from app.services.agents.core import Agent, AgentStatus, AgentType

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Agent 管理器

    负责 Agent 的创建、调度和协调
    """

    def __init__(self):
        """初始化管理器"""
        self.agents: Dict[str, Agent] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}

    def register_agent(self, agent: Agent) -> bool:
        """
        注册 Agent

        Args:
            agent: Agent 实例

        Returns:
            是否成功
        """
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return False

        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销 Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return False

        # 取消正在运行的任务
        if agent_id in self.running_tasks:
            self.running_tasks[agent_id].cancel()
            del self.running_tasks[agent_id]

        del self.agents[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取 Agent"""
        return self.agents.get(agent_id)

    def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None
    ) -> List[Agent]:
        """
        列出 Agent

        Args:
            agent_type: 类型过滤
            status: 状态过滤

        Returns:
            Agent 列表
        """
        agents = list(self.agents.values())

        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    async def execute_agent(
        self,
        agent_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        执行 Agent

        Args:
            agent_id: Agent ID
            task: 任务描述
            context: 上下文
            background: 是否后台运行

        Returns:
            执行结果
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}

        if agent.status == AgentStatus.RUNNING:
            return {"error": f"Agent {agent_id} is already running"}

        # 创建任务
        async def run_agent():
            try:
                result = await agent.run(task, context)
                self.task_results[agent_id] = result
                return result
            except Exception as e:
                logger.error(f"Agent {agent_id} execution failed: {e}")
                return {"error": str(e)}
            finally:
                if agent_id in self.running_tasks:
                    del self.running_tasks[agent_id]

        if background:
            # 后台运行
            task_obj = asyncio.create_task(run_agent())
            self.running_tasks[agent_id] = task_obj
            return {
                "status": "running",
                "agent_id": agent_id,
                "background": True
            }
        else:
            # 同步等待
            return await run_agent()

    def pause_agent(self, agent_id: str) -> bool:
        """暂停 Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.pause()
        return True

    def resume_agent(self, agent_id: str) -> bool:
        """恢复 Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.resume()
        return True

    def cancel_agent(self, agent_id: str) -> bool:
        """取消 Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.cancel()

        # 取消任务
        if agent_id in self.running_tasks:
            self.running_tasks[agent_id].cancel()
            del self.running_tasks[agent_id]

        return True

    def get_agent_result(self, agent_id: str) -> Optional[Any]:
        """获取 Agent 执行结果"""
        return self.task_results.get(agent_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "total_agents": len(self.agents),
            "running_agents": len([
                a for a in self.agents.values()
                if a.status == AgentStatus.RUNNING
            ]),
            "idle_agents": len([
                a for a in self.agents.values()
                if a.status == AgentStatus.IDLE
            ]),
            "agents_by_type": {
                agent_type.value: len([
                    a for a in self.agents.values()
                    if a.agent_type == agent_type
                ])
                for agent_type in AgentType
            }
        }

    async def coordinate_agents(
        self,
        agent_ids: List[str],
        task: str,
        strategy: str = "sequential"
    ) -> Dict[str, Any]:
        """
        协调多个 Agent

        Args:
            agent_ids: Agent ID 列表
            task: 任务
            strategy: 协调策略 (sequential/parallel/pipeline)

        Returns:
            执行结果
        """
        if strategy == "sequential":
            return await self._sequential_execution(agent_ids, task)
        elif strategy == "parallel":
            return await self._parallel_execution(agent_ids, task)
        elif strategy == "pipeline":
            return await self._pipeline_execution(agent_ids, task)
        else:
            return {"error": f"Unknown strategy: {strategy}"}

    async def _sequential_execution(
        self,
        agent_ids: List[str],
        task: str
    ) -> Dict[str, Any]:
        """顺序执行"""
        results = []
        context = {}

        for agent_id in agent_ids:
            result = await self.execute_agent(agent_id, task, context)
            results.append({
                "agent_id": agent_id,
                "result": result
            })

            # 传递上下文
            if "context" in result:
                context.update(result["context"])

        return {
            "strategy": "sequential",
            "results": results,
            "final_context": context
        }

    async def _parallel_execution(
        self,
        agent_ids: List[str],
        task: str
    ) -> Dict[str, Any]:
        """并行执行"""
        tasks = [
            self.execute_agent(agent_id, task)
            for agent_id in agent_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "strategy": "parallel",
            "results": [
                {
                    "agent_id": agent_id,
                    "result": result if not isinstance(result, Exception) else {"error": str(result)}
                }
                for agent_id, result in zip(agent_ids, results)
            ]
        }

    async def _pipeline_execution(
        self,
        agent_ids: List[str],
        task: str
    ) -> Dict[str, Any]:
        """流水线执行"""
        context = {"input": task}
        results = []

        for agent_id in agent_ids:
            # 使用前一个 Agent 的输出作为输入
            result = await self.execute_agent(agent_id, task, context)
            results.append({
                "agent_id": agent_id,
                "result": result
            })

            # 更新上下文
            if "context" in result:
                context = result["context"]

        return {
            "strategy": "pipeline",
            "results": results,
            "final_output": context
        }


class AgentOrchestrator:
    """
    Agent 编排器

    高级 Agent 协调和工作流管理
    """

    def __init__(self, manager: AgentManager):
        """初始化编排器"""
        self.manager = manager
        self.workflows: Dict[str, Dict[str, Any]] = {}

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: List[Dict[str, Any]]
    ):
        """
        创建工作流

        Args:
            workflow_id: 工作流 ID
            name: 名称
            steps: 步骤列表
        """
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "name": name,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Created workflow: {name} ({workflow_id})")

    async def execute_workflow(
        self,
        workflow_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流 ID
            initial_context: 初始上下文

        Returns:
            执行结果
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}

        context = initial_context or {}
        results = []

        for i, step in enumerate(workflow["steps"]):
            step_result = await self._execute_step(step, context)
            results.append({
                "step": i + 1,
                "step_name": step.get("name", f"Step {i+1}"),
                "result": step_result
            })

            # 更新上下文
            if "context" in step_result:
                context.update(step_result["context"])

            # 检查是否有错误
            if step_result.get("error"):
                logger.error(f"Workflow step {i+1} failed: {step_result['error']}")
                break

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "steps_completed": len(results),
            "total_steps": len(workflow["steps"]),
            "results": results,
            "final_context": context
        }

    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工作流步骤"""
        step_type = step.get("type")

        if step_type == "agent":
            # 执行单个 Agent
            agent_id = step.get("agent_id")
            task = step.get("task")
            return await self.manager.execute_agent(agent_id, task, context)

        elif step_type == "coordination":
            # 协调多个 Agent
            agent_ids = step.get("agent_ids", [])
            task = step.get("task")
            strategy = step.get("strategy", "sequential")
            return await self.manager.coordinate_agents(agent_ids, task, strategy)

        elif step_type == "condition":
            # 条件判断
            condition = step.get("condition")
            if self._evaluate_condition(condition, context):
                return await self._execute_step(step.get("then"), context)
            else:
                return await self._execute_step(step.get("else"), context)

        else:
            return {"error": f"Unknown step type: {step_type}"}

    def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件评估
            return eval(condition, {"context": context})
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
