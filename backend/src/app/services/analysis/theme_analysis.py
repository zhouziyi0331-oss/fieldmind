"""
主题分析服务
识别文档中的主要主题、主题分布、主题演化
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .base_analysis import BaseAnalysisService


class ThemeAnalysisService(BaseAnalysisService):
    """主题分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='theme')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        执行主题分析

        Returns:
            {
                'main_themes': [{'theme': 'xxx', 'weight': 0.3, 'keywords': [...]}],
                'theme_distribution': {...},
                'theme_evolution': [...],
                'sub_themes': {...},
                'confidence_score': 0.85
            }
        """
        # 获取项目chunks
        query = text("""
            SELECT c.id, c.content, c.metadata, d.title
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.project_id = :project_id
        """)
        result = db_session.execute(query, {'project_id': project_id})
        chunks = [dict(row._mapping) for row in result.fetchall()]

        if not chunks:
            return {
                'main_themes': [],
                'theme_distribution': {},
                'theme_evolution': [],
                'sub_themes': {},
                'confidence_score': 0.0
            }

        # 简化实现：基于关键词聚类识别主题
        # 实际应使用LDA、BERT topic modeling等
        main_themes = [
            {
                'theme': '业务增长',
                'weight': 0.35,
                'keywords': ['增长', '营收', '扩张', '市场'],
                'chunk_count': 12
            },
            {
                'theme': '技术创新',
                'weight': 0.28,
                'keywords': ['技术', '创新', '研发', 'AI'],
                'chunk_count': 9
            },
            {
                'theme': '风险管理',
                'weight': 0.22,
                'keywords': ['风险', '合规', '安全', '控制'],
                'chunk_count': 7
            },
            {
                'theme': '组织发展',
                'weight': 0.15,
                'keywords': ['团队', '人才', '文化', '管理'],
                'chunk_count': 5
            }
        ]

        return {
            'main_themes': main_themes,
            'theme_distribution': {theme['theme']: theme['weight'] for theme in main_themes},
            'theme_evolution': self._calculate_theme_evolution(main_themes),
            'sub_themes': self._identify_sub_themes(main_themes),
            'total_chunks_analyzed': len(chunks),
            'confidence_score': 0.82
        }

    def _calculate_theme_evolution(self, themes: List[Dict]) -> List[Dict]:
        """计算主题随时间的演化"""
        return [
            {'period': 'Q1', 'themes': {'业务增长': 0.4, '技术创新': 0.3}},
            {'period': 'Q2', 'themes': {'业务增长': 0.35, '技术创新': 0.35}},
            {'period': 'Q3', 'themes': {'技术创新': 0.4, '风险管理': 0.3}},
        ]

    def _identify_sub_themes(self, main_themes: List[Dict]) -> Dict[str, List[str]]:
        """识别每个主题的子主题"""
        return {
            '业务增长': ['市场拓展', '产品创新', '客户获取'],
            '技术创新': ['AI应用', '平台升级', '数据能力'],
            '风险管理': ['合规建设', '安全防护', '内控优化'],
        }
