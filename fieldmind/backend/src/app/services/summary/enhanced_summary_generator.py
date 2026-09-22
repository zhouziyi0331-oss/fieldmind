"""
增强版缩影生成器
Enhanced Summary Generator

功能：
1. 读取九步流水线的所有数据（实体、事件、关系、推理、知识单元）
2. 生成多层次缩影（一句话、段落、完整）
3. 关联知识图谱节点
4. 关联 Wiki 页面
5. 添加本体标签
6. 生成结构化摘要（包含关键信息）
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List, Dict, Any, Optional
import json

from app.models.project import ProjectDocument, FileSummary
from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    InferenceResult, KnowledgeUnit, OntologyConcept, WikiPage,
    KnowledgeGraphNode
)
from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService

logger = logging.getLogger(__name__)


class EnhancedSummaryGenerator:
    """增强版缩影生成器"""

    def __init__(self, db: Session):
        self.db = db
        self.kg_query = KnowledgeGraphQueryService(db)

    def generate_enhanced_summary(self, document_id: int) -> Dict[str, Any]:
        """
        生成增强版缩影

        Args:
            document_id: 文档 ID

        Returns:
            生成结果
        """
        logger.info(f"📝 生成增强版缩影 - 文档 {document_id}")

        try:
            # 获取文档信息
            doc = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc:
                return {'success': False, 'message': '文档不存在'}

            # 收集所有知识组件
            knowledge_components = self._collect_knowledge_components(document_id)

            # 生成多层次摘要
            summaries = self._generate_multilevel_summaries(document_id, knowledge_components)

            # 提取关键信息
            key_info = self._extract_key_information(knowledge_components)

            # 关联知识图谱
            kg_associations = self._associate_knowledge_graph(document_id, knowledge_components)

            # 关联 Wiki 页面
            wiki_associations = self._associate_wiki_pages(doc.project_id, knowledge_components)

            # 添加本体标签
            ontology_tags = self._add_ontology_tags(doc.project_id, knowledge_components)

            # 生成结构化摘要
            structured_summary = self._generate_structured_summary(
                knowledge_components,
                key_info,
                kg_associations,
                ontology_tags
            )

            # 保存或更新缩影
            summary_id = self._save_enhanced_summary(
                document_id,
                doc.project_id,
                summaries,
                key_info,
                structured_summary,
                kg_associations,
                wiki_associations,
                ontology_tags
            )

            result = {
                'success': True,
                'document_id': document_id,
                'summary_id': summary_id,
                'summaries': summaries,
                'key_info': key_info,
                'kg_associations': {
                    'node_count': len(kg_associations.get('nodes', [])),
                    'edge_count': len(kg_associations.get('edges', []))
                },
                'wiki_pages': len(wiki_associations),
                'ontology_tags': len(ontology_tags)
            }

            logger.info(
                f"✅ 缩影生成完成 - 文档 {document_id}, "
                f"关联 {result['kg_associations']['node_count']} 个知识图谱节点, "
                f"{result['wiki_pages']} 个 Wiki 页面"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 缩影生成失败: {e}", exc_info=True)
            raise

    # ============================================================
    # 知识组件收集
    # ============================================================

    def _collect_knowledge_components(self, document_id: int) -> Dict[str, Any]:
        """
        收集所有知识组件

        Returns:
            所有知识组件
        """
        # 获取实体
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).all()

        # 获取事件
        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).all()

        # 获取关系
        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).all()

        # 获取推理
        inferences = self.db.query(InferenceResult).filter(
            InferenceResult.document_id == document_id
        ).all()

        # 获取知识单元
        knowledge_units = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.document_id == document_id
        ).all()

        return {
            'entities': entities,
            'events': events,
            'relationships': relationships,
            'inferences': inferences,
            'knowledge_units': knowledge_units,
            'statistics': {
                'entity_count': len(entities),
                'event_count': len(events),
                'relationship_count': len(relationships),
                'inference_count': len(inferences),
                'knowledge_unit_count': len(knowledge_units)
            }
        }

    # ============================================================
    # 多层次摘要生成
    # ============================================================

    def _generate_multilevel_summaries(
        self,
        document_id: int,
        components: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        生成多层次摘要

        Returns:
            一句话、段落、完整三个层次的摘要
        """
        entities = components['entities']
        events = components['events']
        knowledge_units = components['knowledge_units']

        # 提取关键实体（按提及次数）
        top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:5]
        entity_names = [e.entity_name for e in top_entities]

        # 提取关键事件（按时间排序）
        time_events = [e for e in events if e.normalized_time_start]
        time_events.sort(key=lambda e: e.normalized_time_start)

        # 提取洞察型知识单元
        insights = [ku for ku in knowledge_units if ku.unit_type == 'insight']

        # 一句话摘要
        one_sentence = self._generate_one_sentence_summary(entity_names, time_events, insights)

        # 段落摘要
        paragraph = self._generate_paragraph_summary(
            entity_names,
            time_events,
            components['relationships'],
            insights
        )

        # 完整摘要
        full_summary = self._generate_full_summary(components)

        return {
            'one_sentence': one_sentence,
            'paragraph': paragraph,
            'full': full_summary
        }

    def _generate_one_sentence_summary(
        self,
        entity_names: List[str],
        events: List,
        insights: List
    ) -> str:
        """生成一句话摘要"""
        # 简化版本：基于模板
        if entity_names and events:
            main_entity = entity_names[0]
            event_count = len(events)
            return f"文档主要描述了{main_entity}等{len(entity_names)}个主体，涉及{event_count}个事件。"
        elif entity_names:
            return f"文档主要描述了{', '.join(entity_names[:3])}等实体。"
        else:
            return "文档包含丰富的知识内容。"

    def _generate_paragraph_summary(
        self,
        entity_names: List[str],
        events: List,
        relationships: List,
        insights: List
    ) -> str:
        """生成段落摘要"""
        lines = []

        # 主体介绍
        if entity_names:
            lines.append(f"文档涉及{', '.join(entity_names[:3])}等{len(entity_names)}个主要实体。")

        # 事件描述
        if events:
            lines.append(f"记录了{len(events)}个事件，时间跨度从{events[0].normalized_time_start if events else ''}开始。")

        # 关系描述
        if relationships:
            lines.append(f"建立了{len(relationships)}个关系连接。")

        # 洞察
        if insights:
            top_insight = insights[0]
            lines.append(f"关键洞察：{top_insight.summary}")

        return ' '.join(lines)

    def _generate_full_summary(self, components: Dict[str, Any]) -> str:
        """生成完整摘要"""
        lines = []

        # 统计信息
        stats = components['statistics']
        lines.append(f"## 文档知识概览")
        lines.append(f"")
        lines.append(f"本文档包含：")
        lines.append(f"- {stats['entity_count']} 个实体")
        lines.append(f"- {stats['event_count']} 个事件")
        lines.append(f"- {stats['relationship_count']} 个关系")
        lines.append(f"- {stats['inference_count']} 个推理")
        lines.append(f"- {stats['knowledge_unit_count']} 个知识单元")
        lines.append(f"")

        # 主要实体
        entities = components['entities']
        if entities:
            top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:10]
            lines.append(f"## 主要实体")
            lines.append(f"")
            for entity in top_entities:
                lines.append(f"- **{entity.entity_name}** ({entity.entity_type}): 提及 {entity.mention_count} 次")
            lines.append(f"")

        # 关键事件
        events = components['events']
        time_events = [e for e in events if e.normalized_time_start]
        if time_events:
            time_events.sort(key=lambda e: e.normalized_time_start)
            lines.append(f"## 关键事件")
            lines.append(f"")
            for event in time_events[:5]:
                lines.append(f"- **{event.normalized_time_start}**: {event.event_name}")
            lines.append(f"")

        # 知识洞察
        knowledge_units = components['knowledge_units']
        insights = [ku for ku in knowledge_units if ku.unit_type == 'insight']
        if insights:
            lines.append(f"## 知识洞察")
            lines.append(f"")
            for insight in insights[:3]:
                lines.append(f"- {insight.summary}")
            lines.append(f"")

        return '\n'.join(lines)

    # ============================================================
    # 关键信息提取
    # ============================================================

    def _extract_key_information(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取关键信息

        Returns:
            结构化的关键信息
        """
        entities = components['entities']
        events = components['events']
        knowledge_units = components['knowledge_units']

        # Top 实体
        top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:10]

        # Top 事件
        top_events = sorted(events, key=lambda e: e.confidence, reverse=True)[:10]

        # 高质量知识单元
        high_quality_units = [
            ku for ku in knowledge_units
            if ku.quality_score >= 0.7
        ]

        return {
            'top_entities': [
                {
                    'name': e.entity_name,
                    'type': e.entity_type,
                    'mention_count': e.mention_count
                }
                for e in top_entities
            ],
            'top_events': [
                {
                    'name': e.event_name,
                    'type': e.event_type,
                    'time': e.normalized_time_start
                }
                for e in top_events
            ],
            'high_quality_knowledge': [
                {
                    'title': ku.title,
                    'type': ku.unit_type,
                    'quality_score': ku.quality_score
                }
                for ku in high_quality_units
            ]
        }

    # ============================================================
    # 知识图谱关联
    # ============================================================

    def _associate_knowledge_graph(
        self,
        document_id: int,
        components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        关联知识图谱

        Returns:
            关联的节点和边
        """
        # 获取文档相关的所有知识图谱节点
        all_nodes = []
        all_edges = []

        # 从实体获取节点
        for entity in components['entities']:
            nodes = self.kg_query.get_nodes_by_source('entities_unified', entity.entity_id)
            all_nodes.extend(nodes)

        # 从事件获取节点
        for event in components['events']:
            nodes = self.kg_query.get_nodes_by_source('events_unified', event.event_id)
            all_nodes.extend(nodes)

        # 获取节点间的边
        node_ids = [n['node_id'] for n in all_nodes]
        if node_ids:
            subgraph = self.kg_query.get_subgraph(node_ids, include_edges=True)
            all_edges = subgraph['edges']

        return {
            'nodes': all_nodes,
            'edges': all_edges,
            'node_count': len(all_nodes),
            'edge_count': len(all_edges)
        }

    # ============================================================
    # Wiki 页面关联
    # ============================================================

    def _associate_wiki_pages(
        self,
        project_id: int,
        components: Dict[str, Any]
    ) -> List[Dict]:
        """
        关联 Wiki 页面

        Returns:
            关联的 Wiki 页面列表
        """
        # 获取项目的所有 Wiki 页面
        wiki_pages = self.db.query(WikiPage).filter(
            WikiPage.project_id == project_id
        ).all()

        # 找到与实体相关的页面
        entity_names = {e.entity_name for e in components['entities']}
        related_pages = []

        for page in wiki_pages:
            # 检查页面标题是否匹配实体名称
            if page.page_title in entity_names:
                related_pages.append({
                    'page_id': page.page_id,
                    'title': page.page_title,
                    'type': page.page_type
                })

        return related_pages

    # ============================================================
    # 本体标签
    # ============================================================

    def _add_ontology_tags(
        self,
        project_id: int,
        components: Dict[str, Any]
    ) -> List[str]:
        """
        添加本体标签

        Returns:
            本体标签列表
        """
        # 获取项目的本体概念
        ontology_concepts = self.db.query(OntologyConcept).filter(
            OntologyConcept.project_id == project_id
        ).all()

        # 从实体类型和事件类型推断标签
        entity_types = {e.entity_type for e in components['entities']}
        event_types = {e.event_type for e in components['events']}

        tags = []

        for concept in ontology_concepts:
            # 检查概念是否与实体/事件类型匹配
            if concept.concept_name in entity_types or concept.concept_name in event_types:
                tags.append(concept.concept_name)

        return list(set(tags))

    # ============================================================
    # 结构化摘要生成
    # ============================================================

    def _generate_structured_summary(
        self,
        components: Dict[str, Any],
        key_info: Dict[str, Any],
        kg_associations: Dict[str, Any],
        ontology_tags: List[str]
    ) -> Dict[str, Any]:
        """
        生成结构化摘要（JSON 格式）

        Returns:
            结构化摘要
        """
        return {
            'statistics': components['statistics'],
            'key_information': key_info,
            'knowledge_graph': {
                'node_count': kg_associations['node_count'],
                'edge_count': kg_associations['edge_count']
            },
            'ontology_tags': ontology_tags,
            'entity_types': list({e.entity_type for e in components['entities']}),
            'event_types': list({e.event_type for e in components['events']}),
            'knowledge_unit_types': {
                ku_type: sum(1 for ku in components['knowledge_units'] if ku.unit_type == ku_type)
                for ku_type in ['fact', 'rule', 'pattern', 'insight']
            }
        }

    # ============================================================
    # 保存缩影
    # ============================================================

    def _save_enhanced_summary(
        self,
        document_id: int,
        project_id: int,
        summaries: Dict[str, str],
        key_info: Dict[str, Any],
        structured_summary: Dict[str, Any],
        kg_associations: Dict[str, Any],
        wiki_associations: List[Dict],
        ontology_tags: List[str]
    ) -> int:
        """
        保存增强版缩影

        Returns:
            缩影 ID
        """
        # 查找现有缩影
        existing = self.db.query(FileSummary).filter(
            FileSummary.document_id == document_id
        ).first()

        if existing:
            # 更新现有缩影
            existing.one_sentence_summary = summaries['one_sentence']
            existing.full_summary = summaries['full']

            # 更新新增字段
            if kg_associations['nodes']:
                existing.knowledge_graph_node_id = kg_associations['nodes'][0]['node_id']

            existing.knowledge_units = json.dumps([ku['title'] for ku in key_info.get('high_quality_knowledge', [])])

            if wiki_associations:
                existing.wiki_page_id = wiki_associations[0]['page_id']

            existing.ontology_tags = json.dumps(ontology_tags)
            existing.inference_count = structured_summary['statistics']['inference_count']
            existing.relationships_count = structured_summary['statistics']['relationship_count']

            self.db.commit()

            return existing.id

        else:
            # 创建新缩影
            summary = FileSummary(
                project_id=project_id,
                document_id=document_id,
                one_sentence_summary=summaries['one_sentence'],
                full_summary=summaries['full'],
                knowledge_graph_node_id=kg_associations['nodes'][0]['node_id'] if kg_associations['nodes'] else None,
                knowledge_units=json.dumps([ku['title'] for ku in key_info.get('high_quality_knowledge', [])]),
                wiki_page_id=wiki_associations[0]['page_id'] if wiki_associations else None,
                ontology_tags=json.dumps(ontology_tags),
                inference_count=structured_summary['statistics']['inference_count'],
                relationships_count=structured_summary['statistics']['relationship_count']
            )

            self.db.add(summary)
            self.db.commit()

            return summary.id


# ============================================================
# 便捷函数
# ============================================================

def generate_enhanced_summary(db: Session, document_id: int) -> Dict[str, Any]:
    """
    生成增强版缩影的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        生成结果
    """
    generator = EnhancedSummaryGenerator(db)
    return generator.generate_enhanced_summary(document_id)
