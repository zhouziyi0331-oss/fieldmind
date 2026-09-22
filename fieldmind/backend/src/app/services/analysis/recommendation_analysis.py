"""
建议分析服务
基于所有分析结果生成可执行建议、优先级排序、行动计划
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from .base_analysis import BaseAnalysisService


class RecommendationAnalysisService(BaseAnalysisService):
    """建议分析服务"""

    def __init__(self):
        super().__init__(analysis_type='recommendation')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行建议分析"""
        recommendations = []

        # 综合评估当前项目状态
        project_health = await self._assess_project_health(project_id, db_session)

        # 建议类别1: 数据完整性建议
        if project_health['doc_processing_rate'] < 0.9:
            recommendations.append({
                'category': 'data_completeness',
                'priority': 'high',
                'title': '提升文档处理完整性',
                'current_state': f'{project_health["doc_processing_rate"]*100:.1f}%的文档已处理',
                'target_state': '95%以上文档完整处理',
                'rationale': '未处理的文档会导致分析结果不完整和偏差',
                'actions': [
                    {
                        'step': 1,
                        'action': '识别未处理或处理失败的文档',
                        'method': 'SQL查询documents表中缺少chunks的记录'
                    },
                    {
                        'step': 2,
                        'action': '重新运行chunking和embedding处理',
                        'method': '调用ChunkingAgent处理未完成的文档'
                    },
                    {
                        'step': 3,
                        'action': '验证处理结果',
                        'method': '确认所有文档都有对应的chunks'
                    }
                ],
                'expected_impact': '提升分析覆盖率15-25%',
                'estimated_effort': 'medium'
            })

        # 建议类别2: 知识图谱建设建议
        if project_health['entity_relation_ratio'] < 1.5:
            recommendations.append({
                'category': 'knowledge_graph',
                'priority': 'high',
                'title': '增强实体关系网络',
                'current_state': f'平均每个实体仅有{project_health["entity_relation_ratio"]:.2f}条关系',
                'target_state': '平均每个实体至少2条关系',
                'rationale': '稀疏的关系网络限制了关联分析和推理能力',
                'actions': [
                    {
                        'step': 1,
                        'action': '识别孤立实体和低连接实体',
                        'method': '查询relation_count < 2的实体'
                    },
                    {
                        'step': 2,
                        'action': '针对性运行关系抽取',
                        'method': '对这些实体所在的chunks运行RelationAgent'
                    },
                    {
                        'step': 3,
                        'action': '尝试跨文档关系发现',
                        'method': '使用co-reference resolution和entity linking'
                    }
                ],
                'expected_impact': '提升知识图谱连接度50%以上',
                'estimated_effort': 'high'
            })

        # 建议类别3: 数据质量建议
        if project_health['avg_confidence'] < 0.7:
            recommendations.append({
                'category': 'data_quality',
                'priority': 'medium',
                'title': '提升数据置信度',
                'current_state': f'平均置信度仅{project_health["avg_confidence"]:.2f}',
                'target_state': '平均置信度达到0.75以上',
                'rationale': '低置信度数据影响分析结果的可靠性',
                'actions': [
                    {
                        'step': 1,
                        'action': '识别低置信度数据',
                        'method': '查询confidence < 0.5的entities和relations'
                    },
                    {
                        'step': 2,
                        'action': '启用人工审核机制',
                        'method': '对关键低置信度数据进行人工标注'
                    },
                    {
                        'step': 3,
                        'action': '优化模型参数',
                        'method': '调整抽取阈值，过滤极低置信度结果'
                    }
                ],
                'expected_impact': '数据可靠性提升20-30%',
                'estimated_effort': 'medium'
            })

        # 建议类别4: 引用追溯建议
        if project_health['citation_completeness'] < 0.8:
            recommendations.append({
                'category': 'traceability',
                'priority': 'high',
                'title': '完善知识来源追溯',
                'current_state': f'{project_health["citation_completeness"]*100:.1f}%的知识有来源引用',
                'target_state': '95%以上知识节点可追溯',
                'rationale': '缺少引用的知识无法验证，影响系统可信度',
                'actions': [
                    {
                        'step': 1,
                        'action': '识别缺失引用的知识节点',
                        'method': 'source_chunks为空的knowledge_nodes'
                    },
                    {
                        'step': 2,
                        'action': '反向追溯知识来源',
                        'method': '通过实体和关系回溯到原始chunks'
                    },
                    {
                        'step': 3,
                        'action': '修复知识生成流程',
                        'method': '确保所有Agent生成知识时记录source_chunks'
                    }
                ],
                'expected_impact': '实现完整的数据溯源链',
                'estimated_effort': 'medium'
            })

        # 建议类别5: 深度分析建议
        if project_health['knowledge_depth'] > 0.5:
            recommendations.append({
                'category': 'advanced_analysis',
                'priority': 'medium',
                'title': '启用高级分析功能',
                'current_state': f'知识密度{project_health["knowledge_depth"]:.2f}，适合深度分析',
                'target_state': '充分利用数据进行多维度洞察',
                'rationale': '现有数据质量支持更深层次的分析',
                'actions': [
                    {
                        'step': 1,
                        'action': '运行主题聚类分析',
                        'method': '使用embedding对chunks进行聚类'
                    },
                    {
                        'step': 2,
                        'action': '构建知识图谱可视化',
                        'method': '生成交互式图谱展示'
                    },
                    {
                        'step': 3,
                        'action': '进行跨文档综合分析',
                        'method': '对多文档提及的实体生成综合视图'
                    }
                ],
                'expected_impact': '发现隐藏模式和深层洞察',
                'estimated_effort': 'low'
            })

        # 建议类别6: 性能优化建议
        if project_health['total_chunks'] > 500:
            recommendations.append({
                'category': 'performance',
                'priority': 'low',
                'title': '优化查询性能',
                'current_state': f'数据规模达到{project_health["total_chunks"]}个chunks',
                'target_state': '保持查询响应时间在可接受范围',
                'rationale': '随着数据增长，查询性能可能下降',
                'actions': [
                    {
                        'step': 1,
                        'action': '为常用查询字段添加索引',
                        'method': '在project_id, document_id, entity_type等字段上建立索引'
                    },
                    {
                        'step': 2,
                        'action': '启用查询结果缓存',
                        'method': '使用report_analysis_cache表缓存分析结果'
                    },
                    {
                        'step': 3,
                        'action': '考虑数据分区策略',
                        'method': '按project_id或时间分区大表'
                    }
                ],
                'expected_impact': '查询速度提升2-5倍',
                'estimated_effort': 'low'
            })

        # 建议类别7: 协作和共享建议
        if project_health['total_knowledge'] > 100:
            recommendations.append({
                'category': 'collaboration',
                'priority': 'low',
                'title': '启用协作和导出功能',
                'current_state': f'已积累{project_health["total_knowledge"]}个知识节点',
                'target_state': '数据可共享和复用',
                'rationale': '丰富的知识资产应该被有效利用和共享',
                'actions': [
                    {
                        'step': 1,
                        'action': '实现数据导出功能',
                        'method': '支持导出为JSON-LD, RDF, CSV等格式'
                    },
                    {
                        'step': 2,
                        'action': '构建知识API',
                        'method': '提供RESTful API供外部系统访问'
                    },
                    {
                        'step': 3,
                        'action': '生成知识报告',
                        'method': '定期生成PDF/Word格式的分析报告'
                    }
                ],
                'expected_impact': '提升数据价值和影响力',
                'estimated_effort': 'medium'
            })

        # 按优先级排序建议
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))

        # 生成执行路线图
        roadmap = self._generate_roadmap(recommendations)

        return {
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'priority_summary': {
                'high': sum(1 for r in recommendations if r['priority'] == 'high'),
                'medium': sum(1 for r in recommendations if r['priority'] == 'medium'),
                'low': sum(1 for r in recommendations if r['priority'] == 'low')
            },
            'execution_roadmap': roadmap,
            'project_health_score': project_health['overall_score'],
            'immediate_actions': [
                {
                    'title': r['title'],
                    'first_step': r['actions'][0]['action']
                }
                for r in recommendations if r['priority'] == 'high'
            ],
            'confidence_score': 0.93
        }

    async def _assess_project_health(self, project_id: str, db_session: Session) -> Dict[str, Any]:
        """评估项目健康状况"""
        # 文档处理率
        doc_query = text("""
            SELECT
                COUNT(DISTINCT d.id) as total_docs,
                COUNT(DISTINCT c.document_id) as processed_docs
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            WHERE d.project_id = :project_id
        """)
        doc_stats = db_session.execute(doc_query, {'project_id': project_id}).fetchone()
        doc_processing_rate = (doc_stats['processed_docs'] / doc_stats['total_docs']
                              if doc_stats['total_docs'] > 0 else 0)

        # 实体-关系比率
        entity_relation_query = text("""
            SELECT
                (SELECT COUNT(*) FROM entities WHERE project_id = :project_id) as entities,
                (SELECT COUNT(*) FROM relations WHERE project_id = :project_id) as relations
        """)
        er_stats = db_session.execute(entity_relation_query, {'project_id': project_id}).fetchone()
        entity_relation_ratio = (er_stats['relations'] / er_stats['entities']
                                if er_stats['entities'] > 0 else 0)

        # 平均置信度
        confidence_query = text("""
            SELECT AVG(confidence) as avg_conf
            FROM relations
            WHERE project_id = :project_id
        """)
        avg_conf = db_session.execute(confidence_query, {'project_id': project_id}).fetchone()
        avg_confidence = avg_conf['avg_conf'] if avg_conf['avg_conf'] else 0.0

        # 引用完整性
        citation_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN source_chunks IS NOT NULL AND source_chunks != '[]' THEN 1 END) as with_citation
            FROM knowledge_nodes
            WHERE project_id = :project_id
        """)
        citation_stats = db_session.execute(citation_query, {'project_id': project_id}).fetchone()
        citation_completeness = (citation_stats['with_citation'] / citation_stats['total']
                                if citation_stats['total'] > 0 else 0)

        # 数据规模
        scale_query = text("""
            SELECT
                (SELECT COUNT(*) FROM chunks WHERE project_id = :project_id) as chunks,
                (SELECT COUNT(*) FROM knowledge_nodes WHERE project_id = :project_id) as knowledge
        """)
        scale_stats = db_session.execute(scale_query, {'project_id': project_id}).fetchone()

        # 知识深度（knowledge per chunk）
        knowledge_depth = (scale_stats['knowledge'] / scale_stats['chunks']
                          if scale_stats['chunks'] > 0 else 0)

        # 计算综合健康分数
        health_score = (
            doc_processing_rate * 25 +
            min(entity_relation_ratio / 2, 1.0) * 25 +
            avg_confidence * 20 +
            citation_completeness * 20 +
            min(knowledge_depth, 1.0) * 10
        )

        return {
            'doc_processing_rate': doc_processing_rate,
            'entity_relation_ratio': entity_relation_ratio,
            'avg_confidence': avg_confidence,
            'citation_completeness': citation_completeness,
            'knowledge_depth': knowledge_depth,
            'total_chunks': scale_stats['chunks'],
            'total_knowledge': scale_stats['knowledge'],
            'overall_score': round(health_score, 2)
        }

    def _generate_roadmap(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """生成执行路线图"""
        # 按优先级和依赖关系组织为阶段
        phases = []

        # Phase 1: 高优先级的基础建设
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        if high_priority:
            phases.append({
                'phase': 1,
                'name': '基础完善阶段',
                'duration': '1-2周',
                'recommendations': [r['title'] for r in high_priority],
                'goal': '完善数据基础设施和质量'
            })

        # Phase 2: 中优先级的增强功能
        medium_priority = [r for r in recommendations if r['priority'] == 'medium']
        if medium_priority:
            phases.append({
                'phase': 2,
                'name': '功能增强阶段',
                'duration': '2-3周',
                'recommendations': [r['title'] for r in medium_priority],
                'goal': '提升分析能力和数据质量'
            })

        # Phase 3: 低优先级的优化改进
        low_priority = [r for r in recommendations if r['priority'] == 'low']
        if low_priority:
            phases.append({
                'phase': 3,
                'name': '优化提升阶段',
                'duration': '1-2周',
                'recommendations': [r['title'] for r in low_priority],
                'goal': '性能优化和价值延伸'
            })

        return {
            'total_phases': len(phases),
            'phases': phases,
            'estimated_total_duration': '4-7周'
        }
