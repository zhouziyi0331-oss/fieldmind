"""
WorkflowBase - Workflow基类
所有Workflow继承此类，实现标准化的工作流执行接口
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class V2AgentWrapper:
    """
    v2 Agent包装器

    将v2 Agent包装成旧Agent接口，实现WorkflowBase与v2架构的互操作
    """

    def __init__(self, agent_type: str, adapter):
        self.agent_type = agent_type
        self.adapter = adapter

    def execute_task(self, task):
        """
        执行任务（兼容旧Agent接口）

        Args:
            task: AgentTask对象

        Returns:
            模拟的AgentResult对象
        """
        # 从task中提取数据
        input_data = task.input_data
        metadata = task.metadata

        # 特殊处理：skills类型使用skill_analyzer工具
        if self.agent_type == 'skills':
            return self._execute_skills_analyzer(task)

        # 需要数据库会话，从task中获取或使用全局
        db_session = input_data.get('db_session')
        if not db_session:
            # 如果没有传递db_session，尝试从全局获取
            logger.warning(f"⚠️ V2AgentWrapper未收到db_session，尝试创建新会话")
            from app.database import SessionLocal
            db_session = SessionLocal()
            should_close_session = True
        else:
            should_close_session = False

        try:
            # 调用v2适配器
            v2_result = self.adapter.execute_v2_agent(
                agent_type=self.agent_type,
                input_data=input_data,
                db_session=db_session,
                metadata=metadata
            )

            # 转换为旧AgentResult格式
            from app.services.agents.base_agent import AgentResult

            return AgentResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=v2_result.success,
                output_data=v2_result.output_data,
                errors=v2_result.errors,
                warnings=v2_result.warnings,
                metadata={'agent_type': v2_result.agent_type, 'execution_time': v2_result.execution_time}
            )

        finally:
            if should_close_session:
                db_session.close()

    def _execute_skills_analyzer(self, task):
        """
        执行Skills分析（使用skill_analyzer工具）

        Args:
            task: AgentTask对象

        Returns:
            AgentResult对象
        """
        import time
        from app.services.agents.base_agent import AgentResult

        start_time = time.time()
        input_data = task.input_data

        try:
            project_id = input_data.get('project_id')
            enabled_skills = input_data.get('enabled_skills')
            report_format = input_data.get('report_format', 'full')
            db_session = input_data.get('db_session')

            if not project_id:
                raise ValueError("Skills分析需要project_id参数")

            if not db_session:
                from app.database import SessionLocal
                db_session = SessionLocal()
                should_close_session = True
            else:
                should_close_session = False

            try:
                # 从数据库获取项目的所有chunks文本
                from app.models.pipeline_state import DocumentChunk

                chunks = db_session.query(DocumentChunk).filter(
                    DocumentChunk.project_id == project_id
                ).all()

                if not chunks:
                    raise ValueError(f"项目 {project_id} 没有chunks，无法进行Skills分析")

                # 聚合所有chunks文本
                content = '\n\n'.join([chunk.chunk_text for chunk in chunks])
                logger.info(f"📝 聚合了 {len(chunks)} 个chunks用于Skills分析（总长度={len(content)}字符）")

                # 调用skill_analyzer
                from app.tools.summary.skill_analyzer import analyze_with_skills

                skills_result = analyze_with_skills(
                    content=content,
                    enabled_skills=enabled_skills,
                    report_format=report_format,
                    include_statistics=True
                )

                elapsed_time = time.time() - start_time

                logger.info(f"✅ Skills分析完成（执行了 {len(skills_result.get('skills_executed', []))} 个Skills，耗时={elapsed_time:.2f}秒）")

                return AgentResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    success=True,
                    output_data=skills_result,
                    errors=[],
                    warnings=[],
                    metadata={'execution_time': elapsed_time}
                )

            finally:
                if should_close_session:
                    db_session.close()

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Skills分析失败: {e}", exc_info=True)

            return AgentResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=False,
                output_data={},
                errors=[str(e)],
                warnings=[],
                metadata={'execution_time': elapsed_time}
            )


class WorkflowStatus(Enum):
    """Workflow执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    step_id: str                        # 步骤ID
    step_name: str                      # 步骤名称
    agent_type: str                     # 使用的Agent类型
    input_mapping: Dict[str, str]       # 输入字段映射
    output_mapping: Dict[str, str]      # 输出字段映射
    required: bool = True               # 是否必需
    retry_on_failure: bool = False      # 失败时是否重试
    max_retries: int = 0                # 最大重试次数
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStepResult:
    """工作流步骤执行结果"""
    step_id: str
    step_name: str
    agent_type: str
    success: bool
    output_data: Dict[str, Any]
    execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowInput:
    """工作流输入"""
    workflow_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    success: bool
    steps_results: List[WorkflowStepResult]
    final_output: Dict[str, Any]
    total_execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class WorkflowBase(ABC):
    """
    Workflow基类

    所有Workflow继承此类，定义工作流的步骤和执行逻辑
    """

    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id or self._generate_workflow_id()
        self.status = WorkflowStatus.PENDING
        self.steps = self._define_steps()
        self.agent_pool = {}  # Agent实例池
        self.context = {}     # 工作流上下文数据

    @abstractmethod
    def name(self) -> str:
        """返回Workflow名称"""
        pass

    @abstractmethod
    def description(self) -> str:
        """返回Workflow描述"""
        pass

    @abstractmethod
    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        pass

    def _generate_workflow_id(self) -> str:
        """生成Workflow ID"""
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"workflow_{suffix}"

    def execute(self, workflow_input: WorkflowInput) -> WorkflowResult:
        """
        执行工作流

        Args:
            workflow_input: 工作流输入

        Returns:
            WorkflowResult: 执行结果
        """
        import time

        logger.info(f"Workflow {self.workflow_id} ({self.name()}) 开始执行")

        self.status = WorkflowStatus.RUNNING
        start_time = time.time()

        steps_results = []
        errors = []
        warnings = []

        # 初始化上下文
        self.context = workflow_input.input_data.copy()

        try:
            # 顺序执行步骤
            for step in self.steps:
                logger.info(f"执行步骤: {step.step_name} (agent={step.agent_type})")

                step_result = self._execute_step(step, workflow_input.config)
                steps_results.append(step_result)

                if not step_result.success:
                    if step.required:
                        # 必需步骤失败，终止工作流
                        logger.error(f"必需步骤 {step.step_name} 失败，终止工作流")
                        errors.extend(step_result.errors)
                        break
                    else:
                        # 可选步骤失败，继续执行
                        logger.warning(f"可选步骤 {step.step_name} 失败，继续执行")
                        warnings.extend(step_result.errors)

                # 更新上下文
                self._update_context(step, step_result)

            # 判断整体成功
            required_steps_success = all(
                r.success for r, s in zip(steps_results, self.steps) if s.required
            )

            if required_steps_success:
                self.status = WorkflowStatus.COMPLETED
                success = True
            else:
                self.status = WorkflowStatus.FAILED
                success = False

            elapsed_time = time.time() - start_time

            # 构建最终输出
            final_output = self._build_final_output(steps_results)

            result = WorkflowResult(
                workflow_id=self.workflow_id,
                workflow_name=self.name(),
                status=self.status,
                success=success,
                steps_results=steps_results,
                final_output=final_output,
                total_execution_time=elapsed_time,
                errors=errors,
                warnings=warnings,
                metadata={
                    'total_steps': len(self.steps),
                    'completed_steps': len(steps_results),
                    'failed_steps': sum(1 for r in steps_results if not r.success)
                }
            )

            logger.info(
                f"Workflow {self.workflow_id} 执行完成，"
                f"状态={self.status.value}，耗时={elapsed_time:.2f}秒"
            )

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            elapsed_time = time.time() - start_time

            logger.error(f"Workflow {self.workflow_id} 执行失败: {str(e)}")

            return WorkflowResult(
                workflow_id=self.workflow_id,
                workflow_name=self.name(),
                status=WorkflowStatus.FAILED,
                success=False,
                steps_results=steps_results,
                final_output={},
                total_execution_time=elapsed_time,
                errors=[str(e)],
                warnings=warnings
            )

    def _execute_step(
        self,
        step: WorkflowStep,
        config: Dict[str, Any]
    ) -> WorkflowStepResult:
        """执行单个步骤"""
        import time

        start_time = time.time()

        try:
            # 获取Agent
            agent = self._get_agent(step.agent_type)

            # 准备输入数据
            input_data = self._prepare_step_input(step)

            # 创建任务
            from app.services.agents.base_agent import AgentTask

            task = AgentTask(
                task_id=f"{step.step_id}_{datetime.now().timestamp()}",
                task_type=step.agent_type,
                input_data=input_data,
                priority=5,
                metadata=step.metadata
            )

            # 执行任务
            agent_result = agent.execute_task(task)

            elapsed_time = time.time() - start_time

            return WorkflowStepResult(
                step_id=step.step_id,
                step_name=step.step_name,
                agent_type=step.agent_type,
                success=agent_result.success,
                output_data=agent_result.output_data,
                execution_time=elapsed_time,
                errors=agent_result.errors,
                warnings=agent_result.warnings
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"步骤 {step.step_name} 执行失败: {str(e)}")

            return WorkflowStepResult(
                step_id=step.step_id,
                step_name=step.step_name,
                agent_type=step.agent_type,
                success=False,
                output_data={},
                execution_time=elapsed_time,
                errors=[str(e)]
            )

    def _prepare_step_input(self, step: WorkflowStep) -> Dict[str, Any]:
        """准备步骤输入数据"""
        input_data = {}

        # 根据input_mapping从上下文中提取数据
        for target_key, source_key in step.input_mapping.items():
            if source_key in self.context:
                input_data[target_key] = self.context[source_key]
            else:
                logger.warning(f"上下文中未找到 {source_key}，步骤 {step.step_name}")

        return input_data

    def _update_context(self, step: WorkflowStep, result: WorkflowStepResult):
        """更新工作流上下文"""
        if not result.success:
            return

        # 根据output_mapping更新上下文
        for source_key, target_key in step.output_mapping.items():
            if source_key in result.output_data:
                self.context[target_key] = result.output_data[source_key]

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建最终输出"""
        # 默认实现：返回所有步骤的输出
        output = {
            'steps': [
                {
                    'step_name': r.step_name,
                    'success': r.success,
                    'output': r.output_data
                }
                for r in steps_results
            ]
        }

        # 子类可以覆盖此方法自定义输出格式
        return output

    def _get_agent(self, agent_type: str):
        """获取Agent实例（使用池）"""
        if agent_type in self.agent_pool:
            return self.agent_pool[agent_type]

        # 创建新实例
        agent = self._create_agent(agent_type)
        self.agent_pool[agent_type] = agent
        return agent

    def _create_agent(self, agent_type: str):
        """
        创建Agent实例

        支持三套架构：
        - v2 Agents: ingestion, chunking, vectorization, knowledge, synthesis, report
        - Skills分析: skills (使用skill_analyzer工具)
        - 旧Agents（已废弃）: transcript, entity, relation, search, summary
        """
        # 🔥 优先使用v2适配器
        from .v2_adapter import get_v2_adapter

        adapter = get_v2_adapter()

        # v2 Agents或skills类型
        if adapter.supports_agent_type(agent_type) or agent_type == 'skills':
            # 返回v2适配器包装的伪Agent对象
            return V2AgentWrapper(agent_type, adapter)

        # 回退到旧Agent（已废弃，仅保留兼容性）
        logger.warning(f"⚠️ 使用已废弃的Agent类型: {agent_type}，建议迁移到v2架构")

        if agent_type == 'transcript':
            from app.services.agents.transcript_agent import TranscriptAgent
            return TranscriptAgent()
        elif agent_type == 'entity':
            from app.services.agents.entity_agent import EntityAgent
            return EntityAgent()
        elif agent_type == 'relation':
            from app.services.agents.relation_agent import RelationAgent
            return RelationAgent()
        elif agent_type == 'search':
            from app.services.agents.search_agent import SearchAgent
            return SearchAgent()
        elif agent_type == 'summary':
            from app.services.agents.summary_agent import SummaryAgent
            return SummaryAgent()
        else:
            raise ValueError(f'未知的Agent类型: {agent_type}')
