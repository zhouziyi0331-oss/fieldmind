"""
工作流引擎服务

提供工作流执行、步骤管理和状态追踪功能
"""
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
import asyncio
import json

from app.models.workflow_execution import (
    WorkflowExecution,
    WorkflowStep,
    WorkflowTemplate,
    WorkflowStatus,
    StepStatus
)


class WorkflowService:
    """工作流服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.step_handlers: Dict[str, Callable] = {}

    # ==================== 工作流执行 ====================

    async def create_execution(
        self,
        project_id: int,
        workflow_type: str,
        config: Dict[str, Any],
        template_id: Optional[int] = None,
        triggered_by: Optional[int] = None
    ) -> WorkflowExecution:
        """
        创建工作流执行实例

        Args:
            project_id: 项目ID
            workflow_type: 工作流类型（document_analysis, data_processing等）
            config: 工作流配置参数
            template_id: 可选，使用的模板ID
            triggered_by: 触发者用户ID

        Returns:
            创建的执行实例
        """
        execution = WorkflowExecution(
            project_id=project_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING,
            config=config,
            result={},
            extra_metadata={},
            template_id=template_id,
            triggered_by=triggered_by,
            started_at=None,
            completed_at=None,
            created_at=datetime.utcnow()
        )

        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def start_execution(
        self,
        execution_id: int,
        steps_config: List[Dict[str, Any]]
    ) -> WorkflowExecution:
        """
        启动工作流执行

        Args:
            execution_id: 执行实例ID
            steps_config: 步骤配置列表，每个步骤包含：
                - step_name: 步骤名称
                - step_type: 步骤类型
                - config: 步骤配置
                - dependencies: 依赖的步骤名称列表

        Returns:
            更新后的执行实例
        """
        # 获取执行实例
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"执行实例 {execution_id} 不存在")

        if execution.status != WorkflowStatus.PENDING:
            raise ValueError(f"执行实例状态错误: {execution.status}")

        # 创建步骤
        for idx, step_config in enumerate(steps_config):
            step = WorkflowStep(
                execution_id=execution_id,
                step_name=step_config['step_name'],
                step_type=step_config['step_type'],
                step_order=idx + 1,
                status=StepStatus.PENDING,
                config=step_config.get('config', {}),
                input_data={},
                output_data={},
                error_message=None,
                retry_count=0,
                dependencies=step_config.get('dependencies', []),
                started_at=None,
                completed_at=None,
                created_at=datetime.utcnow()
            )
            self.db.add(step)

        # 更新执行状态
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def execute_workflow(
        self,
        execution_id: int,
        progress_callback: Optional[Callable] = None
    ) -> WorkflowExecution:
        """
        执行工作流（异步执行所有步骤）

        Args:
            execution_id: 执行实例ID
            progress_callback: 可选，进度回调函数 (step_name, status, progress)

        Returns:
            完成后的执行实例
        """
        # 获取执行实例和步骤
        result = await self.db.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.steps))
            .where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"执行实例 {execution_id} 不存在")

        try:
            # 按依赖关系执行步骤
            await self._execute_steps_with_dependencies(
                execution,
                progress_callback
            )

            # 标记完成
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()

        except Exception as e:
            # 标记失败
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.extra_metadata['error'] = str(e)

            if progress_callback:
                await progress_callback("workflow", "failed", 100, error=str(e))

        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def _execute_steps_with_dependencies(
        self,
        execution: WorkflowExecution,
        progress_callback: Optional[Callable]
    ):
        """执行带依赖关系的步骤"""
        steps = sorted(execution.steps, key=lambda s: s.step_order)
        completed_steps = {}

        for step in steps:
            # 等待依赖步骤完成
            if step.dependencies:
                for dep_name in step.dependencies:
                    if dep_name not in completed_steps:
                        raise ValueError(f"步骤 {step.step_name} 的依赖 {dep_name} 未完成")

                    if completed_steps[dep_name].status != StepStatus.COMPLETED:
                        raise ValueError(f"步骤 {step.step_name} 的依赖 {dep_name} 执行失败")

                    # 传递依赖步骤的输出作为输入
                    step.input_data[dep_name] = completed_steps[dep_name].output_data

            # 执行步骤
            await self._execute_step(step, progress_callback)
            completed_steps[step.step_name] = step

    async def _execute_step(
        self,
        step: WorkflowStep,
        progress_callback: Optional[Callable]
    ):
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        await self.db.commit()

        if progress_callback:
            await progress_callback(step.step_name, "running", 0)

        try:
            # 查找步骤处理器
            handler = self.step_handlers.get(step.step_type)

            if not handler:
                raise ValueError(f"未找到步骤类型 {step.step_type} 的处理器")

            # 执行处理器
            output = await handler(step.config, step.input_data, progress_callback)

            # 保存输出
            step.output_data = output
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()

            if progress_callback:
                await progress_callback(step.step_name, "completed", 100)

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.completed_at = datetime.utcnow()

            if progress_callback:
                await progress_callback(step.step_name, "failed", 100, error=str(e))

            raise

        await self.db.commit()

    async def retry_step(
        self,
        step_id: int,
        max_retries: int = 3
    ) -> WorkflowStep:
        """
        重试失败的步骤

        Args:
            step_id: 步骤ID
            max_retries: 最大重试次数

        Returns:
            更新后的步骤
        """
        result = await self.db.execute(
            select(WorkflowStep).where(WorkflowStep.id == step_id)
        )
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError(f"步骤 {step_id} 不存在")

        if step.status != StepStatus.FAILED:
            raise ValueError(f"步骤状态不是失败: {step.status}")

        if step.retry_count >= max_retries:
            raise ValueError(f"已达到最大重试次数: {step.retry_count}/{max_retries}")

        # 重置步骤状态
        step.status = StepStatus.PENDING
        step.error_message = None
        step.retry_count += 1
        step.started_at = None
        step.completed_at = None

        await self.db.commit()
        await self.db.refresh(step)

        return step

    async def cancel_execution(self, execution_id: int) -> WorkflowExecution:
        """
        取消工作流执行

        Args:
            execution_id: 执行实例ID

        Returns:
            更新后的执行实例
        """
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"执行实例 {execution_id} 不存在")

        if execution.status not in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            raise ValueError(f"无法取消状态为 {execution.status} 的执行")

        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    # ==================== 工作流查询 ====================

    async def get_execution(
        self,
        execution_id: int,
        include_steps: bool = True
    ) -> Optional[WorkflowExecution]:
        """
        获取工作流执行实例

        Args:
            execution_id: 执行实例ID
            include_steps: 是否包含步骤信息

        Returns:
            执行实例
        """
        query = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)

        if include_steps:
            query = query.options(selectinload(WorkflowExecution.steps))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_executions(
        self,
        project_id: Optional[int] = None,
        workflow_type: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """
        查询工作流执行列表

        Args:
            project_id: 可选，筛选项目
            workflow_type: 可选，筛选工作流类型
            status: 可选，筛选状态
            limit: 返回数量限制
            offset: 分页偏移

        Returns:
            执行实例列表
        """
        conditions = []
        if project_id:
            conditions.append(WorkflowExecution.project_id == project_id)
        if workflow_type:
            conditions.append(WorkflowExecution.workflow_type == workflow_type)
        if status:
            conditions.append(WorkflowExecution.status == status)

        query = (
            select(WorkflowExecution)
            .where(and_(*conditions) if conditions else True)
            .order_by(desc(WorkflowExecution.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_execution_progress(self, execution_id: int) -> Dict[str, Any]:
        """
        获取工作流执行进度

        Args:
            execution_id: 执行实例ID

        Returns:
            进度信息
        """
        result = await self.db.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.steps))
            .where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            return {}

        total_steps = len(execution.steps)
        completed_steps = sum(1 for s in execution.steps if s.status == StepStatus.COMPLETED)
        failed_steps = sum(1 for s in execution.steps if s.status == StepStatus.FAILED)
        running_steps = sum(1 for s in execution.steps if s.status == StepStatus.RUNNING)

        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return {
            "execution_id": execution_id,
            "status": execution.status.value,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "running_steps": running_steps,
            "progress_percentage": progress_percentage,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "current_step": next(
                (s.step_name for s in execution.steps if s.status == StepStatus.RUNNING),
                None
            ),
            "steps": [
                {
                    "name": s.step_name,
                    "status": s.status.value,
                    "order": s.step_order,
                    "error": s.error_message
                }
                for s in sorted(execution.steps, key=lambda x: x.step_order)
            ]
        }

    # ==================== 模板管理 ====================

    async def create_template(
        self,
        name: str,
        workflow_type: str,
        description: Optional[str],
        steps_definition: List[Dict[str, Any]],
        default_config: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> WorkflowTemplate:
        """
        创建工作流模板

        Args:
            name: 模板名称
            workflow_type: 工作流类型
            description: 模板描述
            steps_definition: 步骤定义
            default_config: 默认配置
            created_by: 创建者用户ID

        Returns:
            创建的模板
        """
        template = WorkflowTemplate(
            name=name,
            workflow_type=workflow_type,
            description=description,
            steps_definition=steps_definition,
            default_config=default_config,
            is_active=True,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        return template

    async def list_templates(
        self,
        workflow_type: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[WorkflowTemplate]:
        """
        查询工作流模板列表

        Args:
            workflow_type: 可选，筛选工作流类型
            is_active: 可选，筛选是否激活

        Returns:
            模板列表
        """
        conditions = []
        if workflow_type:
            conditions.append(WorkflowTemplate.workflow_type == workflow_type)
        if is_active is not None:
            conditions.append(WorkflowTemplate.is_active == is_active)

        query = (
            select(WorkflowTemplate)
            .where(and_(*conditions) if conditions else True)
            .order_by(desc(WorkflowTemplate.created_at))
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    # ==================== 步骤处理器注册 ====================

    def register_step_handler(self, step_type: str, handler: Callable):
        """
        注册步骤处理器

        Args:
            step_type: 步骤类型
            handler: 处理器函数，签名: async def handler(config, input_data, progress_callback) -> output_data
        """
        self.step_handlers[step_type] = handler

    def get_registered_handlers(self) -> List[str]:
        """获取已注册的步骤处理器类型列表"""
        return list(self.step_handlers.keys())
