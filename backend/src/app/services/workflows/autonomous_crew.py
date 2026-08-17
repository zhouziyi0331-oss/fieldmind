"""
AutonomousCrew - 自主工作流（已废弃）

⚠️ 已废弃：此版本使用旧CoordinatorAgent架构
建议使用6-Agent v2的AgentCoordinator进行流程编排

使用CoordinatorAgent动态调度任务和工作流
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class AutonomousCrew(WorkflowBase):
    """
    自主工作流

    使用CoordinatorAgent作为大脑，根据任务类型动态选择和调度其他Agents：
    1. 任务分析 - 理解用户意图和任务类型
    2. 动态调度 - 根据任务类型选择合适的Agents或Workflows
    3. 结果整合 - 聚合所有子任务结果
    """

    def name(self) -> str:
        return "自主工作流"

    def description(self) -> str:
        return "使用CoordinatorAgent动态调度：任务分析 → 智能调度 → 结果整合"

    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            # 步骤1: 任务分析（使用EntityAgent提取关键信息）
            WorkflowStep(
                step_id="step_1_analyze",
                step_name="任务分析",
                agent_type="entity",
                input_mapping={
                    'content': 'task_description'  # 任务描述
                },
                output_mapping={
                    'entities': 'task_entities',
                    'entity_types': 'task_entity_types'
                },
                required=True,
                metadata={'description': '分析任务描述，提取关键实体'}
            ),

            # 步骤2: 动态调度（使用CoordinatorAgent）
            WorkflowStep(
                step_id="step_2_coordinate",
                step_name="动态任务调度",
                agent_type="coordinator",
                input_mapping={
                    'workflow_type': 'workflow_type',      # 工作流类型
                    'workflow_steps': 'workflow_steps',    # 自定义步骤
                    'input_data': 'coordinator_input',     # 协调器输入
                    'parallel': 'parallel'                 # 是否并行
                },
                output_mapping={
                    'workflow_name': 'executed_workflow',
                    'results': 'coordination_results',
                    'completed_steps': 'completed_steps'
                },
                required=True,
                metadata={'description': '协调器动态调度子任务'}
            ),

            # 步骤3: 结果整合（使用SummaryAgent）
            WorkflowStep(
                step_id="step_3_integrate",
                step_name="结果整合",
                agent_type="summary",
                input_mapping={
                    'content': 'integration_content',
                    'report_format': 'report_format'
                },
                output_mapping={
                    'insights': 'final_insights',
                    'skills_executed': 'skills_executed'
                },
                required=False,  # 可选，取决于是否需要最终分析
                metadata={'description': '整合所有结果并生成最终报告'}
            )
        ]

    def _prepare_step_input(self, step: WorkflowStep) -> Dict[str, Any]:
        """准备步骤输入（智能决策）"""
        input_data = super()._prepare_step_input(step)

        # 步骤2: 根据任务类型决定工作流
        if step.step_id == 'step_2_coordinate':
            if 'workflow_type' not in self.context:
                # 智能推断工作流类型
                self.context['workflow_type'] = self._infer_workflow_type()

            input_data['workflow_type'] = self.context['workflow_type']

            # 如果是custom类型，需要提供步骤
            if self.context['workflow_type'] == 'custom':
                if 'workflow_steps' not in self.context:
                    self.context['workflow_steps'] = self._build_custom_steps()
                input_data['workflow_steps'] = self.context['workflow_steps']

            # 准备协调器输入数据
            if 'coordinator_input' not in self.context:
                self.context['coordinator_input'] = self._prepare_coordinator_input()

            input_data['input_data'] = self.context['coordinator_input']

        # 步骤3: 聚合结果用于最终整合
        if step.step_id == 'step_3_integrate':
            if 'integration_content' not in self.context:
                self.context['integration_content'] = self._aggregate_results()

            input_data['content'] = self.context['integration_content']

        return input_data

    def _infer_workflow_type(self) -> str:
        """智能推断工作流类型"""
        task_desc = self.context.get('task_description', '').lower()
        entities = self.context.get('task_entities', [])

        # 基于关键词推断
        if any(word in task_desc for word in ['搜索', '研究', '调研', 'search', 'research']):
            logger.info("推断为research_report工作流")
            return 'custom'  # 使用搜索工作流

        elif any(word in task_desc for word in ['问答', '查询', '问题', 'query', 'question']):
            logger.info("推断为rag_query工作流")
            return 'custom'  # 使用RAG查询

        elif any(word in task_desc for word in ['转录', '音频', '视频', 'transcript', 'audio', 'video']):
            logger.info("推断为document_processing工作流")
            return 'custom'  # 使用文档处理

        else:
            # 默认：简单的搜索+分析
            logger.info("使用默认工作流：搜索+分析")
            return 'custom'

    def _build_custom_steps(self) -> List[Dict[str, Any]]:
        """根据任务构建自定义步骤"""
        task_desc = self.context.get('task_description', '').lower()

        # 基于任务描述构建步骤
        if '搜索' in task_desc or 'search' in task_desc:
            # 搜索工作流
            return [
                {'agent': 'search', 'name': '信息搜索'},
                {'agent': 'summary', 'name': 'Skills分析'}
            ]

        elif '问答' in task_desc or 'query' in task_desc:
            # RAG查询工作流
            return [
                {'agent': 'entity', 'name': '查询分析'},
                {'agent': 'search', 'name': '信息检索'},
                {'agent': 'summary', 'name': '答案生成'}
            ]

        else:
            # 默认：简单分析
            return [
                {'agent': 'summary', 'name': 'Skills分析'}
            ]

    def _prepare_coordinator_input(self) -> Dict[str, Any]:
        """准备协调器的输入数据"""
        # 从原始输入中提取
        coordinator_input = {}

        # 传递关键参数
        for key in ['query', 'content', 'file_path', 'max_results']:
            if key in self.context:
                coordinator_input[key] = self.context[key]

        # 如果没有明确内容，使用任务描述
        if 'content' not in coordinator_input and 'task_description' in self.context:
            coordinator_input['content'] = self.context['task_description']

        # 如果有查询意图，设置query
        if 'query' not in coordinator_input:
            task_desc = self.context.get('task_description', '')
            if any(word in task_desc for word in ['搜索', '查询', '问题']):
                coordinator_input['query'] = task_desc

        return coordinator_input

    def _aggregate_results(self) -> str:
        """聚合协调结果用于最终整合"""
        aggregated = []

        # 任务描述
        if 'task_description' in self.context:
            aggregated.append(f"任务: {self.context['task_description']}\n")

        # 执行的工作流
        if 'executed_workflow' in self.context:
            aggregated.append(f"执行工作流: {self.context['executed_workflow']}\n")

        # 协调结果
        if 'coordination_results' in self.context:
            results = self.context['coordination_results']
            aggregated.append("\n=== 执行结果 ===\n")

            for idx, result in enumerate(results, 1):
                step_name = result.get('step_name', f'步骤{idx}')
                success = result.get('success', False)
                aggregated.append(f"{idx}. {step_name}: {'成功' if success else '失败'}")

                # 提取关键信息
                if success and 'result' in result:
                    step_result = result['result']
                    if isinstance(step_result, dict):
                        # 提取部分关键数据
                        if 'total_results' in step_result:
                            aggregated.append(f"   检索结果: {step_result['total_results']}")
                        if 'total_entities' in step_result:
                            aggregated.append(f"   实体数: {step_result['total_entities']}")
                        if 'skills_executed' in step_result:
                            aggregated.append(f"   Skills: {step_result['skills_executed']}")

        return '\n'.join(aggregated)

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建自主工作流输出"""
        output = {
            'workflow': self.name(),
            'task_description': self.context.get('task_description', ''),
            'status': 'success' if all(r.success for r in steps_results if r.step_id != 'step_3_integrate') else 'partial'
        }

        # 任务分析结果
        output['task_analysis'] = {
            'entities': self.context.get('task_entities', [])[:5],
            'inferred_workflow': self.context.get('workflow_type', 'unknown')
        }

        # 协调执行结果
        if 'coordination_results' in self.context:
            output['coordination'] = {
                'workflow_executed': self.context.get('executed_workflow', ''),
                'completed_steps': self.context.get('completed_steps', 0),
                'results': self.context['coordination_results']
            }

        # 最终洞察（如果有整合步骤）
        if 'final_insights' in self.context:
            output['final_insights'] = self.context['final_insights']

        # 执行摘要
        output['execution_summary'] = {
            'total_steps': len(steps_results),
            'successful_steps': sum(1 for r in steps_results if r.success),
            'total_time': sum(r.execution_time for r in steps_results)
        }

        return output

    def execute_autonomous(
        self,
        task_description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        便捷方法：执行自主任务

        Args:
            task_description: 任务描述（AI会自动理解和执行）
            **kwargs: 额外参数

        Returns:
            执行结果字典
        """
        from .base_workflow import WorkflowInput

        input_data = {
            'task_description': task_description,
            'report_format': kwargs.get('report_format', 'summary')
        }

        # 合并其他参数
        input_data.update(kwargs)

        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data=input_data
        )

        result = self.execute(workflow_input)
        return result.final_output

    def _create_agent(self, agent_type: str):
        """创建Agent实例（支持coordinator）"""
        if agent_type == 'coordinator':
            from app.services.agents.coordinator_agent import CoordinatorAgent
            return CoordinatorAgent()
        else:
            return super()._create_agent(agent_type)
