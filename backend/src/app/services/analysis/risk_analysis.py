"""
风险分析服务
识别潜在风险、评估数据质量风险、发现系统性问题
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from .base_analysis import BaseAnalysisService


class RiskAnalysisService(BaseAnalysisService):
    """风险分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='risk')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行风险分析"""
        risks = []

        # 风险1: 数据覆盖风险（文档未充分处理）
        doc_processing_query = text("""
            SELECT
                COUNT(DISTINCT d.id) as total_docs,
                COUNT(DISTINCT c.document_id) as docs_with_chunks,
                COUNT(DISTINCT e.source_document_id) as docs_with_entities
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            LEFT JOIN entities e ON e.source_document_id = d.id
            WHERE d.project_id = :project_id
        """)
        doc_stats = db_session.execute(doc_processing_query, {'project_id': project_id}).fetchone()

        total_docs = doc_stats['total_docs']
        if total_docs > 0:
            chunk_coverage = doc_stats['docs_with_chunks'] / total_docs
            entity_coverage = doc_stats['docs_with_entities'] / total_docs

            if chunk_coverage < 0.8:
                risks.append({
                    'risk_type': 'incomplete_chunking',
                    'severity': 'high',
                    'coverage_rate': round(chunk_coverage, 2),
                    'affected_docs': total_docs - doc_stats['docs_with_chunks'],
                    'description': f'{round((1-chunk_coverage)*100, 1)}%的文档未被分块处理',
                    'impact': '数据未充分利用，影响分析完整性',
                    'mitigation': '重新运行chunking处理流程'
                })

            if entity_coverage < 0.5:
                risks.append({
                    'risk_type': 'low_entity_extraction',
                    'severity': 'medium',
                    'coverage_rate': round(entity_coverage, 2),
                    'affected_docs': total_docs - doc_stats['docs_with_entities'],
                    'description': f'{round((1-entity_coverage)*100, 1)}%的文档未提取实体',
                    'impact': '知识图谱不完整，影响关系分析',
                    'mitigation': '检查实体抽取模型和参数配置'
                })

        # 风险2: 数据质量风险（低置信度数据占比高）
        low_confidence_query = text("""
            SELECT
                COUNT(*) as total_relations,
                COUNT(CASE WHEN confidence < 0.5 THEN 1 END) as low_confidence_count
            FROM relations
            WHERE project_id = :project_id
        """)
        relation_quality = db_session.execute(low_confidence_query, {'project_id': project_id}).fetchone()

        if relation_quality['total_relations'] > 0:
            low_confidence_rate = relation_quality['low_confidence_count'] / relation_quality['total_relations']
            if low_confidence_rate > 0.3:
                risks.append({
                    'risk_type': 'low_confidence_relations',
                    'severity': 'medium',
                    'low_confidence_rate': round(low_confidence_rate, 2),
                    'affected_count': relation_quality['low_confidence_count'],
                    'description': f'{round(low_confidence_rate*100, 1)}%的关系置信度低于0.5',
                    'impact': '数据可靠性存疑，可能导致错误结论',
                    'mitigation': '启用人工审核或提高抽取阈值'
                })

        # 风险3: 引用链断裂风险（知识无法追溯）
        citation_integrity_query = text("""
            SELECT
                COUNT(*) as total_knowledge,
                COUNT(CASE WHEN source_chunks IS NULL OR source_chunks = '[]' THEN 1 END) as no_citation,
                COUNT(CASE WHEN source_document_ids IS NULL OR source_document_ids = '[]' THEN 1 END) as no_doc_ref
            FROM knowledge_nodes
            WHERE project_id = :project_id
        """)
        citation_stats = db_session.execute(citation_integrity_query, {'project_id': project_id}).fetchone()

        if citation_stats['total_knowledge'] > 0:
            no_citation_rate = citation_stats['no_citation'] / citation_stats['total_knowledge']
            if no_citation_rate > 0.2:
                risks.append({
                    'risk_type': 'broken_citation_chain',
                    'severity': 'high',
                    'affected_rate': round(no_citation_rate, 2),
                    'affected_count': citation_stats['no_citation'],
                    'description': f'{round(no_citation_rate*100, 1)}%的知识节点缺少来源引用',
                    'impact': '知识不可追溯，无法验证准确性',
                    'mitigation': '修复知识生成流程，确保记录source_chunks'
                })

        # 风险4: 数据孤岛风险（未连接的子图）
        connected_components_query = text("""
            SELECT COUNT(DISTINCT e.id) as total_entities
            FROM entities e
            WHERE e.project_id = :project_id
            AND NOT EXISTS (
                SELECT 1 FROM relations r
                WHERE r.project_id = :project_id
                AND (r.source_entity_id = e.id OR r.target_entity_id = e.id)
            )
        """)
        isolated_entities = db_session.execute(connected_components_query, {'project_id': project_id}).fetchone()

        total_entities_query = text("""
            SELECT COUNT(*) as count FROM entities WHERE project_id = :project_id
        """)
        total_entities = db_session.execute(total_entities_query, {'project_id': project_id}).fetchone()

        if total_entities['count'] > 0:
            isolation_rate = isolated_entities['total_entities'] / total_entities['count']
            if isolation_rate > 0.4:
                risks.append({
                    'risk_type': 'data_fragmentation',
                    'severity': 'high',
                    'isolation_rate': round(isolation_rate, 2),
                    'isolated_entities': isolated_entities['total_entities'],
                    'description': f'{round(isolation_rate*100, 1)}%的实体形成数据孤岛',
                    'impact': '知识图谱碎片化，无法进行跨域分析',
                    'mitigation': '增强跨文档关系抽取，建立连接'
                })

        # 风险5: 容量风险（数据规模不足）
        scale_query = text("""
            SELECT
                (SELECT COUNT(*) FROM documents WHERE project_id = :project_id) as docs,
                (SELECT COUNT(*) FROM chunks WHERE project_id = :project_id) as chunks,
                (SELECT COUNT(*) FROM entities WHERE project_id = :project_id) as entities,
                (SELECT COUNT(*) FROM knowledge_nodes WHERE project_id = :project_id) as knowledge
        """)
        scale_stats = db_session.execute(scale_query, {'project_id': project_id}).fetchone()

        # 判断数据规模是否足够支撑可靠分析
        scale_issues = []
        if scale_stats['docs'] < 5:
            scale_issues.append(f'文档数过少({scale_stats["docs"]}个)')
        if scale_stats['chunks'] < 20:
            scale_issues.append(f'文本块过少({scale_stats["chunks"]}个)')
        if scale_stats['entities'] < 10:
            scale_issues.append(f'实体数过少({scale_stats["entities"]}个)')

        if scale_issues:
            risks.append({
                'risk_type': 'insufficient_data_scale',
                'severity': 'medium',
                'issues': scale_issues,
                'description': '数据规模不足以支撑可靠的统计分析',
                'impact': '分析结果可能不稳定，置信度低',
                'mitigation': '增加数据源或扩大数据采集范围'
            })

        # 风险6: 元数据缺失风险
        metadata_query = text("""
            SELECT
                COUNT(*) as total_entities,
                COUNT(CASE WHEN properties IS NULL OR properties = '{}' THEN 1 END) as no_properties
            FROM entities
            WHERE project_id = :project_id
        """)
        metadata_stats = db_session.execute(metadata_query, {'project_id': project_id}).fetchone()

        if metadata_stats['total_entities'] > 0:
            no_metadata_rate = metadata_stats['no_properties'] / metadata_stats['total_entities']
            if no_metadata_rate > 0.5:
                risks.append({
                    'risk_type': 'missing_metadata',
                    'severity': 'low',
                    'affected_rate': round(no_metadata_rate, 2),
                    'affected_count': metadata_stats['no_properties'],
                    'description': f'{round(no_metadata_rate*100, 1)}%的实体缺少属性信息',
                    'impact': '实体信息不丰富，限制深度分析能力',
                    'mitigation': '增强实体属性抽取'
                })

        # 风险7: 时间完整性风险
        temporal_query = text("""
            SELECT
                COUNT(*) as total_events,
                COUNT(CASE WHEN event_date IS NULL THEN 1 END) as missing_dates
            FROM timeline_events
            WHERE project_id = :project_id
        """)
        temporal_stats = db_session.execute(temporal_query, {'project_id': project_id}).fetchone()

        if temporal_stats['total_events'] > 0:
            missing_date_rate = temporal_stats['missing_dates'] / temporal_stats['total_events']
            if missing_date_rate > 0.3:
                risks.append({
                    'risk_type': 'incomplete_temporal_data',
                    'severity': 'medium',
                    'missing_rate': round(missing_date_rate, 2),
                    'affected_count': temporal_stats['missing_dates'],
                    'description': f'{round(missing_date_rate*100, 1)}%的时间线事件缺少日期',
                    'impact': '无法进行准确的时序分析',
                    'mitigation': '补充事件时间信息或从文本中抽取'
                })

        # 计算整体风险评分
        severity_scores = {'high': 3, 'medium': 2, 'low': 1}
        total_risk_score = sum(severity_scores.get(r['severity'], 0) for r in risks)
        max_risk_score = len(risks) * 3 if risks else 1

        # 风险等级：0-30分=低，31-60分=中，61-100分=高
        risk_level_score = (total_risk_score / max_risk_score * 100) if risks else 0

        if risk_level_score > 60:
            overall_risk_level = 'high'
        elif risk_level_score > 30:
            overall_risk_level = 'medium'
        else:
            overall_risk_level = 'low'

        return {
            'total_risks': len(risks),
            'risks': risks,
            'risk_distribution': {
                'high': sum(1 for r in risks if r['severity'] == 'high'),
                'medium': sum(1 for r in risks if r['severity'] == 'medium'),
                'low': sum(1 for r in risks if r['severity'] == 'low')
            },
            'overall_risk_level': overall_risk_level,
            'risk_score': round(risk_level_score, 2),
            'requires_immediate_action': any(r['severity'] == 'high' for r in risks),
            'confidence_score': 0.91
        }
