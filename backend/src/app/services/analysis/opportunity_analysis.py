"""
机会分析服务
识别潜在机会、发现数据价值点、提供增值建议
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from .base_analysis import BaseAnalysisService


class OpportunityAnalysisService(BaseAnalysisService):
    """机会分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='opportunity')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行机会分析"""
        opportunities = []

        # 机会1: 高质量数据深挖机会
        high_quality_chunks_query = text("""
            SELECT
                c.id,
                c.document_id,
                d.title,
                LENGTH(c.content) as chunk_length,
                COUNT(DISTINCT e.id) as entity_density
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            LEFT JOIN entities e ON e.source_chunk_id = c.id
            WHERE c.project_id = :project_id
            AND LENGTH(c.content) > 500
            GROUP BY c.id, c.document_id, d.title, c.content
            HAVING entity_density >= 5
            ORDER BY entity_density DESC
            LIMIT 10
        """)
        rich_chunks = db_session.execute(high_quality_chunks_query, {'project_id': project_id}).fetchall()

        if rich_chunks:
            opportunities.append({
                'opportunity_type': 'deep_analysis_targets',
                'priority': 'high',
                'value': len(rich_chunks),
                'description': f'发现{len(rich_chunks)}个信息密度高的文本块，适合深度分析',
                'potential_gain': '提取更多隐含关系和深层知识',
                'action_items': [
                    '对这些chunks运行更深层次的语义分析',
                    '尝试抽取隐含关系和推理性知识',
                    '构建局部知识子图进行深度推理'
                ],
                'examples': [
                    {'document': row['title'], 'entities': row['entity_density']}
                    for row in rich_chunks[:3]
                ]
            })

        # 机会2: 未充分利用的实体类型
        underutilized_entities_query = text("""
            SELECT
                e.entity_type,
                COUNT(DISTINCT e.id) as entity_count,
                COUNT(DISTINCT r.id) as relation_count,
                CAST(COUNT(DISTINCT r.id) AS FLOAT) / COUNT(DISTINCT e.id) as relation_ratio
            FROM entities e
            LEFT JOIN relations r ON e.project_id = r.project_id
                AND (r.source_entity_id = e.id OR r.target_entity_id = e.id)
            WHERE e.project_id = :project_id
            GROUP BY e.entity_type
            HAVING entity_count >= 5 AND relation_ratio < 2.0
            ORDER BY entity_count DESC
        """)
        underutilized = db_session.execute(underutilized_entities_query, {'project_id': project_id}).fetchall()

        if underutilized:
            opportunities.append({
                'opportunity_type': 'relation_expansion',
                'priority': 'medium',
                'value': sum(row['entity_count'] for row in underutilized),
                'description': f'{len(underutilized)}类实体连接不足，可挖掘更多关系',
                'potential_gain': '扩展知识图谱连接度，提升关联分析能力',
                'action_items': [
                    '针对这些实体类型运行专门的关系抽取',
                    '使用跨文档关系识别技术',
                    '考虑引入外部知识库补充关系'
                ],
                'entity_types': [
                    {
                        'type': row['entity_type'],
                        'count': row['entity_count'],
                        'avg_relations': round(row['relation_ratio'], 2)
                    }
                    for row in underutilized[:5]
                ]
            })

        # 机会3: 跨文档知识整合机会
        cross_doc_entities_query = text("""
            SELECT
                e.entity_name,
                e.entity_type,
                COUNT(DISTINCT e.source_document_id) as doc_count,
                COUNT(DISTINCT e.id) as mention_count
            FROM entities e
            WHERE e.project_id = :project_id
            AND e.source_document_id IS NOT NULL
            GROUP BY e.entity_name, e.entity_type
            HAVING doc_count >= 3
            ORDER BY doc_count DESC, mention_count DESC
            LIMIT 15
        """)
        cross_doc_entities = db_session.execute(cross_doc_entities_query, {'project_id': project_id}).fetchall()

        if cross_doc_entities:
            opportunities.append({
                'opportunity_type': 'cross_document_synthesis',
                'priority': 'high',
                'value': len(cross_doc_entities),
                'description': f'{len(cross_doc_entities)}个实体出现在多个文档中，可进行跨文档综合',
                'potential_gain': '发现跨文档的一致性、矛盾和演化模式',
                'action_items': [
                    '对这些实体进行跨文档视角整合',
                    '识别不同文档中的观点差异',
                    '构建实体的完整知识档案'
                ],
                'key_entities': [
                    {
                        'name': row['entity_name'],
                        'type': row['entity_type'],
                        'documents': row['doc_count'],
                        'mentions': row['mention_count']
                    }
                    for row in cross_doc_entities[:5]
                ]
            })

        # 机会4: 知识图谱可视化机会
        graph_stats_query = text("""
            SELECT
                (SELECT COUNT(*) FROM entities WHERE project_id = :project_id) as entity_count,
                (SELECT COUNT(*) FROM relations WHERE project_id = :project_id) as relation_count,
                (SELECT COUNT(DISTINCT entity_type) FROM entities WHERE project_id = :project_id) as entity_types
        """)
        graph_stats = db_session.execute(graph_stats_query, {'project_id': project_id}).fetchone()

        if graph_stats['entity_count'] > 20 and graph_stats['relation_count'] > 10:
            opportunities.append({
                'opportunity_type': 'knowledge_graph_visualization',
                'priority': 'medium',
                'value': graph_stats['entity_count'] + graph_stats['relation_count'],
                'description': f'已有{graph_stats["entity_count"]}个实体和{graph_stats["relation_count"]}条关系，适合可视化展示',
                'potential_gain': '直观展示知识结构，发现隐藏模式',
                'action_items': [
                    '构建交互式知识图谱可视化',
                    '突出显示核心实体和关键路径',
                    '提供多层次缩放和过滤功能'
                ],
                'graph_metrics': {
                    'entities': graph_stats['entity_count'],
                    'relations': graph_stats['relation_count'],
                    'entity_types': graph_stats['entity_types']
                }
            })

        # 机会5: 主题聚类机会
        cluster_potential_query = text("""
            SELECT COUNT(DISTINCT id) as chunk_count
            FROM chunks
            WHERE project_id = :project_id
            AND LENGTH(content) > 200
        """)
        cluster_potential = db_session.execute(cluster_potential_query, {'project_id': project_id}).fetchone()

        if cluster_potential['chunk_count'] > 30:
            opportunities.append({
                'opportunity_type': 'topic_clustering',
                'priority': 'medium',
                'value': cluster_potential['chunk_count'],
                'description': f'{cluster_potential["chunk_count"]}个文本块可进行主题聚类分析',
                'potential_gain': '自动发现主题结构和内容组织',
                'action_items': [
                    '运行embedding-based聚类算法',
                    '识别主要主题和子主题',
                    '生成主题层次结构'
                ]
            })

        # 机会6: 时间序列分析机会
        timeline_query = text("""
            SELECT COUNT(*) as event_count
            FROM timeline_events
            WHERE project_id = :project_id
            AND event_date IS NOT NULL
        """)
        timeline_stats = db_session.execute(timeline_query, {'project_id': project_id}).fetchone()

        if timeline_stats['event_count'] > 10:
            opportunities.append({
                'opportunity_type': 'temporal_pattern_mining',
                'priority': 'high',
                'value': timeline_stats['event_count'],
                'description': f'{timeline_stats["event_count"]}个时间事件可进行时序模式挖掘',
                'potential_gain': '发现事件规律、预测未来趋势',
                'action_items': [
                    '分析事件时间间隔分布',
                    '识别周期性模式',
                    '构建事件因果链'
                ]
            })

        # 机会7: 知识补全机会（基于现有模式推断缺失知识）
        incomplete_knowledge_query = text("""
            SELECT COUNT(*) as count
            FROM knowledge_nodes
            WHERE project_id = :project_id
            AND (
                properties IS NULL
                OR properties = '{}'
                OR related_nodes IS NULL
                OR related_nodes = '[]'
            )
        """)
        incomplete_knowledge = db_session.execute(incomplete_knowledge_query, {'project_id': project_id}).fetchone()

        if incomplete_knowledge['count'] > 5:
            opportunities.append({
                'opportunity_type': 'knowledge_completion',
                'priority': 'medium',
                'value': incomplete_knowledge['count'],
                'description': f'{incomplete_knowledge["count"]}个知识节点信息不完整，可基于模式补全',
                'potential_gain': '提升知识完整性和连贯性',
                'action_items': [
                    '使用相似节点的模式进行推断',
                    '从原始文本中补充缺失信息',
                    '通过关系传播补全属性'
                ]
            })

        # 机会8: 数据导出和共享机会
        export_readiness_query = text("""
            SELECT
                (SELECT COUNT(*) FROM entities WHERE project_id = :project_id) as entities,
                (SELECT COUNT(*) FROM relations WHERE project_id = :project_id) as relations,
                (SELECT COUNT(*) FROM knowledge_nodes WHERE project_id = :project_id) as knowledge
        """)
        export_stats = db_session.execute(export_readiness_query, {'project_id': project_id}).fetchone()

        total_structured_data = export_stats['entities'] + export_stats['relations'] + export_stats['knowledge']
        if total_structured_data > 50:
            opportunities.append({
                'opportunity_type': 'data_export_sharing',
                'priority': 'low',
                'value': total_structured_data,
                'description': f'已积累{total_structured_data}条结构化数据，可导出为标准格式',
                'potential_gain': '数据复用、团队协作、外部集成',
                'action_items': [
                    '导出为RDF/JSON-LD格式供知识图谱工具使用',
                    '生成CSV/Excel便于人工审阅',
                    '提供API接口供其他系统调用'
                ]
            })

        # 计算总体机会价值
        total_opportunity_value = sum(opp['value'] for opp in opportunities)
        high_priority_count = sum(1 for opp in opportunities if opp['priority'] == 'high')

        return {
            'total_opportunities': len(opportunities),
            'opportunities': opportunities,
            'priority_distribution': {
                'high': sum(1 for opp in opportunities if opp['priority'] == 'high'),
                'medium': sum(1 for opp in opportunities if opp['priority'] == 'medium'),
                'low': sum(1 for opp in opportunities if opp['priority'] == 'low')
            },
            'total_potential_value': total_opportunity_value,
            'has_high_priority_opportunities': high_priority_count > 0,
            'recommended_next_actions': [
                opp['action_items'][0]
                for opp in opportunities
                if opp['priority'] == 'high'
            ][:3],
            'confidence_score': 0.87
        }
