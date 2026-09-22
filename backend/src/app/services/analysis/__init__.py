"""
Phase 5 分析服务模块
15个分析服务，为三层报告提供数据基础

这些服务的设计原则：
1. 每个服务独立运行，结果存储到 report_analysis_cache 表
2. 所有服务都可验证、可追溯
3. 结果可被 ReportAgent 的三层报告复用
"""

from .sentiment_analysis import SentimentAnalysisService
from .theme_analysis import ThemeAnalysisService
from .entity_analysis import EntityAnalysisService
from .relation_analysis import RelationAnalysisService
from .timeline_analysis import TimelineAnalysisService
from .category_analysis import CategoryAnalysisService
from .summary_analysis import SummaryAnalysisService
from .keyword_analysis import KeywordAnalysisService
from .anomaly_analysis import AnomalyAnalysisService
from .trend_analysis import TrendAnalysisService
from .comparison_analysis import ComparisonAnalysisService
from .impact_analysis import ImpactAnalysisService
from .risk_analysis import RiskAnalysisService
from .opportunity_analysis import OpportunityAnalysisService
from .recommendation_analysis import RecommendationAnalysisService

__all__ = [
    'SentimentAnalysisService',
    'ThemeAnalysisService',
    'EntityAnalysisService',
    'RelationAnalysisService',
    'TimelineAnalysisService',
    'CategoryAnalysisService',
    'SummaryAnalysisService',
    'KeywordAnalysisService',
    'AnomalyAnalysisService',
    'TrendAnalysisService',
    'ComparisonAnalysisService',
    'ImpactAnalysisService',
    'RiskAnalysisService',
    'OpportunityAnalysisService',
    'RecommendationAnalysisService',
]
