"""
ResearchReportCrew - 研究报告工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构，请使用 ResearchReportCrewV2

搜索 → 内容提取 → Skills分析 → 报告生成
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class ResearchReportCrew(WorkflowBase):
    """
    研究报告工作流

    基于关键词的研究报告生成流程：
    1. 搜索 (SearchAgent) - 互联网信息检索
    2. 内容提取 (SearchAgent) - 提取网页详细内容
    3. Skills分析 (SummaryAgent) - 学术框架分析和报告生成
    """

    def name(self) -> str:
        return "研究报告工作流"

    def description(self) -> str:
        return "基于关键词的研究报告生成：搜索 → 内容提取 → Skills分析 → 报告"

    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            # 步骤1: 信息搜索
            WorkflowStep(
                step_id="step_1_search",
                step_name="信息搜索",
                agent_type="search",
                input_mapping={
                    'query': 'query',              # 搜索关键词
                    'max_results': 'max_results',  # 结果数量
                    'region': 'region'             # 搜索地区
                },
                output_mapping={
                    'results': 'search_results',
                    'total_results': 'total_search_results',
                    'query': 'search_query'
                },
                required=True,
                metadata={'description': '执行互联网搜索获取相关信息'}
            ),

            # 步骤2: 内容提取（可选，取决于配置）
            WorkflowStep(
                step_id="step_2_extract",
                step_name="内容提取",
                agent_type="search",
                input_mapping={
                    'query': 'query',
                    'max_results': 'extract_count',  # 提取几个网页
                    'extract_content': 'extract_content'  # 固定为True
                },
                output_mapping={
                    'results': 'extracted_contents',
                    'total_results': 'total_extracted'
                },
                required=False,  # 可选步骤
                metadata={'description': '提取搜索结果的详细网页内容'}
            ),

            # 步骤3: Skills分析
            WorkflowStep(
                step_id="step_3_analysis",
                step_name="Skills分析",
                agent_type="summary",
                input_mapping={
                    'content': 'aggregated_content',  # 聚合后的内容
                    'report_format': 'report_format',
                    'enabled_skills': 'enabled_skills'
                },
                output_mapping={
                    'skills_executed': 'skills_executed',
                    'insights': 'key_insights',
                    'statistics': 'analysis_statistics',
                    'skills_results': 'detailed_skills_results'
                },
                required=True,
                metadata={'description': '使用6个学术Skills分析内容'}
            )
        ]

    def _prepare_step_input(self, step: WorkflowStep) -> Dict[str, Any]:
        """准备步骤输入（特殊处理内容聚合）"""
        input_data = super()._prepare_step_input(step)

        # 步骤2: 固定extract_content=True
        if step.step_id == 'step_2_extract':
            input_data['extract_content'] = True
            # 默认提取3个网页
            if 'extract_count' not in input_data:
                input_data['max_results'] = 3

        # 步骤3: 聚合搜索结果为分析内容
        if step.step_id == 'step_3_analysis':
            if 'aggregated_content' not in self.context:
                # 聚合搜索结果
                self.context['aggregated_content'] = self._aggregate_search_results()

            input_data['content'] = self.context['aggregated_content']

        return input_data

    def _aggregate_search_results(self) -> str:
        """聚合搜索结果为分析内容"""
        aggregated = []

        # 添加搜索查询
        if 'search_query' in self.context:
            aggregated.append(f"研究主题: {self.context['search_query']}\n")

        # 添加搜索结果摘要
        if 'search_results' in self.context:
            results = self.context['search_results']
            aggregated.append("\n=== 搜索结果 ===\n")
            for idx, result in enumerate(results, 1):
                aggregated.append(f"\n{idx}. {result.get('title', '')}")
                aggregated.append(f"来源: {result.get('url', '')}")
                aggregated.append(f"摘要: {result.get('snippet', '')}\n")

        # 添加提取的详细内容
        if 'extracted_contents' in self.context:
            contents = self.context['extracted_contents']
            aggregated.append("\n=== 详细内容 ===\n")
            for idx, item in enumerate(contents, 1):
                if 'content' in item and item['content']:
                    aggregated.append(f"\n--- 来源 {idx}: {item.get('title', '')} ---")
                    # 限制每个内容长度
                    content = item['content'][:2000]
                    aggregated.append(content)
                    aggregated.append("\n")

        return '\n'.join(aggregated)

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建研究报告输出"""
        output = {
            'workflow': self.name(),
            'query': self.context.get('search_query', ''),
            'status': 'success' if all(r.success for r in steps_results if r.step_id != 'step_2_extract') else 'partial'
        }

        # 搜索结果摘要
        if 'search_results' in self.context:
            results = self.context['search_results']
            output['search_summary'] = {
                'total_results': len(results),
                'sources': [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('url', '')
                    }
                    for r in results[:5]  # 前5个
                ]
            }

        # Skills分析结果
        if 'key_insights' in self.context:
            output['key_insights'] = self.context['key_insights']

        if 'analysis_statistics' in self.context:
            output['analysis_statistics'] = self.context['analysis_statistics']

        if 'skills_executed' in self.context:
            output['skills_executed'] = self.context['skills_executed']

        # 执行摘要
        output['execution_summary'] = {
            'total_steps': len(steps_results),
            'successful_steps': sum(1 for r in steps_results if r.success),
            'total_time': sum(r.execution_time for r in steps_results),
            'content_length': len(self.context.get('aggregated_content', ''))
        }

        return output

    def execute_research(
        self,
        query: str,
        max_results: int = 10,
        extract_content: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        便捷方法：执行研究报告生成

        Args:
            query: 研究查询关键词
            max_results: 搜索结果数量
            extract_content: 是否提取网页内容
            **kwargs: 其他配置

        Returns:
            研究报告字典
        """
        from .base_workflow import WorkflowInput

        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data={
                'query': query,
                'max_results': max_results,
                'extract_count': kwargs.get('extract_count', 3),
                'region': kwargs.get('region', 'cn-zh'),
                'report_format': kwargs.get('report_format', 'full'),
                'enabled_skills': kwargs.get('enabled_skills', None)
            },
            config={'extract_content': extract_content}
        )

        result = self.execute(workflow_input)
        return result.final_output
