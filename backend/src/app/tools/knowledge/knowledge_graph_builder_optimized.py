"""知识图谱构建服务 - 性能优化版本"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
from datetime import datetime
from collections import defaultdict

from app.models.project import ProjectDocument
from app.models.entity import Entity, EntityType
from app.models.timeline import TimelineEvent
from app.tools.entity import create_engine

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilderOptimized:
    """知识图谱构建器 - 优化版"""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = create_engine()
        # 缓存：避免重复查询
        self._entity_cache = {}

    def build_from_document(self, document_id: int, project_id: int) -> Dict:
        """
        从单个文档构建知识图谱（优化版）

        优化点：
        1. 批量查询已存在实体（减少N+1问题）
        2. 批量插入新实体
        3. 合并事务提交（减少事务开销）
        4. 使用缓存避免重复查询
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

        # === 优化1: 批量查询已存在实体 ===
        entity_names = [e['name'] for e in extracted_entities]
        entity_types = [e['type'] for e in extracted_entities]

        # 一次查询获取所有可能存在的实体
        existing_entities = self.db.query(Entity).filter(
            Entity.name.in_(entity_names)
        ).all()

        # 构建快速查找映射：(name, type) -> Entity
        existing_map = {
            (e.name, e.entity_type): e
            for e in existing_entities
        }

        logger.info(f"📊 找到 {len(existing_entities)} 个已存在实体")

        # === 优化2: 批量处理实体 ===
        entities_to_create = []
        entities_to_update = []
        entity_map = {}  # name -> entity_id

        for ent_data in extracted_entities:
            key = (ent_data['name'], ent_data['type'])
            existing = existing_map.get(key)

            if existing:
                # 更新已有实体
                existing.mention_count += ent_data['mention_count']
                existing.confidence = max(existing.confidence, ent_data['confidence'])

                # 添加文档ID
                if existing.document_ids is None:
                    existing.document_ids = []
                if document_id not in existing.document_ids:
                    existing.document_ids.append(document_id)
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(existing, "document_ids")

                entities_to_update.append(existing)
                entity_map[ent_data['name']] = existing.id
            else:
                # 准备创建新实体
                new_entity = Entity(
                    entity_type=ent_data['type'],
                    name=ent_data['name'],
                    confidence=ent_data['confidence'],
                    mention_count=ent_data['mention_count'],
                    document_ids=[document_id],
                    first_mentioned_doc=str(document_id),
                    properties={"positions": ent_data.get('positions', [])}
                )
                entities_to_create.append(new_entity)

        # === 优化3: 批量添加到会话 ===
        entities_created = len(entities_to_create)
        for entity in entities_to_create:
            self.db.add(entity)

        # 刷新以获取ID
        self.db.flush()

        # 更新entity_map（新创建的实体）
        for entity in entities_to_create:
            entity_map[entity.name] = entity.id

        logger.info(f"✅ 准备创建 {entities_created} 个新实体，更新 {len(entities_to_update)} 个已有实体")

        # 2. 批量提取和处理关系
        relationships = self.extractor.extract_relationships(extracted_entities, doc.text_content)
        relationships_created = 0

        # 批量获取需要更新的实体
        entities_needing_update = {}

        for rel in relationships:
            from_name = rel['from']
            to_name = rel['to']

            if from_name in entity_map and to_name in entity_map:
                from_id = entity_map[from_name]

                # 收集需要更新的关系
                if from_id not in entities_needing_update:
                    from_entity = self.db.query(Entity).filter(Entity.id == from_id).first()
                    if from_entity:
                        if from_entity.related_entities is None:
                            from_entity.related_entities = []
                        entities_needing_update[from_id] = from_entity

                if from_id in entities_needing_update:
                    from_entity = entities_needing_update[from_id]
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

        logger.info(f"✅ 准备创建 {relationships_created} 个实体关系")

        # 3. 批量创建时间线事件
        time_expressions = self.extractor.extract_time_expressions(doc.text_content)
        timeline_events_list = []

        for time_expr in time_expressions:
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
            timeline_events_list.append(event)
            self.db.add(event)

        timeline_events = len(timeline_events_list)
        logger.info(f"✅ 准备创建 {timeline_events} 个时间线事件")

        # 4. 更新文档的实体字段
        doc.entities = extracted_entities

        # === 优化4: 一次性提交所有更改 ===
        try:
            self.db.commit()
            logger.info(f"✅ 成功提交所有更改到数据库")
        except Exception as e:
            logger.error(f"❌ 提交失败: {e}")
            self.db.rollback()
            raise

        return {
            "entities_created": entities_created,
            "entities_updated": len(entities_to_update),
            "relationships_created": relationships_created,
            "timeline_events": timeline_events
        }

    def build_from_project(self, project_id: int, force_rebuild: bool = False) -> Dict:
        """
        从项目所有文档构建知识图谱（优化版）

        优化点：
        1. 批量查询文档
        2. 按批次处理，避免内存溢出
        3. 进度跟踪
        """
        # 获取项目所有文档
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        if not documents:
            logger.warning(f"项目 {project_id} 没有文档")
            return {
                "documents_processed": 0,
                "entities_created": 0,
                "entities_updated": 0,
                "relationships_created": 0,
                "timeline_events": 0,
                "errors": []
            }

        logger.info(f"📚 开始处理项目 {project_id} 的 {len(documents)} 个文档...")

        total_stats = {
            "documents_processed": 0,
            "entities_created": 0,
            "entities_updated": 0,
            "relationships_created": 0,
            "timeline_events": 0,
            "errors": []
        }

        # 分批处理文档（每批10个）
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"📦 处理批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

            for doc in batch:
                try:
                    stats = self.build_from_document(doc.id, project_id)
                    total_stats["documents_processed"] += 1
                    total_stats["entities_created"] += stats["entities_created"]
                    total_stats["entities_updated"] += stats.get("entities_updated", 0)
                    total_stats["relationships_created"] += stats["relationships_created"]
                    total_stats["timeline_events"] += stats["timeline_events"]

                    logger.info(f"✅ 完成 {doc.filename}: {stats['entities_created']} 实体, {stats['relationships_created']} 关系")
                except Exception as e:
                    logger.error(f"❌ 处理文档 {doc.id} ({doc.filename}) 失败: {e}")
                    total_stats["errors"].append({
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "error": str(e)
                    })

        logger.info(f"🎉 项目处理完成: {total_stats}")
        return total_stats

    def get_graph_visualization_data(self, project_id: int, limit: int = 100) -> Dict:
        """获取知识图谱可视化数据（优化版）"""
        # 获取项目的所有文档ID
        doc_ids = [doc.id for doc in self.db.query(ProjectDocument.id).filter(
            ProjectDocument.project_id == project_id
        ).all()]

        if not doc_ids:
            return {"nodes": [], "edges": []}

        # === 优化: 批量查询实体和关系 ===
        entities = self.db.query(Entity).filter(
            Entity.document_ids.isnot(None)
        ).order_by(
            Entity.mention_count.desc()
        ).limit(limit).all()

        # 过滤相关实体
        relevant_entities = [
            ent for ent in entities
            if ent.document_ids and any(doc_id in doc_ids for doc_id in ent.document_ids)
        ]

        # 构建节点
        nodes = []
        entity_id_map = {}

        for idx, ent in enumerate(relevant_entities):
            nodes.append({
                "id": idx,
                "label": ent.name,
                "group": ent.entity_type,
                "title": f"{ent.name} ({ent.entity_type})\n提及: {ent.mention_count}次",
                "value": ent.mention_count
            })
            entity_id_map[ent.id] = idx

        # 构建边
        edges = []
        edge_id = 0

        for ent in relevant_entities:
            if ent.related_entities:
                from_idx = entity_id_map.get(ent.id)
                if from_idx is not None:
                    for rel in ent.related_entities:
                        to_idx = entity_id_map.get(rel["entity_id"])
                        if to_idx is not None:
                            edges.append({
                                "id": edge_id,
                                "from": from_idx,
                                "to": to_idx,
                                "label": rel["relation_type"],
                                "title": f"{rel['relation_type']} (置信度: {rel['confidence']:.2f})"
                            })
                            edge_id += 1

        logger.info(f"📊 生成可视化数据: {len(nodes)} 节点, {len(edges)} 边")

        return {
            "nodes": nodes,
            "edges": edges
        }


# 单例模式
_builder_instance = None

def get_knowledge_graph_builder(db: Session) -> KnowledgeGraphBuilderOptimized:
    """获取知识图谱构建器实例（优化版）"""
    return KnowledgeGraphBuilderOptimized(db)
