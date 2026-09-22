"""
Step 7: 逻辑推理服务
Logical Inference Service

功能：
1. 演绎推理（基于规则）
2. 归纳推理（发现模式）
3. 溯因推理（推测原因）
4. 类比推理
5. 保存到 inference_results 表
6. 支持验证和反馈
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List, Dict, Any, Tuple
import uuid
import json

from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    InferenceResult
)
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class LogicalInferenceService:
    """逻辑推理服务（Step 7）"""

    def __init__(self, db: Session):
        self.db = db

    def perform_inference(self, document_id: int) -> Dict[str, Any]:
        """
        执行逻辑推理

        Args:
            document_id: 文档 ID

        Returns:
            推理结果
        """
        logger.info(f"🧠 Step 7: 开始逻辑推理 - 文档 {document_id}")

        try:
            # 获取知识基础
            entities = self._get_entities(document_id)
            events = self._get_events(document_id)
            relationships = self._get_relationships(document_id)

            if not entities and not events and not relationships:
                logger.warning(f"文档 {document_id} 没有知识基础")
                return {'success': False, 'message': '没有知识基础'}

            inferences = []

            # 1. 演绎推理
            deductive = self._deductive_inference(entities, events, relationships)
            inferences.extend(deductive)

            # 2. 归纳推理
            inductive = self._inductive_inference(entities, events, relationships)
            inferences.extend(inductive)

            # 3. 溯因推理
            abductive = self._abductive_inference(entities, events, relationships)
            inferences.extend(abductive)

            # 4. 类比推理
            analogical = self._analogical_inference(entities, events)
            inferences.extend(analogical)

            # 保存到数据库
            saved_count = self._save_inferences(document_id, inferences)

            result = {
                'success': True,
                'document_id': document_id,
                'inferences_created': saved_count,
                'inference_types': self._count_by_type(inferences),
                'deductive': len([i for i in inferences if i['inference_type'] == 'deductive']),
                'inductive': len([i for i in inferences if i['inference_type'] == 'inductive']),
                'abductive': len([i for i in inferences if i['inference_type'] == 'abductive']),
                'analogical': len([i for i in inferences if i['inference_type'] == 'analogical'])
            }

            logger.info(
                f"✅ Step 7 完成: 生成了 {saved_count} 个推理, "
                f"演绎:{result['deductive']}, 归纳:{result['inductive']}, "
                f"溯因:{result['abductive']}, 类比:{result['analogical']}"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.INFERENCE_COMPLETED,
                payload={
                    'step': 7,
                    'step_name': 'logical_inference',
                    'document_id': document_id,
                    'result': result
                },
                publisher='LogicalInferenceService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 7 失败: {e}", exc_info=True)
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
                'type': e.entity_type
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
                'time': e.normalized_time_start,
                'location': e.normalized_location,
                'participants': json.loads(e.participants) if e.participants else []
            }
            for e in events
        ]

    def _get_relationships(self, document_id: int) -> List[Dict]:
        """获取关系"""
        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == document_id
        ).all()

        return [
            {
                'id': r.relationship_id,
                'subject_id': r.subject_id,
                'subject_type': r.subject_type,
                'predicate': r.predicate,
                'object_id': r.object_id,
                'object_type': r.object_type
            }
            for r in relationships
        ]

    def _deductive_inference(
        self,
        entities: List[Dict],
        events: List[Dict],
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        演绎推理（基于规则）

        规则示例：
        1. 如果 A 参与 B，B 发生于 C，则 A 位于 C
        2. 如果 A 是 B 的一部分，B 有属性 X，则 A 也有属性 X
        """
        inferences = []

        # 规则1: 实体-事件-地点传递
        # 如果实体参与了事件，事件发生在某地，则实体在某地
        for rel in relationships:
            if rel['predicate'] in ['参与', '发起', '经历']:
                # 找到事件
                event = next((e for e in events if e['id'] == rel['object_id']), None)
                if event and event.get('location'):
                    # 推理：实体位于该地点
                    inferences.append({
                        'inference_type': 'deductive',
                        'inference_rule': '实体-事件-地点传递',
                        'premises': [
                            {'type': 'relationship', 'id': rel['id'], 'description': f"{rel['subject_id']} {rel['predicate']} {rel['object_id']}"},
                            {'type': 'fact', 'description': f"{event['name']} 发生于 {event['location']}"}
                        ],
                        'conclusion_type': 'relationship',
                        'conclusion_description': f"{rel['subject_id']} 位于 {event['location']}",
                        'confidence': 0.7,
                        'explanation': f"因为实体参与了事件，事件发生在该地点，所以实体在该地点"
                    })

        # 规则2: 时间传递
        # 如果事件 A 早于事件 B，事件 B 早于事件 C，则事件 A 早于事件 C
        time_ordered_events = [e for e in events if e.get('time')]
        time_ordered_events.sort(key=lambda e: e.get('time', ''))

        for i in range(len(time_ordered_events) - 2):
            event_a = time_ordered_events[i]
            event_b = time_ordered_events[i + 1]
            event_c = time_ordered_events[i + 2]

            inferences.append({
                'inference_type': 'deductive',
                'inference_rule': '时间传递性',
                'premises': [
                    {'type': 'fact', 'description': f"{event_a['name']} 早于 {event_b['name']}"},
                    {'type': 'fact', 'description': f"{event_b['name']} 早于 {event_c['name']}"}
                ],
                'conclusion_type': 'relationship',
                'conclusion_description': f"{event_a['name']} 早于 {event_c['name']}",
                'confidence': 0.9,
                'explanation': '基于时间的传递性'
            })

        return inferences

    def _inductive_inference(
        self,
        entities: List[Dict],
        events: List[Dict],
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        归纳推理（发现模式）

        从多个具体案例中归纳出一般规律
        """
        inferences = []

        # 模式1: 如果多个同类型实体都有相同的关系，归纳出规律
        entity_type_relations = {}
        for rel in relationships:
            # 查找实体类型
            entity = next((e for e in entities if e['id'] == rel['subject_id']), None)
            if entity:
                entity_type = entity['type']
                if entity_type not in entity_type_relations:
                    entity_type_relations[entity_type] = []
                entity_type_relations[entity_type].append(rel['predicate'])

        # 检查是否有共同模式
        for entity_type, predicates in entity_type_relations.items():
            # 统计谓词频率
            from collections import Counter
            predicate_counts = Counter(predicates)

            # 如果某个谓词出现3次以上，归纳为模式
            for predicate, count in predicate_counts.items():
                if count >= 3:
                    inferences.append({
                        'inference_type': 'inductive',
                        'inference_rule': '频繁模式发现',
                        'premises': [
                            {'type': 'pattern', 'description': f"{entity_type} 类实体经常 {predicate}（出现{count}次）"}
                        ],
                        'conclusion_type': 'pattern',
                        'conclusion_description': f"{entity_type} 通常会 {predicate}",
                        'confidence': min(0.5 + count * 0.1, 0.9),
                        'explanation': f"观察到{count}个{entity_type}都有{predicate}关系，归纳出一般规律"
                    })

        return inferences

    def _abductive_inference(
        self,
        entities: List[Dict],
        events: List[Dict],
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        溯因推理（推测原因）

        给定结果，推测可能的原因
        """
        inferences = []

        # 模式：如果观察到某个事件，推测可能的原因
        for event in events:
            # 查找参与者
            participants = event.get('participants', [])

            if participants:
                # 推测：可能是参与者的行为导致了该事件
                for participant in participants:
                    if participant.get('role') == 'agent':
                        inferences.append({
                            'inference_type': 'abductive',
                            'inference_rule': '原因推测',
                            'premises': [
                                {'type': 'observation', 'description': f"观察到事件: {event['name']}"},
                                {'type': 'fact', 'description': f"{participant['entity_name']} 是施事者"}
                            ],
                            'conclusion_type': 'hypothesis',
                            'conclusion_description': f"{participant['entity_name']} 的行为可能导致了 {event['name']}",
                            'confidence': 0.5,
                            'explanation': '基于施事者通常是事件原因的假设'
                        })

        return inferences

    def _analogical_inference(
        self,
        entities: List[Dict],
        events: List[Dict]
    ) -> List[Dict]:
        """
        类比推理

        基于相似情况进行推理
        """
        inferences = []

        # 简化版本：如果有相似的事件，推测可能有相似的结果
        event_types = {}
        for event in events:
            event_type = event['type']
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(event)

        # 如果同一类型的事件有多个，可以类比
        for event_type, event_list in event_types.items():
            if len(event_list) >= 2:
                inferences.append({
                    'inference_type': 'analogical',
                    'inference_rule': '事件类比',
                    'premises': [
                        {'type': 'analogy', 'description': f"有{len(event_list)}个相似的{event_type}事件"}
                    ],
                    'conclusion_type': 'hypothesis',
                    'conclusion_description': f"这些{event_type}事件可能有相似的模式和结果",
                    'confidence': 0.6,
                    'explanation': '基于相似事件通常有相似模式的假设'
                })

        return inferences

    def _save_inferences(self, document_id: int, inferences: List[Dict]) -> int:
        """保存推理结果到数据库"""
        saved_count = 0

        for inference in inferences:
            inference_id = f"inference_{uuid.uuid4().hex[:16]}"

            # 获取项目 ID
            from app.models.project import ProjectDocument
            doc = self.db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc:
                continue

            db_inference = InferenceResult(
                inference_id=inference_id,
                document_id=document_id,
                project_id=doc.project_id,
                inference_type=inference['inference_type'],
                inference_rule=inference.get('inference_rule'),
                premises=json.dumps(inference.get('premises', [])),
                conclusion_type=inference['conclusion_type'],
                conclusion_description=inference['conclusion_description'],
                confidence=inference.get('confidence', 0.5),
                explanation=inference.get('explanation'),
                reasoning_chain=json.dumps(inference.get('premises', [])),
                validation_status='pending'
            )

            self.db.add(db_inference)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _count_by_type(self, inferences: List[Dict]) -> Dict[str, int]:
        """统计各类型推理数量"""
        type_counts = {}
        for inference in inferences:
            inference_type = inference['inference_type']
            type_counts[inference_type] = type_counts.get(inference_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def perform_document_inference(db: Session, document_id: int) -> Dict[str, Any]:
    """
    执行文档推理的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        推理结果
    """
    service = LogicalInferenceService(db)
    return service.perform_inference(document_id)
