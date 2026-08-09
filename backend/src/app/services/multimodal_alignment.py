"""
🎯 多模态语义对齐服务 - 时间戳锚点系统

功能：
1. 确保所有fact都绑定时间戳
2. 实体和事件都反写回时间戳
3. 支持播放器实时高亮对应内容
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.federation import FactStatement, FieldMindObject
from app.services.data_federation_service import DataFederationService


class MultimodalAlignmentService:
    """多模态语义对齐服务"""

    def __init__(self, db: Session):
        self.db = db
        self.federation = DataFederationService(db)

    # ==================== 时间戳对齐 ====================

    def align_facts_with_timestamps(self, project_id: int, document_id: int) -> int:
        """
        为文档中的所有fact补全时间戳信息

        对于音视频转录：
        - Whisper的segment已有start/end时间
        - 需要将这些时间传递到fact层

        Returns:
            对齐的fact数量
        """
        # 查找该文档的所有facts（没有时间戳的）
        facts_without_time = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.document_id == document_id,
            FactStatement.start_sec.is_(None)
        ).all()

        aligned_count = 0

        for fact in facts_without_time:
            # 通过血缘链找到源segment
            if fact.source_fid:
                source_obj = self.db.query(FieldMindObject).filter(
                    FieldMindObject.fid == fact.source_fid
                ).first()

                if source_obj and source_obj.object_type == "segment":
                    # 从segment的metadata中读取时间戳
                    start_sec = source_obj.object_metadata.get("start_sec")
                    end_sec = source_obj.object_metadata.get("end_sec")

                    if start_sec is not None:
                        fact.start_sec = start_sec
                        fact.end_sec = end_sec
                        aligned_count += 1

        self.db.commit()
        return aligned_count

    # ==================== 实时查询：根据时间戳找内容 ====================

    def get_content_at_time(
        self,
        project_id: int,
        document_id: int,
        current_sec: float,
        window_sec: float = 2.0
    ) -> Dict[str, Any]:
        """
        获取指定时间点附近的所有内容（用于播放器实时高亮）

        Args:
            current_sec: 当前播放时间（秒）
            window_sec: 时间窗口（前后容差）

        Returns:
            {
                "facts": [...],
                "entities": [...],
                "events": [...],
                "keywords": [...]
            }
        """
        # 查找时间窗口内的facts
        facts = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.document_id == document_id,
            FactStatement.start_sec >= current_sec - window_sec,
            FactStatement.start_sec <= current_sec + window_sec
        ).all()

        # 提取实体、事件、关键词
        entities = set()
        events = set()
        keywords = set()
        entity_fids = set()

        for fact in facts:
            if fact.entity_names:
                import json
                # 解析JSON字符串
                entity_list = json.loads(fact.entity_names) if isinstance(fact.entity_names, str) else fact.entity_names
                entities.update(entity_list)
            if fact.entity_fids:
                import json
                fid_list = json.loads(fact.entity_fids) if isinstance(fact.entity_fids, str) else fact.entity_fids
                entity_fids.update(fid_list)
            if fact.event_summary:
                events.add(fact.event_summary)
            if fact.keywords:
                import json
                keyword_list = json.loads(fact.keywords) if isinstance(fact.keywords, str) else fact.keywords
                keywords.update(keyword_list)

        return {
            "current_time": current_sec,
            "facts": [
                {
                    "fid": f.fid,
                    "text": f.statement_text,
                    "start_sec": f.start_sec,
                    "end_sec": f.end_sec,
                    "type": f.statement_type,
                    "confidence": f.confidence_score
                }
                for f in facts
            ],
            "entities": list(entities),
            "entity_fids": list(entity_fids),
            "events": list(events),
            "keywords": list(keywords)
        }

    # ==================== 反向查询：根据实体找时间戳 ====================

    def get_entity_timeline(
        self,
        project_id: int,
        entity_name: str,
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取实体在时间轴上的所有出现点

        Returns:
            [
                {
                    "time": 145.3,
                    "fact_fid": "fact_abc",
                    "text": "老王说杀猪菜要腊月二十三做",
                    "context": {...}
                }
            ]
        """
        query = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.start_sec.isnot(None)
        )

        if document_id:
            query = query.filter(FactStatement.document_id == document_id)

        all_facts = query.order_by(FactStatement.start_sec).all()

        # Filter in Python to handle JSON encoding issues with Chinese characters
        facts = []
        for fact in all_facts:
            if fact.entity_names:
                # Parse entity_names if it's a JSON string
                if isinstance(fact.entity_names, str):
                    import json
                    try:
                        entity_list = json.loads(fact.entity_names)
                    except:
                        continue
                else:
                    entity_list = fact.entity_names

                if entity_name in entity_list:
                    facts.append(fact)

        timeline = []
        for fact in facts:
            # Ensure entity_names is a list
            entity_list = fact.entity_names if isinstance(fact.entity_names, list) else []

            timeline.append({
                "time": fact.start_sec,
                "end_time": fact.end_sec,
                "fact_fid": fact.fid,
                "text": fact.statement_text,
                "type": fact.statement_type,
                "other_entities": [e for e in entity_list if e != entity_name],
                "event": fact.event_summary,
                "confidence": fact.confidence_score
            })

        return timeline

    # ==================== 实体聚合：一个实体的所有信息 ====================

    def get_entity_full_profile(
        self,
        project_id: int,
        entity_name: str
    ) -> Dict[str, Any]:
        """
        获取实体的完整画像（跨文档）

        Returns:
            {
                "entity_name": "老王",
                "total_mentions": 15,
                "documents": [1, 3, 5],
                "timeline": [...],  # 所有时间戳
                "co_entities": {"杀猪菜": 8, "腊月二十三": 3},
                "events": ["制作杀猪菜", "参与祭祀"],
                "facts": [...]
            }
        """
        # 查找所有提到该实体的facts
        all_facts = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id
        ).all()

        # Filter in Python to handle JSON encoding issues with Chinese characters
        facts = []
        for fact in all_facts:
            if fact.entity_names:
                # Parse entity_names if it's a JSON string
                if isinstance(fact.entity_names, str):
                    import json
                    try:
                        entity_list = json.loads(fact.entity_names)
                    except:
                        continue
                else:
                    entity_list = fact.entity_names

                if entity_name in entity_list:
                    facts.append(fact)

        # 统计信息
        document_ids = set()
        co_entities_count = {}
        events = set()

        for fact in facts:
            if fact.document_id:
                document_ids.add(fact.document_id)

            if fact.entity_names:
                # Parse entity_names if it's a JSON string
                if isinstance(fact.entity_names, str):
                    import json
                    try:
                        entity_list = json.loads(fact.entity_names)
                    except:
                        entity_list = []
                else:
                    entity_list = fact.entity_names

                for other in entity_list:
                    if other != entity_name:
                        co_entities_count[other] = co_entities_count.get(other, 0) + 1

            if fact.event_summary:
                events.add(fact.event_summary)

        # 获取时间线
        timeline = self.get_entity_timeline(project_id, entity_name)

        return {
            "entity_name": entity_name,
            "total_mentions": len(facts),
            "documents": list(document_ids),
            "timeline": timeline,
            "co_entities": co_entities_count,
            "events": list(events),
            "facts": [
                {
                    "fid": f.fid,
                    "text": f.statement_text,
                    "time": f.start_sec,
                    "document_id": f.document_id
                }
                for f in facts[:20]  # 最多返回20条
            ]
        }

    # ==================== 事件聚合 ====================

    def get_event_full_profile(
        self,
        project_id: int,
        event_summary: str
    ) -> Dict[str, Any]:
        """
        获取事件的完整画像

        Returns:
            {
                "event": "制作杀猪菜",
                "total_mentions": 5,
                "participants": ["老王", "村民"],
                "timeline": [...],
                "facts": [...]
            }
        """
        # 查找所有提到该事件的facts
        facts = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.event_summary == event_summary
        ).all()

        # 提取参与者
        participants = set()
        for fact in facts:
            if fact.entity_names:
                participants.update(fact.entity_names)

        # 时间线
        timeline = [
            {
                "time": f.start_sec,
                "text": f.statement_text,
                "entities": f.entity_names
            }
            for f in facts if f.start_sec is not None
        ]
        timeline.sort(key=lambda x: x["time"])

        return {
            "event": event_summary,
            "total_mentions": len(facts),
            "participants": list(participants),
            "timeline": timeline,
            "facts": [
                {
                    "fid": f.fid,
                    "text": f.statement_text,
                    "time": f.start_sec
                }
                for f in facts
            ]
        }

    # ==================== 批量验证：检查时间戳完整性 ====================

    def validate_timestamp_coverage(self, project_id: int, document_id: int) -> Dict[str, Any]:
        """
        验证文档的时间戳覆盖率

        Returns:
            {
                "total_facts": 100,
                "with_timestamp": 95,
                "coverage": 0.95,
                "missing_fids": [...]
            }
        """
        total = self.db.query(func.count(FactStatement.id)).filter(
            FactStatement.project_id == project_id,
            FactStatement.document_id == document_id
        ).scalar()

        with_timestamp = self.db.query(func.count(FactStatement.id)).filter(
            FactStatement.project_id == project_id,
            FactStatement.document_id == document_id,
            FactStatement.start_sec.isnot(None)
        ).scalar()

        # 找出缺失时间戳的facts
        missing = self.db.query(FactStatement.fid).filter(
            FactStatement.project_id == project_id,
            FactStatement.document_id == document_id,
            FactStatement.start_sec.is_(None)
        ).limit(10).all()

        return {
            "total_facts": total,
            "with_timestamp": with_timestamp,
            "coverage": with_timestamp / total if total > 0 else 0,
            "missing_fids": [f[0] for f in missing]
        }
