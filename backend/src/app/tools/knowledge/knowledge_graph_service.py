"""
知识图谱数据库服务
提供实体、关系的增量持久化
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.knowledge_graph import Entity, Relation, CoOccurrence, KnowledgeGraph
from app.database import get_db

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱数据库服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 实体操作 ====================

    def save_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """
        保存或更新实体（跨文档合并）

        Args:
            entity_data: 实体数据字典
                {
                    "entity_id": "entity_0001",
                    "entity_name": "张三",
                    "entity_type": "人物",
                    "mention_count": 5,
                    "documents": ["doc_001"],
                    "contexts": ["上下文1", "上下文2"],
                    "related_entities": ["李四", "王五"],
                    "first_timestamp": 12.5
                }

        Returns:
            Entity: 保存的实体对象
        """
        entity_name = entity_data["entity_name"]
        entity_type = entity_data["entity_type"]

        # 查找是否已存在（按名称+类型）
        existing = self.db.query(Entity).filter(
            and_(
                Entity.entity_name == entity_name,
                Entity.entity_type == entity_type
            )
        ).first()

        if existing:
            # 已存在：合并数据
            existing.mention_count += entity_data.get("mention_count", 1)

            # 合并文档列表（去重）
            existing_docs = set(existing.documents or [])
            new_docs = set(entity_data.get("documents", []))
            existing.documents = list(existing_docs | new_docs)

            # 合并上下文（限制数量）
            existing_contexts = existing.contexts or []
            new_contexts = entity_data.get("contexts", [])
            existing.contexts = (existing_contexts + new_contexts)[:10]

            # 合并关联实体（去重）
            existing_related = set(existing.related_entities or [])
            new_related = set(entity_data.get("related_entities", []))
            existing.related_entities = list(existing_related | new_related)

            existing.updated_at = datetime.utcnow()

            logger.debug(f"   ✅ 更新实体: {entity_name} (总提及: {existing.mention_count})")
            return existing
        else:
            # 不存在：新建
            new_entity = Entity(
                entity_id=entity_data["entity_id"],
                entity_name=entity_name,
                entity_type=entity_type,
                mention_count=entity_data.get("mention_count", 1),
                documents=entity_data.get("documents", []),
                contexts=entity_data.get("contexts", []),
                related_entities=entity_data.get("related_entities", []),
                first_timestamp=entity_data.get("first_timestamp", 0.0)
            )
            self.db.add(new_entity)
            logger.debug(f"   ✅ 新建实体: {entity_name}")
            return new_entity

    def get_entity_by_name(self, entity_name: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """根据名称查询实体"""
        query = self.db.query(Entity).filter(Entity.entity_name == entity_name)
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        return query.first()

    def get_all_entities(self, entity_type: Optional[str] = None, min_mentions: int = 0) -> List[Entity]:
        """获取所有实体"""
        query = self.db.query(Entity)
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        if min_mentions > 0:
            query = query.filter(Entity.mention_count >= min_mentions)
        return query.order_by(Entity.mention_count.desc()).all()

    # ==================== 关系操作 ====================

    def save_relation(self, relation_data: Dict[str, Any]) -> Relation:
        """
        保存关系

        Args:
            relation_data: 关系数据字典
                {
                    "relation_id": "rel_0001",
                    "subject": "张三",
                    "relation_type": "师徒",
                    "object": "李四",
                    "context": "张三教李四唱山歌",
                    "timestamp": 12.5,
                    "source_document": "doc_001",
                    "confidence": 0.9
                }

        Returns:
            Relation: 保存的关系对象
        """
        # 查找主体和客体实体
        subject = self.get_entity_by_name(relation_data["subject"])
        obj = self.get_entity_by_name(relation_data["object"])

        if not subject or not obj:
            logger.warning(f"   ⚠️ 实体不存在，跳过关系: {relation_data['subject']} -> {relation_data['object']}")
            return None

        # 检查关系是否已存在（避免重复）
        existing = self.db.query(Relation).filter(
            and_(
                Relation.subject_entity_id == subject.entity_id,
                Relation.relation_type == relation_data["relation_type"],
                Relation.object_entity_id == obj.entity_id,
                Relation.source_document == relation_data["source_document"]
            )
        ).first()

        if existing:
            logger.debug(f"   ⏭️ 关系已存在: {relation_data['subject']} --[{relation_data['relation_type']}]--> {relation_data['object']}")
            return existing

        # 创建新关系
        new_relation = Relation(
            relation_id=relation_data["relation_id"],
            subject_entity_id=subject.entity_id,
            relation_type=relation_data["relation_type"],
            object_entity_id=obj.entity_id,
            context=relation_data.get("context", ""),
            timestamp=relation_data.get("timestamp", 0.0),
            source_document=relation_data.get("source_document", ""),
            confidence=relation_data.get("confidence", 1.0)
        )
        self.db.add(new_relation)
        logger.debug(f"   ✅ 新建关系: {relation_data['subject']} --[{relation_data['relation_type']}]--> {relation_data['object']}")
        return new_relation

    def get_relations_by_entity(self, entity_name: str) -> List[Relation]:
        """获取某个实体的所有关系"""
        entity = self.get_entity_by_name(entity_name)
        if not entity:
            return []

        return self.db.query(Relation).filter(
            or_(
                Relation.subject_entity_id == entity.entity_id,
                Relation.object_entity_id == entity.entity_id
            )
        ).all()

    def get_all_relations(self, relation_type: Optional[str] = None) -> List[Relation]:
        """获取所有关系"""
        query = self.db.query(Relation)
        if relation_type:
            query = query.filter(Relation.relation_type == relation_type)
        return query.all()

    # ==================== 共现操作 ====================

    def save_co_occurrence(self, co_occurrence_data: Dict[str, Any]) -> CoOccurrence:
        """
        保存或更新共现关系

        Args:
            co_occurrence_data: 共现数据字典
                {
                    "entities": ["张三", "李四", "王五"],
                    "frequency": 5,
                    "window_type": "sentence"
                }

        Returns:
            CoOccurrence: 保存的共现对象
        """
        entities = sorted(co_occurrence_data["entities"])  # 排序确保一致性

        # 查找是否已存在
        existing = self.db.query(CoOccurrence).filter(
            CoOccurrence.entities == entities
        ).first()

        if existing:
            # 累加频次
            existing.frequency += co_occurrence_data.get("frequency", 1)
            existing.updated_at = datetime.utcnow()
            logger.debug(f"   ✅ 更新共现: {entities} (总频次: {existing.frequency})")
            return existing
        else:
            # 创建新共现
            new_co_occurrence = CoOccurrence(
                entities=entities,
                frequency=co_occurrence_data.get("frequency", 1),
                window_type=co_occurrence_data.get("window_type", "sentence")
            )
            self.db.add(new_co_occurrence)
            logger.debug(f"   ✅ 新建共现: {entities}")
            return new_co_occurrence

    def get_all_co_occurrences(self, min_frequency: int = 0) -> List[CoOccurrence]:
        """获取所有共现关系"""
        query = self.db.query(CoOccurrence)
        if min_frequency > 0:
            query = query.filter(CoOccurrence.frequency >= min_frequency)
        return query.order_by(CoOccurrence.frequency.desc()).all()

    # ==================== 知识图谱元数据 ====================

    def save_knowledge_graph_metadata(self, graph_data: Dict[str, Any]) -> KnowledgeGraph:
        """
        保存或更新知识图谱元数据

        Args:
            graph_data: 图谱元数据
                {
                    "graph_id": "graph_001",
                    "name": "田野调研知识图谱",
                    "description": "基于音频转录的知识图谱",
                    "entity_count": 100,
                    "relation_count": 50,
                    "document_count": 10,
                    "statistics": {...}
                }

        Returns:
            KnowledgeGraph: 保存的图谱元数据
        """
        graph_id = graph_data["graph_id"]

        existing = self.db.query(KnowledgeGraph).filter(
            KnowledgeGraph.graph_id == graph_id
        ).first()

        if existing:
            # 更新
            existing.entity_count = graph_data.get("entity_count", 0)
            existing.relation_count = graph_data.get("relation_count", 0)
            existing.document_count = graph_data.get("document_count", 0)
            existing.statistics = graph_data.get("statistics", {})
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            # 创建
            new_graph = KnowledgeGraph(
                graph_id=graph_id,
                name=graph_data.get("name", "未命名图谱"),
                description=graph_data.get("description", ""),
                entity_count=graph_data.get("entity_count", 0),
                relation_count=graph_data.get("relation_count", 0),
                document_count=graph_data.get("document_count", 0),
                statistics=graph_data.get("statistics", {})
            )
            self.db.add(new_graph)
            return new_graph

    # ==================== 批量操作 ====================

    def commit(self):
        """提交事务"""
        try:
            self.db.commit()
            logger.info("   ✅ 数据库事务提交成功")
        except Exception as e:
            self.db.rollback()
            logger.error(f"   ❌ 数据库事务提交失败: {e}")
            raise

    def rollback(self):
        """回滚事务"""
        self.db.rollback()
        logger.warning("   ⚠️ 数据库事务已回滚")
