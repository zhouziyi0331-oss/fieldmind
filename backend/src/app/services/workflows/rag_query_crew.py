"""
RAGQueryCrew - RAG查询工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构（entity/search/summary）
建议使用6-Agent v2架构结合SynthesisAgent的记忆检索功能

实体提取 → 检索 → 答案生成
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class RAGQueryCrew(WorkflowBase):
    """
    RAG查询工作流

    基于检索增强生成(RAG)的问答流程：
    1. 实体提取 (EntityAgent) - 提取查询中的关键实体
    2. 检索 (SearchAgent) - 基于实体检索相关信息
    3. 答案生成 (SummaryAgent) - Skills分析生成结构化答案
    """

    def name(self) -> str:
        return "RAG查询工作流"

    def description(self) -> str:
        return "基于检索增强生成的问答：实体提取 → 检索 → 答案生成"

    def _define_steps(self) -> List[WorkflowStep]:
        """定义工作流步骤"""
        return [
            # 步骤1: 查询实体提取
            WorkflowStep(
                step_id="step_1_entity",
                step_name="查询实体提取",
                agent_type="entity",
                input_mapping={
                    'content': 'query'  # 用户查询作为内容
                },
                output_mapping={
                    'entities': 'query_entities',
                    'entity_types': 'entity_types',
                    'total_entities': 'total_entities'
                },
                required=True,
                metadata={'description': '从用户查询中提取关键实体'}
            ),

            # 步骤2: 检索相关信息
            WorkflowStep(
                step_id="step_2_search",
                step_name="信息检索",
                agent_type="search",
                input_mapping={
                    'query': 'search_query',       # 从实体构建的查询
                    'max_results': 'max_results',
                    'extract_content': 'extract_content'
                },
                output_mapping={
                    'results': 'retrieved_results',
                    'total_results': 'total_retrieved'
                },
                required=True,
                metadata={'description': '检索与查询实体相关的信息'}
            ),

            # 步骤3: 生成答案
            WorkflowStep(
                step_id="step_3_answer",
                step_name="答案生成",
                agent_type="summary",
                input_mapping={
                    'content': 'context_content',  # 检索到的内容
                    'report_format': 'report_format',
                    'enabled_skills': 'enabled_skills'
                },
                output_mapping={
                    'insights': 'answer_insights',
                    'skills_executed': 'skills_executed',
                    'statistics': 'answer_statistics'
                },
                required=True,
                metadata={'description': 'Skills分析生成结构化答案'}
            )
        ]

    def _prepare_step_input(self, step: WorkflowStep) -> Dict[str, Any]:
        """准备步骤输入（特殊处理查询构建和内容聚合）"""
        input_data = super()._prepare_step_input(step)

        # 步骤2: 从实体构建搜索查询
        if step.step_id == 'step_2_search':
            if 'search_query' not in self.context:
                # 从提取的实体构建搜索查询
                self.context['search_query'] = self._build_search_query()

            input_data['query'] = self.context['search_query']
            input_data['extract_content'] = True  # RAG需要详细内容

            # 默认检索5个结果
            if 'max_results' not in input_data:
                input_data['max_results'] = 5

        # 步骤3: 聚合检索内容作为上下文
        if step.step_id == 'step_3_answer':
            if 'context_content' not in self.context:
                self.context['context_content'] = self._aggregate_context()

            input_data['content'] = self.context['context_content']

        return input_data

    def _build_search_query(self) -> str:
        """从提取的实体构建搜索查询"""
        original_query = self.context.get('query', '')
        entities = self.context.get('query_entities', [])

        if not entities:
            # 没有实体，直接使用原查询
            return original_query

        # 提取实体名称
        entity_names = []
        for entity in entities[:5]:  # 最多使用5个实体
            if isinstance(entity, dict):
                name = entity.get('entity', '')
                if name:
                    entity_names.append(name)

        if entity_names:
            # 组合实体为查询
            query = ' '.join(entity_names)
            logger.info(f"从实体构建查询: {query}")
            return query
        else:
            return original_query

    def _aggregate_context(self) -> str:
        """聚合检索结果为上下文"""
        aggregated = []

        # 添加原始查询
        if 'query' in self.context:
            aggregated.append(f"问题: {self.context['query']}\n")

        # 添加提取的实体
        if 'query_entities' in self.context:
            entities = self.context['query_entities']
            if entities:
                aggregated.append("\n关键实体:")
                for entity in entities[:5]:
                    if isinstance(entity, dict):
                        aggregated.append(f"  - {entity.get('entity', '')}")
                aggregated.append("")

        # 添加检索到的内容
        if 'retrieved_results' in self.context:
            results = self.context['retrieved_results']
            aggregated.append("\n=== 相关信息 ===\n")

            for idx, result in enumerate(results, 1):
                aggregated.append(f"\n{idx}. {result.get('title', '')}")
                aggregated.append(f"来源: {result.get('url', '')}")

                # 如果有详细内容，使用详细内容
                if 'content' in result and result['content']:
                    content = result['content'][:1500]  # 限制长度
                    aggregated.append(f"内容: {content}")
                else:
                    # 否则使用摘要
                    aggregated.append(f"摘要: {result.get('snippet', '')}")

                aggregated.append("")

        return '\n'.join(aggregated)

    def _build_final_output(self, steps_results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """构建RAG答案输出"""
        output = {
            'workflow': self.name(),
            'query': self.context.get('query', ''),
            'status': 'success' if all(r.success for r in steps_results) else 'partial'
        }

        # 查询分析
        output['query_analysis'] = {
            'entities': self.context.get('query_entities', [])[:5],
            'entity_count': self.context.get('total_entities', 0),
            'search_query': self.context.get('search_query', '')
        }

        # 检索结果
        if 'retrieved_results' in self.context:
            results = self.context['retrieved_results']
            output['retrieval'] = {
                'total_results': len(results),
                'sources': [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'has_content': bool(r.get('content', ''))
                    }
                    for r in results
                ]
            }

        # 生成的答案（从Skills分析中提取）
        if 'answer_insights' in self.context:
            insights = self.context['answer_insights']
            output['answer'] = {
                'insights': insights,
                'insight_count': len(insights) if isinstance(insights, list) else 0
            }

        if 'answer_statistics' in self.context:
            output['answer']['statistics'] = self.context['answer_statistics']

        # 执行摘要
        output['execution_summary'] = {
            'total_steps': len(steps_results),
            'successful_steps': sum(1 for r in steps_results if r.success),
            'total_time': sum(r.execution_time for r in steps_results)
        }

        return output

    def query(
        self,
        question: str,
        max_results: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        便捷方法：执行RAG查询

        Args:
            question: 用户问题
            max_results: 检索结果数量
            **kwargs: 其他配置

        Returns:
            RAG答案字典
        """
        from .base_workflow import WorkflowInput

        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data={
                'query': question,
                'max_results': max_results,
                'report_format': kwargs.get('report_format', 'insights'),
                'enabled_skills': kwargs.get('enabled_skills', None)
            }
        )

        result = self.execute(workflow_input)
        return result.final_output
