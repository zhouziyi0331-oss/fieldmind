"""
DocumentProcessingCrew - 文档处理工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构（transcript/entity/relation/summary）
建议使用6-Agent v2架构的完整流程：
- IngestionAgent → ChunkingAgent → VectorizationAgent → KnowledgeAgent → SynthesisAgent → ReportAgent

转录 → 实体提取 → 关系抽取 → 报告生成
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class DocumentProcessingCrew(WorkflowBase):
    """
    文档处理工作流

    处理音视频文档的完整流程：
    1. 转录 (TranscriptAgent) - 音视频转文本
    2. 实体提取 (EntityAgent) - 识别命名实体
    3. 关系抽取 (RelationAgent) - 构建知识图谱
    4. 报告生成 (SummaryAgent) - Skills分析和报告
    """

    def name(self) -> str:
        return "文档处理工作流"

    def description(self) -> str:
        return "音视频文档的完整处理流程：转录 → 实体提取 → 关系抽取 → Skills分析报告"

    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            # 步骤1: 音视频转录
            WorkflowStep(
                step_id="step_1_transcript",
                step_name="音视频转录",
                agent_type="transcript",
                input_mapping={
                    'file_path': 'file_path',    # 从输入获取
                    'language': 'language',       # 可选
                    'model_size': 'model_size'    # 可选
                },
                output_mapping={
                    'text': 'transcript_text',
                    'segments': 'transcript_segments',
                    'language': 'detected_language',
                    'duration': 'audio_duration'
                },
                required=True,
                metadata={'description': '将音视频文件转换为文本'}
            ),

            # 步骤2: 实体提取
            WorkflowStep(
                step_id="step_2_entity",
                step_name="实体提取",
                agent_type="entity",
                input_mapping={
                    'content': 'transcript_text'  # 使用转录结果
                },
                output_mapping={
                    'entities': 'extracted_entities',
                    'entity_types': 'entity_types',
                    'total_entities': 'total_entities'
                },
                required=True,
                metadata={'description': '从文本中提取命名实体'}
            ),

            # 步骤3: 关系抽取
            WorkflowStep(
                step_id="step_3_relation",
                step_name="关系抽取",
                agent_type="relation",
                input_mapping={
                    'content': 'transcript_text',        # 使用转录文本
                    'entities': 'extracted_entities'     # 使用提取的实体
                },
                output_mapping={
                    'triples': 'knowledge_triples',
                    'relation_types': 'relation_types',
                    'total_triples': 'total_triples'
                },
                required=True,
                metadata={'description': '构建知识图谱三元组'}
            ),

            # 步骤4: Skills分析报告
            WorkflowStep(
                step_id="step_4_summary",
                step_name="Skills分析报告",
                agent_type="summary",
                input_mapping={
                    'content': 'transcript_text',
                    'report_format': 'report_format',    # 从输入或默认
                    'enabled_skills': 'enabled_skills'   # 从输入或默认全部
                },
                output_mapping={
                    'skills_executed': 'skills_executed',
                    'insights': 'key_insights',
                    'statistics': 'analysis_statistics'
                },
                required=True,
                metadata={'description': '执行6个学术Skills分析'}
            )
        ]

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建结构化的最终输出"""
        output = {
            'workflow': self.name(),
            'status': 'success' if all(r.success for r in steps_results) else 'partial',
            'processing_stages': {}
        }

        # 整理各阶段结果
        for result in steps_results:
            stage_key = result.step_id.replace('step_', 'stage_')

            output['processing_stages'][stage_key] = {
                'name': result.step_name,
                'success': result.success,
                'execution_time': result.execution_time,
                'data': result.output_data if result.success else None,
                'errors': result.errors if not result.success else []
            }

        # 提取关键摘要信息
        output['summary'] = {
            'total_steps': len(steps_results),
            'successful_steps': sum(1 for r in steps_results if r.success),
            'total_execution_time': sum(r.execution_time for r in steps_results)
        }

        # 从上下文提取关键数据
        if 'transcript_text' in self.context:
            output['transcript_length'] = len(self.context['transcript_text'])

        if 'total_entities' in self.context:
            output['total_entities'] = self.context['total_entities']

        if 'total_triples' in self.context:
            output['total_triples'] = self.context['total_triples']

        if 'key_insights' in self.context:
            insights = self.context['key_insights']
            output['top_insights'] = insights[:3] if isinstance(insights, list) else []

        return output

    def execute_from_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        便捷方法：从文件路径直接执行工作流

        Args:
            file_path: 音视频文件路径
            **kwargs: 其他配置参数

        Returns:
            最终输出字典
        """
        from .base_workflow import WorkflowInput

        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data={
                'file_path': file_path,
                'language': kwargs.get('language', 'auto'),
                'model_size': kwargs.get('model_size', 'base'),
                'report_format': kwargs.get('report_format', 'summary'),
                'enabled_skills': kwargs.get('enabled_skills', None)
            },
            config=kwargs.get('config', {})
        )

        result = self.execute(workflow_input)
        return result.final_output
