"""
Agent 协调器
负责多个 Agent 之间的协作、任务分配和结果聚合
"""
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime

from .agent_registry import agent_registry

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Agent 任务"""
    task_id: str
    agent_name: str
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentCoordinator:
    """
    Agent 协调器

    功能：
    - 任务分配：根据 Agent 能力自动分配任务
    - 并发执行：支持多个 Agent 并发工作
    - 依赖管理：处理 Agent 之间的依赖关系
    - 结果聚合：收集和整合多个 Agent 的结果
    """

    def __init__(self, max_workers: int = 5):
        """
        初始化协调器

        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, AgentTask] = {}
        self.futures: Dict[str, Future] = {}
        logger.info(f"Agent 协调器已初始化 (max_workers={max_workers})")

    def submit_task(
        self,
        task_id: str,
        agent_name: str,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentTask:
        """
        提交一个任务给指定的 Agent

        Args:
            task_id: 任务唯一标识
            agent_name: Agent 名称
            input_data: 输入数据
            metadata: 任务元数据

        Returns:
            AgentTask 对象

        Raises:
            ValueError: 如果 Agent 不存在
        """
        # 检查 Agent 是否存在
        agent_class = agent_registry.get(agent_name)
        if agent_class is None:
            raise ValueError(f"Agent '{agent_name}' 不存在")

        # 创建任务
        task = AgentTask(
            task_id=task_id,
            agent_name=agent_name,
            input_data=input_data,
            metadata=metadata or {}
        )

        self.tasks[task_id] = task

        # 提交到线程池
        future = self.executor.submit(self._execute_task, task)
        self.futures[task_id] = future

        logger.info(f"任务 {task_id} 已提交给 Agent '{agent_name}'")
        return task

    def _execute_task(self, task: AgentTask) -> Any:
        """
        执行任务（内部方法）

        Args:
            task: 任务对象

        Returns:
            执行结果
        """
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # 获取 Agent 类
            agent_class = agent_registry.get(task.agent_name)

            # 实例化 Agent
            agent = agent_class()

            # 执行 Agent
            result = agent.execute(task.input_data)

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()

            logger.info(f"✓ 任务 {task.task_id} 完成")
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"✗ 任务 {task.task_id} 失败: {e}")
            raise

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态，如果任务不存在返回 None
        """
        task = self.tasks.get(task_id)
        return task.status if task else None

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果（阻塞等待）

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务结果

        Raises:
            ValueError: 如果任务不存在
            TimeoutError: 如果超时
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务 {task_id} 不存在")

        future = self.futures.get(task_id)
        if future is None:
            raise ValueError(f"任务 {task_id} 的 Future 不存在")

        return future.result(timeout=timeout)

    def wait_all(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        等待多个任务完成

        Args:
            task_ids: 任务ID列表
            timeout: 超时时间（秒）

        Returns:
            任务结果字典 {task_id: result}
        """
        results = {}
        futures_map = {self.futures[tid]: tid for tid in task_ids if tid in self.futures}

        for future in as_completed(futures_map, timeout=timeout):
            task_id = futures_map[future]
            try:
                results[task_id] = future.result()
            except Exception as e:
                results[task_id] = {"error": str(e)}
                logger.error(f"任务 {task_id} 失败: {e}")

        return results

    def submit_workflow(
        self,
        workflow_id: str,
        tasks: List[Dict[str, Any]],
        sequential: bool = False
    ) -> Dict[str, AgentTask]:
        """
        提交一个工作流（多个任务）

        Args:
            workflow_id: 工作流ID
            tasks: 任务列表，每个任务包含 agent_name 和 input_data
            sequential: 是否顺序执行（默认并行）

        Returns:
            任务字典 {task_id: AgentTask}

        Example:
            tasks = [
                {"agent_name": "chunking_agent", "input_data": {...}},
                {"agent_name": "entity_agent", "input_data": {...}},
            ]
            coordinator.submit_workflow("wf_001", tasks)
        """
        submitted_tasks = {}

        if sequential:
            # 顺序执行
            for idx, task_config in enumerate(tasks):
                task_id = f"{workflow_id}_task_{idx}"
                task = self.submit_task(
                    task_id=task_id,
                    agent_name=task_config["agent_name"],
                    input_data=task_config["input_data"],
                    metadata={"workflow_id": workflow_id, "task_index": idx}
                )
                submitted_tasks[task_id] = task

                # 等待当前任务完成
                self.get_task_result(task_id)

        else:
            # 并行执行
            for idx, task_config in enumerate(tasks):
                task_id = f"{workflow_id}_task_{idx}"
                task = self.submit_task(
                    task_id=task_id,
                    agent_name=task_config["agent_name"],
                    input_data=task_config["input_data"],
                    metadata={"workflow_id": workflow_id, "task_index": idx}
                )
                submitted_tasks[task_id] = task

        logger.info(f"工作流 {workflow_id} 已提交 {len(tasks)} 个任务")
        return submitted_tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        if task_id not in self.futures:
            return False

        future = self.futures[task_id]
        cancelled = future.cancel()

        if cancelled:
            task = self.tasks[task_id]
            task.status = TaskStatus.CANCELLED
            logger.info(f"任务 {task_id} 已取消")

        return cancelled

    def get_all_tasks(self) -> List[AgentTask]:
        """获取所有任务"""
        return list(self.tasks.values())

    def get_running_tasks(self) -> List[AgentTask]:
        """获取正在运行的任务"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]

    def shutdown(self, wait: bool = True):
        """
        关闭协调器

        Args:
            wait: 是否等待所有任务完成
        """
        logger.info("正在关闭 Agent 协调器...")
        self.executor.shutdown(wait=wait)
        logger.info("Agent 协调器已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# 全局协调器实例
_global_coordinator: Optional[AgentCoordinator] = None


def get_coordinator(max_workers: int = 5) -> AgentCoordinator:
    """
    获取全局协调器实例（单例）

    Args:
        max_workers: 最大并发工作线程数

    Returns:
        AgentCoordinator 实例
    """
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = AgentCoordinator(max_workers=max_workers)
    return _global_coordinator
