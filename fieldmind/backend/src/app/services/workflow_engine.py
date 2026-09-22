"""
工作流执行引擎 - 链路十二核心模块
支持同步和异步工作流执行，不依赖Celery
"""
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    task_name: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds
        }


@dataclass
class WorkflowTask:
    """工作流任务定义"""
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务名称
    retry_count: int = 0
    retry_on_failure: bool = False
    timeout: Optional[int] = None  # 秒


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    tasks: List[WorkflowTask]
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "task_results": {k: v.to_dict() for k, v in self.task_results.items()},
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.executions: Dict[str, WorkflowExecution] = {}

    def create_workflow(
        self,
        name: str,
        description: Optional[str] = None
    ) -> WorkflowDefinition:
        """创建工作流定义"""
        return WorkflowDefinition(
            name=name,
            tasks=[],
            description=description
        )

    def add_task(
        self,
        workflow: WorkflowDefinition,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        dependencies: List[str] = None,
        retry_on_failure: bool = False,
        timeout: Optional[int] = None
    ):
        """添加任务到工作流"""
        task = WorkflowTask(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or [],
            retry_on_failure=retry_on_failure,
            timeout=timeout
        )
        workflow.tasks.append(task)
        logger.info(f"添加任务 {name} 到工作流 {workflow.name}")

    def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Dict[str, Any] = None
    ) -> WorkflowExecution:
        """
        同步执行工作流

        Args:
            workflow: 工作流定义
            context: 共享上下文，任务间可传递数据

        Returns:
            WorkflowExecution: 执行实例
        """
        workflow_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.utcnow(),
            metadata=workflow.metadata
        )
        self.executions[workflow_id] = execution

        logger.info(f"🚀 开始执行工作流: {workflow.name} (ID: {workflow_id})")

        context = context or {}
        completed_tasks = set()

        try:
            # 构建任务依赖图
            task_map = {task.name: task for task in workflow.tasks}

            # 按依赖顺序执行任务
            while len(completed_tasks) < len(workflow.tasks):
                # 找到所有依赖已满足的任务
                ready_tasks = []
                for task in workflow.tasks:
                    if task.name in completed_tasks:
                        continue
                    if all(dep in completed_tasks for dep in task.dependencies):
                        ready_tasks.append(task)

                if not ready_tasks:
                    # 检测循环依赖
                    remaining = [t.name for t in workflow.tasks if t.name not in completed_tasks]
                    raise RuntimeError(f"检测到循环依赖或无法执行的任务: {remaining}")

                # 并行执行所有ready的任务
                for task in ready_tasks:
                    task_result = self._execute_task(task, context, workflow_id)
                    execution.task_results[task.name] = task_result
                    completed_tasks.add(task.name)

                    # 将任务结果放入上下文
                    if task_result.status == TaskStatus.COMPLETED:
                        context[task.name] = task_result.result
                    elif task_result.status == TaskStatus.FAILED and not task.retry_on_failure:
                        raise RuntimeError(f"任务 {task.name} 执行失败: {task_result.error}")

            execution.status = WorkflowStatus.COMPLETED
            logger.info(f"✅ 工作流执行完成: {workflow.name}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            logger.error(f"❌ 工作流执行失败: {workflow.name}, 错误: {e}", exc_info=True)

        finally:
            execution.end_time = datetime.utcnow()

        return execution

    def _execute_task(
        self,
        task: WorkflowTask,
        context: Dict[str, Any],
        workflow_id: str
    ) -> TaskResult:
        """执行单个任务"""
        task_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        logger.info(f"  ▶️ 执行任务: {task.name}")

        result = TaskResult(
            task_id=task_id,
            task_name=task.name,
            status=TaskStatus.RUNNING,
            start_time=start_time
        )

        try:
            # 解析参数中的上下文引用
            resolved_kwargs = self._resolve_context_refs(task.kwargs, context)

            # 执行任务
            task_result = task.func(*task.args, **resolved_kwargs, _context=context)

            result.result = task_result
            result.status = TaskStatus.COMPLETED
            logger.info(f"  ✅ 任务完成: {task.name}")

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error(f"  ❌ 任务失败: {task.name}, 错误: {e}")

            # 重试逻辑
            if task.retry_on_failure and task.retry_count < 3:
                logger.info(f"  🔄 重试任务: {task.name} (尝试 {task.retry_count + 1}/3)")
                task.retry_count += 1
                return self._execute_task(task, context, workflow_id)

        finally:
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - start_time).total_seconds()

        return result

    def _resolve_context_refs(
        self,
        kwargs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析参数中的上下文引用"""
        resolved = {}
        for key, value in kwargs.items():
            if isinstance(value, str) and value.startswith("$"):
                # 上下文引用：$task_name 或 $task_name.field
                ref = value[1:]
                if "." in ref:
                    task_name, field = ref.split(".", 1)
                    resolved[key] = context.get(task_name, {}).get(field)
                else:
                    resolved[key] = context.get(ref)
            else:
                resolved[key] = value
        return resolved

    def get_execution(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """获取工作流执行实例"""
        return self.executions.get(workflow_id)

    def list_executions(self) -> List[WorkflowExecution]:
        """列出所有工作流执行实例"""
        return list(self.executions.values())

    def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流执行（仅标记状态）"""
        execution = self.executions.get(workflow_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.utcnow()
            logger.info(f"⏹️ 工作流已取消: {workflow_id}")
            return True
        return False


# 全局工作流引擎实例
workflow_engine = WorkflowEngine(max_workers=5)
