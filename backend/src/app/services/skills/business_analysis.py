"""
business_analysis Skill
商业分析技能：运行15个分析服务，生成综合商业洞察

作用：
1. 串联15个分析服务的执行
2. 收集所有分析结果
3. 进行跨维度综合分析
4. 生成商业级别的洞察和建议

使用场景：
- SynthesisAgent调用此Skill获取完整的数据分析基础
- ReportAgent可直接使用缓存的分析结果构建三层报告
"""
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.analysis import (
    SentimentAnalysisService,
    ThemeAnalysisService,
    EntityAnalysisService,
    RelationAnalysisService,
    TimelineAnalysisService,
    CategoryAnalysisService,
    SummaryAnalysisService,
    KeywordAnalysisService,
    AnomalyAnalysisService,
    TrendAnalysisService,
    ComparisonAnalysisService,
    ImpactAnalysisService,
    RiskAnalysisService,
    OpportunityAnalysisService,
    RecommendationAnalysisService,
)


class BusinessAnalysisSkill:
    """商业分析技能"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化15个分析服务"""
        self.services = {
            'sentiment': SentimentAnalysisService(),
            'theme': ThemeAnalysisService(),
            'entity': EntityAnalysisService(),
            'relation': RelationAnalysisService(),
            'timeline': TimelineAnalysisService(),
            'category': CategoryAnalysisService(),
            'summary': SummaryAnalysisService(),
            'keyword': KeywordAnalysisService(),
            'anomaly': AnomalyAnalysisService(),
            'trend': TrendAnalysisService(),
            'comparison': ComparisonAnalysisService(),
            'impact': ImpactAnalysisService(),
            'risk': RiskAnalysisService(),
            'opportunity': OpportunityAnalysisService(),
            'recommendation': RecommendationAnalysisService(),
        }

    async def execute(
        self,
        project_id: str,
        db_session: Session,
        selected_analyses: List[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        执行商业分析

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            selected_analyses: 要运行的分析类型列表，None表示运行全部
            force_refresh: 是否强制刷新缓存

        Returns:
            综合分析结果字典
        """
        # 确定要运行的分析
        if selected_analyses is None:
            selected_analyses = list(self.services.keys())
        else:
            # 验证请求的分析类型是否存在
            selected_analyses = [a for a in selected_analyses if a in self.services]

        # 并发运行所有分析服务（每个服务内部会检查缓存）
        analysis_results = {}
        errors = {}

        for analysis_type in selected_analyses:
            service = self.services[analysis_type]
            try:
                result = await service.get_or_compute(
                    project_id=project_id,
                    db_session=db_session,
                    force_refresh=force_refresh
                )
                analysis_results[analysis_type] = result
            except Exception as e:
                errors[analysis_type] = str(e)
                # 即使某个分析失败，也继续执行其他分析
                print(f"Warning: {analysis_type} analysis failed: {e}")

        # 生成综合洞察
        synthesis = self._synthesize_insights(analysis_results)

        # 构建返回结果
        return {
            'project_id': project_id,
            'analyses_run': len(analysis_results),
            'analyses_requested': len(selected_analyses),
            'analysis_results': analysis_results,
            'errors': errors if errors else None,
            'synthesis': synthesis,
            'execution_metadata': {
                'force_refresh': force_refresh,
                'cache_usage': self._calculate_cache_usage(analysis_results)
            }
        }

    def _synthesize_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合所有分析结果，生成跨维度洞察

        这是商业分析的核心价值：不是简单罗列15个分析结果，
        而是找出它们之间的关联、矛盾、互补关系
        """
        synthesis = {
            'key_findings': [],
            'cross_dimensional_insights': [],
            'attention_points': [],
            'confidence_assessment': {}
        }

        # 1. 识别关键发现（从各个分析中提取最重要的点）
        if 'summary' in results:
            summary = results['summary']
            synthesis['key_findings'].append({
                'aspect': 'project_scale',
                'finding': f"项目包含{summary.get('documents', {}).get('total', 0)}个文档，"
                          f"提取了{summary.get('entities', {}).get('total', 0)}个实体和"
                          f"{summary.get('knowledge', {}).get('nodes', 0)}个知识节点"
            })

        if 'risk' in results and results['risk'].get('total_risks', 0) > 0:
            risk = results['risk']
            high_risks = risk.get('risk_distribution', {}).get('high', 0)
            if high_risks > 0:
                synthesis['attention_points'].append({
                    'urgency': 'high',
                    'point': f"发现{high_risks}个高风险项，需要立即关注"
                })

        if 'opportunity' in results and results['opportunity'].get('total_opportunities', 0) > 0:
            opp = results['opportunity']
            high_priority = opp.get('priority_distribution', {}).get('high', 0)
            if high_priority > 0:
                synthesis['key_findings'].append({
                    'aspect': 'growth_potential',
                    'finding': f"识别出{high_priority}个高价值机会点"
                })

        # 2. 跨维度洞察（发现不同分析之间的关联）

        # 洞察：情感 vs 风险
        if 'sentiment' in results and 'risk' in results:
            sentiment = results['sentiment'].get('overall_sentiment')
            risk_level = results['risk'].get('overall_risk_level')
            if sentiment == 'negative' and risk_level == 'high':
                synthesis['cross_dimensional_insights'].append({
                    'pattern': 'sentiment_risk_alignment',
                    'description': '负面情感与高风险评估相互印证，建议谨慎推进',
                    'sources': ['sentiment', 'risk']
                })
            elif sentiment == 'positive' and risk_level == 'low':
                synthesis['cross_dimensional_insights'].append({
                    'pattern': 'positive_outlook',
                    'description': '正面情感与低风险状态一致，项目健康度良好',
                    'sources': ['sentiment', 'risk']
                })

        # 洞察：趋势 vs 机会
        if 'trend' in results and 'opportunity' in results:
            trend = results['trend']
            if trend.get('overall_direction') == 'positive':
                synthesis['cross_dimensional_insights'].append({
                    'pattern': 'growth_momentum',
                    'description': '数据呈增长趋势，当前是扩展投入的好时机',
                    'sources': ['trend', 'opportunity']
                })

        # 洞察：异常 vs 风险
        if 'anomaly' in results and 'risk' in results:
            anomaly_count = results['anomaly'].get('total_anomalies', 0)
            risk_count = results['risk'].get('total_risks', 0)
            if anomaly_count > 3 or risk_count > 3:
                synthesis['attention_points'].append({
                    'urgency': 'medium',
                    'point': f"数据质量存在{anomaly_count}个异常和{risk_count}个风险，影响分析准确性"
                })

        # 洞察：影响力 vs 关键词
        if 'impact' in results and 'keyword' in results:
            high_impact_entities = results['impact'].get('high_impact_entities', [])
            top_keywords = results['keyword'].get('top_keywords', [])
            if high_impact_entities and top_keywords:
                synthesis['cross_dimensional_insights'].append({
                    'pattern': 'core_focus_areas',
                    'description': f"核心影响力集中在{len(high_impact_entities)}个关键实体，"
                                 f"主要围绕{len(top_keywords[:5])}个核心概念",
                    'sources': ['impact', 'keyword']
                })

        # 3. 置信度评估（评估整体分析结果的可靠性）
        confidence_scores = []
        for analysis_type, result in results.items():
            if isinstance(result, dict) and 'confidence_score' in result:
                confidence_scores.append(result['confidence_score'])

        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            synthesis['confidence_assessment'] = {
                'average_confidence': round(avg_confidence, 2),
                'high_confidence_count': sum(1 for c in confidence_scores if c >= 0.85),
                'low_confidence_count': sum(1 for c in confidence_scores if c < 0.70),
                'overall_reliability': 'high' if avg_confidence >= 0.85 else 'medium' if avg_confidence >= 0.70 else 'low'
            }

        # 4. 如果有recommendation分析，提取立即行动项
        if 'recommendation' in results:
            rec = results['recommendation']
            immediate_actions = rec.get('immediate_actions', [])
            if immediate_actions:
                synthesis['attention_points'].extend([
                    {
                        'urgency': 'high',
                        'point': f"建议行动：{action.get('title')}"
                    }
                    for action in immediate_actions[:3]
                ])

        return synthesis

    def _calculate_cache_usage(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """计算缓存使用情况（用于性能监控）"""
        # 注意：实际的缓存命中信息需要在service层记录
        # 这里只是返回分析数量，实际实现中可以扩展
        return {
            'total_analyses': len(results),
            'note': 'Actual cache hit rate tracked in BaseAnalysisService'
        }

    async def get_single_analysis(
        self,
        project_id: str,
        db_session: Session,
        analysis_type: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取单个分析结果（便捷方法）

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            analysis_type: 分析类型（如'sentiment', 'risk'等）
            force_refresh: 是否强制刷新

        Returns:
            单个分析结果
        """
        if analysis_type not in self.services:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

        service = self.services[analysis_type]
        return await service.get_or_compute(
            project_id=project_id,
            db_session=db_session,
            force_refresh=force_refresh
        )


# 全局单例（可选，用于避免重复初始化）
_business_analysis_skill = None


def get_business_analysis_skill() -> BusinessAnalysisSkill:
    """获取商业分析技能单例"""
    global _business_analysis_skill
    if _business_analysis_skill is None:
        _business_analysis_skill = BusinessAnalysisSkill()
    return _business_analysis_skill
