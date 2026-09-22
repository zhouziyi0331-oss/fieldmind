"""
摘要分析服务
生成项目整体摘要、识别核心要点、提取关键信息
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from .base_analysis import BaseAnalysisService


class SummaryAnalysisService(BaseAnalysisService):
    """摘要分析服务"""

    def __init__(self):
        super().__init__(analysis_type='summary')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行摘要分析"""
        # 获取项目基本信息
        project_query = text("""
            SELECT name, description, created_at
            FROM projects
            WHERE id = :project_id
        """)
        project_result = db_session.execute(project_query, {'project_id': project_id})
        project = project_result.fetchone()

        if not project:
            return {
                'error': 'Project not found',
                'confidence_score': 0.0
            }

        # 统计文档数量和类型
        doc_stats_query = text("""
            SELECT
                COUNT(*) as total_docs,
                COUNT(DISTINCT doc_type) as doc_types,
                SUM(CAST(json_extract(metadata, '$.word_count') AS INTEGER)) as total_words
            FROM documents
            WHERE project_id = :project_id
        """)
        doc_stats = db_session.execute(doc_stats_query, {'project_id': project_id}).fetchone()

        # 获取chunks统计
        chunk_stats_query = text("""
            SELECT
                COUNT(*) as total_chunks,
                AVG(LENGTH(content)) as avg_chunk_length
            FROM chunks
            WHERE project_id = :project_id
        """)
        chunk_stats = db_session.execute(chunk_stats_query, {'project_id': project_id}).fetchone()

        # 获取实体统计
        entity_stats_query = text("""
            SELECT
                COUNT(*) as total_entities,
                COUNT(DISTINCT entity_type) as entity_types
            FROM entities
            WHERE project_id = :project_id
        """)
        entity_stats = db_session.execute(entity_stats_query, {'project_id': project_id}).fetchone()

        # 获取关系统计
        relation_stats_query = text("""
            SELECT
                COUNT(*) as total_relations,
                COUNT(DISTINCT relation_type) as relation_types
            FROM relations
            WHERE project_id = :project_id
        """)
        relation_stats = db_session.execute(relation_stats_query, {'project_id': project_id}).fetchone()

        # 获取知识节点统计
        knowledge_stats_query = text("""
            SELECT
                COUNT(*) as total_nodes,
                COUNT(DISTINCT node_type) as node_types
            FROM knowledge_nodes
            WHERE project_id = :project_id
        """)
        knowledge_stats = db_session.execute(knowledge_stats_query, {'project_id': project_id}).fetchone()

        # 获取最近的thinking patterns用于了解思考深度
        thinking_query = text("""
            SELECT COUNT(*) as thinking_count
            FROM thinking_patterns
            WHERE project_id = :project_id
        """)
        thinking_stats = db_session.execute(thinking_query, {'project_id': project_id}).fetchone()

        # 构建项目摘要
        project_dict = dict(project._mapping)
        doc_stats_dict = dict(doc_stats._mapping)
        chunk_stats_dict = dict(chunk_stats._mapping)
        entity_stats_dict = dict(entity_stats._mapping)
        relation_stats_dict = dict(relation_stats._mapping)
        knowledge_stats_dict = dict(knowledge_stats._mapping)
        thinking_stats_dict = dict(thinking_stats._mapping)

        # 计算数据密度（entities + relations per document）
        total_docs = doc_stats_dict.get('total_docs', 0)
        data_density = 0.0
        if total_docs > 0:
            total_connections = (entity_stats_dict.get('total_entities', 0) +
                               relation_stats_dict.get('total_relations', 0))
            data_density = total_connections / total_docs

        # 计算知识深度（knowledge nodes per chunk）
        total_chunks = chunk_stats_dict.get('total_chunks', 0)
        knowledge_depth = 0.0
        if total_chunks > 0:
            knowledge_depth = knowledge_stats_dict.get('total_nodes', 0) / total_chunks

        return {
            'project_name': project_dict.get('name'),
            'project_description': project_dict.get('description'),
            'created_at': str(project_dict.get('created_at')),
            'documents': {
                'total': doc_stats_dict.get('total_docs', 0),
                'types': doc_stats_dict.get('doc_types', 0),
                'total_words': doc_stats_dict.get('total_words', 0)
            },
            'chunks': {
                'total': chunk_stats_dict.get('total_chunks', 0),
                'avg_length': round(chunk_stats_dict.get('avg_chunk_length', 0), 2)
            },
            'entities': {
                'total': entity_stats_dict.get('total_entities', 0),
                'types': entity_stats_dict.get('entity_types', 0)
            },
            'relations': {
                'total': relation_stats_dict.get('total_relations', 0),
                'types': relation_stats_dict.get('relation_types', 0)
            },
            'knowledge': {
                'nodes': knowledge_stats_dict.get('total_nodes', 0),
                'node_types': knowledge_stats_dict.get('node_types', 0)
            },
            'thinking_patterns': thinking_stats_dict.get('thinking_count', 0),
            'metrics': {
                'data_density': round(data_density, 2),
                'knowledge_depth': round(knowledge_depth, 3)
            },
            'confidence_score': 0.95
        }
