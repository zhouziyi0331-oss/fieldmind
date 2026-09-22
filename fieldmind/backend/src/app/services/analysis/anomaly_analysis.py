"""
异常检测分析服务
识别数据异常、检测不一致性、发现潜在问题
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timedelta
from .base_analysis import BaseAnalysisService


class AnomalyAnalysisService(BaseAnalysisService):
    """异常检测分析服务"""

    def __init__(self):
        super().__init__(analysis_type='anomaly')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行异常检测分析"""
        anomalies = []

        # 检测1: 空内容的chunks
        empty_chunks_query = text("""
            SELECT COUNT(*) as count
            FROM chunks
            WHERE project_id = :project_id
            AND (content IS NULL OR TRIM(content) = '')
        """)
        empty_chunks = db_session.execute(empty_chunks_query, {'project_id': project_id}).fetchone()
        if empty_chunks['count'] > 0:
            anomalies.append({
                'type': 'empty_chunks',
                'severity': 'medium',
                'count': empty_chunks['count'],
                'description': f'发现 {empty_chunks["count"]} 个空内容的文本块',
                'recommendation': '检查数据导入流程，确保文本块内容完整'
            })

        # 检测2: 孤立的实体（没有任何关系的实体）
        orphan_entities_query = text("""
            SELECT COUNT(DISTINCT e.id) as count
            FROM entities e
            WHERE e.project_id = :project_id
            AND NOT EXISTS (
                SELECT 1 FROM relations r
                WHERE r.project_id = :project_id
                AND (r.source_entity_id = e.id OR r.target_entity_id = e.id)
            )
        """)
        orphan_entities = db_session.execute(orphan_entities_query, {'project_id': project_id}).fetchone()
        total_entities_query = text("""
            SELECT COUNT(*) as count
            FROM entities
            WHERE project_id = :project_id
        """)
        total_entities = db_session.execute(total_entities_query, {'project_id': project_id}).fetchone()

        if total_entities['count'] > 0:
            orphan_rate = orphan_entities['count'] / total_entities['count']
            if orphan_rate > 0.3:  # 超过30%的实体是孤立的
                anomalies.append({
                    'type': 'orphan_entities',
                    'severity': 'high',
                    'count': orphan_entities['count'],
                    'rate': round(orphan_rate, 2),
                    'description': f'{orphan_entities["count"]} 个实体({round(orphan_rate*100, 1)}%)没有关系连接',
                    'recommendation': '增强关系抽取，建立实体之间的连接'
                })

        # 检测3: 异常长度的chunks（过长或过短）
        chunk_length_query = text("""
            SELECT
                AVG(LENGTH(content)) as avg_length,
                MAX(LENGTH(content)) as max_length,
                MIN(LENGTH(content)) as min_length
            FROM chunks
            WHERE project_id = :project_id
            AND content IS NOT NULL
        """)
        chunk_length = db_session.execute(chunk_length_query, {'project_id': project_id}).fetchone()

        if chunk_length['avg_length']:
            avg_len = chunk_length['avg_length']
            max_len = chunk_length['max_length']
            min_len = chunk_length['min_length']

            # 检测异常长的chunks（超过平均值5倍）
            if max_len > avg_len * 5:
                long_chunks_query = text("""
                    SELECT COUNT(*) as count
                    FROM chunks
                    WHERE project_id = :project_id
                    AND LENGTH(content) > :threshold
                """)
                long_chunks = db_session.execute(
                    long_chunks_query,
                    {'project_id': project_id, 'threshold': avg_len * 5}
                ).fetchone()

                if long_chunks['count'] > 0:
                    anomalies.append({
                        'type': 'oversized_chunks',
                        'severity': 'low',
                        'count': long_chunks['count'],
                        'threshold': round(avg_len * 5, 0),
                        'description': f'{long_chunks["count"]} 个文本块长度异常（超过平均值5倍）',
                        'recommendation': '考虑重新分块，确保chunks大小适中'
                    })

            # 检测异常短的chunks（小于平均值的10%）
            if min_len < avg_len * 0.1 and min_len > 0:
                short_chunks_query = text("""
                    SELECT COUNT(*) as count
                    FROM chunks
                    WHERE project_id = :project_id
                    AND LENGTH(content) > 0
                    AND LENGTH(content) < :threshold
                """)
                short_chunks = db_session.execute(
                    short_chunks_query,
                    {'project_id': project_id, 'threshold': avg_len * 0.1}
                ).fetchone()

                if short_chunks['count'] > 0:
                    anomalies.append({
                        'type': 'undersized_chunks',
                        'severity': 'low',
                        'count': short_chunks['count'],
                        'threshold': round(avg_len * 0.1, 0),
                        'description': f'{short_chunks["count"]} 个文本块过短（小于平均值10%）',
                        'recommendation': '检查分块策略，可能需要合并过短的文本块'
                    })

        # 检测4: 重复的实体名称（可能是数据质量问题）
        duplicate_entities_query = text("""
            SELECT entity_name, COUNT(*) as count
            FROM entities
            WHERE project_id = :project_id
            GROUP BY entity_name
            HAVING COUNT(*) > 5
        """)
        duplicate_entities = db_session.execute(duplicate_entities_query, {'project_id': project_id}).fetchall()

        if duplicate_entities:
            duplicate_count = len(duplicate_entities)
            anomalies.append({
                'type': 'duplicate_entities',
                'severity': 'medium',
                'count': duplicate_count,
                'examples': [
                    {'name': row['entity_name'], 'occurrences': row['count']}
                    for row in duplicate_entities[:5]
                ],
                'description': f'{duplicate_count} 个实体名称出现频率异常高（>5次）',
                'recommendation': '检查是否需要实体合并或去重'
            })

        # 检测5: 文档缺少元数据
        missing_metadata_query = text("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE project_id = :project_id
            AND (metadata IS NULL OR metadata = '{}' OR metadata = '')
        """)
        missing_metadata = db_session.execute(missing_metadata_query, {'project_id': project_id}).fetchone()
        total_docs_query = text("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE project_id = :project_id
        """)
        total_docs = db_session.execute(total_docs_query, {'project_id': project_id}).fetchone()

        if total_docs['count'] > 0:
            missing_rate = missing_metadata['count'] / total_docs['count']
            if missing_rate > 0.2:  # 超过20%的文档缺少元数据
                anomalies.append({
                    'type': 'missing_metadata',
                    'severity': 'medium',
                    'count': missing_metadata['count'],
                    'rate': round(missing_rate, 2),
                    'description': f'{missing_metadata["count"]} 个文档({round(missing_rate*100, 1)}%)缺少元数据',
                    'recommendation': '补充文档元数据以提高分析质量'
                })

        # 检测6: 知识节点引用缺失
        missing_citations_query = text("""
            SELECT COUNT(*) as count
            FROM knowledge_nodes
            WHERE project_id = :project_id
            AND (source_chunks IS NULL OR source_chunks = '[]' OR source_chunks = '')
        """)
        missing_citations = db_session.execute(missing_citations_query, {'project_id': project_id}).fetchone()
        total_nodes_query = text("""
            SELECT COUNT(*) as count
            FROM knowledge_nodes
            WHERE project_id = :project_id
        """)
        total_nodes = db_session.execute(total_nodes_query, {'project_id': project_id}).fetchone()

        if total_nodes['count'] > 0:
            missing_citation_rate = missing_citations['count'] / total_nodes['count']
            if missing_citation_rate > 0.1:  # 超过10%的知识节点缺少引用
                anomalies.append({
                    'type': 'missing_citations',
                    'severity': 'high',
                    'count': missing_citations['count'],
                    'rate': round(missing_citation_rate, 2),
                    'description': f'{missing_citations["count"]} 个知识节点({round(missing_citation_rate*100, 1)}%)缺少来源引用',
                    'recommendation': '为知识节点添加source_chunks以确保可追溯性'
                })

        # 计算总体数据质量分数
        severity_weights = {'low': 1, 'medium': 2, 'high': 3}
        total_severity = sum(severity_weights.get(a['severity'], 0) for a in anomalies)
        max_possible_severity = len(anomalies) * 3 if anomalies else 1
        quality_score = max(0, 100 - (total_severity / max_possible_severity * 100))

        return {
            'total_anomalies': len(anomalies),
            'anomalies': anomalies,
            'severity_distribution': {
                'high': sum(1 for a in anomalies if a['severity'] == 'high'),
                'medium': sum(1 for a in anomalies if a['severity'] == 'medium'),
                'low': sum(1 for a in anomalies if a['severity'] == 'low')
            },
            'data_quality_score': round(quality_score, 2),
            'has_critical_issues': any(a['severity'] == 'high' for a in anomalies),
            'confidence_score': 0.92
        }
