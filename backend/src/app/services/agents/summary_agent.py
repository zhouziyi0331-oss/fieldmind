"""
SummaryAgent - 总结专员Agent

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.summary.skill_analyzer

负责调用Skills分析结果、生成综合报告、智能摘要
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import importlib

from .base_agent import AgentBase, AgentRole, AgentTask, AgentResult
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


@deprecated(
    reason="旧Agent架构已被6-Agent v2替代",
    replacement="app.tools.summary.skill_analyzer",
    version="2.0"
)
class SummaryAgent(AgentBase):
    """总结专员 - 负责生成综合分析报告"""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.available_skills = self._load_available_skills()

    @property
    def role(self) -> AgentRole:
        return AgentRole.SUMMARY

    @property
    def name(self) -> str:
        return "总结专员"

    @property
    def description(self) -> str:
        return "负责调用Skills分析、生成综合报告、智能摘要和洞察提取"

    @property
    def capabilities(self) -> List[str]:
        return [
            "调用6个学术Skills进行分析",
            "生成综合分析报告",
            "提取关键洞察和发现",
            "多维度结果聚合",
            "报告结构化输出"
        ]

    def _initialize_tools(self):
        """初始化总结工具"""
        self.tools = {
            'skills_executor': 'Execute academic Skills analysis',
            'report_generator': 'Generate structured reports',
            'insight_extractor': 'Extract key insights'
        }

    def _load_available_skills(self) -> Dict[str, Dict[str, str]]:
        """加载可用的Skills定义"""
        return {
            'heritage_dadi': {
                'name': '大地遗产方法论',
                'module': 'heritage_dadi',
                'class': 'HeritageDADISkill'
            },
            'business_feasibility': {
                'name': '商业可行性验证',
                'module': 'business_feasibility',
                'class': 'BusinessFeasibilitySkill'
            },
            'multi_village_sop': {
                'name': '多村联动SOP',
                'module': 'multi_village_sop',
                'class': 'MultiVillageSOPSkill'
            },
            'literature_market_research': {
                'name': '文献市场研究',
                'module': 'literature_market_research',
                'class': 'LiteratureMarketResearchSkill'
            },
            'xiangtu_china': {
                'name': '乡土中国理论分析',
                'module': 'xiangtu_china',
                'class': 'XiangtuChinaSkill'
            },
            'sacred_memory': {
                'name': '神圣记忆理论分析',
                'module': 'sacred_memory',
                'class': 'SacredMemorySkill'
            }
        }

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行总结任务

        task.input_data:
          - content: 要分析的文本内容（必需）
          - enabled_skills: 要执行的Skills列表（默认全部）
          - report_format: 报告格式 'full'|'summary'|'insights' (默认'full')
          - include_statistics: 是否包含统计信息（默认True）
        """
        content = task.input_data.get('content', '')
        if not content or not content.strip():
            raise ValueError('分析内容不能为空')

        # 获取参数
        enabled_skills = task.input_data.get('enabled_skills', list(self.available_skills.keys()))
        report_format = task.input_data.get('report_format', 'full')
        include_statistics = task.input_data.get('include_statistics', True)

        logger.info(f"Executing summary task with {len(enabled_skills)} skills")

        # 执行Skills分析
        skills_results = self._execute_skills(content, enabled_skills)

        # 生成报告
        report = self._generate_report(
            content=content,
            skills_results=skills_results,
            report_format=report_format,
            include_statistics=include_statistics
        )

        return report

    def _execute_skills(self, content: str, enabled_skills: List[str]) -> Dict[str, Any]:
        """执行Skills分析"""
        results = {}

        for skill_id in enabled_skills:
            if skill_id not in self.available_skills:
                logger.warning(f"Unknown skill: {skill_id}, skipping")
                continue

            skill_def = self.available_skills[skill_id]

            try:
                # 动态加载Skill
                skill_module = importlib.import_module(
                    f"app.services.skills.{skill_def['module']}"
                )
                skill_class = getattr(skill_module, skill_def['class'])
                skill_instance = skill_class()

                # 执行分析
                start_time = datetime.now()
                skill_result = skill_instance.analyze(content)
                elapsed = (datetime.now() - start_time).total_seconds()

                # 提取关键信息
                results[skill_id] = {
                    'name': skill_def['name'],
                    'success': skill_result.success,
                    'total_matches': skill_result.total_matches,
                    'avg_confidence': skill_result.avg_confidence,
                    'dimensions': {
                        dim_id: {
                            'dimension_name': matches[0].dimension_name if matches else '',
                            'match_count': len(matches),
                            'top_matches': [
                                {
                                    'sentence': m.sentence,
                                    'similarity': m.similarity,
                                    'keywords': m.keywords_found
                                }
                                for m in matches[:3]  # 只保留前3条
                            ]
                        }
                        for dim_id, matches in skill_result.dimensions.items()
                        if matches  # 只包含有匹配的维度
                    },
                    'execution_time': round(elapsed, 2)
                }

                logger.info(
                    f"Skill {skill_id} completed: "
                    f"{skill_result.total_matches} matches, "
                    f"confidence={skill_result.avg_confidence:.2f}"
                )

            except Exception as e:
                logger.error(f"Skill {skill_id} failed: {str(e)}")
                results[skill_id] = {
                    'name': skill_def['name'],
                    'success': False,
                    'error': str(e)
                }

        return results

    def _generate_report(
        self,
        content: str,
        skills_results: Dict[str, Any],
        report_format: str,
        include_statistics: bool
    ) -> Dict[str, Any]:
        """生成分析报告"""

        # 统计信息
        total_skills = len(skills_results)
        successful_skills = sum(1 for r in skills_results.values() if r.get('success', False))
        total_matches = sum(r.get('total_matches', 0) for r in skills_results.values())
        total_dimensions = sum(
            len(r.get('dimensions', {}))
            for r in skills_results.values()
            if r.get('success', False)
        )

        # 提取关键洞察
        insights = self._extract_insights(skills_results)

        # 构建报告
        report = {
            'content_length': len(content),
            'analysis_timestamp': datetime.now().isoformat(),
            'skills_executed': total_skills,
            'skills_successful': successful_skills,
        }

        if include_statistics:
            report['statistics'] = {
                'total_matches': total_matches,
                'total_dimensions': total_dimensions,
                'avg_matches_per_skill': round(total_matches / successful_skills, 1) if successful_skills > 0 else 0,
                'avg_confidence': round(
                    sum(r.get('avg_confidence', 0) for r in skills_results.values() if r.get('success', False)) / successful_skills,
                    3
                ) if successful_skills > 0 else 0
            }

        if report_format == 'insights':
            # 只返回关键洞察
            report['insights'] = insights

        elif report_format == 'summary':
            # 返回摘要信息
            report['insights'] = insights
            report['skills_summary'] = {
                skill_id: {
                    'name': result['name'],
                    'success': result.get('success', False),
                    'matches': result.get('total_matches', 0),
                    'confidence': result.get('avg_confidence', 0)
                }
                for skill_id, result in skills_results.items()
            }

        else:  # full
            # 返回完整报告
            report['insights'] = insights
            report['skills_results'] = skills_results

        return report

    def _extract_insights(self, skills_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取关键洞察"""
        insights = []

        for skill_id, result in skills_results.items():
            if not result.get('success', False):
                continue

            dimensions = result.get('dimensions', {})
            if not dimensions:
                continue

            # 找出最强的维度
            top_dimension = max(
                dimensions.items(),
                key=lambda x: x[1]['match_count']
            )

            dim_id, dim_data = top_dimension

            if dim_data['match_count'] > 0:
                top_match = dim_data['top_matches'][0]

                insights.append({
                    'skill': result['name'],
                    'skill_id': skill_id,
                    'dimension': dim_data['dimension_name'],
                    'dimension_id': dim_id,
                    'match_count': dim_data['match_count'],
                    'key_sentence': top_match['sentence'],
                    'confidence': top_match['similarity'],
                    'keywords': top_match['keywords']
                })

        # 按匹配数量排序
        insights.sort(key=lambda x: x['match_count'], reverse=True)

        return insights

    def analyze_sync(
        self,
        content: str,
        enabled_skills: Optional[List[str]] = None,
        report_format: str = 'full'
    ) -> Dict[str, Any]:
        """同步分析方法（便于直接调用）"""
        task = AgentTask(
            task_id=f"summary_{datetime.now().timestamp()}",
            task_type="summary",
            input_data={
                'content': content,
                'enabled_skills': enabled_skills or list(self.available_skills.keys()),
                'report_format': report_format
            },
            priority=5
        )

        result = self.execute_task(task)
        return result.output_data
