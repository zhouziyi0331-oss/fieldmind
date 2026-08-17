"""
ResearchReportCrew v2 - 研究报告工作流（更新版）
文档摄入 → 分块 → 向量化 → Skills分析 → 知识图谱 → 综合 → 报告
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class ResearchReportCrewV2(WorkflowBase):
    """
    研究报告工作流 v2

    完整流程（基于6-Agent v2架构 + Skills集成）：
    1. Ingestion (IngestionAgent) - 文档摄入与验证
    2. Chunking (ChunkingAgent) - 智能分块
    3. Vectorization (VectorizationAgent) - 向量化与实体提取
    4. Skills分析 (skill_analyzer工具) - 学术框架分析
    5. Knowledge (KnowledgeAgent) - 知识图谱构建（整合Skills结果）
    6. Synthesis (SynthesisAgent) - 记忆综合与引用溯源
    7. Report (ReportAgent) - 综合报告生成
    """

    def name(self) -> str:
        return "研究报告工作流 v2"

    def description(self) -> str:
        return "完整的研究报告生成流程：文档→分块→向量化→Skills分析→知识图谱→综合→报告"

    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            # 步骤1: 文档摄入
            WorkflowStep(
                step_id="step_1_ingestion",
                step_name="文档摄入",
                agent_type="ingestion",  # v2 Agent
                input_mapping={
                    'project_id': 'project_id'
                },
                output_mapping={
                    'documents': 'documents',
                    'document_count': 'document_count'
                },
                required=True,
                metadata={'description': '加载项目文档'}
            ),

            # 步骤2: 智能分块
            WorkflowStep(
                step_id="step_2_chunking",
                step_name="智能分块",
                agent_type="chunking",  # v2 Agent
                input_mapping={
                    'documents': 'documents',
                    'project_id': 'project_id'
                },
                output_mapping={
                    'stored_chunk_ids': 'stored_chunk_ids',
                    'chunk_count': 'chunk_count'
                },
                required=True,
                metadata={'description': '将文档分割为语义块'}
            ),

            # 步骤3: 向量化分析
            WorkflowStep(
                step_id="step_3_vectorization",
                step_name="向量化分析",
                agent_type="vectorization",  # v2 Agent
                input_mapping={
                    'stored_chunk_ids': 'stored_chunk_ids',
                    'project_id': 'project_id'
                },
                output_mapping={
                    'vectorized_count': 'vectorized_count',
                    'embedding_model': 'embedding_model'
                },
                required=True,
                metadata={'description': '向量化并提取实体'}
            ),

            # 步骤4: Skills学术分析
            WorkflowStep(
                step_id="step_4_skills_analysis",
                step_name="Skills学术分析",
                agent_type="skills",  # 特殊类型，使用skill_analyzer
                input_mapping={
                    'project_id': 'project_id',
                    'enabled_skills': 'enabled_skills',
                    'report_format': 'report_format'
                },
                output_mapping={
                    'skills_results': 'skills_results',
                    'skills_executed': 'skills_executed'
                },
                required=True,
                metadata={'description': '使用8个学术Skills分析内容'}
            ),

            # 步骤5: 知识图谱构建
            WorkflowStep(
                step_id="step_5_knowledge",
                step_name="知识图谱构建",
                agent_type="knowledge",  # v2 Agent
                input_mapping={
                    'project_id': 'project_id',
                    'skills_results': 'skills_results'  # 传递Skills结果
                },
                output_mapping={
                    'entity_count': 'entity_count',
                    'relation_count': 'relation_count'
                },
                required=True,
                metadata={'description': '构建知识图谱并整合Skills维度'}
            ),

            # 步骤6: 综合合成
            WorkflowStep(
                step_id="step_6_synthesis",
                step_name="综合合成",
                agent_type="synthesis",  # v2 Agent
                input_mapping={
                    'project_id': 'project_id',
                    'query': 'query'
                },
                output_mapping={
                    'synthesis_result_id': 'synthesis_result_id',
                    'key_insights_count': 'key_insights_count'
                },
                required=True,
                metadata={'description': '综合记忆与引用溯源'}
            ),

            # 步骤7: 报告生成
            WorkflowStep(
                step_id="step_7_report",
                step_name="报告生成",
                agent_type="report",  # v2 Agent
                input_mapping={
                    'project_id': 'project_id',
                    'synthesis_result_id': 'synthesis_result_id',
                    'report_level': 'report_level'
                },
                output_mapping={
                    'report_type': 'report_type',
                    'total_words': 'total_words',
                    'layer_1_id': 'layer_1_id'
                },
                required=True,
                metadata={'description': '生成三层报告'}
            )
        ]

    def _prepare_step_input(self, step: WorkflowStep) -> Dict[str, Any]:
        """准备步骤输入（特殊处理db_session）"""
        input_data = super()._prepare_step_input(step)

        # 所有v2 Agent都需要db_session
        if 'db_session' not in input_data and hasattr(self, '_db_session'):
            input_data['db_session'] = self._db_session

        # 步骤4: Skills分析（特殊处理）
        if step.step_id == 'step_4_skills_analysis':
            # 设置默认值
            if 'enabled_skills' not in input_data or input_data['enabled_skills'] is None:
                # 默认启用驾驭工程核心Skills
                input_data['enabled_skills'] = [
                    'heritage_dadi',
                    'xiangtu_china',
                    'sacred_memory',
                    'business_feasibility',
                    'multi_village_sop',
                    'literature_market_research'
                ]

            if 'report_format' not in input_data:
                input_data['report_format'] = 'full'

        # 步骤6: 综合合成（设置默认query）
        if step.step_id == 'step_6_synthesis':
            if 'query' not in input_data:
                input_data['query'] = '生成项目综合研究报告'

        # 步骤7: 报告生成（设置默认level）
        if step.step_id == 'step_7_report':
            if 'report_level' not in input_data:
                input_data['report_level'] = 'dynamic'

        return input_data

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建最终输出"""
        output = {
            'workflow': self.name(),
            'workflow_version': 'v2',
            'project_id': self.context.get('project_id', ''),
            'status': 'success' if all(r.success for r in steps_results) else 'partial'
        }

        # 文档摄入结果
        if 'document_count' in self.context:
            output['document_count'] = self.context['document_count']

        # 分块结果
        if 'chunk_count' in self.context:
            output['chunk_count'] = self.context['chunk_count']

        # 向量化结果
        if 'vectorized_count' in self.context:
            output['vectorized_count'] = self.context['vectorized_count']
            output['embedding_model'] = self.context.get('embedding_model', 'N/A')

        # Skills分析结果
        if 'skills_executed' in self.context:
            output['skills_executed'] = self.context['skills_executed']
            output['skills_results'] = self.context.get('skills_results', {})

        # 知识图谱结果
        if 'entity_count' in self.context:
            output['entity_count'] = self.context['entity_count']
            output['relation_count'] = self.context.get('relation_count', 0)

        # 综合结果
        if 'synthesis_result_id' in self.context:
            output['synthesis_result_id'] = self.context['synthesis_result_id']
            output['key_insights_count'] = self.context.get('key_insights_count', 0)

        # 报告结果
        if 'report_type' in self.context:
            output['report_type'] = self.context['report_type']
            output['total_words'] = self.context.get('total_words', 0)
            output['layer_1_id'] = self.context.get('layer_1_id')

        # 执行摘要
        output['execution_summary'] = {
            'total_steps': len(steps_results),
            'successful_steps': sum(1 for r in steps_results if r.success),
            'failed_steps': sum(1 for r in steps_results if not r.success),
            'total_time': sum(r.execution_time for r in steps_results)
        }

        return output

    def execute_research_v2(
        self,
        project_id: int,
        db_session,
        enabled_skills: List[str] = None,
        report_level: str = 'dynamic',
        **kwargs
    ) -> Dict[str, Any]:
        """
        便捷方法：执行v2研究报告生成

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            enabled_skills: 启用的Skills列表
            report_level: 报告等级
            **kwargs: 其他配置

        Returns:
            研究报告字典
        """
        from .base_workflow import WorkflowInput

        # 保存db_session供所有步骤使用
        self._db_session = db_session

        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data={
                'project_id': project_id,
                'enabled_skills': enabled_skills,
                'report_format': kwargs.get('report_format', 'full'),
                'report_level': report_level,
                'query': kwargs.get('query', '生成项目综合研究报告'),
                'db_session': db_session
            },
            config=kwargs.get('config', {})
        )

        result = self.execute(workflow_input)
        return result.final_output
