"""
Agent基类 - 所有专业Agent的抽象基类

基于CrewAI框架设计，每个Agent代表一个特定职能的专家
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent角色枚举"""
    TRANSCRIPT = "transcript"           # 转录专员
    ENTITY = "entity"                   # 实体识别专员
    RELATION = "relation"               # 关系抽取专员
    SEARCH = "search"                   # 搜索专员
    SUMMARY = "summary"                 # 总结专员
    COORDINATOR = "coordinator"         # 协调专员
    KNOWLEDGE = "knowledge"             # 知识提取专员


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"                       # 空闲
    WORKING = "working"                 # 工作中
    COMPLETED = "completed"             # 已完成
    FAILED = "failed"                   # 失败
    WAITING = "waiting"                 # 等待中


@dataclass
class AgentTask:
    """
    Agent任务定义
    """
    task_id: str                        # 任务ID
    task_type: str                      # 任务类型
    input_data: Dict[str, Any]          # 输入数据
    priority: int = 0                   # 优先级（越大越高）
    deadline: Optional[datetime] = None # 截止时间
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResult:
    """
    Agent执行结果
    """
    task_id: str                        # 任务ID
    status: AgentStatus                 # 执行状态
    output_data: Dict[str, Any]         # 输出数据
    agent_id: Optional[str] = None      # Agent ID
    agent_role: Optional[AgentRole] = None  # Agent角色
    success: Optional[bool] = None      # 是否成功（向后兼容）
    execution_time: float = 0.0         # 执行时间（秒）
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文数据


class AgentBase(ABC):
    """
    Agent基类

    设计原则：
    1. 每个Agent代表一个专业角色，具有特定技能
    2. 支持异步任务执行
    3. 可配置的工具集
    4. 标准化的输入输出
    5. 可观测的执行状态
    """

    def __init__(self, agent_id: Optional[str] = None):
        """
        初始化Agent

        Args:
            agent_id: Agent唯一标识（可选，默认生成）
        """
        self.agent_id = agent_id or self._generate_agent_id()
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.task_history: List[AgentResult] = []
        self.tools: Dict[str, Any] = {}

        # Agent Mesh集成点
        self.message_bus: Optional[Any] = None  # 将由AgentMesh注入
        self.shared_context: Optional[Any] = None  # 将由AgentMesh注入

        # 初始化Agent特定的工具和配置
        self._initialize_tools()

        logger.info(f"Agent {self.agent_id} ({self.role.value}) 初始化完成")

    def _generate_agent_id(self) -> str:
        """生成Agent ID"""
        import uuid
        return f"{self.role.value}_{uuid.uuid4().hex[:8]}"

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """返回Agent角色"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """返回Agent名称（中文）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """返回Agent描述"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """返回Agent能力列表"""
        pass

    @abstractmethod
    def _initialize_tools(self):
        """
        初始化Agent工具集

        子类必须实现，定义该Agent可用的工具

        例如：
        self.tools = {
            'whisper': WhisperService(),
            'file_handler': FileHandler()
        }
        """
        pass

    @abstractmethod
    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务的具体实现

        子类必须实现，定义该Agent如何处理任务

        Args:
            task: 任务对象

        Returns:
            输出数据字典

        Raises:
            Exception: 任务执行失败时抛出异常
        """
        pass

    def execute_task(self, task: AgentTask) -> AgentResult:
        """
        执行任务（公共接口）

        Args:
            task: 任务对象

        Returns:
            AgentResult: 执行结果
        """
        import time

        logger.info(f"Agent {self.agent_id} 开始执行任务 {task.task_id}")

        # 更新状态
        self.status = AgentStatus.WORKING
        self.current_task = task

        start_time = time.time()

        try:
            # 执行任务
            output_data = self._execute_task_impl(task)

            elapsed_time = time.time() - start_time

            # 构建结果
            result = AgentResult(
                task_id=task.task_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                agent_id=self.agent_id,
                agent_role=self.role,
                success=True,
                execution_time=elapsed_time,
                metadata={
                    'task_type': task.task_type,
                    'input_size': len(str(task.input_data))
                }
            )

            # 更新状态
            self.status = AgentStatus.COMPLETED
            self.current_task = None
            self.task_history.append(result)

            logger.info(f"Agent {self.agent_id} 任务 {task.task_id} 执行成功，耗时 {elapsed_time:.2f}秒")

            return result

        except Exception as e:
            elapsed_time = time.time() - start_time

            logger.error(f"Agent {self.agent_id} 任务 {task.task_id} 执行失败: {e}", exc_info=True)

            # 构建失败结果
            result = AgentResult(
                task_id=task.task_id,
                status=AgentStatus.FAILED,
                output_data={},
                agent_id=self.agent_id,
                agent_role=self.role,
                success=False,
                execution_time=elapsed_time,
                errors=[str(e)],
                metadata={
                    'task_type': task.task_type,
                    'error_type': type(e).__name__
                }
            )

            # 更新状态
            self.status = AgentStatus.FAILED
            self.current_task = None
            self.task_history.append(result)

            return result

    def get_status(self) -> Dict[str, Any]:
        """
        获取Agent状态

        Returns:
            状态字典
        """
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'name': self.name,
            'status': self.status.value,
            'current_task': self.current_task.task_id if self.current_task else None,
            'completed_tasks': len([r for r in self.task_history if r.success]),
            'failed_tasks': len([r for r in self.task_history if not r.success]),
            'total_tasks': len(self.task_history),
            'capabilities': self.capabilities
        }

    def reset(self):
        """重置Agent状态"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        logger.info(f"Agent {self.agent_id} 状态已重置")

    def get_task_history(self, limit: int = 10) -> List[AgentResult]:
        """
        获取任务历史

        Args:
            limit: 返回的最大记录数

        Returns:
            最近的任务结果列表
        """
        return self.task_history[-limit:]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} role={self.role.value} status={self.status.value}>"
