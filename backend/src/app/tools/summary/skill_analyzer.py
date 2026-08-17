"""
Skill Analyzer Tool - Skills分析工具
从 SummaryAgent 提取的核心功能

职责：调用6个学术Skills进行分析、生成综合报告

Author: Extracted from SummaryAgent
Date: 2026-08-14
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import importlib

logger = logging.getLogger(__name__)

# 可用的Skills定义
AVAILABLE_SKILLS = {
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


def analyze_with_skills(
    content: str,
    enabled_skills: Optional[List[str]] = None,
    report_format: str = 'full',
    include_statistics: bool = True
) -> Dict[str, Any]:
    """
    使用Skills分析文本内容

    Args:
        content: 要分析的文本内容
        enabled_skills: 要执行的Skills列表（默认全部）
        report_format: 报告格式 'full'|'summary'|'insights' (默认'full')
        include_statistics: 是否包含统计信息（默认True）

    Returns:
        {
            'content_length': 5000,
            'analysis_timestamp': '2026-08-14T...',
            'skills_executed': 6,
            'skills_successful': 5,
            'statistics': {
                'total_matches': 42,
                'total_dimensions': 15,
                'avg_matches_per_skill': 8.4,
                'avg_confidence': 0.75
            },
            'insights': [
                {
                    'skill': '大地遗产方法论',
                    'dimension': '文化景观',
                    'match_count': 8,
                    'key_sentence': '...',
                    'similarity': 0.85
                },
                ...
            ],
            'skills_results': {
                'heritage_dadi': {
                    'name': '大地遗产方法论',
                    'success': True,
                    'total_matches': 12,
                    'avg_confidence': 0.78,
                    'dimensions': {...},
                    'execution_time': 1.2
                },
                ...
            }
        }
    """
    if not content or not content.strip():
        raise ValueError('分析内容不能为空')

    # 默认启用所有Skills
    if enabled_skills is None:
        enabled_skills = list(AVAILABLE_SKILLS.keys())

    logger.info(f"开始执行Skills分析，启用 {len(enabled_skills)} 个Skills")

    # 执行Skills分析
    skills_results = _execute_skills(content, enabled_skills)

    # 生成报告
    report = _generate_report(
        content=content,
        skills_results=skills_results,
        report_format=report_format,
        include_statistics=include_statistics
    )

    return report


# ==================== 私有辅助函数 ====================

def _execute_skills(content: str, enabled_skills: List[str]) -> Dict[str, Any]:
    """执行Skills分析"""
    results = {}

    for skill_id in enabled_skills:
        if skill_id not in AVAILABLE_SKILLS:
            logger.warning(f"Unknown skill: {skill_id}, skipping")
            continue

        skill_def = AVAILABLE_SKILLS[skill_id]

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
    insights = _extract_insights(skills_results)

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


def _extract_insights(skills_results: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                'similarity': top_match['similarity'],
                'keywords': top_match['keywords']
            })

    # 按匹配数排序
    insights.sort(key=lambda x: x['match_count'], reverse=True)

    return insights
