"""
实时知识提炼API - 从真实文档中流式提取知识
支持SSE (Server-Sent Events) 实时推送提炼进度
集成真实AI模型: NER + Claude AI
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator, Optional, List, Dict
import json
import asyncio
from datetime import datetime
import logging
import re

from app.core.database import get_db
from app.models.unified_pipeline import (
    DirtyChannelDocument,
    CleanChannelEntity,
    CleanChannelEvent,
    CleanChannelRelation,
    NineStepPipelineStatus
)
from app.schemas.response import success_response
from app.services.entity_extraction import get_entity_extraction_service
from app.core.ai_call_manager import get_ai_call_manager, ModelTier

router = APIRouter()
logger = logging.getLogger(__name__)


class LiveExtractionService:
    """实时提炼服务 - 使用真实AI模型进行知识提取"""

    def __init__(self, db: Session):
        self.db = db
        # 初始化NER服务（jieba实体提取）
        self.entity_service = get_entity_extraction_service()
        # 初始化AI管理器（Claude API）
        try:
            self.ai_manager = get_ai_call_manager()
        except Exception as e:
            logger.warning(f"AI管理器初始化失败: {e}，将使用基础NER")
            self.ai_manager = None

    async def extract_step_3_entities(
        self,
        dirty_doc_id: int,
        text: str
    ) -> AsyncGenerator[dict, None]:
        """
        步骤3: 实体构建 - 使用jieba NER提取实体
        实时yield每个提取出的实体
        """
        logger.info(f"[步骤3] 开始实体提取，文档ID: {dirty_doc_id}")

        # 使用jieba进行实体提取（真实NER）
        entities_extracted = self.entity_service.extract_entities(
            text,
            min_confidence=0.6
        )

        logger.info(f"[步骤3] 提取到 {len(entities_extracted)} 个实体")

        for entity_data in entities_extracted:
            # 保存到数据库
            entity = CleanChannelEntity(
                dirty_doc_id=dirty_doc_id,
                entity_name=entity_data['name'],
                entity_type=entity_data['type'],
                importance_score=entity_data['confidence'],
                properties={
                    'mention_count': entity_data.get('mention_count', 1),
                    'positions': entity_data.get('positions', [])
                }
            )
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)

            # 获取上下文文本
            positions = entity_data.get('positions', [])
            source_text = ""
            if positions:
                pos = positions[0]
                start = max(0, pos[0] - 20)
                end = min(len(text), pos[1] + 20)
                source_text = text[start:end]

            # 实时推送提取事件
            yield {
                "step": 3,
                "type": "node",
                "action": "add",
                "data": {
                    "id": f"entity_{entity.id}",
                    "label": entity.entity_name,
                    "type": entity.entity_type,
                    "layer": 2,
                    "is_core": entity.importance_score >= 0.8,
                    "size": 10 + int(entity.importance_score * 10),
                    "pipeline_step": 3,
                    "properties": entity.properties
                },
                "timestamp": int(datetime.now().timestamp() * 1000),
                "reasoning": f"NER识别为{entity.entity_type}实体，置信度{entity.importance_score}",
                "source_text": source_text
            }

            await asyncio.sleep(0.2)

    async def extract_step_4_events(
        self,
        dirty_doc_id: int,
        text: str
    ) -> AsyncGenerator[dict, None]:
        """
        步骤4: 事件提取 - 使用Claude AI提取历史事件
        """
        logger.info(f"[步骤4] 开始事件提取")

        if not self.ai_manager:
            logger.warning("[步骤4] AI管理器不可用，跳过事件提取")
            return

        # 构建事件提取prompt
        prompt = f"""
请从以下文本中提取重要事件。每个事件应包含：
1. 事件标题（简短概括）
2. 事件摘要（详细描述）
3. 5W1H信息（What, When, Where, Who, Why, How）

文本内容：
{text[:2000]}

