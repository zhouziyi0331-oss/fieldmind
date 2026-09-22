"""
Agent 系统核心

提供智能 Agent 的定义、管理和执行框架
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent 状态"""
    IDLE = "idle"              # 空闲
    RUNNING = "running"        # 运行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 取消


class AgentType(str, Enum):
    """Agent 类型"""
    TASK = "task"              # 任务型
    REACTIVE = "reactive"      # 反应型
    PROACTIVE = "proactive"    # 主动型
    COLLABORATIVE = "collaborative"  # 协作型


class ToolType(str, Enum):
    """工具类型"""
    SEARCH = "search"          # 搜索
    CALCULATOR = "calculator"  # 计算器
    CODE_EXECUTOR = "code_executor"  # 代码执行
    WEB_BROWSER = "web_browser"      # 网页浏览
    FILE_READER = "file_reader"      # 文件读取
    API_CALL = "api_call"      # API 调用
    DATABASE = "database"      # 数据库查询
    LLM = "llm"               # LLM 调用


@dataclass
class Tool:
    """工具定义"""
    name: str
    tool_type: ToolType
    description: str
    parameters: Dict[str, Any]
    executor: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.tool_type.value,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class AgentAction:
    """Agent 动作"""
    action_id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration
        }


@dataclass
class AgentMemory:
    """Agent 记忆"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: Dict[str, Any] = field(default_factory=dict)
    working_memory: Dict[str, Any] = field(default_factory=dict)

    def add_to_short_term(self, item: Dict[str, Any], max_size: int = 10):
        """添加到短期记忆"""
        self.short_term.append(item)
        if len(self.short_term) > max_size:
            # 移除最旧的记忆
            self.short_term.pop(0)

    def update_long_term(self, key: str, value: Any):
        """更新长期记忆"""
        self.long_term[key] = value

    def get_working_memory(self, key: str) -> Optional[Any]:
        """获取工作记忆"""
        return self.working_memory.get(key)

    def set_working_memory(self, key: str, value: Any):
        """设置工作记忆"""
        self.working_memory[key] = value

    def clear_working_memory(self):
        """清空工作记忆"""
        self.working_memory.clear()


class Agent:
    """
    智能 Agent 基类

    提供 Agent 的基础能力：感知、决策、执行
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: AgentType,
        description: str = "",
        tools: Optional[List[Tool]] = None,
        max_iterations: int = 10
    ):
        """
        初始化 Agent

        Args:
            agent_id: Agent ID
            name: Agent 名称
            agent_type: Agent 类型
            description: 描述
            tools: 可用工具列表
            max_iterations: 最大迭代次数
        """
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.max_iterations = max_iterations

        # 状态管理
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.iteration_count = 0

        # 记忆系统
        self.memory = AgentMemory()

        # 执行历史
        self.action_history: List[AgentAction] = []

        # 统计信息
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0

    def add_tool(self, tool: Tool):
        """添加工具"""
        self.tools[tool.name] = tool
        logger.info(f"Agent {self.name} added tool: {tool.name}")

    def remove_tool(self, tool_name: str):
        """移除工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Agent {self.name} removed tool: {tool_name}")

    async def execute_action(
        self,
        action: AgentAction
    ) -> AgentAction:
        """
        执行动作

        Args:
            action: 要执行的动作

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 查找工具
            tool = self.tools.get(action.tool_name)
            if not tool:
                raise ValueError(f"Tool {action.tool_name} not found")

            if not tool.executor:
                raise ValueError(f"Tool {action.tool_name} has no executor")

            # 执行工具
            logger.info(f"Agent {self.name} executing {action.tool_name}")
            result = await tool.executor(**action.parameters)

            action.result = result
            self.successful_actions += 1

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.error = str(e)
            self.failed_actions += 1

        # 记录执行时间
        action.duration = (datetime.now() - start_time).total_seconds()

        # 添加到历史
        self.action_history.append(action)
        self.total_actions += 1
        self.last_active = datetime.now()

        # 添加到短期记忆
        self.memory.add_to_short_term({
            "action": action.tool_name,
            "result": action.result,
            "timestamp": action.timestamp.isoformat()
        })

        return action

    async def think(self, task: str, context: Dict[str, Any]) -> List[AgentAction]:
        """
        思考并生成动作计划

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            动作列表
        """
        # 基础实现：子类应该重写此方法
        raise NotImplementedError("Subclass must implement think()")

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        运行 Agent

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        self.status = AgentStatus.RUNNING
        self.current_task = task
        self.iteration_count = 0
        context = context or {}

        try:
            while self.iteration_count < self.max_iterations:
                self.iteration_count += 1

                # 思考
                actions = await self.think(task, context)

                if not actions:
                    # 没有更多动作，任务完成
                    break

                # 执行动作
                for action in actions:
                    result_action = await self.execute_action(action)

                    if result_action.error:
                        logger.warning(
                            f"Action {action.action_id} failed: {result_action.error}"
                        )

                    # 更新上下文
                    context[action.action_id] = result_action.result

                # 检查是否完成
                if self._is_task_complete(context):
                    break

            self.status = AgentStatus.COMPLETED

            return {
                "status": "completed",
                "iterations": self.iteration_count,
                "actions": len(self.action_history),
                "context": context
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.status = AgentStatus.FAILED
            return {
                "status": "failed",
                "error": str(e),
                "iterations": self.iteration_count
            }

        finally:
            self.current_task = None

    def _is_task_complete(self, context: Dict[str, Any]) -> bool:
        """
        检查任务是否完成

        Args:
            context: 当前上下文

        Returns:
            是否完成
        """
        # 基础实现：子类可以重写
        return False

    def pause(self):
        """暂停 Agent"""
        if self.status == AgentStatus.RUNNING:
            self.status = AgentStatus.PAUSED
            logger.info(f"Agent {self.name} paused")

    def resume(self):
        """恢复 Agent"""
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.RUNNING
            logger.info(f"Agent {self.name} resumed")

    def cancel(self):
        """取消 Agent"""
        self.status = AgentStatus.CANCELLED
        logger.info(f"Agent {self.name} cancelled")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "status": self.status.value,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "success_rate": (
                self.successful_actions / self.total_actions
                if self.total_actions > 0 else 0
            ),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "description": self.description,
            "status": self.status.value,
            "tools": [tool.to_dict() for tool in self.tools.values()],
            "current_task": self.current_task,
            "iteration_count": self.iteration_count,
            "statistics": self.get_statistics()
        }


