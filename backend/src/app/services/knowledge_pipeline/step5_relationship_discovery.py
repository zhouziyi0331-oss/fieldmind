"""
Step 5: 关系发现服务
Relationship Discovery Service

功能：
1. 发现实体间关系
2. 发现实体-事件关系
3. 使用依存句法分析
4. 使用语义模式匹配
5. 关系类型分类
6. 保存到 relationships_unified 表
7. 创建知识图谱边
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any, Set, Tuple
import uuid
import json

from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    KnowledgeGraphNode, KnowledgeGraphEdge
)
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class RelationshipDiscoveryService:
    """关系发现服务（Step 5）"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def discover_relationships(self, document_id: int) -> Dict[str, Any]:
        """
        发现文档中的所有关系

        Args:
            document_id: 文档 ID

        Returns:
            发现结果
        """
        logger.info(f"🔗 Step 5: 开始关系发现 - 文档 {document_id}")

        try:
            # 获取实体和事件
            entities = self._get_entities(document_id)
            events = self._get_events(document_id)

            if not entities and not events:
                logger.warning(f"文档 {document_id} 没有实体和事件")
                return {'success': False, 'message': '没有实体和事件'}

            # 发现关系
            relationships = []

            # 1. 实体-实体关系
            entity_relationships = self._find_entity_relationships(document_id, entities)
            relationships.extend(entity_relationships)

            # 2. 实体-事件关系
            event_relationships = self._find_entity_event_relationships(document_id, entities, events)
            relationships.extend(event_relationships)

            # 3. 事件-事件关系
            event_event_relationships = self._find_event_relationships(document_id, events)
            relationships.extend(event_event_relationships)

            # 去重
            unique_relationships = self._deduplicate_relationships(relationships)

            # 保存到数据库
            saved_count = self._save_relationships(document_id, unique_relationships)

            # 创建知识图谱边
            kg_edges_count = self._create_kg_edges(unique_relationships)

            result = {
                'success': True,
                'document_id': document_id,
                'relationships_discovered': saved_count,
                'kg_edges_created': kg_edges_count,
                'relationship_types': self._count_by_predicate(unique_relationships),
                'entity_entity': len([r for r in unique_relationships if r['subject_type'] == 'entity' and r['object_type'] == 'entity']),
                'entity_event': len([r for r in unique_relationships if 'event' in [r['subject_type'], r['object_type']]]),
                'event_event': len([r for r in unique_relationships if r['subject_type'] == 'event' and r['object_type'] == 'event'])
            }

            logger.info(
                f"✅ Step 5 完成: 发现了 {saved_count} 个关系, "
                f"创建 {kg_edges_count} 条知识图谱边"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.RELATIONSHIPS_DISCOVERED,
                payload={
                    'step': 5,
                    'step_name': 'relationship_discovery',
                    'document_id': document_id,
                    'result': result
                },
                publisher='RelationshipDiscoveryService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 5 失败: {e}", exc_info=True)
            raise

    def _get_entities(self, document_id: int) -> List[Dict]:
        """获取实体"""
        entities = self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).all()

        return [
            {
                'id': e.entity_id,
                'name': e.entity_name,
                'type': e.entity_type,
                'chunk_ids': json.loads(e.chunk_ids) if e.chunk_ids else []
            }
            for e in entities
        ]

    def _get_events(self, document_id: int) -> List[Dict]:
        """获取事件"""
        events = self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).all()

        return [
            {
                'id': e.event_id,
                'name': e.event_name,
                'type': e.event_type,
                'chunk_ids': json.loads(e.chunk_ids) if e.chunk_ids else [],
                'participants': json.loads(e.participants) if e.participants else []
            }
            for e in events
        ]

    def _find_entity_relationships(
        self,
        document_id: int,
        entities: List[Dict]
    ) -> List[Dict]:
        """
        发现实体-实体关系

        策略：
        1. 共现关系（在同一个 chunk 中出现）
        2. 语义模式匹配
        """
        relationships = []

        # 按 chunk 分组实体
        chunk_entities = {}
        for entity in entities:
            for chunk_id in entity['chunk_ids']:
                if chunk_id not in chunk_entities:
                    chunk_entities[chunk_id] = []
                chunk_entities[chunk_id].append(entity)

        # 在同一个 chunk 中的实体可能有关系
        for chunk_id, chunk_ents in chunk_entities.items():
            if len(chunk_ents) < 2:
                continue

            # 获取 chunk 文本
            from app.models.project import DocumentChunk
            chunk = self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
            if not chunk:
                continue

            text = chunk.cleaned_text or chunk.text

            # 对实体两两组合，尝试发现关系
            for i in range(len(chunk_ents)):
                for j in range(i + 1, len(chunk_ents)):
                    entity1 = chunk_ents[i]
                    entity2 = chunk_ents[j]

                    # 使用模式匹配识别关系
                    predicate = self._identify_predicate(entity1, entity2, text)

                    if predicate:
                        relationships.append({
                            'subject_id': entity1['id'],
                            'subject_type': 'entity',
                            'predicate': predicate,
                            'object_id': entity2['id'],
                            'object_type': 'entity',
                            'context_chunk_ids': [chunk_id],
                            'confidence': 0.7,
                            'extraction_method': 'pattern'
                        })

        return relationships

    def _identify_predicate(
        self,
        entity1: Dict,
        entity2: Dict,
        text: str
    ) -> str:
        """
        识别两个实体之间的关系谓词

        策略：
        1. 查找实体之间的连接词
        2. 根据实体类型推断关系
        """
        name1 = entity1['name']
        name2 = entity2['name']

        # 查找实体在文本中的位置
        pos1 = text.find(name1)
        pos2 = text.find(name2)

        if pos1 == -1 or pos2 == -1:
            return None

        # 确定顺序
        if pos1 > pos2:
            name1, name2 = name2, name1
            pos1, pos2 = pos2, pos1
            entity1, entity2 = entity2, entity1

        # 获取两个实体之间的文本
        between_text = text[pos1 + len(name1):pos2]

        # 关系模式
        relation_patterns = [
            (r'的', '属于'),
            (r'是', '是'),
            (r'在', '位于'),
            (r'来自', '来自'),
            (r'前往', '前往'),
            (r'参加|参与', '参与'),
            (r'组织|举办', '组织'),
            (r'认识|知道', '认识'),
            (r'父|母|子|女|兄|弟|姐|妹', '亲属关系'),
            (r'老师|学生|师傅|徒弟', '师徒关系'),
        ]

        for pattern, predicate in relation_patterns:
            if re.search(pattern, between_text):
                return predicate

        # 根据实体类型推断默认关系
        type1 = entity1['type']
        type2 = entity2['type']

        if type1 == 'person' and type2 == 'organization':
            return '属于'
        elif type1 == 'person' and type2 == 'location':
            return '位于'
        elif type1 == 'person' and type2 == 'person':
            return '相关'

        # 默认共现关系
        return '共现'

    def _find_entity_event_relationships(
        self,
        document_id: int,
        entities: List[Dict],
        events: List[Dict]
    ) -> List[Dict]:
        """
        发现实体-事件关系

        策略：
        1. 使用事件的 participants 字段
        2. 共现分析
        """
        relationships = []

        for event in events:
            # 从 participants 直接获取关系
            for participant in event.get('participants', []):
                entity_id = participant.get('entity_id')
                role = participant.get('role', 'participant')

                # 根据角色确定关系类型
                if role == 'agent':
                    predicate = '发起'
                elif role == 'patient':
                    predicate = '经历'
                else:
                    predicate = '参与'

                relationships.append({
                    'subject_id': entity_id,
                    'subject_type': 'entity',
                    'predicate': predicate,
                    'object_id': event['id'],
                    'object_type': 'event',
                    'context_chunk_ids': event['chunk_ids'],
                    'confidence': 0.8,
                    'extraction_method': 'participant'
                })

        return relationships

    def _find_event_relationships(
        self,
        document_id: int,
        events: List[Dict]
    ) -> List[Dict]:
        """
        发现事件-事件关系

        策略：
        1. 时间顺序关系
        2. 因果关系
        """
        relationships = []

        # 按时间排序事件
        events_with_time = [e for e in events if e.get('normalized_time_start')]
        events_with_time.sort(key=lambda e: e.get('normalized_time_start', ''))

        # 相邻事件建立时间关系
        for i in range(len(events_with_time) - 1):
            event1 = events_with_time[i]
            event2 = events_with_time[i + 1]

            relationships.append({
                'subject_id': event1['id'],
                'subject_type': 'event',
                'predicate': '早于',
                'object_id': event2['id'],
                'object_type': 'event',
                'context_chunk_ids': list(set(event1['chunk_ids'] + event2['chunk_ids'])),
                'confidence': 0.6,
                'extraction_method': 'temporal'
            })

        # TODO: 可以添加更复杂的因果关系识别

        return relationships

    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """去重关系"""
        seen = set()
        unique = []

        for rel in relationships:
            key = (rel['subject_id'], rel['predicate'], rel['object_id'])
            if key not in seen:
                seen.add(key)
                unique.append(rel)

        return unique

    def _save_relationships(self, document_id: int, relationships: List[Dict]) -> int:
        """保存关系到数据库"""
        # 先删除旧的关系
        self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).delete()

        saved_count = 0

        for rel in relationships:
            relationship_id = f"rel_{uuid.uuid4().hex[:16]}"

            db_rel = RelationshipUnified(
                relationship_id=relationship_id,
                document_id=document_id,
                subject_id=rel['subject_id'],
                subject_type=rel['subject_type'],
                predicate=rel['predicate'],
                object_id=rel['object_id'],
                object_type=rel['object_type'],
                context_chunk_ids=json.dumps(rel.get('context_chunk_ids', [])),
                confidence=rel.get('confidence', 0.7),
                extraction_method=rel.get('extraction_method', 'unknown')
            )

            self.db.add(db_rel)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _create_kg_edges(self, relationships: List[Dict]) -> int:
        """为关系创建知识图谱边"""
        created_count = 0

        for rel in relationships:
            # 查找源节点和目标节点
            source_node = self.db.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.source_id == rel['subject_id']
            ).first()

            target_node = self.db.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.source_id == rel['object_id']
            ).first()

            if not source_node or not target_node:
                continue

            # 检查边是否已存在
            existing = self.db.query(KnowledgeGraphEdge).filter(
                KnowledgeGraphEdge.source_node_id == source_node.node_id,
                KnowledgeGraphEdge.target_node_id == target_node.node_id,
                KnowledgeGraphEdge.edge_type == rel['predicate']
            ).first()

            if existing:
                existing.weight += 0.1
                continue

            # 创建新边
            edge_id = f"edge_{uuid.uuid4().hex[:16]}"

            kg_edge = KnowledgeGraphEdge(
                edge_id=edge_id,
                source_node_id=source_node.node_id,
                target_node_id=target_node.node_id,
                edge_type=rel['predicate'],
                edge_label=rel['predicate'],
                weight=1.0,
                confidence=rel.get('confidence', 0.7),
                is_directed=True,
                source_table='relationships_unified',
                source_id=rel.get('subject_id')
            )

            self.db.add(kg_edge)

            # 更新节点度数
            source_node.out_degree += 1
            source_node.degree += 1
            target_node.in_degree += 1
            target_node.degree += 1

            created_count += 1

        self.db.commit()

        return created_count

    def _count_by_predicate(self, relationships: List[Dict]) -> Dict[str, int]:
        """统计各类型关系数量"""
        predicate_counts = {}
        for rel in relationships:
            predicate = rel['predicate']
            predicate_counts[predicate] = predicate_counts.get(predicate, 0) + 1
        return predicate_counts


# ============================================================
# 便捷函数
# ============================================================

def discover_document_relationships(db: Session, document_id: int) -> Dict[str, Any]:
    """
    发现文档关系的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        发现结果
    """
    service = RelationshipDiscoveryService(db)
    return service.discover_relationships(document_id)