请以JSON格式返回，格式如下：
[
  {{
    "title": "事件标题",
    "summary": "事件摘要",
    "what": "发生了什么",
    "when": "什么时候",
    "where": "在哪里",
    "who": "涉及谁",
    "why": "为什么",
    "how": "如何发生"
  }}
]
"""

        try:
            # 调用Claude AI
            response = await self.ai_manager.smart_call(
                messages=[{"role": "user", "content": prompt}],
                task_complexity="medium",
                max_tokens=2048,
                temperature=0.3
            )

            # 解析AI返回的JSON
            events_json = self._extract_json_from_text(response['text'])
            events_list = json.loads(events_json) if events_json else []

            logger.info(f"[步骤4] AI提取到 {len(events_list)} 个事件")

            for event_data in events_list:
                # 保存到数据库
                event = CleanChannelEvent(
                    dirty_doc_id=dirty_doc_id,
                    event_title=event_data.get('title', '未命名事件'),
                    event_summary=event_data.get('summary', ''),
                    information_nodes={
                        'what': event_data.get('what', ''),
                        'when': event_data.get('when', ''),
                        'where': event_data.get('where', ''),
                        'who': event_data.get('who', ''),
                        'why': event_data.get('why', ''),
                        'how': event_data.get('how', '')
                    },
                    importance_score=0.85
                )
                self.db.add(event)
                self.db.commit()
                self.db.refresh(event)

                # 实时推送事件节点
                yield {
                    "step": 4,
                    "type": "node",
                    "action": "add",
                    "data": {
                        "id": f"event_{event.id}",
                        "label": event.event_title,
                        "type": "EVENT",
                        "layer": 1,
                        "is_core": True,
                        "size": 18,
                        "pipeline_step": 4,
                        "properties": {
                            "summary": event.event_summary,
                            "5w1h": event.information_nodes
                        }
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "reasoning": f"AI识别的重要事件: {event.event_title}",
                    "source_text": event.event_summary[:100]
                }

                await asyncio.sleep(0.3)

        except Exception as e:
            logger.error(f"[步骤4] 事件提取失败: {e}")

    async def extract_step_5_relations(
        self,
        dirty_doc_id: int,
        text: str
    ) -> AsyncGenerator[dict, None]:
        """
        步骤5: 关系发现 - 使用NER服务的关系提取
        """
        logger.info(f"[步骤5] 开始关系发现")

        # 获取已提取的实体
        entities = self.db.query(CleanChannelEntity).filter(
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).all()

        if len(entities) < 2:
            logger.warning("[步骤5] 实体数量不足，跳过关系发现")
            return

        # 准备实体列表
        entities_list = [
            {
                'name': e.entity_name,
                'type': e.entity_type,
                'id': e.id
            }
            for e in entities
        ]

        # 使用jieba服务进行基础关系提取
        relations_found = self.entity_service.extract_relationships(
            [{'name': e['name'], 'type': e['type']} for e in entities_list],
            text
        )

        logger.info(f"[步骤5] 发现 {len(relations_found)} 个关系")

        # 保存关系到数据库并推送
        for rel_data in relations_found:
            # 查找实体ID
            source_entity = next(
                (e for e in entities_list if e['name'] == rel_data['from']),
                None
            )
            target_entity = next(
                (e for e in entities_list if e['name'] == rel_data['to']),
                None
            )

            if not source_entity or not target_entity:
                continue

            # 保存关系
            relation = CleanChannelRelation(
                dirty_doc_id=dirty_doc_id,
                source_entity_id=source_entity['id'],
                target_entity_id=target_entity['id'],
                relation_type=rel_data['type'],
                relation_description=rel_data.get('context', ''),
                strength_score=rel_data.get('confidence', 0.7)
            )
            self.db.add(relation)
            self.db.commit()
            self.db.refresh(relation)

            # 实时推送边
            yield {
                "step": 5,
                "type": "edge",
                "action": "add",
                "data": {
                    "id": f"relation_{relation.id}",
                    "source": f"entity_{relation.source_entity_id}",
                    "target": f"entity_{relation.target_entity_id}",
                    "type": relation.relation_type,
                    "weight": relation.strength_score,
                    "pipeline_step": 5
                },
                "timestamp": int(datetime.now().timestamp() * 1000),
                "reasoning": f"发现关系: {rel_data['from']} -[{rel_data['type']}]-> {rel_data['to']}",
                "source_text": rel_data.get('context', '')[:100]
            }

            await asyncio.sleep(0.25)

    async def extract_step_6_ontology(
        self,
        dirty_doc_id: int
    ) -> AsyncGenerator[dict, None]:
        """
        步骤6: 本体构建 - 建立知识分类体系
        """
        logger.info(f"[步骤6] 开始本体构建")

        entities = self.db.query(CleanChannelEntity).filter(
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).all()

        # 按类型分组
        type_groups = {}
        for entity in entities:
            if entity.entity_type not in type_groups:
                type_groups[entity.entity_type] = []
            type_groups[entity.entity_type].append(entity)

        # 为每个实体创建IS_A关系
        idx = 0
        for entity_type, entity_list in type_groups.items():
            for entity in entity_list[:5]:  # 每种类型最多5个
                yield {
                    "step": 6,
                    "type": "edge",
                    "action": "add",
                    "data": {
                        "id": f"ontology_{idx}",
                        "source": f"entity_{entity.id}",
                        "target": f"type_{entity_type}",
                        "type": "IS_A",
                        "weight": 1.0,
                        "pipeline_step": 6
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "reasoning": f"{entity.entity_name} 属于 {entity_type} 类别",
                    "source_text": ""
                }
                idx += 1
                await asyncio.sleep(0.15)

    async def extract_step_7_inference(
        self,
        dirty_doc_id: int
    ) -> AsyncGenerator[dict, None]:
        """
        步骤7: 逻辑推理 - 推断潜在关系（传递性推理）
        """
        logger.info(f"[步骤7] 开始逻辑推理")

        relations = self.db.query(CleanChannelRelation).filter(
            CleanChannelRelation.dirty_doc_id == dirty_doc_id
        ).all()

        if len(relations) < 2:
            logger.warning("[步骤7] 关系数量不足，跳过推理")
            return

        # 构建关系图：source_id -> [target_ids]
        relation_map = {}
        for rel in relations:
            if rel.source_entity_id not in relation_map:
                relation_map[rel.source_entity_id] = []
            relation_map[rel.source_entity_id].append(rel.target_entity_id)

        # 传递推理: A->B, B->C => A->C
        inferred_count = 0
        for source_id, targets in relation_map.items():
            for target_id in targets:
                if target_id in relation_map:
                    # 发现传递关系
                    for final_target in relation_map[target_id]:
                        if final_target != source_id:  # 避免自环
                            yield {
                                "step": 7,
                                "type": "edge",
                                "action": "add",
                                "data": {
                                    "id": f"inferred_{inferred_count}",
                                    "source": f"entity_{source_id}",
                                    "target": f"entity_{final_target}",
                                    "type": "INFERRED",
                                    "weight": 0.6,
                                    "pipeline_step": 7
                                },
                                "timestamp": int(datetime.now().timestamp() * 1000),
                                "reasoning": "基于传递性推理发现的潜在关系",
                                "source_text": ""
                            }
                            inferred_count += 1
                            await asyncio.sleep(0.2)

                            if inferred_count >= 5:  # 限制推理数量
                                return

    async def extract_step_8_unitization(
        self,
        dirty_doc_id: int
    ) -> AsyncGenerator[dict, None]:
        """
        步骤8: 知识单元化 - 标记核心知识单元
        """
        logger.info(f"[步骤8] 开始知识单元化")

        entities = self.db.query(CleanChannelEntity).filter(
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).all()

        events = self.db.query(CleanChannelEvent).filter(
            CleanChannelEvent.dirty_doc_id == dirty_doc_id
        ).all()

        # 所有事件都是核心单元
        for event in events:
            yield {
                "step": 8,
                "type": "property",
                "action": "update",
                "data": {
                    "id": f"event_{event.id}",
                    "is_core": True,
                    "layer": 1,
                    "unit_type": "event_unit"
                },
                "timestamp": int(datetime.now().timestamp() * 1000),
                "reasoning": "事件节点标记为核心知识单元",
                "source_text": ""
            }
            await asyncio.sleep(0.15)

        # 高重要性实体标记为核心
        for entity in entities:
            if entity.importance_score >= 0.8:
                yield {
                    "step": 8,
                    "type": "property",
                    "action": "update",
                    "data": {
                        "id": f"entity_{entity.id}",
                        "is_core": True,
                        "layer": 1,
                        "unit_type": "entity_unit"
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "reasoning": f"高重要性实体 {entity.entity_name} (置信度:{entity.importance_score})",
                    "source_text": ""
                }
                await asyncio.sleep(0.15)

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """从AI返回的文本中提取JSON数组"""
        # 尝试找到JSON数组
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return match.group(0)
        return None


@router.post("/document/{dirty_doc_id}/extract-realtime")
async def extract_knowledge_realtime(
    dirty_doc_id: int,
    db: Session = Depends(get_db)
):
    """
    实时提取知识（SSE流式传输）
    从步骤3到步骤8，逐步提取知识并实时推送给前端
    """

    async def event_stream():
        """SSE事件流生成器"""
        try:
            # 1. 获取脏数据文档
            dirty_doc = db.query(DirtyChannelDocument).filter(
                DirtyChannelDocument.id == dirty_doc_id
            ).first()

            if not dirty_doc:
                yield f"data: {json.dumps({'error': '文档不存在'})}\n\n"
                return

            text = dirty_doc.complete_text
            service = LiveExtractionService(db)

            # 2. 步骤3: 实体构建
            yield f"data: {json.dumps({'step': 3, 'status': 'started', 'message': '开始提取实体...'})}\n\n"

            async for event in service.extract_step_3_entities(dirty_doc_id, text):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 3, 'status': 'completed'})}\n\n"

            # 3. 步骤4: 事件提取
            yield f"data: {json.dumps({'step': 4, 'status': 'started', 'message': '开始提取事件...'})}\n\n"

            async for event in service.extract_step_4_events(dirty_doc_id, text):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 4, 'status': 'completed'})}\n\n"

            # 4. 步骤5: 关系发现
            yield f"data: {json.dumps({'step': 5, 'status': 'started', 'message': '分析实体关系...'})}\n\n"

            async for event in service.extract_step_5_relations(dirty_doc_id, text):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 5, 'status': 'completed'})}\n\n"

            # 5. 步骤6: 本体构建
            yield f"data: {json.dumps({'step': 6, 'status': 'started', 'message': '构建知识本体...'})}\n\n"

            async for event in service.extract_step_6_ontology(dirty_doc_id):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 6, 'status': 'completed'})}\n\n"

            # 6. 步骤7: 逻辑推理
            yield f"data: {json.dumps({'step': 7, 'status': 'started', 'message': '进行逻辑推理...'})}\n\n"

            async for event in service.extract_step_7_inference(dirty_doc_id):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 7, 'status': 'completed'})}\n\n"

            # 7. 步骤8: 知识单元化
            yield f"data: {json.dumps({'step': 8, 'status': 'started', 'message': '知识单元化...'})}\n\n"

            async for event in service.extract_step_8_unitization(dirty_doc_id):
                yield f"data: {json.dumps(event)}\n\n"

            yield f"data: {json.dumps({'step': 8, 'status': 'completed'})}\n\n"

            # 8. 完成
            yield f"data: {json.dumps({'status': 'finished', 'message': '知识提炼完成！'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/document/{dirty_doc_id}/text-preview")
async def get_document_text_preview(
    dirty_doc_id: int,
    db: Session = Depends(get_db)
):
    """获取文档文本预览（前500字）"""
    dirty_doc = db.query(DirtyChannelDocument).filter(
        DirtyChannelDocument.id == dirty_doc_id
    ).first()

    if not dirty_doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    text = dirty_doc.complete_text or ""
    preview = text[:500] + "..." if len(text) > 500 else text

    return success_response(data={
        "dirty_doc_id": dirty_doc_id,
        "source_type": dirty_doc.source_type,
        "text_preview": preview,
        "total_length": len(text),
        "word_count": dirty_doc.word_count
    })
