"""
SOP 服务
工作流编排和执行管理
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.sop import SOP, SOPExecution, SOPStatus, SOPCategory
from app.agents.agent_coordinator import AgentCoordinator
from app.services.skill_service import SkillService
import asyncio

logger = logging.getLogger(__name__)


class SOPService:
    """
    SOP 工作流服务

    功能：
    - SOP 创建和管理
    - 工作流执行
    - 步骤编排
    - 结果追踪
    """

    def __init__(self, db: Session):
        self.db = db
        self.coordinator = AgentCoordinator()
        self.skill_service = SkillService()

    # ========== SOP 管理 ==========

    def create_sop(
        self,
        name: str,
        display_name: str,
        category: SOPCategory,
        workflow: Dict[str, Any],
        description: str = None,
        project_id: int = None,
        tags: List[str] = None
    ) -> SOP:
        """
        创建新 SOP

        Args:
            name: SOP 唯一名称
            display_name: 显示名称
            category: 分类
            workflow: 工作流定义
            description: 描述
            project_id: 关联项目
            tags: 标签

        Returns:
            SOP 对象
        """
        sop = SOP(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            status=SOPStatus.DRAFT,
            workflow=workflow,
            tags=tags or [],
            project_id=project_id
        )

        self.db.add(sop)
        self.db.commit()
        self.db.refresh(sop)

        logger.info(f"创建 SOP: {name} (id={sop.id})")
        return sop

    def get_sop(self, sop_id: int) -> Optional[SOP]:
        """获取 SOP"""
        return self.db.query(SOP).filter(SOP.id == sop_id).first()

    def get_sop_by_name(self, name: str) -> Optional[SOP]:
        """根据名称获取 SOP"""
        return self.db.query(SOP).filter(SOP.name == name).first()

    def list_sops(
        self,
        category: Optional[SOPCategory] = None,
        status: Optional[SOPStatus] = None,
        project_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SOP]:
        """
        列出 SOP

        Args:
            category: 筛选分类
            status: 筛选状态
            project_id: 筛选项目
            limit: 数量限制

        Returns:
            SOP 列表
        """
        query = self.db.query(SOP)

        if category:
            query = query.filter(SOP.category == category)
        if status:
            query = query.filter(SOP.status == status)
        if project_id:
            query = query.filter(SOP.project_id == project_id)

        return query.order_by(SOP.created_at.desc()).limit(limit).all()

    def update_sop(self, sop_id: int, **kwargs) -> Optional[SOP]:
        """更新 SOP"""
        sop = self.get_sop(sop_id)
        if not sop:
            return None

        for key, value in kwargs.items():
            if hasattr(sop, key):
                setattr(sop, key, value)

        self.db.commit()
        self.db.refresh(sop)
        return sop

    def activate_sop(self, sop_id: int) -> bool:
        """激活 SOP"""
        sop = self.get_sop(sop_id)
        if not sop:
            return False

        sop.status = SOPStatus.ACTIVE
        self.db.commit()
        logger.info(f"激活 SOP: {sop.name}")
        return True

    def archive_sop(self, sop_id: int) -> bool:
        """归档 SOP"""
        sop = self.get_sop(sop_id)
        if not sop:
            return False

        sop.status = SOPStatus.ARCHIVED
        self.db.commit()
        logger.info(f"归档 SOP: {sop.name}")
        return True

    # ========== 工作流执行 ==========

    async def execute_sop(
        self,
        sop_id: int,
        input_data: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> SOPExecution:
        """
        执行 SOP 工作流

        Args:
            sop_id: SOP ID
            input_data: 输入数据
            project_id: 项目 ID

        Returns:
            SOPExecution 执行记录
        """
        sop = self.get_sop(sop_id)
        if not sop:
            raise ValueError(f"SOP {sop_id} 不存在")

        if sop.status != SOPStatus.ACTIVE:
            raise ValueError(f"SOP {sop.name} 未激活，当前状态: {sop.status}")

        # 创建执行记录
        execution = SOPExecution(
            sop_id=sop_id,
            project_id=project_id,
            status="pending",
            input_data=input_data,
            total_steps=len(sop.workflow.get("steps", [])),
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        logger.info(f"开始执行 SOP: {sop.name} (execution_id={execution.id})")

        try:
            # 更新状态为运行中
            execution.status = "running"
            self.db.commit()

            # 执行工作流
            result = await self._run_workflow(sop, execution, input_data)

            # 更新完成状态
            execution.status = "completed"
            execution.output_data = result
            execution.completed_at = datetime.utcnow()
            execution.duration = int((execution.completed_at - execution.started_at).total_seconds())

            self.db.commit()
            logger.info(f"SOP 执行完成: {sop.name}")

        except Exception as e:
            # 更新失败状态
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"SOP 执行失败: {sop.name} - {e}")
            raise

        return execution

    async def _run_workflow(
        self,
        sop: SOP,
        execution: SOPExecution,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        运行工作流

        Args:
            sop: SOP 对象
            execution: 执行记录
            input_data: 输入数据

        Returns:
            执行结果
        """
        workflow = sop.workflow
        steps = workflow.get("steps", [])
        context = {"input": input_data, "results": {}}

        for i, step in enumerate(steps):
            execution.current_step = i
            self.db.commit()

            logger.info(f"执行步骤 {i+1}/{len(steps)}: {step.get('name')}")

            try:
                step_result = await self._execute_step(step, context)
                context["results"][step["name"]] = step_result

                # 记录步骤结果
                if not execution.step_results:
                    execution.step_results = []
                execution.step_results.append({
                    "step": i,
                    "name": step["name"],
                    "status": "success",
                    "result": step_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.db.commit()

            except Exception as e:
                logger.error(f"步骤 {step['name']} 执行失败: {e}")
                execution.step_results.append({
                    "step": i,
                    "name": step["name"],
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.db.commit()
                raise

        return context["results"]

    async def _execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        执行单个步骤

        Args:
            step: 步骤定义
            context: 上下文

        Returns:
            步骤结果
        """
        step_type = step.get("type")
        step_config = step.get("config", {})

        # 解析参数（支持引用上下文）
        params = self._resolve_params(step_config.get("params", {}), context)

        if step_type == "agent":
            # 执行 Agent
            agent_name = step_config["agent"]
            return await self.coordinator.execute_agent(agent_name, **params)

        elif step_type == "skill":
            # 执行 Skill
            skill_name = step_config["skill"]
            return await self.skill_service.execute_skill(skill_name, **params)

        elif step_type == "workflow":
            # 执行子工作流
            tasks = []
            for task in step_config.get("tasks", []):
                task_params = self._resolve_params(task.get("params", {}), context)
                if task["type"] == "agent":
                    tasks.append(self.coordinator.execute_agent(task["agent"], **task_params))
                elif task["type"] == "skill":
                    tasks.append(self.skill_service.execute_skill(task["skill"], **task_params))

            results = await asyncio.gather(*tasks)
            return results

        elif step_type == "condition":
            # 条件分支
            condition = step_config["condition"]
            if self._evaluate_condition(condition, context):
                return await self._execute_step(step_config["then"], context)
            elif "else" in step_config:
                return await self._execute_step(step_config["else"], context)
            return None

        else:
            raise ValueError(f"未知步骤类型: {step_type}")

    def _resolve_params(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析参数（支持 ${context.path} 引用）

        Args:
            params: 参数定义
            context: 上下文

        Returns:
            解析后的参数
        """
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 引用上下文
                path = value[2:-1]
                resolved[key] = self._get_context_value(path, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_params({"item": v}, context)["item"] if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                resolved[key] = value
        return resolved

    def _get_context_value(self, path: str, context: Dict[str, Any]) -> Any:
        """从上下文中获取值"""
        parts = path.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        评估条件

        Args:
            condition: 条件定义
            context: 上下文

        Returns:
            条件是否满足
        """
        left = self._get_context_value(condition["left"], context)
        right = condition.get("right")
        operator = condition.get("operator", "==")

        if operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        elif operator == ">":
            return left > right
        elif operator == ">=":
            return left >= right
        elif operator == "<":
            return left < right
        elif operator == "<=":
            return left <= right
        elif operator == "in":
            return left in right
        elif operator == "not_in":
            return left not in right
        else:
            return False

    # ========== 执行记录查询 ==========

    def get_execution(self, execution_id: int) -> Optional[SOPExecution]:
        """获取执行记录"""
        return self.db.query(SOPExecution).filter(SOPExecution.id == execution_id).first()

    def list_executions(
        self,
        sop_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SOPExecution]:
        """列出执行记录"""
        query = self.db.query(SOPExecution)

        if sop_id:
            query = query.filter(SOPExecution.sop_id == sop_id)
        if project_id:
            query = query.filter(SOPExecution.project_id == project_id)
        if status:
            query = query.filter(SOPExecution.status == status)

        return query.order_by(SOPExecution.created_at.desc()).limit(limit).all()

    def cancel_execution(self, execution_id: int) -> bool:
        """取消执行"""
        execution = self.get_execution(execution_id)
        if not execution or execution.status not in ["pending", "running"]:
            return False

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"取消 SOP 执行: {execution_id}")
        return True