class ReasoningAgent(Agent):
    """
    推理型 Agent

    具有推理和规划能力的 Agent
    """
    def __init__(self, agent_id: str, name: str, use_workflow_engine: bool = True, **kwargs):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(agent_id, name, AgentType.TASK, **kwargs)
        self.reasoning_steps: List[Dict[str, Any]] = []

    async def think(self, task: str, context: Dict[str, Any]) -> List[AgentAction]:
        """
        推理和规划

        Args:
            task: 任务
            context: 上下文

        Returns:
            动作列表
        """
        # 分析任务
        reasoning_step = {
            "step": len(self.reasoning_steps) + 1,
            "task": task,
            "context_keys": list(context.keys()),
            "timestamp": datetime.now().isoformat()
        }

        # 简单的规则基推理
        actions = []

        # 检查是否需要搜索
        if "search" in self.tools and not context.get("search_done"):
            actions.append(AgentAction(
                action_id=f"action_{len(self.action_history) + 1}",
                tool_name="search",
                parameters={"query": task}
            ))
            reasoning_step["decision"] = "Need to search for information"

        # 检查是否需要计算
        elif "calculator" in self.tools and any(
            word in task.lower() for word in ["calculate", "compute", "sum"]
        ):
            actions.append(AgentAction(
                action_id=f"action_{len(self.action_history) + 1}",
                tool_name="calculator",
                parameters={"expression": task}
            ))
            reasoning_step["decision"] = "Need to perform calculation"

        self.reasoning_steps.append(reasoning_step)
        return actions

    def _is_task_complete(self, context: Dict[str, Any]) -> bool:
        """检查任务是否完成"""
        # 如果有结果，认为完成
        return len(context) > 0 and any(
            v is not None for v in context.values()
        )
