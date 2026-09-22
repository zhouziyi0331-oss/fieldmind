"""
Step 6: 本体构建服务
Ontology Construction Service

功能：
1. 从实体和事件中提取概念
2. 构建概念层次（IS-A 关系）
3. 定义概念属性和约束
4. 实例化概念
5. 保存到 ontology_concepts 表
6. 更新知识图谱
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any, Set
import uuid
import json
from collections import defaultdict

from app.models.unified_models import (
    EntityUnified, EventUnified, OntologyConcept,
    KnowledgeGraphNode
)
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class OntologyConstructionService:
    """本体构建服务（Step 6）"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def build_ontology(self, project_id: int, document_id: int = None) -> Dict[str, Any]:
        """
        构建本体

        Args:
            project_id: 项目 ID
            document_id: 文档 ID（可选，如果提供则只处理该文档）

        Returns:
            构建结果
        """
        logger.info(f"🏛️ Step 6: 开始本体构建 - 项目 {project_id}")

        try:
            # 获取实体和事件
            entities = self._get_entities(project_id, document_id)
            events = self._get_events(project_id, document_id)

            if not entities and not events:
                logger.warning(f"项目 {project_id} 没有实体和事件")
                return {'success': False, 'message': '没有实体和事件'}

            # 提取概念
            concepts = self._extract_concepts(entities, events)

            # 构建层次
            concepts_with_hierarchy = self._build_hierarchy(concepts)

            # 定义属性
            concepts_with_properties = self._define_properties(concepts_with_hierarchy, entities, events)

            # 实例化概念
            concepts_with_instances = self._instantiate_concepts(concepts_with_properties, entities, events)

            # 保存到数据库
            saved_count = self._save_concepts(project_id, concepts_with_instances)

            # 更新知识图谱
            kg_updates = self._update_kg(concepts_with_instances)

            result = {
                'success': True,
                'project_id': project_id,
                'document_id': document_id,
                'concepts_created': saved_count,
                'concept_types': self._count_by_type(concepts_with_instances),
                'max_hierarchy_level': max([c['hierarchy_level'] for c in concepts_with_instances]) if concepts_with_instances else 0,
                'kg_nodes_updated': kg_updates
            }

            logger.info(
                f"✅ Step 6 完成: 创建了 {saved_count} 个概念, "
                f"最大层级 {result['max_hierarchy_level']}"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.ONTOLOGY_BUILT,
                payload={
                    'step': 6,
                    'step_name': 'ontology_construction',
                    'project_id': project_id,
                    'document_id': document_id,
                    'result': result
                },
                publisher='OntologyConstructionService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 6 失败: {e}", exc_info=True)
            raise

    def _get_entities(self, project_id: int, document_id: int = None) -> List[Dict]:
        """获取实体"""
        query = self.db.query(EntityUnified)

        if document_id:
            query = query.filter(EntityUnified.document_id == document_id)
        else:
            # 获取项目下所有文档的实体
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            query = query.filter(EntityUnified.document_id.in_(doc_ids))

        entities = query.all()

        return [
            {
                'id': e.entity_id,
                'name': e.entity_name,
                'type': e.entity_type,
                'category': e.entity_category,
                'properties': json.loads(e.properties) if e.properties else {}
            }
            for e in entities
        ]

    def _get_events(self, project_id: int, document_id: int = None) -> List[Dict]:
        """获取事件"""
        query = self.db.query(EventUnified)

        if document_id:
            query = query.filter(EventUnified.document_id == document_id)
        else:
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            query = query.filter(EventUnified.document_id.in_(doc_ids))

        events = query.all()

        return [
            {
                'id': e.event_id,
                'name': e.event_name,
                'type': e.event_type
            }
            for e in events
        ]

    def _extract_concepts(self, entities: List[Dict], events: List[Dict]) -> List[Dict]:
        """
        从实体和事件中提取概念

        策略：
        1. 实体类型 -> 概念类
        2. 事件类型 -> 概念类
        3. 基于频次聚合相似实体
        """
        concepts = []

        # 从实体类型提取概念
        entity_type_counts = defaultdict(list)
        for entity in entities:
            entity_type = entity['type']
            entity_type_counts[entity_type].append(entity)

        for entity_type, entity_list in entity_type_counts.items():
            concepts.append({
                'concept_name': self._normalize_concept_name(entity_type),
                'concept_type': 'class',
                'definition': f"表示{entity_type}的概念类",
                'instances': [e['id'] for e in entity_list],
                'instance_count': len(entity_list),
                'source': 'entity_type'
            })

        # 从事件类型提取概念
        event_type_counts = defaultdict(list)
        for event in events:
            event_type = event['type']
            event_type_counts[event_type].append(event)

        for event_type, event_list in event_type_counts.items():
            concepts.append({
                'concept_name': self._normalize_concept_name(event_type),
                'concept_type': 'class',
                'definition': f"表示{event_type}的概念类",
                'instances': [e['id'] for e in event_list],
                'instance_count': len(event_list),
                'source': 'event_type'
            })

        return concepts

    def _normalize_concept_name(self, name: str) -> str:
        """规范化概念名称"""
        # 映射表
        name_map = {
            'person': '人物',
            'location': '地点',
            'organization': '组织',
            'concept': '概念',
            'action': '动作',
            'occurrence': '事件',
            'state_change': '状态变化'
        }

        return name_map.get(name, name)

    def _build_hierarchy(self, concepts: List[Dict]) -> List[Dict]:
        """
        构建概念层次

        策略：
        1. 基于概念名称的包含关系
        2. 基于实例数量（实例多的概念层级更高）
        3. 预定义的上下位关系
        """
        # 预定义层次
        hierarchy_rules = {
            '实体': {'parent': None, 'level': 0},
            '人物': {'parent': '实体', 'level': 1},
            '地点': {'parent': '实体', 'level': 1},
            '组织': {'parent': '实体', 'level': 1},
            '概念': {'parent': '实体', 'level': 1},
            '事件': {'parent': None, 'level': 0},
            '动作': {'parent': '事件', 'level': 1},
            '状态变化': {'parent': '事件', 'level': 1},
        }

        # 应用规则
        for concept in concepts:
            name = concept['concept_name']
            if name in hierarchy_rules:
                concept['parent_concept'] = hierarchy_rules[name]['parent']
                concept['hierarchy_level'] = hierarchy_rules[name]['level']
            else:
                concept['parent_concept'] = None
                concept['hierarchy_level'] = 1

        # 如果没有父概念，根据来源设置
        for concept in concepts:
            if concept['parent_concept'] is None:
                if concept['source'] == 'entity_type':
                    concept['parent_concept'] = '实体'
                    concept['hierarchy_level'] = 1
                elif concept['source'] == 'event_type':
                    concept['parent_concept'] = '事件'
                    concept['hierarchy_level'] = 1

        return concepts

    def _define_properties(
        self,
        concepts: List[Dict],
        entities: List[Dict],
        events: List[Dict]
    ) -> List[Dict]:
        """
        定义概念的属性

        策略：
        1. 从实例中提取共同属性
        2. 统计属性的值域
        """
        for concept in concepts:
            properties = {}
            constraints = {}

            # 获取该概念的所有实例
            instance_ids = concept.get('instances', [])

            if concept['source'] == 'entity_type':
                # 从实体中提取属性
                concept_entities = [e for e in entities if e['id'] in instance_ids]

                # 统计属性
                for entity in concept_entities:
                    for prop_name, prop_value in entity.get('properties', {}).items():
                        if prop_name not in properties:
                            properties[prop_name] = {
                                'type': type(prop_value).__name__,
                                'values': []
                            }
                        properties[prop_name]['values'].append(prop_value)

            elif concept['source'] == 'event_type':
                # 事件的属性（时间、地点等）
                properties['temporal'] = {'type': 'datetime', 'values': []}
                properties['spatial'] = {'type': 'location', 'values': []}

            concept['properties'] = properties
            concept['constraints'] = constraints

        return concepts

    def _instantiate_concepts(
        self,
        concepts: List[Dict],
        entities: List[Dict],
        events: List[Dict]
    ) -> List[Dict]:
        """
        实例化概念

        已在 _extract_concepts 中完成，这里只是补充信息
        """
        return concepts

    def _save_concepts(self, project_id: int, concepts: List[Dict]) -> int:
        """保存概念到数据库"""
        saved_count = 0

        for concept in concepts:
            concept_id = f"concept_{uuid.uuid4().hex[:16]}"

            # 查找父概念 ID
            parent_concept_id = None
            if concept.get('parent_concept'):
                parent = self.db.query(OntologyConcept).filter(
                    OntologyConcept.project_id == project_id,
                    OntologyConcept.concept_name == concept['parent_concept']
                ).first()
                if parent:
                    parent_concept_id = parent.concept_id

            db_concept = OntologyConcept(
                concept_id=concept_id,
                project_id=project_id,
                concept_name=concept['concept_name'],
                concept_type=concept['concept_type'],
                definition=concept.get('definition'),
                parent_concept_id=parent_concept_id,
                hierarchy_level=concept.get('hierarchy_level', 0),
                properties=json.dumps(concept.get('properties', {})),
                constraints=json.dumps(concept.get('constraints', {})),
                instances=json.dumps(concept.get('instances', [])),
                instance_count=concept.get('instance_count', 0),
                source_documents=json.dumps([])
            )

            self.db.add(db_concept)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _update_kg(self, concepts: List[Dict]) -> int:
        """更新知识图谱（为概念创建节点）"""
        updated_count = 0

        for concept in concepts:
            # 检查节点是否已存在
            existing = self.db.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.source_table == 'ontology_concepts',
                KnowledgeGraphNode.label == concept['concept_name']
            ).first()

            if existing:
                continue

            # 创建新节点
            node_id = f"node_{uuid.uuid4().hex[:16]}"

            kg_node = KnowledgeGraphNode(
                node_id=node_id,
                node_type='concept',
                source_table='ontology_concepts',
                source_id=concept['concept_name'],
                label=concept['concept_name'],
                display_name=concept['concept_name'],
                properties=json.dumps({
                    'type': concept['concept_type'],
                    'level': concept.get('hierarchy_level', 0),
                    'instance_count': concept.get('instance_count', 0)
                }),
                importance_score=0.6
            )

            self.db.add(kg_node)
            updated_count += 1

        self.db.commit()

        return updated_count

    def _count_by_type(self, concepts: List[Dict]) -> Dict[str, int]:
        """统计各类型概念数量"""
        type_counts = {}
        for concept in concepts:
            concept_type = concept['concept_type']
            type_counts[concept_type] = type_counts.get(concept_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def build_document_ontology(db: Session, project_id: int, document_id: int = None) -> Dict[str, Any]:
    """
    构建文档本体的便捷函数

    Args:
        db: 数据库会话
        project_id: 项目 ID
        document_id: 文档 ID（可选）

    Returns:
        构建结果
    """
    service = OntologyConstructionService(db)
    return service.build_ontology(project_id, document_id)
