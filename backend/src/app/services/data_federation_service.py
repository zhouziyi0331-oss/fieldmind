"""
🧠 数据联邦服务 - 全局对象管理和血缘追踪

负责：
1. 统一的对象创建和注册
2. 跨库对象查询
3. 血缘链追踪
4. 对象关系管理
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.federation import FieldMindObject, ObjectRelation, FactStatement, generate_fid
from app.models.project import ProjectDocument


class DataFederationService:
    """数据联邦服务 - 全局对象ID体系的中控"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 对象注册 ====================

    def register_object(
        self,
        object_type: str,
        project_id: int,
        storage_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        source_fid: Optional[str] = None,
        derived_chain: Optional[List[str]] = None
    ) -> str:
        """
        注册一个新对象到全局对象表

        Args:
            object_type: document/segment/fact/entity/event/relation/topic/dimension
            project_id: 所属项目ID
            storage_info: 存储位置信息
            metadata: 对象元数据摘要
            source_fid: 直接来源对象的fid
            derived_chain: 完整派生链（如果为空且有source_fid，会自动构建）

        Returns:
            新对象的fid
        """
        fid = generate_fid(object_type)

        # 如果有source_fid但没有derived_chain，自动构建
        if source_fid and not derived_chain:
            parent_obj = self.db.query(FieldMindObject).filter(
                FieldMindObject.fid == source_fid
            ).first()
            if parent_obj and parent_obj.derived_from_chain:
                derived_chain = parent_obj.derived_from_chain + [source_fid]
            else:
                derived_chain = [source_fid]

        obj = FieldMindObject(
            fid=fid,
            object_type=object_type,
            project_id=project_id,
            source_fid=source_fid,
            derived_from_chain=derived_chain,
            storage_info=storage_info,
            object_metadata=metadata or {}
        )
        self.db.add(obj)
        self.db.flush()

        # 如果有source_fid，自动创建派生关系
        if source_fid:
            self.add_relation(
                from_fid=source_fid,
                to_fid=fid,
                relation_type="derived_from",
                confidence=1.0,
                project_id=project_id
            )

        return fid

    def register_document(self, doc_id: int, project_id: int, metadata: Dict[str, Any]) -> str:
        """注册文档对象"""
        return self.register_object(
            object_type="document",
            project_id=project_id,
            storage_info={
                "storage_type": "sqlite",
                "table_name": "project_documents",
                "record_id": doc_id
            },
            metadata=metadata
        )

    def register_fact(
        self,
        fact_id: int,
        project_id: int,
        document_id: int,
        source_fid: str,
        metadata: Dict[str, Any]
    ) -> str:
        """注册事实陈述对象"""
        return self.register_object(
            object_type="fact",
            project_id=project_id,
            storage_info={
                "storage_type": "sqlite",
                "table_name": "fact_statements",
                "record_id": fact_id
            },
            metadata=metadata,
            source_fid=source_fid
        )

    # ==================== 关系管理 ====================

    def add_relation(
        self,
        from_fid: str,
        to_fid: str,
        relation_type: str,
        confidence: float,
        project_id: int,
        evidence_fids: Optional[List[str]] = None,
        relation_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加对象关系"""
        relation = ObjectRelation(
            from_fid=from_fid,
            to_fid=to_fid,
            relation_type=relation_type,
            confidence=confidence,
            strength=confidence,
            evidence_fids=evidence_fids or [],
            relation_data=relation_data or {},
            project_id=project_id
        )
        self.db.add(relation)
        self.db.flush()
        return relation.id

    def get_relations(
        self,
        fid: str,
        relation_type: Optional[str] = None,
        direction: str = "both"  # "from", "to", "both"
    ) -> List[ObjectRelation]:
        """获取对象的所有关系"""
        query = self.db.query(ObjectRelation)

        if direction == "from":
            query = query.filter(ObjectRelation.from_fid == fid)
        elif direction == "to":
            query = query.filter(ObjectRelation.to_fid == fid)
        else:  # both
            query = query.filter(
                (ObjectRelation.from_fid == fid) | (ObjectRelation.to_fid == fid)
            )

        if relation_type:
            query = query.filter(ObjectRelation.relation_type == relation_type)

        return query.all()

    # ==================== 血缘追踪 ====================

    def get_lineage(self, fid: str) -> Dict[str, Any]:
        """
        获取对象的完整血缘链

        Returns:
            {
                "current": {...},
                "ancestors": [...],  # 从根到父
                "descendants": [...] # 所有子孙
            }
        """
        current = self.db.query(FieldMindObject).filter(
            FieldMindObject.fid == fid
        ).first()

        if not current:
            return {"error": "Object not found"}

        # 获取祖先链
        ancestors = []
        if current.derived_from_chain:
            for ancestor_fid in current.derived_from_chain:
                ancestor = self.db.query(FieldMindObject).filter(
                    FieldMindObject.fid == ancestor_fid
                ).first()
                if ancestor:
                    ancestors.append({
                        "fid": ancestor.fid,
                        "type": ancestor.object_type,
                        "metadata": ancestor.object_metadata
                    })

        # 获取所有后代（递归查询source_fid）
        descendants = self._get_descendants_recursive(fid)

        return {
            "current": {
                "fid": current.fid,
                "type": current.object_type,
                "metadata": current.object_metadata,
                "storage": current.storage_info
            },
            "ancestors": ancestors,
            "descendants": descendants
        }

    def _get_descendants_recursive(self, fid: str, visited: Optional[set] = None) -> List[Dict[str, Any]]:
        """递归获取所有后代"""
        if visited is None:
            visited = set()

        if fid in visited:
            return []

        visited.add(fid)

        children = self.db.query(FieldMindObject).filter(
            FieldMindObject.source_fid == fid
        ).all()

        result = []
        for child in children:
            result.append({
                "fid": child.fid,
                "type": child.object_type,
                "metadata": child.object_metadata
            })
            # 递归获取子孙
            result.extend(self._get_descendants_recursive(child.fid, visited))

        return result

    # ==================== 跨库查询 ====================

    def get_object_full_data(self, fid: str) -> Optional[Dict[str, Any]]:
        """
        获取对象的完整数据（从实际存储位置读取）

        Returns:
            {
                "fid": "fact_abc123",
                "type": "fact",
                "metadata": {...},
                "full_data": {...},  # 从实际表中读取的完整数据
                "relations": [...]
            }
        """
        obj = self.db.query(FieldMindObject).filter(
            FieldMindObject.fid == fid
        ).first()

        if not obj:
            return None

        # 读取实际存储的数据
        full_data = None
        storage = obj.storage_info

        if storage.get("storage_type") == "sqlite":
            table_name = storage.get("table_name")
            record_id = storage.get("record_id")

            if table_name == "project_documents":
                doc = self.db.query(ProjectDocument).filter(
                    ProjectDocument.id == record_id
                ).first()
                if doc:
                    full_data = {
                        "id": doc.id,
                        "filename": doc.filename,
                        "file_type": doc.file_type,
                        "text_content": doc.text_content[:500] if doc.text_content else None,
                        "summary": doc.summary,
                        "status": doc.status
                    }

            elif table_name == "fact_statements":
                fact = self.db.query(FactStatement).filter(
                    FactStatement.id == record_id
                ).first()
                if fact:
                    full_data = {
                        "id": fact.id,
                        "statement_text": fact.statement_text,
                        "statement_type": fact.statement_type,
                        "start_sec": fact.start_sec,
                        "end_sec": fact.end_sec,
                        "entity_names": fact.entity_names,
                        "event_summary": fact.event_summary,
                        "confidence_score": fact.confidence_score
                    }

        # 获取关系
        relations = self.get_relations(fid)
        relation_data = [
            {
                "from": r.from_fid,
                "to": r.to_fid,
                "type": r.relation_type,
                "confidence": r.confidence
            }
            for r in relations
        ]

        return {
            "fid": obj.fid,
            "type": obj.object_type,
            "metadata": obj.object_metadata,
            "storage": obj.storage_info,
            "full_data": full_data,
            "relations": relation_data,
            "lineage": {
                "source": obj.source_fid,
                "chain": obj.derived_from_chain
            }
        }

    # ==================== 批量查询 ====================

    def find_objects_by_type(
        self,
        project_id: int,
        object_type: str,
        limit: int = 100
    ) -> List[FieldMindObject]:
        """查找项目中某类型的所有对象"""
        return self.db.query(FieldMindObject).filter(
            FieldMindObject.project_id == project_id,
            FieldMindObject.object_type == object_type
        ).limit(limit).all()

    def find_objects_by_metadata(
        self,
        project_id: int,
        metadata_key: str,
        metadata_value: Any
    ) -> List[FieldMindObject]:
        """根据元数据查找对象（JSON查询）"""
        # SQLite JSON查询
        return self.db.query(FieldMindObject).filter(
            FieldMindObject.project_id == project_id,
            FieldMindObject.object_metadata[metadata_key].as_string() == str(metadata_value)
        ).all()
