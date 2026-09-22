"""
Agent协调器 (Agent Coordinator)

多Agent编排系统，提供：
1. 任务依赖图管理
2. 并行/串行/依赖执行模式
3. Agent间通信和数据传递
4. 结果聚合和融合
5. 错误恢复和重试

支持复杂的多Agent工作流编排
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
import asyncio
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    PARALLEL = "parallel"      # 并行执行
    SEQUENTIAL = "sequential"  # 串行执行
    DEPENDENCY = "dependency"  # 依赖图执行


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentTask:
    """Agent任务"""

    def __init__(
        self,
        task_id: str,
        agent_type: str,
        input_data: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.agent_type = agent_type
        self.input_data = input_data
        self.dependencies = dependencies or []
        self.metadata = metadata or {}

        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.retry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'agent_type': self.agent_type,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'retry_count': self.retry_count,
            'metadata': self.metadata
        }


class DependencyGraph:
    """依赖图"""

    def __init__(self):
        self.graph = defaultdict(list)  # task_id -> [dependent_task_ids]
        self.reverse_graph = defaultdict(list)  # task_id -> [dependency_task_ids]
        self.in_degree = defaultdict(int)  # task_id -> 入度

    def add_task(self, task_id: str, dependencies: List[str]):
        """添加任务及其依赖"""
        for dep in dependencies:
            self.graph[dep].append(task_id)
            self.reverse_graph[task_id].append(dep)

        self.in_degree[task_id] = len(dependencies)

        # 确保依赖的任务也在图中
        for dep in dependencies:
            if dep not in self.in_degree:
                self.in_degree[dep] = 0

    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """获取可以执行的任务（所有依赖已完成）"""
        ready = []
        for task_id, degree in self.in_degree.items():
            if degree == 0 and task_id not in completed_tasks:
                ready.append(task_id)
        return ready

    def mark_completed(self, task_id: str):
        """标记任务完成，更新依赖任务的入度"""
        for dependent in self.graph[task_id]:
            self.in_degree[dependent] -= 1

    def has_cycle(self) -> bool:
        """检测是否有循环依赖"""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.in_degree.keys():
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def topological_sort(self) -> List[List[str]]:
        """拓扑排序，返回分层的任务列表"""
        layers = []
        temp_in_degree = self.in_degree.copy()

        while any(degree >= 0 for degree in temp_in_degree.values()):
            # 找到当前层（入度为0的任务）
            current_layer = [
                task_id for task_id, degree in temp_in_degree.items()
                if degree == 0
            ]

            if not current_layer:
                break

            layers.append(current_layer)

            # 更新入度
            for task_id in current_layer:
                temp_in_degree[task_id] = -1  # 标记为已处理
                for dependent in self.graph[task_id]:
                    temp_in_degree[dependent] -= 1

        return layers


class AgentCoordinator:
    """Agent协调器"""

    def __init__(self, agent_registry=None):
        """
        初始化协调器

        Args:
            agent_registry: Agent注册中心
        """
        self.agent_registry = agent_registry
        self.tasks: Dict[str, AgentTask] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # 配置
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒
        self.max_parallel_tasks = 10

        logger.info("✅ Agent协调器初始化")

    # ==================== 核心编排方法 ====================

    def orchestrate(
        self,
        tasks: List[Dict[str, Any]],
        mode: ExecutionMode = ExecutionMode.DEPENDENCY,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        编排多个Agent任务

        Args:
            tasks: 任务列表，每个任务包含：
                {
                    'task_id': str,
                    'agent_type': str,
                    'input_data': dict,
                    'dependencies': [task_ids],  # 可选
                    'metadata': dict  # 可选
                }
            mode: 执行模式
            config: 配置选项

        Returns:
            编排结果
        """
        start_time = datetime.now()
        config = config or {}

        logger.info(
            f"🎯 开始Agent编排: mode={mode.value}, "
            f"tasks={len(tasks)}"
        )

        try:
            # 1. 创建任务对象
            self.tasks = {}
            for task_def in tasks:
                task = AgentTask(
                    task_id=task_def['task_id'],
                    agent_type=task_def['agent_type'],
                    input_data=task_def['input_data'],
                    dependencies=task_def.get('dependencies', []),
                    metadata=task_def.get('metadata', {})
                )
                self.tasks[task.task_id] = task

            # 2. 根据模式执行
            if mode == ExecutionMode.PARALLEL:
                results = self._execute_parallel()
            elif mode == ExecutionMode.SEQUENTIAL:
                results = self._execute_sequential()
            else:  # DEPENDENCY
                results = self._execute_dependency()

            # 3. 聚合结果
            aggregated = self._aggregate_results(results, config)

            # 4. 记录历史
            execution_time = (datetime.now() - start_time).total_seconds()

            execution_record = {
                'mode': mode.value,
                'total_tasks': len(tasks),
                'successful_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                'failed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.execution_history.append(execution_record)

            logger.info(
                f"✅ Agent编排完成: "
                f"successful={execution_record['successful_tasks']}, "
                f"failed={execution_record['failed_tasks']}, "
                f"time={execution_time:.2f}s"
            )

            return {
                'success': execution_record['failed_tasks'] == 0,
                'results': aggregated,
                'task_details': {tid: t.to_dict() for tid, t in self.tasks.items()},
                'execution_record': execution_record
            }

        except Exception as e:
            logger.error(f"❌ Agent编排失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'task_details': {tid: t.to_dict() for tid, t in self.tasks.items()}
            }

    # ==================== 执行模式实现 ====================

    def _execute_parallel(self) -> Dict[str, Any]:
        """并行执行所有任务"""
        logger.info("⚡ 并行执行模式")

        results = {}

        # 分批执行（限制并发数）
        task_ids = list(self.tasks.keys())

        for i in range(0, len(task_ids), self.max_parallel_tasks):
            batch = task_ids[i:i + self.max_parallel_tasks]

            batch_results = asyncio.run(
                self._execute_tasks_async(batch)
            )

            results.update(batch_results)

        return results

    def _execute_sequential(self) -> Dict[str, Any]:
        """串行执行所有任务"""
        logger.info("📝 串行执行模式")

        results = {}

        for task_id in self.tasks.keys():
            result = self._execute_single_task(task_id)
            results[task_id] = result

            # 如果失败且不允许继续，则停止
            if self.tasks[task_id].status == TaskStatus.FAILED:
                logger.warning(f"⚠️ 任务 {task_id} 失败，停止串行执行")
                break

        return results

    def _execute_dependency(self) -> Dict[str, Any]:
        """基于依赖图执行"""
        logger.info("🔗 依赖图执行模式")

        # 1. 构建依赖图
        dep_graph = DependencyGraph()
        for task_id, task in self.tasks.items():
            dep_graph.add_task(task_id, task.dependencies)

        # 2. 检测循环依赖
        if dep_graph.has_cycle():
            logger.error("❌ 检测到循环依赖！")
            for task in self.tasks.values():
                task.status = TaskStatus.FAILED
                task.error = "Circular dependency detected"
            return {}

        # 3. 拓扑排序得到执行层次
        layers = dep_graph.topological_sort()

        logger.info(f"📊 依赖图层次: {len(layers)} 层")
        for i, layer in enumerate(layers):
            logger.debug(f"  层 {i}: {layer}")

        # 4. 按层执行
        results = {}
        completed_tasks = set()

        for layer_idx, layer in enumerate(layers):
            logger.info(f"🔄 执行第 {layer_idx + 1}/{len(layers)} 层: {len(layer)} 个任务")

            # 并行执行当前层的任务
            layer_results = asyncio.run(
                self._execute_tasks_async(layer)
            )

            results.update(layer_results)

            # 更新完成状态
            for task_id in layer:
                if self.tasks[task_id].status == TaskStatus.COMPLETED:
                    completed_tasks.add(task_id)
                    dep_graph.mark_completed(task_id)

        return results

    async def _execute_tasks_async(
        self,
        task_ids: List[str]
    ) -> Dict[str, Any]:
        """异步并行执行多个任务"""
        tasks = [
            self._execute_single_task_async(task_id)
            for task_id in task_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            task_id: result if not isinstance(result, Exception) else {'error': str(result)}
            for task_id, result in zip(task_ids, results)
        }

    async def _execute_single_task_async(self, task_id: str) -> Any:
        """异步执行单个任务"""
        return self._execute_single_task(task_id)

    def _execute_single_task(self, task_id: str) -> Any:
        """执行单个任务（带重试）"""
        task = self.tasks[task_id]

        logger.debug(f"▶️  执行任务: {task_id} ({task.agent_type})")

        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        for attempt in range(self.max_retries):
            try:
                # 检查依赖是否满足
                if not self._check_dependencies(task):
                    task.status = TaskStatus.SKIPPED
                    task.error = "Dependencies not satisfied"
                    logger.warning(f"⚠️ 任务 {task_id} 跳过：依赖未满足")
                    return None

                # 准备输入（包含依赖任务的结果）
                enhanced_input = self._prepare_task_input(task)

                # 执行Agent
                result = self._execute_agent(
                    agent_type=task.agent_type,
                    input_data=enhanced_input
                )

                # 标记成功
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.end_time = datetime.now()

                logger.debug(f"✅ 任务 {task_id} 完成")

                return result

            except Exception as e:
                task.retry_count = attempt + 1
                logger.warning(
                    f"⚠️ 任务 {task_id} 失败 "
                    f"(尝试 {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.retry_delay)
                else:
                    # 最终失败
                    task.status = TaskStatus.FAILED
                    task.error = e
                    task.end_time = datetime.now()
                    logger.error(f"❌ 任务 {task_id} 最终失败: {e}")
                    return None

    def _check_dependencies(self, task: AgentTask) -> bool:
        """检查任务的依赖是否都已成功完成"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False

            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def _prepare_task_input(self, task: AgentTask) -> Dict[str, Any]:
        """准备任务输入，包含依赖任务的结果"""
        enhanced_input = task.input_data.copy()

        # 添加依赖任务的结果
        if task.dependencies:
            dependency_results = {}
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    dependency_results[dep_id] = self.tasks[dep_id].result

            enhanced_input['_dependency_results'] = dependency_results

        return enhanced_input

    def _execute_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any]
    ) -> Any:
        """执行具体的Agent"""
        if not self.agent_registry:
            raise RuntimeError("Agent registry not initialized")

        # 从注册中心获取Agent并执行
        agent = self.agent_registry.get_agent(agent_type)

        if not agent:
            raise ValueError(f"Agent type '{agent_type}' not found in registry")

        result = agent.execute(input_data)

        return result

    # ==================== 结果聚合 ====================

    def _aggregate_results(
        self,
        results: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """聚合多个Agent的结果"""
        aggregation_strategy = config.get('aggregation_strategy', 'merge')

        if aggregation_strategy == 'merge':
            return self._merge_results(results)
        elif aggregation_strategy == 'hierarchy':
            return self._hierarchy_results(results)
        elif aggregation_strategy == 'summary':
            return self._summarize_results(results)
        else:
            return results

    def _merge_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """合并结果"""
        merged = {
            'task_results': results,
            'task_count': len(results),
            'successful_count': sum(1 for r in results.values() if r is not None)
        }

        return merged

    def _hierarchy_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """层次化结果"""
        hierarchy = {}

        for task_id, result in results.items():
            task = self.tasks[task_id]
            agent_type = task.agent_type

            if agent_type not in hierarchy:
                hierarchy[agent_type] = []

            hierarchy[agent_type].append({
                'task_id': task_id,
                'result': result,
                'metadata': task.metadata
            })

        return hierarchy

    def _summarize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """总结结果"""
        # TODO: 使用LLM生成结果摘要
        summary = {
            'total_tasks': len(results),
            'successful_tasks': sum(1 for r in results.values() if r is not None),
            'key_insights': []  # 从各Agent结果中提取关键见解
        }

        return summary

    # ==================== 工具方法 ====================

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        return None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务（如果尚未执行）"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.SKIPPED
                task.error = "Cancelled by user"
                return True
        return False

    def get_coordinator_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            'active_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            'total_executions': len(self.execution_history),
            'config': {
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'max_parallel_tasks': self.max_parallel_tasks
            }
        }


# 全局单例
_coordinator_instance = None


def get_agent_coordinator(agent_registry=None) -> AgentCoordinator:
    """获取Agent协调器单例"""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = AgentCoordinator(agent_registry)
    return _coordinator_instance
