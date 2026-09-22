"""
Step 4: 事件提取服务
Event Extraction Service

功能：
1. 从文本中提取事件（动作、状态变化、发生的事情）
2. 识别时间信息（时间表达式提取 + 规范化）
3. 识别空间信息（地点提取）
4. 识别参与者（关联实体）
5. 识别因果关系
6. 保存到 events_unified 表
7. 创建知识图谱节点
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime

from app.models.project import DocumentChunk
from app.models.unified_models import EventUnified, EntityUnified, KnowledgeGraphNode
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class EventExtractionService:
    """事件提取服务（Step 4）"""

    def __init__(self, db: Session):
        self.db = db

    def extract_events(self, document_id: int) -> Dict[str, Any]:
        """
        提取文档中的所有事件

        Args:
            document_id: 文档 ID

        Returns:
            提取结果
        """
        logger.info(f"⏰ Step 4: 开始事件提取 - 文档 {document_id}")

        try:
            # 获取所有 chunks
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            if not chunks:
                logger.warning(f"文档 {document_id} 没有 chunks")
                return {'success': False, 'message': '文档没有 chunks'}

            # 获取已提取的实体（用于关联参与者）
            entities = self._get_entities(document_id)

            # 提取事件
            events = self._extract_from_chunks(document_id, chunks, entities)

            # 识别因果关系
            events_with_causality = self._identify_causality(events)

            # 保存到数据库
            saved_count = self._save_events(document_id, events_with_causality)

            # 创建知识图谱节点
            kg_nodes_count = self._create_kg_nodes(events_with_causality)

            result = {
                'success': True,
                'document_id': document_id,
                'events_extracted': saved_count,
                'kg_nodes_created': kg_nodes_count,
                'event_types': self._count_by_type(events_with_causality),
                'with_time': sum(1 for e in events_with_causality if e.get('normalized_time_start')),
                'with_location': sum(1 for e in events_with_causality if e.get('normalized_location'))
            }

            logger.info(
                f"✅ Step 4 完成: 提取了 {saved_count} 个事件, "
                f"创建 {kg_nodes_count} 个知识图谱节点"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.EVENTS_EXTRACTED,
                payload={
                    'step': 4,
                    'step_name': 'event_extraction',
                    'document_id': document_id,
                    'result': result
                },
                publisher='EventExtractionService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 4 失败: {e}", exc_info=True)
            raise

    def _get_entities(self, document_id: int) -> List[Dict]:
        """获取已提取的实体"""
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

    def _extract_from_chunks(
        self,
        document_id: int,
        chunks: List[DocumentChunk],
        entities: List[Dict]
    ) -> List[Dict]:
        """从所有 chunks 提取事件"""
        all_events = []

        for chunk in chunks:
            text = chunk.cleaned_text or chunk.text
            if not text:
                continue

            # 提取事件
            chunk_events = self._extract_by_patterns(text)

            # 为每个事件添加信息
            for event in chunk_events:
                event['chunk_id'] = chunk.id
                event['document_id'] = document_id

                # 提取时间信息
                temporal_info = self._extract_temporal(text, event.get('event_text', ''))
                event.update(temporal_info)

                # 提取空间信息
                spatial_info = self._extract_spatial(text, event.get('event_text', ''))
                event.update(spatial_info)

                # 识别参与者
                participants = self._identify_participants(event, entities, text)
                event['participants'] = participants

            all_events.extend(chunk_events)

        return all_events

    def _extract_by_patterns(self, text: str) -> List[Dict]:
        """
        使用模式提取事件

        事件模式：
        1. 动词 + 宾语（如：举办活动、进行调查）
        2. 主语 + 动词（如：人们聚集、村民祭祀）
        3. 状态变化（如：变得、成为、转变为）
        """
        events = []

        # 模式1: 动作事件（动词 + 对象）
        action_patterns = [
            r'(举办|进行|开展|实施|执行|完成|建立|创建|发起|组织)([一-龥]{2,10})',
            r'(参加|参与|出席|加入|离开|前往|到达|返回)([一-龥]{2,10})',
            r'(发现|发明|创造|制作|生产|种植|采集|收获)([一-龥]{2,10})',
            r'(说|讲|唱|演|表演|展示|展现)([一-龥]{2,10})',
        ]

        for pattern in action_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                events.append({
                    'event_type': 'action',
                    'event_name': match.group(0),
                    'event_text': match.group(0),
                    'description': f"{match.group(1)}{match.group(2)}",
                    'confidence': 0.7
                })

        # 模式2: 发生事件
        occurrence_patterns = [
            r'发生了?([一-龥]{2,10})',
            r'出现了?([一-龥]{2,10})',
            r'产生了?([一-龥]{2,10})',
        ]

        for pattern in occurrence_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                events.append({
                    'event_type': 'occurrence',
                    'event_name': match.group(1),
                    'event_text': match.group(0),
                    'description': f"发生{match.group(1)}",
                    'confidence': 0.6
                })

        # 模式3: 状态变化
        state_change_patterns = [
            r'([一-龥]{2,8})(变得|成为|转变为|变成)([一-龥]{2,8})',
        ]

        for pattern in state_change_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                events.append({
                    'event_type': 'state_change',
                    'event_name': f"{match.group(1)}{match.group(2)}{match.group(3)}",
                    'event_text': match.group(0),
                    'description': f"{match.group(1)}的状态变化",
                    'confidence': 0.7
                })

        return events

    def _extract_temporal(self, text: str, event_text: str) -> Dict:
        """
        提取时间信息

        识别时间表达式并规范化
        """
        temporal_info = {
            'temporal_expression': None,
            'normalized_time_start': None,
            'normalized_time_end': None,
            'time_confidence': 0.0
        }

        # 时间模式
        time_patterns = [
            # 具体年份
            (r'(\d{4})年', lambda m: (f"{m.group(1)}-01-01", 0.9)),
            # 年月
            (r'(\d{4})年(\d{1,2})月', lambda m: (f"{m.group(1)}-{int(m.group(2)):02d}-01", 0.95)),
            # 年月日
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: (f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", 1.0)),
            # 相对时间
            (r'(今年|去年|前年|明年|后年)', lambda m: (None, 0.5)),
            (r'(春天|夏天|秋天|冬天)', lambda m: (None, 0.4)),
            (r'(早上|上午|中午|下午|晚上|夜里)', lambda m: (None, 0.3)),
        ]

        # 在事件文本附近查找时间
        context = text[max(0, text.find(event_text)-100):text.find(event_text)+100] if event_text in text else text[:200]

        for pattern, normalizer in time_patterns:
            match = re.search(pattern, context)
            if match:
                temporal_info['temporal_expression'] = match.group(0)
                normalized, confidence = normalizer(match)
                if normalized:
                    temporal_info['normalized_time_start'] = normalized
                    temporal_info['time_confidence'] = confidence
                break

        return temporal_info

    def _extract_spatial(self, text: str, event_text: str) -> Dict:
        """
        提取空间信息

        识别地点表达式
        """
        spatial_info = {
            'spatial_expression': None,
            'normalized_location': None,
            'location_confidence': 0.0
        }

        # 地点模式
        location_patterns = [
            r'在([一-龥]{2,10}(?:省|市|县|区|镇|乡|村))',
            r'位于([一-龥]{2,10})',
            r'来自([一-龥]{2,10})',
            r'前往([一-龥]{2,10})',
        ]

        # 在事件文本附近查找地点
        context = text[max(0, text.find(event_text)-100):text.find(event_text)+100] if event_text in text else text[:200]

        for pattern in location_patterns:
            match = re.search(pattern, context)
            if match:
                spatial_info['spatial_expression'] = match.group(0)
                spatial_info['normalized_location'] = match.group(1)
                spatial_info['location_confidence'] = 0.8
                break

        return spatial_info

    def _identify_participants(
        self,
        event: Dict,
        entities: List[Dict],
        text: str
    ) -> List[Dict]:
        """
        识别事件参与者

        策略：
        1. 在事件文本附近查找实体
        2. 根据语义推断角色（agent/patient/instrument）
        """
        participants = []

        event_text = event.get('event_text', '')
        if not event_text or event_text not in text:
            return participants

        # 获取事件上下文（前后 50 字）
        event_pos = text.find(event_text)
        context_start = max(0, event_pos - 50)
        context_end = min(len(text), event_pos + len(event_text) + 50)
        context = text[context_start:context_end]

        # 查找上下文中出现的实体
        for entity in entities:
            if entity['name'] in context:
                # 推断角色（简化版本）
                role = 'agent'  # 默认为施事

                # 如果实体在动词前，可能是施事
                # 如果实体在动词后，可能是受事
                if context.find(entity['name']) < context.find(event_text):
                    role = 'agent'
                else:
                    role = 'patient'

                participants.append({
                    'entity_id': entity['id'],
                    'entity_name': entity['name'],
                    'role': role
                })

        return participants

    def _identify_causality(self, events: List[Dict]) -> List[Dict]:
        """
        识别事件间的因果关系

        策略：
        1. 查找因果标记词（因为、所以、导致、引起）
        2. 时间顺序推断
        """
        # 简化版本：只标记相邻事件的可能因果关系
        for i, event in enumerate(events):
            event['causes'] = []
            event['effects'] = []

            # 检查是否有明显的因果标记
            description = event.get('description', '')

            if any(marker in description for marker in ['因为', '由于', '因']):
                # 前一个事件可能是原因
                if i > 0:
                    event['causes'] = [events[i-1].get('event_name')]

            if any(marker in description for marker in ['所以', '因此', '导致', '引起']):
                # 后一个事件可能是结果
                if i < len(events) - 1:
                    event['effects'] = [events[i+1].get('event_name')]

        return events

    def _save_events(self, document_id: int, events: List[Dict]) -> int:
        """保存事件到数据库"""
        # 先删除旧的事件
        self.db.query(EventUnified).filter(
            EventUnified.document_id == document_id
        ).delete()

        saved_count = 0

        for event in events:
            event_id = f"event_{uuid.uuid4().hex[:16]}"

            db_event = EventUnified(
                event_id=event_id,
                document_id=document_id,
                event_type=event['event_type'],
                event_name=event['event_name'],
                description=event.get('description'),
                chunk_ids=json.dumps([event['chunk_id']]),
                temporal_expression=event.get('temporal_expression'),
                normalized_time_start=event.get('normalized_time_start'),
                time_confidence=event.get('time_confidence', 0.0),
                spatial_expression=event.get('spatial_expression'),
                normalized_location=event.get('normalized_location'),
                location_confidence=event.get('location_confidence', 0.0),
                participants=json.dumps(event.get('participants', [])),
                causes=json.dumps(event.get('causes', [])),
                effects=json.dumps(event.get('effects', [])),
                extraction_method='pattern',
                confidence=event.get('confidence', 0.7)
            )

            self.db.add(db_event)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _create_kg_nodes(self, events: List[Dict]) -> int:
        """为事件创建知识图谱节点"""
        created_count = 0

        for event in events:
            # 检查节点是否已存在
            existing = self.db.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.source_table == 'events_unified',
                KnowledgeGraphNode.label == event['event_name']
            ).first()

            if existing:
                existing.degree += 1
                continue

            # 创建新节点
            node_id = f"node_{uuid.uuid4().hex[:16]}"

            kg_node = KnowledgeGraphNode(
                node_id=node_id,
                node_type='event',
                source_table='events_unified',
                source_id=event['event_name'],
                label=event['event_name'],
                display_name=event['event_name'],
                properties=json.dumps({
                    'type': event['event_type'],
                    'confidence': event.get('confidence', 0.7),
                    'time': event.get('normalized_time_start'),
                    'location': event.get('normalized_location')
                }),
                importance_score=0.5
            )

            self.db.add(kg_node)
            created_count += 1

        self.db.commit()

        return created_count

    def _count_by_type(self, events: List[Dict]) -> Dict[str, int]:
        """统计各类型事件数量"""
        type_counts = {}
        for event in events:
            event_type = event['event_type']
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def extract_document_events(db: Session, document_id: int) -> Dict[str, Any]:
    """
    提取文档事件的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        提取结果
    """
    service = EventExtractionService(db)
    return service.extract_events(document_id)
