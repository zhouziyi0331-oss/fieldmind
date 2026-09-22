"""统一知识图谱构建入口。

保留历史 API 名称，但底层统一使用：
ProjectDocument -> DocumentChunk -> Entity -> EntityRelation。
"""

import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import logger, log_document_processing
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation
from app.models.project import ProjectDocument
from app.services.entity_extractor import EntityExtractor, EntityDeduplicator
from app.services.relation_extractor import RelationExtractor, RelationValidator


class KnowledgeGraphBuilder:
    """从当前结构化分块构建可持久化知识图谱。"""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()

    def build_from_document(
        self,
        document_id: int,
        project_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """处理单个项目文档；project_id 是旧 API 的兼容参数。"""
        owns_session = db is None
        db = db or SessionLocal()
        started = time.time()
        try:
            document = db.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()
            if not document:
                raise ValueError(f"文档不存在: {document_id}")
            if project_id is not None and document.project_id != project_id:
                raise ValueError(f"文档 {document_id} 不属于项目 {project_id}")

            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
            if not chunks:
                return {
                    "document_id": document_id,
                    "project_id": document.project_id,
                    "entities_created": 0,
                    "entities_updated": 0,
                    "relations_created": 0,
                    "relationships_created": 0,
                    "timeline_events": 0,
                    "status": "no_chunks",
                }

            all_entities: List[Dict[str, Any]] = []
            all_relations: List[Dict[str, Any]] = []
            for chunk in chunks:
                entities = EntityDeduplicator.deduplicate(
                    self.entity_extractor.extract(chunk.text or "")
                )
                all_entities.extend(entities)
                all_relations.extend(
                    relation
                    for relation in self.relation_extractor.extract(chunk.text or "", entities)
                    if RelationValidator.validate(relation)
                )

            merged_entities = self._merge_global_entities(all_entities)
            created, updated, entity_map = self._save_entities(
                db, document, merged_entities
            )
            relations_created = self._save_relations(
                db, document, all_relations, entity_map
            )
            db.commit()

            result = {
                "document_id": document_id,
                "project_id": document.project_id,
                "entities_created": created,
                "entities_updated": updated,
                "relations_created": relations_created,
                "relationships_created": relations_created,
                "timeline_events": 0,
                "status": "success",
                "duration": time.time() - started,
            }
            log_document_processing(
                document_id=document_id,
                operation="build_knowledge_graph",
                status="completed",
                duration=result["duration"],
                details=result,
            )
            return result
        except Exception:
            db.rollback()
            logger.exception("知识图谱构建失败: document_id=%s", document_id)
            raise
        finally:
            if owns_session:
                db.close()

    def build_from_project(
        self,
        project_id: int,
        force_rebuild: bool = False,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """处理项目下所有已有结构化分块的文档。"""
        owns_session = db is None
        db = db or SessionLocal()
        try:
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status.in_(["completed", "review_needed", "processing"]),
            ).order_by(ProjectDocument.id).all()
            totals = {
                "documents_processed": 0,
                "entities_created": 0,
                "entities_updated": 0,
                "relationships_created": 0,
                "timeline_events": 0,
                "errors": [],
            }
            for document in documents:
                try:
                    result = self.build_from_document(
                        document.id, project_id=project_id, db=db
                    )
                    if result.get("status") != "no_chunks":
                        totals["documents_processed"] += 1
                    totals["entities_created"] += result.get("entities_created", 0)
                    totals["entities_updated"] += result.get("entities_updated", 0)
                    totals["relationships_created"] += result.get(
                        "relationships_created", 0
                    )
                except Exception as exc:
                    totals["errors"].append({"document_id": document.id, "error": str(exc)})
            db.commit()
            totals["status"] = "completed" if not totals["errors"] else "completed_with_errors"
            totals["force_rebuild"] = force_rebuild
            return totals
        finally:
            if owns_session:
                db.close()

    def _merge_global_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: Dict[tuple[str, str], Dict[str, Any]] = {}
        for entity in entities:
            text = EntityDeduplicator.normalize(
                str(entity.get("text", "")), str(entity.get("type", "UNKNOWN"))
            )
            entity_type = str(entity.get("type", "UNKNOWN")).upper()
            if not text:
                continue
            current = merged.setdefault(
                (text, entity_type),
                {"text": text, "type": entity_type, "occurrences": 0, "confidence": 0.0},
            )
            current["occurrences"] += 1
            current["confidence"] = max(
                current["confidence"], float(entity.get("confidence") or 0.0)
            )
        return list(merged.values())

    def _save_entities(
        self,
        db: Session,
        document: ProjectDocument,
        entities: List[Dict[str, Any]],
    ) -> tuple[int, int, Dict[str, Entity]]:
        created = 0
        updated = 0
        entity_map: Dict[str, Entity] = {}
        for data in entities:
            text = data["text"]
            entity_type = data["type"]
            row = db.query(Entity).filter(
                Entity.text == text,
                Entity.type == entity_type,
            ).first()
            if row is None:
                row = Entity(
                    text=text,
                    type=entity_type,
                    canonical_form=text,
                    legacy_name=text,
                    legacy_entity_type=entity_type,
                    metadata_json={"source": "knowledge_graph_builder"},
                    confidence=data["confidence"],
                    mention_count=0,
                    document_ids=[],
                )
                db.add(row)
                db.flush()
                created += 1
            else:
                updated += 1

            row.mention_count = int(row.mention_count or 0) + int(data["occurrences"])
            row.confidence = max(float(row.confidence or 0.0), data["confidence"])
            document_ids = list(row.document_ids or [])
            if document.id not in document_ids:
                document_ids.append(document.id)
            row.document_ids = document_ids
            metadata = dict(row.metadata_json or {})
            project_ids = list(metadata.get("project_ids") or [])
            if document.project_id not in project_ids:
                project_ids.append(document.project_id)
            metadata.update({"project_ids": project_ids, "last_document_id": document.id})
            row.metadata_json = metadata
            row.legacy_name = text
            row.legacy_entity_type = entity_type
            entity_map[text] = row
        return created, updated, entity_map

    def _save_relations(
        self,
        db: Session,
        document: ProjectDocument,
        relations: List[Dict[str, Any]],
        entity_map: Dict[str, Entity],
    ) -> int:
        from sqlalchemy import func

        saved = 0
        next_relation_id = int(db.query(func.max(EntityRelation.id)).scalar() or 0) + 1
        for relation in relations:
            source = entity_map.get(str(relation.get("source", "")).strip())
            target = entity_map.get(str(relation.get("target", "")).strip())
            if not source or not target or source.id == target.id:
                continue
            relation_type = str(relation.get("relation", "RELATED"))
            row = db.query(EntityRelation).filter(
                EntityRelation.source_entity_id == source.id,
                EntityRelation.target_entity_id == target.id,
                EntityRelation.relation_type == relation_type,
            ).first()
            if row is None:
                db.add(EntityRelation(
                    id=next_relation_id,
                    source_entity_id=source.id,
                    target_entity_id=target.id,
                    relation_type=relation_type,
                    confidence=float(relation.get("confidence") or 0.5),
                    source_documents=[document.id],
                    metadata_json={"project_ids": [document.project_id]},
                ))
                next_relation_id += 1
                saved += 1
            else:
                row.confidence = max(
                    float(row.confidence or 0.0), float(relation.get("confidence") or 0.5)
                )
                source_documents = list(row.source_documents or [])
                if document.id not in source_documents:
                    source_documents.append(document.id)
                row.source_documents = source_documents
        return saved

    def get_graph_visualization_data(
        self,
        project_id: Optional[int] = None,
        limit: int = 100,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """返回旧前端需要的 nodes/edges 格式，数据来自当前实体关系表。"""
        owns_session = db is None
        db = db or SessionLocal()
        try:
            rows = db.query(Entity).order_by(Entity.mention_count.desc()).all()
            if project_id is not None:
                rows = [
                    row for row in rows
                    if project_id in list((row.metadata_json or {}).get("project_ids") or [])
                ]
            rows = rows[:limit]
            ids = {row.id for row in rows}
            nodes = [
                {
                    "id": str(row.id),
                    "entity_id": str(row.id),
                    "label": row.text,
                    "title": row.description or row.text,
                    "group": row.type,
                    "value": int(row.mention_count or 0),
                }
                for row in rows
            ]
            relation_rows = db.query(EntityRelation).filter(
                EntityRelation.source_entity_id.in_(ids or ["__none__"]),
                EntityRelation.target_entity_id.in_(ids or ["__none__"]),
            ).all()
            edges = [
                {
                    "id": str(row.id),
                    "from": str(row.source_entity_id),
                    "to": str(row.target_entity_id),
                    "label": row.relation_type,
                    "width": max(1, int((row.confidence or 0.5) * 5)),
                }
                for row in relation_rows
            ]
            return {"nodes": nodes, "edges": edges}
        finally:
            if owns_session:
                db.close()


def build_knowledge_graph(document_id: int) -> Dict[str, Any]:
    return KnowledgeGraphBuilder().build_from_document(document_id)


_knowledge_graph_builder: Optional[KnowledgeGraphBuilder] = None


def get_knowledge_graph_builder(db=None) -> KnowledgeGraphBuilder:
    global _knowledge_graph_builder
    if _knowledge_graph_builder is None:
        _knowledge_graph_builder = KnowledgeGraphBuilder()
    return _knowledge_graph_builder
