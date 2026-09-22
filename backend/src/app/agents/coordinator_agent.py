"""
协调 Agent
高级 Agent 协调和任务编排
"""
from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio
from datetime import datetime
from app.agents.agent_registry import register_agent, get_agent_registry

logger = logging.getLogger(__name__)


@register_agent("coordinator")
class CoordinatorAgent:
    """
    协调 Agent

    功能：
    - 多 Agent 任务编排
    - 依赖管理和执行顺序
    - 结果聚合和分发
    - 错误处理和重试
    """

    def __init__(self):
        self.name = "coordinator"
        self.description = "多 Agent 协调和任务编排"
        self.registry = get_agent_registry()

    async def execute(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行协调计划

        Args:
            plan: 执行计划
                {
                    "tasks": [
                        {
                            "id": "task1",
                            "agent": "entity_relation",
                            "params": {...},
                            "depends_on": []
                        }
                    ],
                    "mode": "sequential" | "parallel" | "dag"
                }
            context: 上下文数据

        Returns:
            {
                "results": {task_id: result},
                "execution_time": float,
                "status": "completed" | "failed"
            }
        """
        start_time = datetime.now()
        logger.info(f"开始执行协调计划 (tasks={len(plan.get('tasks', []))})")

        context = context or {}
        mode = plan.get("mode", "sequential")
        tasks = plan.get("tasks", [])

        try:
            if mode == "sequential":
                results = await self._execute_sequential(tasks, context)
            elif mode == "parallel":
                results = await self._execute_parallel(tasks, context)
            elif mode == "dag":
                results = await self._execute_dag(tasks, context)
            else:
                raise ValueError(f"未知执行模式: {mode}")

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"协调计划执行完成 (time={execution_time:.2f}s)")

            return {
                "results": results,
                "execution_time": execution_time,
                "status": "completed"
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"协调计划执行失败: {e}")

            return {
                "results": {},
                "execution_time": execution_time,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_sequential(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """顺序执行任务"""
        results = {}

        for task in tasks:
            task_id = task["id"]
            logger.info(f"执行任务: {task_id}")

            try:
                result = await self._execute_task(task, context, results)
                results[task_id] = result
                logger.info(f"✓ 任务 {task_id} 完成")

            except Exception as e:
                logger.error(f"✗ 任务 {task_id} 失败: {e}")
                results[task_id] = {"error": str(e), "status": "failed"}

                # 检查是否允许失败
                if not task.get("allow_failure", False):
                    raise

        return results

    async def _execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """并行执行任务"""
        logger.info(f"并行执行 {len(tasks)} 个任务")

        # 创建所有任务的协程
        task_coroutines = []
        task_ids = []

        for task in tasks:
            task_id = task["id"]
            task_ids.append(task_id)
            task_coroutines.append(self._execute_task(task, context, {}))

        # 并行执行
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # 组装结果
        results = {}
        for task_id, result in zip(task_ids, task_results):
            if isinstance(result, Exception):
                results[task_id] = {"error": str(result), "status": "failed"}
                logger.error(f"✗ 任务 {task_id} 失败: {result}")
            else:
                results[task_id] = result
                logger.info(f"✓ 任务 {task_id} 完成")

        return results

    async def _execute_dag(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        DAG 模式执行（有向无环图）
        根据依赖关系智能调度
        """
        logger.info(f"DAG 模式执行 {len(tasks)} 个任务")

        # 构建依赖图
        task_map = {task["id"]: task for task in tasks}
        results = {}
        completed = set()
        running = {}

        # 找到所有没有依赖的任务（入口点）
        ready_tasks = [
            task for task in tasks
            if not task.get("depends_on") or len(task.get("depends_on", [])) == 0
        ]

        while len(completed) < len(tasks):
            # 启动所有就绪的任务
            if ready_tasks:
                batch_coroutines = []
                batch_ids = []

                for task in ready_tasks:
                    task_id = task["id"]
                    if task_id not in completed and task_id not in running:
                        batch_ids.append(task_id)
                        batch_coroutines.append(self._execute_task(task, context, results))
                        running[task_id] = True

                if batch_coroutines:
                    logger.info(f"启动任务批次: {batch_ids}")
                    batch_results = await asyncio.gather(*batch_coroutines, return_exceptions=True)

                    # 处理结果
                    for task_id, result in zip(batch_ids, batch_results):
                        if isinstance(result, Exception):
                            results[task_id] = {"error": str(result), "status": "failed"}
                            logger.error(f"✗ 任务 {task_id} 失败: {result}")

                            # 检查是否允许失败
                            task = task_map[task_id]
                            if not task.get("allow_failure", False):
                                raise result
                        else:
                            results[task_id] = result
                            logger.info(f"✓ 任务 {task_id} 完成")

                        completed.add(task_id)
                        del running[task_id]

                ready_tasks = []

            # 找到新的就绪任务
            for task in tasks:
                task_id = task["id"]
                if task_id in completed:
                    continue

                depends_on = task.get("depends_on", [])
                if all(dep in completed for dep in depends_on):
                    ready_tasks.append(task)

            # 防止死锁
            if not ready_tasks and len(completed) < len(tasks) and not running:
                uncompleted = [t["id"] for t in tasks if t["id"] not in completed]
                raise RuntimeError(f"DAG 执行死锁，未完成任务: {uncompleted}")

        return results

    async def _execute_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Any:
        """
        执行单个任务

        Args:
            task: 任务定义
            context: 全局上下文
            results: 已完成任务的结果

        Returns:
            任务执行结果
        """
        agent_name = task["agent"]
        params = task.get("params", {})

        # 解析参数（支持引用上下文和其他任务结果）
        resolved_params = self._resolve_params(params, context, results)

        # 获取 Agent
        agent = self.registry.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' 不存在")

        # 执行 Agent
        result = await agent.execute(**resolved_params)

        # 后处理
        if "transform" in task:
            result = self._apply_transform(result, task["transform"])

        return result

    def _resolve_params(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析参数引用

        支持：
        - ${context.key}: 引用上下文
        - ${results.task_id.key}: 引用其他任务结果
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 引用表达式
                ref_path = value[2:-1]
                resolved[key] = self._resolve_reference(ref_path, context, results)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value, context, results)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_params({"item": v}, context, results)["item"]
                    if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                resolved[key] = value

        return resolved

    def _resolve_reference(
        self,
        ref_path: str,
        context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Any:
        """解析引用路径"""
        parts = ref_path.split(".")

        if parts[0] == "context":
            # 引用上下文
            value = context
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value

        elif parts[0] == "results":
            # 引用任务结果
            if len(parts) < 2:
                return None

            task_id = parts[1]
            value = results.get(task_id)

            for part in parts[2:]:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value

        return None

    def _apply_transform(self, result: Any, transform: Dict[str, Any]) -> Any:
        """应用结果转换"""
        transform_type = transform.get("type")

        if transform_type == "extract":
            # 提取字段
            field = transform.get("field")
            return result.get(field) if isinstance(result, dict) else result

        elif transform_type == "aggregate":
            # 聚合列表
            if not isinstance(result, list):
                return result

            agg_func = transform.get("function", "list")
            if agg_func == "count":
                return len(result)
            elif agg_func == "sum":
                return sum(result)
            elif agg_func == "avg":
                return sum(result) / len(result) if result else 0
            else:
                return result

        elif transform_type == "filter":
            # 过滤结果
            if not isinstance(result, list):
                return result

            condition = transform.get("condition", {})
            return [item for item in result if self._match_condition(item, condition)]

        return result

    def _match_condition(self, item: Any, condition: Dict[str, Any]) -> bool:
        """匹配条件"""
        if not isinstance(item, dict):
            return False

        for key, expected in condition.items():
            if item.get(key) != expected:
                return False

        return True

    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行预定义工作流

        Args:
            workflow_name: 工作流名称
            input_data: 输入数据

        Returns:
            工作流执行结果
        """
        # 加载工作流定义（从配置或数据库）
        workflow = self._load_workflow(workflow_name)

        if not workflow:
            raise ValueError(f"工作流 '{workflow_name}' 不存在")

        # 执行
        return await self.execute(workflow, context=input_data)

    def _load_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """加载工作流定义（占位符，实际应从配置或数据库加载）"""
        # TODO: 从配置文件或数据库加载工作流定义
        workflows = {
            "full_analysis": {
                "mode": "dag",
                "tasks": [
                    {
                        "id": "extract_entities",
                        "agent": "entity_relation",
                        "params": {"content": "${context.content}"},
                        "depends_on": []
                    },
                    {
                        "id": "search_related",
                        "agent": "search",
                        "params": {
                            "query": "${results.extract_entities.keywords}",
                            "top_k": 10
                        },
                        "depends_on": ["extract_entities"]
                    },
                    {
                        "id": "summarize",
                        "agent": "summary",
                        "params": {"documents": "${results.search_related.documents}"},
                        "depends_on": ["search_related"]
                    }
                ]
            }
        }

        return workflows.get(workflow_name)
