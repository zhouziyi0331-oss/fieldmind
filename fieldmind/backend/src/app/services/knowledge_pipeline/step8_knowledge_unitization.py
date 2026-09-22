"""
Step 8: 知识单元化服务
Knowledge Unitization Service

功能：
1. 聚合实体、事件、关系、推理
2. 组织为独立的知识单元（事实、规则、模式、洞察）
3. 生成摘要和标题
4. 计算质量评分
5. 生成向量嵌入
6. 保存到 knowledge_units 表
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List, Dict, Any
import uuid
import json

from app.models.unified_models import (
    EntityUnified, EventUnified, RelationshipUnified,
    InferenceResult, KnowledgeUnit
)
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class KnowledgeUnitizationService:
    """知识单元化服务（Step 8）"""

    def __init__(self, db: Session):
        self.db = db

    def create_knowledge_units(self, document_id: int) -> Dict[str, Any]:
        """
        创建知识单元

        Args:
            document_id: 文档 ID

        Returns:
            创建结果
        """
        logger.info(f"📦 Step 8: 开始知识单元化 - 文档 {document_id}")

        try:
            # 获取所有知识组件
            entities = self._get_entities(document_id)
            events = self._get_events(document_id)
            relationships = self._get_relationships(document_id)
            inferences = self._get_inferences(document_id)

            if not any([entities, events, relationships, inferences]):
                logger.warning(f"文档 {document_id} 没有知识组件")
                return {'success': False, 'message': '没有知识组件'}

            knowledge_units = []

            # 1. 创建事实型知识单元（基于实体和关系）
            fact_units = self._create_fact_units(entities, relationships)
            knowledge_units.extend(fact_units)

            # 2. 创建规则型知识单元（基于推理）
            rule_units = self._create_rule_units(inferences)
            knowledge_units.extend(rule_units)

            # 3. 创建模式型知识单元（基于事件序列）
            pattern_units = self._create_pattern_units(events, relationships)
            knowledge_units.extend(pattern_units)

            # 4. 创建洞察型知识单元（基于归纳推理）
            insight_units = self._create_insight_units(inferences)
            knowledge_units.extend(insight_units)

            # 计算质量评分
            knowledge_units = self._calculate_quality_scores(knowledge_units)

            # 生成向量嵌入（可选）
            knowledge_units = self._generate_embeddings(knowledge_units)

            # 保存到数据库
            saved_count = self._save_knowledge_units(document_id, knowledge_units)

            result = {
                'success': True,
                'document_id': document_id,
                'units_created': saved_count,
                'unit_types': self._count_by_type(knowledge_units),
                'facts': len([u for u in knowledge_units if u['unit_type'] == 'fact']),
                'rules': len([u for u in knowledge_units if u['unit_type'] == 'rule']),
                'patterns': len([u for u in knowledge_units if u['unit_type'] == 'pattern']),
                'insights': len([u for u in knowledge_units if u['unit_type'] == 'insight']),
                'avg_quality_score': sum(u['quality_score'] for u in knowledge_units) / len(knowledge_units) if knowledge_units else 0
            }

            logger.info(
                f"✅ Step 8 完成: 创建了 {saved_count} 个知识单元, "
                f"事实:{result['facts']}, 规则:{result['rules']}, "
                f"模式:{result['patterns']}, 洞察:{result['insights']}"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.KNOWLEDGE_UNITS_CREATED,
                payload={
                    'step': 8,
                    'step_name': 'knowledge_unitization',
                    'document_id': document_id,
                    'result': result
                },
                publisher='KnowledgeUnitizationService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 8 失败: {e}", exc_info=True)
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
                'time': e.normalized_time_start
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
                'predicate': r.predicate,
                'object_id': r.object_id
            }
            for r in relationships
        ]

    def _get_inferences(self, document_id: int) -> List[Dict]:
        """获取推理"""
        inferences = self.db.query(InferenceResult).filter(
            InferenceResult.document_id == document_id
        ).all()

        return [
            {
                'id': i.inference_id,
                'type': i.inference_type,
                'conclusion': i.conclusion_description,
                'confidence': i.confidence
            }
            for i in inferences
        ]

    def _create_fact_units(
        self,
        entities: List[Dict],
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        创建事实型知识单元

        事实：单个陈述，如 "王大爷是布依族山歌传承人"
        """
        fact_units = []

        # 从关系创建事实
        for rel in relationships:
            # 查找实体名称
            subject_name = next((e['name'] for e in entities if e['id'] == rel['subject_id']), rel['subject_id'])
            object_name = next((e['name'] for e in entities if e['id'] == rel['object_id']), rel['object_id'])

            fact_units.append({
                'unit_type': 'fact',
                'title': f"{subject_name}{rel['predicate']}{object_name}",
                'summary': f"{subject_name} {rel['predicate']} {object_name}",
                'full_content': {
                    'subject': subject_name,
                    'predicate': rel['predicate'],
                    'object': object_name,
                    'subject_id': rel['subject_id'],
                    'object_id': rel['object_id']
                },
                'entities': [rel['subject_id'], rel['object_id']],
                'relationships': [rel['id']]
            })

        return fact_units

    def _create_rule_units(self, inferences: List[Dict]) -> List[Dict]:
        """
        创建规则型知识单元

        规则：通用模式，如 "传承人通过口传身授传播山歌"
        """
        rule_units = []

        # 从演绎推理创建规则
        for inference in inferences:
            if inference['type'] == 'deductive':
                rule_units.append({
                    'unit_type': 'rule',
                    'title': f"推理规则: {inference['conclusion'][:30]}",
                    'summary': inference['conclusion'],
                    'full_content': {
                        'inference_id': inference['id'],
                        'conclusion': inference['conclusion'],
                        'confidence': inference['confidence']
                    },
                    'inferences': [inference['id']]
                })

        return rule_units

    def _create_pattern_units(
        self,
        events: List[Dict],
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        创建模式型知识单元

        模式：重复出现的结构，如 "节庆活动通常包括表演、聚餐、祭祀"
        """
        pattern_units = []

        # 简化版本：如果有多个相同类型的事件，识别为模式
        event_types = {}
        for event in events:
            event_type = event['type']
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(event)

        for event_type, event_list in event_types.items():
            if len(event_list) >= 2:
                pattern_units.append({
                    'unit_type': 'pattern',
                    'title': f"{event_type}事件模式（{len(event_list)}次）",
                    'summary': f"文档中出现了{len(event_list)}次{event_type}事件",
                    'full_content': {
                        'event_type': event_type,
                        'count': len(event_list),
                        'events': [e['id'] for e in event_list]
                    },
                    'events': [e['id'] for e in event_list]
                })

        return pattern_units

    def _create_insight_units(self, inferences: List[Dict]) -> List[Dict]:
        """
        创建洞察型知识单元

        洞察：深层发现，如 "非遗传承面临后继无人的困境"
        """
        insight_units = []

        # 从归纳推理和溯因推理创建洞察
        for inference in inferences:
            if inference['type'] in ['inductive', 'abductive']:
                insight_units.append({
                    'unit_type': 'insight',
                    'title': f"洞察: {inference['conclusion'][:30]}",
                    'summary': inference['conclusion'],
                    'full_content': {
                        'inference_id': inference['id'],
                        'inference_type': inference['type'],
                        'conclusion': inference['conclusion'],
                        'confidence': inference['confidence']
                    },
                    'inferences': [inference['id']]
                })

        return insight_units

    def _calculate_quality_scores(self, knowledge_units: List[Dict]) -> List[Dict]:
        """
        计算知识单元的质量评分

        评分维度：
        1. 完整性（是否包含所有必要信息）
        2. 可靠性（基于置信度）
        3. 可用性（是否易于理解和使用）
        """
        for unit in knowledge_units:
            # 完整性评分
            completeness = 0.5
            if unit.get('title') and unit.get('summary'):
                completeness += 0.2
            if unit.get('full_content'):
                completeness += 0.2
            if unit.get('entities') or unit.get('events') or unit.get('relationships'):
                completeness += 0.1

            # 可靠性评分（基于组件的置信度）
            reliability = 0.7  # 默认值

            # 可用性评分（基于摘要长度和结构）
            usability = 0.6
            if unit.get('summary') and 10 <= len(unit['summary']) <= 200:
                usability += 0.2

            # 综合质量评分
            quality_score = (completeness * 0.4 + reliability * 0.4 + usability * 0.2)

            unit['quality_score'] = round(quality_score, 2)
            unit['completeness_score'] = round(completeness, 2)
            unit['reliability_score'] = round(reliability, 2)

        return knowledge_units

    def _generate_embeddings(self, knowledge_units: List[Dict]) -> List[Dict]:
        """
        生成向量嵌入（可选）

        如果有嵌入模型，可以在这里生成
        """
        # TODO: 集成向量嵌入模型（如 sentence-transformers）
        # for unit in knowledge_units:
        #     text = unit['summary']
        #     embedding = model.encode(text)
        #     unit['embedding'] = embedding.tobytes()

        return knowledge_units

    def _save_knowledge_units(self, document_id: int, knowledge_units: List[Dict]) -> int:
        """保存知识单元到数据库"""
        saved_count = 0

        # 获取项目 ID
        from app.models.project import ProjectDocument
        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            return 0

        for unit in knowledge_units:
            unit_id = f"ku_{uuid.uuid4().hex[:16]}"

            db_unit = KnowledgeUnit(
                unit_id=unit_id,
                document_id=document_id,
                project_id=doc.project_id,
                unit_type=unit['unit_type'],
                title=unit.get('title'),
                summary=unit['summary'],
                full_content=json.dumps(unit.get('full_content', {})),
                entities=json.dumps(unit.get('entities', [])),
                events=json.dumps(unit.get('events', [])),
                relationships=json.dumps(unit.get('relationships', [])),
                inferences=json.dumps(unit.get('inferences', [])),
                quality_score=unit.get('quality_score', 0.5),
                completeness_score=unit.get('completeness_score', 0.5),
                reliability_score=unit.get('reliability_score', 0.5),
                embedding=unit.get('embedding')
            )

            self.db.add(db_unit)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _count_by_type(self, knowledge_units: List[Dict]) -> Dict[str, int]:
        """统计各类型知识单元数量"""
        type_counts = {}
        for unit in knowledge_units:
            unit_type = unit['unit_type']
            type_counts[unit_type] = type_counts.get(unit_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def create_document_knowledge_units(db: Session, document_id: int) -> Dict[str, Any]:
    """
    创建文档知识单元的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        创建结果
    """
    service = KnowledgeUnitizationService(db)
    return service.create_knowledge_units(document_id)
