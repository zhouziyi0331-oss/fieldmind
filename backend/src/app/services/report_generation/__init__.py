"""
报告生成模块

三层递进报告系统：
- Level 1: 田野调查报告（数据驱动，客观呈现）
- Level 2: 学术专家分析报告（费孝通等理论视角）
- Level 3: 商业市场分析报告（商业决策导向）
"""

from .data_driven_report_builder import DataDrivenReportBuilder, ReportMaterial
from .report_content_engine import ReportContentEngine
from .citation_validator import CitationValidator

__all__ = [
    'DataDrivenReportBuilder',
    'ReportMaterial',
    'ReportContentEngine',
    'CitationValidator'
]
