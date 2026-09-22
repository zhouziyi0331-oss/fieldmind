"""
影响力分析服务
评估关键实体和概念的影响力、识别核心节点、分析传播路径
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import defaultdict
import json
from .base_analysis import BaseAnalysisService


class ImpactAnalysisService(BaseAnalysisService):
    """影响力分析服务"""

    def __init__(self):
        super().__init__(analysis_type='impact')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行影响力分析"""

        # 分析1: 实体影响力（基于关系连接度）
        entity_degree_query = text("""
            SELECT
                e.id,
                e.entity_name,
                e.entity_type,
                COUNT(DISTINCT r.id) as relationship_count,
                COUNT(DISTINCT CASE WHEN r.source_entity_id = e.id THEN r.id END) as outgoing_relations,
                COUNT(DISTINCT CASE WHEN r.target_entity_id = e.id THEN r.id END) as incoming_relations
            FROM entities e
            LEFT JOIN relations r ON e.project_id = r.project_id
                AND (r.source_entity_id = e.id OR r.target_entity_id = e.id)
            WHERE e.project_id = :project_id
            GROUP BY e.id, e.entity_name, e.entity_type
            HAVING relationship_count > 0
            ORDER BY relationship_count DESC
            LIMIT 20
        """)
        top_entities = db_session.execute(entity_degree_query, {'project_id': project_id}).fetchall()

        high_impact_entities = []
        for entity in top_entities:
            # 计算影响力得分：出度和入度的加权组合
            impact_score = (entity['outgoing_relations'] * 1.2 + entity['incoming_relations'] * 0.8)
            high_impact_entities.append({
                'entity_id': entity['id'],
                'entity_name': entity['entity_name'],
                'entity_type': entity['entity_type'],
                'total_connections': entity['relationship_count'],
                'outgoing': entity['outgoing_relations'],
                'incoming': entity['incoming_relations'],
                'impact_score': round(impact_score, 2)
            })

        # 分析2: 知识节点影响力（基于被引用次数）
        knowledge_impact_query = text("""
            SELECT
                kn.id,
                kn.node_type,
                kn.content,
                kn.confidence_score,
                LENGTH(kn.source_chunks) as source_count_proxy
            FROM knowledge_nodes kn
            WHERE kn.project_id = :project_id
            AND kn.confidence_score IS NOT NULL
            ORDER BY kn.confidence_score DESC, source_count_proxy DESC
            LIMIT 15
        """)
        top_knowledge = db_session.execute(knowledge_impact_query, {'project_id': project_id}).fetchall()

        high_impact_knowledge = []
        for node in top_knowledge:
            content_preview = node['content'][:100] + '...' if len(node['content']) > 100 else node['content']
            high_impact_knowledge.append({
                'node_id': node['id'],
                'node_type': node['node_type'],
                'content_preview': content_preview,
                'confidence_score': round(node['confidence_score'], 2),
                'impact_score': round(node['confidence_score'] * (1 + node['source_count_proxy'] * 0.01), 2)
            })

        # 分析3: 文档影响力（基于被引用和衍生数据）
        doc_impact_query = text("""
            SELECT
                d.id,
                d.title,
                d.doc_type,
                COUNT(DISTINCT c.id) as chunk_count,
                COUNT(DISTINCT e.id) as entity_count
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            LEFT JOIN entities e ON e.source_chunk_id = c.id
            WHERE d.project_id = :project_id
            GROUP BY d.id, d.title, d.doc_type
            HAVING chunk_count > 0
            ORDER BY entity_count DESC, chunk_count DESC
            LIMIT 15
        """)
        top_documents = db_session.execute(doc_impact_query, {'project_id': project_id}).fetchall()

        high_impact_documents = []
        for doc in top_documents:
            # 影响力得分：衍生实体数 * 2 + chunk数
            impact_score = doc['entity_count'] * 2 + doc['chunk_count']
            high_impact_documents.append({
                'document_id': doc['id'],
                'title': doc['title'],
                'doc_type': doc['doc_type'],
                'chunks': doc['chunk_count'],
                'entities_derived': doc['entity_count'],
                'impact_score': impact_score
            })

        # 分析4: 关系类型影响力分布
        relation_type_impact_query = text("""
            SELECT
                relation_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                COUNT(DISTINCT source_entity_id) as unique_sources,
                COUNT(DISTINCT target_entity_id) as unique_targets
            FROM relations
            WHERE project_id = :project_id
            GROUP BY relation_type
            ORDER BY count DESC
        """)
        relation_type_impact = db_session.execute(relation_type_impact_query, {'project_id': project_id}).fetchall()

        relation_impacts = []
        for rel_type in relation_type_impact:
            # 影响力：数量 * 置信度 * 连接多样性
            diversity = (rel_type['unique_sources'] + rel_type['unique_targets']) / 2
            impact = rel_type['count'] * rel_type['avg_confidence'] * (1 + diversity * 0.01)
            relation_impacts.append({
                'relation_type': rel_type['relation_type'],
                'count': rel_type['count'],
                'avg_confidence': round(rel_type['avg_confidence'], 2),
                'connection_diversity': round(diversity, 2),
                'impact_score': round(impact, 2)
            })

        # 分析5: 中心性分析（识别网络中的关键桥梁节点）
        # 查找连接多个不同实体类型的实体（桥梁节点）
        bridge_entities_query = text("""
            SELECT
                e.id,
                e.entity_name,
                e.entity_type,
                COUNT(DISTINCT r.relation_type) as relation_diversity,
                COUNT(DISTINCT e2.entity_type) as connected_type_diversity
            FROM entities e
            JOIN relations r ON e.project_id = r.project_id
                AND (r.source_entity_id = e.id OR r.target_entity_id = e.id)
            JOIN entities e2 ON e2.project_id = e.project_id
                AND e2.id != e.id
                AND (e2.id = r.source_entity_id OR e2.id = r.target_entity_id)
            WHERE e.project_id = :project_id
            GROUP BY e.id, e.entity_name, e.entity_type
            HAVING relation_diversity > 1 AND connected_type_diversity > 1
            ORDER BY relation_diversity DESC, connected_type_diversity DESC
            LIMIT 10
        """)
        bridge_entities = db_session.execute(bridge_entities_query, {'project_id': project_id}).fetchall()

        bridge_nodes = []
        for entity in bridge_entities:
            bridge_score = entity['relation_diversity'] * entity['connected_type_diversity']
            bridge_nodes.append({
                'entity_name': entity['entity_name'],
                'entity_type': entity['entity_type'],
                'relation_types': entity['relation_diversity'],
                'connects_types': entity['connected_type_diversity'],
                'bridge_score': bridge_score
            })

        # 计算整体影响力指标
        total_entities = len(high_impact_entities)
        total_knowledge = len(high_impact_knowledge)
        total_docs = len(high_impact_documents)

        # 网络密度指标
        entity_count_query = text("""
            SELECT COUNT(*) as count FROM entities WHERE project_id = :project_id
        """)
        total_entity_count = db_session.execute(entity_count_query, {'project_id': project_id}).fetchone()['count']

        relation_count_query = text("""
            SELECT COUNT(*) as count FROM relations WHERE project_id = :project_id
        """)
        total_relation_count = db_session.execute(relation_count_query, {'project_id': project_id}).fetchone()['count']

        # 网络密度 = 实际关系数 / 最大可能关系数
        max_possible_relations = total_entity_count * (total_entity_count - 1) if total_entity_count > 1 else 1
        network_density = total_relation_count / max_possible_relations if max_possible_relations > 0 else 0

        return {
            'high_impact_entities': high_impact_entities,
            'high_impact_knowledge': high_impact_knowledge,
            'high_impact_documents': high_impact_documents,
            'relation_type_impacts': relation_impacts,
            'bridge_nodes': bridge_nodes,
            'network_metrics': {
                'total_entities': total_entity_count,
                'total_relations': total_relation_count,
                'network_density': round(network_density, 4),
                'bridge_node_count': len(bridge_nodes)
            },
            'summary': {
                'top_influencers_count': total_entities + total_knowledge + total_docs,
                'has_bridge_nodes': len(bridge_nodes) > 0,
                'network_connectivity': 'high' if network_density > 0.1 else 'medium' if network_density > 0.01 else 'low'
            },
            'confidence_score': 0.89
        }
