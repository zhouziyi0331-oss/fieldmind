"""
统一查询接口
Unified Query Interface

功能：
1. 跨模块统一查询（实体、事件、关系、知识单元、缩影）
2. 复杂条件查询
3. 聚合查询
4. 关联查询（一次查询返回关联数据）
5. 分页和排序
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import logging
from typing import List, Dict, Any, Optional
import json

from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    KnowledgeUnit, OntologyConcept, InferenceResult,
    WikiPage
)
from app.models.project import FileSummary
from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService

logger = logging.getLogger(__name__)


class UnifiedQueryInterface:
    """统一查询接口"""

    def __init__(self, db: Session):
        self.db = db
        self.kg_query = KnowledgeGraphQueryService(db)

    # ============================================================
    # 统一搜索
    # ============================================================

    def unified_search(
        self,
        query: str,
        search_types: Optional[List[str]] = None,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        统一搜索（跨所有数据类型）

        Args:
            query: 搜索关键词
            search_types: 搜索类型列表（entity/event/relationship/knowledge_unit/wiki/summary/kg_node）
            project_id: 项目 ID（可选）
            document_id: 文档 ID（可选）
            limit: 每种类型返回数量

        Returns:
            搜索结果
        """
        if not search_types:
            search_types = ['entity', 'event', 'knowledge_unit', 'wiki', 'summary', 'kg_node']

        results = {}

        # 搜索实体
        if 'entity' in search_types:
            results['entities'] = self._search_entities(query, project_id, document_id, limit)

        # 搜索事件
        if 'event' in search_types:
            results['events'] = self._search_events(query, project_id, document_id, limit)

        # 搜索关系
        if 'relationship' in search_types:
            results['relationships'] = self._search_relationships(query, project_id, document_id, limit)

        # 搜索知识单元
        if 'knowledge_unit' in search_types:
            results['knowledge_units'] = self._search_knowledge_units(query, project_id, document_id, limit)

        # 搜索 Wiki 页面
        if 'wiki' in search_types:
            results['wiki_pages'] = self._search_wiki_pages(query, project_id, limit)

        # 搜索缩影
        if 'summary' in search_types:
            results['summaries'] = self._search_summaries(query, project_id, document_id, limit)

        # 搜索知识图谱节点
        if 'kg_node' in search_types:
            results['kg_nodes'] = self.kg_query.search_nodes(query, limit=limit)

        # 统计总数
        total_count = sum(len(v) for v in results.values())

        return {
            'query': query,
            'total_count': total_count,
            'results': results,
            'result_counts': {k: len(v) for k, v in results.items()}
        }

    # ============================================================
    # 关联查询
    # ============================================================

    def get_entity_with_relations(self, entity_id: str) -> Dict[str, Any]:
        """
        获取实体及其所有关联数据

        Args:
            entity_id: 实体 ID

        Returns:
            实体及关联数据
        """
        # 获取实体
        entity = self.db.query(EntityUnified).filter(
            EntityUnified.entity_id == entity_id
        ).first()

        if not entity:
            return {'error': 'Entity not found'}

        entity_dict = self._entity_to_dict(entity)

        # 获取关系
        relationships = self.db.query(RelationshipUnified).filter(
            or_(
                RelationshipUnified.subject_id == entity_id,
                RelationshipUnified.object_id == entity_id
            )
        ).all()

        # 获取参与的事件
        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == entity.document_id
        ).all()

        entity_events = []
        for event in events:
            participants = json.loads(event.participants) if event.participants else []
            if any(p.get('entity_id') == entity_id for p in participants):
                entity_events.append(self._event_to_dict(event))

        # 获取相关知识单元
        knowledge_units = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.entities.like(f'%{entity_id}%')
        ).all()

        # 获取知识图谱信息
        kg_node = self.kg_query.get_nodes_by_source('entities_unified', entity_id)
        kg_neighbors = None
        if kg_node:
            kg_neighbors = self.kg_query.get_direct_neighbors(kg_node[0]['node_id'])

        return {
            'entity': entity_dict,
            'relationships': [self._relationship_to_dict(r) for r in relationships],
            'events': entity_events,
            'knowledge_units': [self._knowledge_unit_to_dict(ku) for ku in knowledge_units],
            'kg_node': kg_node[0] if kg_node else None,
            'kg_neighbors': kg_neighbors,
            'statistics': {
                'relationship_count': len(relationships),
                'event_count': len(entity_events),
                'knowledge_unit_count': len(knowledge_units)
            }
        }

    def get_document_knowledge(self, document_id: int) -> Dict[str, Any]:
        """
        获取文档的完整知识

        Args:
            document_id: 文档 ID

        Returns:
            文档知识全景
        """
        # 获取所有组件
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).all()

        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).all()

        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).all()

        inferences = self.db.query(InferenceResult).filter(
            InferenceResult.document_id == document_id
        ).all()

        knowledge_units = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.document_id == document_id
        ).all()

        # 获取缩影
        summary = self.db.query(FileSummary).filter(
            FileSummary.document_id == document_id
        ).first()

        # 获取 Wiki 页面
        from app.models.project import ProjectDocument
        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        wiki_pages = []
        if doc:
            wiki_pages = self.db.query(WikiPage).filter(
                WikiPage.project_id == doc.project_id
            ).all()

        return {
            'document_id': document_id,
            'entities': [self._entity_to_dict(e) for e in entities],
            'events': [self._event_to_dict(e) for e in events],
            'relationships': [self._relationship_to_dict(r) for r in relationships],
            'inferences': [self._inference_to_dict(i) for i in inferences],
            'knowledge_units': [self._knowledge_unit_to_dict(ku) for ku in knowledge_units],
            'summary': self._summary_to_dict(summary) if summary else None,
            'wiki_pages': [self._wiki_page_to_dict(wp) for wp in wiki_pages],
            'statistics': {
                'entity_count': len(entities),
                'event_count': len(events),
                'relationship_count': len(relationships),
                'inference_count': len(inferences),
                'knowledge_unit_count': len(knowledge_units),
                'wiki_page_count': len(wiki_pages)
            }
        }

    def get_project_overview(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目知识概览

        Args:
            project_id: 项目 ID

        Returns:
            项目知识概览
        """
        # 获取项目下所有文档
        from app.models.project import ProjectDocument
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        doc_ids = [d.id for d in documents]

        # 统计各类知识数量
        entity_count = self.db.query(EntityUnified).filter(
            EntityUnified.document_id.in_(doc_ids)
        ).count()

        event_count = self.db.query(EventUnified).filter(
            EventUnified.document_id.in_(doc_ids)
        ).count()

        relationship_count = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id.in_(doc_ids)
        ).count()

        knowledge_unit_count = self.db.query(KnowledgeUnit).filter(
            KnowledgeUnit.project_id == project_id
        ).count()

        # 获取本体概念
        ontology_concepts = self.db.query(OntologyConcept).filter(
            OntologyConcept.project_id == project_id
        ).all()

        # 获取 Wiki 页面
        wiki_pages = self.db.query(WikiPage).filter(
            WikiPage.project_id == project_id
        ).all()

        # 知识图谱统计
        kg_stats = self.kg_query.get_graph_statistics()

        return {
            'project_id': project_id,
            'document_count': len(documents),
            'entity_count': entity_count,
            'event_count': event_count,
            'relationship_count': relationship_count,
            'knowledge_unit_count': knowledge_unit_count,
            'ontology_concept_count': len(ontology_concepts),
            'wiki_page_count': len(wiki_pages),
            'kg_statistics': kg_stats,
            'top_entities': self._get_top_entities(doc_ids, limit=10),
            'top_events': self._get_top_events(doc_ids, limit=10),
            'ontology_concepts': [self._ontology_to_dict(oc) for oc in ontology_concepts[:20]]
        }

    # ============================================================
    # 复杂查询
    # ============================================================

    def query_with_filters(
        self,
        data_type: str,
        filters: Dict[str, Any],
        sort_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        带过滤条件的查询

        Args:
            data_type: 数据类型（entity/event/relationship/knowledge_unit）
            filters: 过滤条件
            sort_by: 排序字段
            limit: 返回数量
            offset: 偏移量

        Returns:
            查询结果
        """
        if data_type == 'entity':
            return self._query_entities_with_filters(filters, sort_by, limit, offset)
        elif data_type == 'event':
            return self._query_events_with_filters(filters, sort_by, limit, offset)
        elif data_type == 'relationship':
            return self._query_relationships_with_filters(filters, sort_by, limit, offset)
        elif data_type == 'knowledge_unit':
            return self._query_knowledge_units_with_filters(filters, sort_by, limit, offset)
        else:
            return {'error': f'Unknown data type: {data_type}'}

    # ============================================================
    # 私有方法：搜索实现
    # ============================================================

    def _search_entities(
        self,
        query: str,
        project_id: Optional[int],
        document_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索实体"""
        q = self.db.query(EntityUnified).filter(
            EntityUnified.entity_name.like(f'%{query}%')
        )

        if document_id:
            q = q.filter(EntityUnified.document_id == document_id)
        elif project_id:
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            q = q.filter(EntityUnified.document_id.in_(doc_ids))

        entities = q.order_by(EntityUnified.mention_count.desc()).limit(limit).all()
        return [self._entity_to_dict(e) for e in entities]

    def _search_events(
        self,
        query: str,
        project_id: Optional[int],
        document_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索事件"""
        q = self.db.query(EventUnified).filter(
            EventUnified.event_name.like(f'%{query}%')
        )

        if document_id:
            q = q.filter(EventUnified.document_id == document_id)
        elif project_id:
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            q = q.filter(EventUnified.document_id.in_(doc_ids))

        events = q.limit(limit).all()
        return [self._event_to_dict(e) for e in events]

    def _search_relationships(
        self,
        query: str,
        project_id: Optional[int],
        document_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索关系"""
        q = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.predicate.like(f'%{query}%')
        )

        if document_id:
            q = q.filter(RelationshipUnified.document_id == document_id)

        relationships = q.limit(limit).all()
        return [self._relationship_to_dict(r) for r in relationships]

    def _search_knowledge_units(
        self,
        query: str,
        project_id: Optional[int],
        document_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索知识单元"""
        q = self.db.query(KnowledgeUnit).filter(
            or_(
                KnowledgeUnit.title.like(f'%{query}%'),
                KnowledgeUnit.summary.like(f'%{query}%')
            )
        )

        if document_id:
            q = q.filter(KnowledgeUnit.document_id == document_id)
        elif project_id:
            q = q.filter(KnowledgeUnit.project_id == project_id)

        units = q.order_by(KnowledgeUnit.quality_score.desc()).limit(limit).all()
        return [self._knowledge_unit_to_dict(ku) for ku in units]

    def _search_wiki_pages(
        self,
        query: str,
        project_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索 Wiki 页面"""
        q = self.db.query(WikiPage).filter(
            WikiPage.page_title.like(f'%{query}%')
        )

        if project_id:
            q = q.filter(WikiPage.project_id == project_id)

        pages = q.limit(limit).all()
        return [self._wiki_page_to_dict(wp) for wp in pages]

    def _search_summaries(
        self,
        query: str,
        project_id: Optional[int],
        document_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """搜索缩影"""
        q = self.db.query(FileSummary).filter(
            or_(
                FileSummary.one_sentence_summary.like(f'%{query}%'),
                FileSummary.full_summary.like(f'%{query}%')
            )
        )

        if document_id:
            q = q.filter(FileSummary.document_id == document_id)
        elif project_id:
            q = q.filter(FileSummary.project_id == project_id)

        summaries = q.limit(limit).all()
        return [self._summary_to_dict(s) for s in summaries]

    # ============================================================
    # 私有方法：过滤查询
    # ============================================================

    def _query_entities_with_filters(
        self,
        filters: Dict,
        sort_by: Optional[str],
        limit: int,
        offset: int
    ) -> Dict:
        """带过滤条件查询实体"""
        q = self.db.query(EntityUnified)

        # 应用过滤器
        if 'entity_type' in filters:
            q = q.filter(EntityUnified.entity_type == filters['entity_type'])

        if 'document_id' in filters:
            q = q.filter(EntityUnified.document_id == filters['document_id'])

        if 'min_mention_count' in filters:
            q = q.filter(EntityUnified.mention_count >= filters['min_mention_count'])

        # 排序
        if sort_by == 'mention_count':
            q = q.order_by(EntityUnified.mention_count.desc())
        elif sort_by == 'confidence':
            q = q.order_by(EntityUnified.confidence.desc())

        total = q.count()
        entities = q.limit(limit).offset(offset).all()

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': [self._entity_to_dict(e) for e in entities]
        }

    def _query_events_with_filters(self, filters: Dict, sort_by: Optional[str], limit: int, offset: int) -> Dict:
        """带过滤条件查询事件"""
        # 类似 _query_entities_with_filters 的实现
        pass

    def _query_relationships_with_filters(self, filters: Dict, sort_by: Optional[str], limit: int, offset: int) -> Dict:
        """带过滤条件查询关系"""
        pass

    def _query_knowledge_units_with_filters(self, filters: Dict, sort_by: Optional[str], limit: int, offset: int) -> Dict:
        """带过滤条件查询知识单元"""
        pass

    # ============================================================
    # 私有方法：辅助方法
    # ============================================================

    def _get_top_entities(self, doc_ids: List[int], limit: int) -> List[Dict]:
        """获取 Top 实体"""
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id.in_(doc_ids)
        ).order_by(EntityUnified.mention_count.desc()).limit(limit).all()

        return [self._entity_to_dict(e) for e in entities]

    def _get_top_events(self, doc_ids: List[int], limit: int) -> List[Dict]:
        """获取 Top 事件"""
        events = self.db.query(EventUnified).filter(
            EventUnified.document_id.in_(doc_ids)
        ).order_by(EventUnified.confidence.desc()).limit(limit).all()

        return [self._event_to_dict(e) for e in events]

    # 数据转换方法
    def _entity_to_dict(self, entity: EntityUnified) -> Dict:
        return {
            'entity_id': entity.entity_id,
            'name': entity.entity_name,
            'type': entity.entity_type,
            'category': entity.entity_category,
            'mention_count': entity.mention_count,
            'confidence': entity.confidence,
            'description': entity.description
        }

    def _event_to_dict(self, event: EventUnified) -> Dict:
        return {
            'event_id': event.event_id,
            'name': event.event_name,
            'type': event.event_type,
            'description': event.description,
            'time': event.normalized_time_start,
            'location': event.normalized_location
        }

    def _relationship_to_dict(self, rel: RelationshipUnified) -> Dict:
        return {
            'relationship_id': rel.relationship_id,
            'subject_id': rel.subject_id,
            'predicate': rel.predicate,
            'object_id': rel.object_id,
            'confidence': rel.confidence
        }

    def _knowledge_unit_to_dict(self, ku: KnowledgeUnit) -> Dict:
        return {
            'unit_id': ku.unit_id,
            'type': ku.unit_type,
            'title': ku.title,
            'summary': ku.summary,
            'quality_score': ku.quality_score
        }

    def _summary_to_dict(self, summary: FileSummary) -> Dict:
        return {
            'id': summary.id,
            'document_id': summary.document_id,
            'one_sentence_summary': summary.one_sentence_summary,
            'full_summary': summary.full_summary
        }

    def _wiki_page_to_dict(self, page: WikiPage) -> Dict:
        return {
            'page_id': page.page_id,
            'title': page.page_title,
            'type': page.page_type,
            'category': page.category
        }

    def _ontology_to_dict(self, concept: OntologyConcept) -> Dict:
        return {
            'concept_id': concept.concept_id,
            'name': concept.concept_name,
            'type': concept.concept_type,
            'definition': concept.definition,
            'instance_count': concept.instance_count
        }

    def _inference_to_dict(self, inference: InferenceResult) -> Dict:
        return {
            'inference_id': inference.inference_id,
            'type': inference.inference_type,
            'conclusion': inference.conclusion_description,
            'confidence': inference.confidence
        }


# ============================================================
# 便捷函数
# ============================================================

def unified_query(db: Session) -> UnifiedQueryInterface:
    """
    获取统一查询接口实例

    Args:
        db: 数据库会话

    Returns:
        统一查询接口实例
    """
    return UnifiedQueryInterface(db)
