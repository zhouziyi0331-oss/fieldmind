"""知识图谱构建服务 - 从文档自动构建知识图谱"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
from datetime import datetime

from app.models.project import ProjectDocument
from app.models.entity import Entity, EntityType
from app.models.timeline import TimelineEvent
from app.services.entity_extraction import get_entity_extraction_service

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = get_entity_extraction_service()

    def build_from_document(self, document_id: int, project_id: int) -> Dict:
        """
        从单个文档构建知识图谱

        Args:
            document_id: 文档ID
            project_id: 项目ID

        Returns:
            构建结果统计 {"entities_created": 10, "relationships_created": 5, "timeline_events": 3}
        """
        # 读取文档
        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id
        ).first()

        if not doc or not doc.text_content:
            logger.warning(f"文档 {document_id} 不存在或无文本内容")
            return {"entities_created": 0, "relationships_created": 0, "timeline_events": 0}

        logger.info(f"🔍 开始从文档 {doc.filename} 提取实体...")

        # 1. 提取实体
        extracted_entities = self.extractor.extract_entities(doc.text_content, min_confidence=0.6)
        logger.info(f"✅ 提取到 {len(extracted_entities)} 个实体")

        entities_created = 0
        entity_map = {}  # name -> entity_id

        for ent_data in extracted_entities:
            # 检查实体是否已存在
            existing = self.db.query(Entity).filter(
                Entity.name == ent_data['name'],
                Entity.entity_type == ent_data['type']
            ).first()

            if existing:
                # 更新提及次数
                existing.mention_count += ent_data['mention_count']
                existing.confidence = max(existing.confidence, ent_data['confidence'])

                # 添加文档ID
                if existing.document_ids is None:
                    existing.document_ids = []
                if document_id not in existing.document_ids:
                    existing.document_ids.append(document_id)
                    # 标记为已修改
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(existing, "document_ids")

                entity_map[ent_data['name']] = existing.id
                logger.debug(f"更新已有实体: {existing.name}")
            else:
                # 创建新实体
                new_entity = Entity(
                    entity_type=ent_data['type'],
                    name=ent_data['name'],
                    confidence=ent_data['confidence'],
                    mention_count=ent_data['mention_count'],
                    document_ids=[document_id],
                    first_mentioned_doc=str(document_id),
                    properties={"positions": ent_data.get('positions', [])}
                )
                self.db.add(new_entity)
                self.db.flush()  # 获取ID
                entity_map[ent_data['name']] = new_entity.id
                entities_created += 1
                logger.debug(f"创建新实体: {new_entity.name} ({new_entity.entity_type})")

        self.db.commit()
        logger.info(f"✅ 创建 {entities_created} 个新实体，更新 {len(extracted_entities) - entities_created} 个已有实体")

        # 2. 提取关系（简化版：存储在Entity的related_entities字段）
        relationships = self.extractor.extract_relationships(extracted_entities, doc.text_content)
        relationships_created = 0

        for rel in relationships:
            from_name = rel['from']
            to_name = rel['to']

            if from_name in entity_map and to_name in entity_map:
                from_entity = self.db.query(Entity).filter(Entity.id == entity_map[from_name]).first()
                if from_entity:
                    if from_entity.related_entities is None:
                        from_entity.related_entities = []

                    relation_data = {
                        "entity_id": entity_map[to_name],
                        "relation_type": rel['type'],
                        "confidence": rel['confidence']
                    }

                    if relation_data not in from_entity.related_entities:
                        from_entity.related_entities.append(relation_data)
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(from_entity, "related_entities")
                        relationships_created += 1

        self.db.commit()
        logger.info(f"✅ 创建 {relationships_created} 个实体关系")

        # 3. 提取时间线事件
        time_expressions = self.extractor.extract_time_expressions(doc.text_content)
        timeline_events = 0

        for time_expr in time_expressions:
            # 为每个时间表达式创建时间线事件
            event = TimelineEvent(
                date=time_expr['parsed'],
                title=f"{doc.filename} - {time_expr['raw']}",
                description=f"从文档中提取的时间点：{time_expr['raw']}",
                category="document_extraction",
                document_ids=[document_id],
                source=doc.filename,
                confidence=time_expr['confidence'],
                tags=["auto-extracted"]
            )
            self.db.add(event)
            timeline_events += 1

        self.db.commit()
        logger.info(f"✅ 创建 {timeline_events} 个时间线事件")

        # 4. 更新文档的实体字段
        doc.entities = extracted_entities
        self.db.commit()

        return {
            "entities_created": entities_created,
            "entities_updated": len(extracted_entities) - entities_created,
            "relationships_created": relationships_created,
            "timeline_events": timeline_events,
            "document_id": document_id
        }

    def build_from_project(self, project_id: int, force_rebuild: bool = False) -> Dict:
        """
        从项目的所有文档构建知识图谱

        Args:
            project_id: 项目ID
            force_rebuild: 是否强制重建（清空已有实体）

        Returns:
            总体统计
        """
        logger.info(f"🚀 开始为项目 {project_id} 构建知识图谱...")

        if force_rebuild:
            # 删除项目相关的所有实体和时间线
            logger.warning(f"⚠️ 强制重建：清空项目 {project_id} 的已有实体和时间线")
            self.db.query(Entity).filter(
                Entity.document_ids.contains([str(project_id)])
            ).delete(synchronize_session=False)

            # 查询该项目的所有文档ID
            doc_ids = [doc.id for doc in self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()]

            if doc_ids:
                self.db.query(TimelineEvent).filter(
                    TimelineEvent.document_ids.in_(doc_ids)
                ).delete(synchronize_session=False)

            self.db.commit()

        # 获取项目所有已处理的文档
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed",
            ProjectDocument.text_content.isnot(None)
        ).all()

        logger.info(f"📚 找到 {len(documents)} 个待处理文档")

        total_stats = {
            "documents_processed": 0,
            "entities_created": 0,
            "entities_updated": 0,
            "relationships_created": 0,
            "timeline_events": 0,
            "errors": []
        }

        for doc in documents:
            try:
                stats = self.build_from_document(doc.id, project_id)
                total_stats["documents_processed"] += 1
                total_stats["entities_created"] += stats["entities_created"]
                total_stats["entities_updated"] += stats.get("entities_updated", 0)
                total_stats["relationships_created"] += stats["relationships_created"]
                total_stats["timeline_events"] += stats["timeline_events"]
            except Exception as e:
                logger.error(f"❌ 处理文档 {doc.filename} 失败: {e}", exc_info=True)
                total_stats["errors"].append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "error": str(e)
                })

        logger.info(f"🎉 知识图谱构建完成: {total_stats}")
        return total_stats

    def get_graph_visualization_data(self, project_id: int, limit: int = 100) -> Dict:
        """
        获取可视化数据（vis-network格式）

        Returns:
            {"nodes": [...], "edges": [...]}
        """
        # 获取项目相关文档
        doc_ids = [doc.id for doc in self.db.query(ProjectDocument.id).filter(
            ProjectDocument.project_id == project_id
        ).all()]

        if not doc_ids:
            return {"nodes": [], "edges": []}

        # 查询实体（限制数量）
        entities = self.db.query(Entity).filter(
            Entity.document_ids.isnot(None)
        ).limit(limit).all()

        # 过滤：只保留与项目相关的实体
        relevant_entities = []
        for ent in entities:
            if ent.document_ids and any(doc_id in doc_ids for doc_id in ent.document_ids):
                relevant_entities.append(ent)

        # 构建节点
        nodes = []
        entity_id_map = {}

        for idx, entity in enumerate(relevant_entities):
            entity_id_map[entity.id] = idx
            nodes.append({
                "id": idx,
                "label": entity.name,
                "title": f"{entity.name} ({entity.entity_type})\n提及次数: {entity.mention_count}",
                "group": entity.entity_type,
                "value": entity.mention_count,  # 节点大小
                "font": {"size": 14 + min(entity.mention_count * 2, 20)},
                "entity_id": entity.id
            })

        # 构建边
        edges = []
        edge_id = 0
        for entity in relevant_entities:
            if entity.related_entities:
                from_idx = entity_id_map.get(entity.id)
                if from_idx is not None:
                    for rel in entity.related_entities:
                        to_id = rel.get("entity_id")
                        to_idx = entity_id_map.get(to_id)
                        if to_idx is not None:
                            edges.append({
                                "id": edge_id,
                                "from": from_idx,
                                "to": to_idx,
                                "label": rel.get("relation_type", "related"),
                                "arrows": "to",
                                "width": 1 + rel.get("confidence", 0.5) * 2
                            })
                            edge_id += 1

        logger.info(f"📊 生成可视化数据: {len(nodes)} 个节点, {len(edges)} 条边")
        return {"nodes": nodes, "edges": edges}


def get_knowledge_graph_builder(db: Session) -> KnowledgeGraphBuilder:
    """获取知识图谱构建器"""
    return KnowledgeGraphBuilder(db)
