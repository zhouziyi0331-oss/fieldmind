"""
实体服务统一接口
整合现有的多个实体提取服务，提供统一的API
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, DocumentEntity

logger = logging.getLogger(__name__)


class EntityService:
    """实体提取服务统一接口"""

    def __init__(self, db: Session):
        self.db = db

    async def extract_entities_from_document(self, doc_id: str) -> List[Entity]:
        """
        从文档提取实体

        Args:
            doc_id: 文档ID

        Returns:
            List[Entity]: 提取的实体列表
        """
        # 获取文档
        document = self.db.query(Document).filter_by(id=doc_id).first()
        if not document:
            raise ValueError(f"Document {doc_id} not found")

        # 获取文档块
        chunks = self.db.query(DocumentChunk).filter_by(document_id=doc_id).all()
        if not chunks:
            logger.warning(f"Document {doc_id} has no chunks")
            return []

        # 尝试使用现有的实体提取服务
        entities = []
        try:
            # 方案1: 使用 entity_extraction_service
            from app.services.entity_extraction_service import EntityExtractionService

            extraction_service = EntityExtractionService(self.db)

            # 检查服务是否有extract方法
            if hasattr(extraction_service, 'extract_entities_from_text'):
                for chunk in chunks:
                    if not chunk.content:
                        continue

                    # 提取实体
                    extracted = await extraction_service.extract_entities_from_text(
                        text=chunk.content,
                        doc_id=doc_id
                    )
                    entities.extend(extracted)
            else:
                # 服务接口不匹配，使用简单方法
                logger.warning("EntityExtractionService interface mismatch, using simple extraction")
                entities = await self._extract_entities_simple(doc_id, chunks)

        except ImportError:
            logger.warning("EntityExtractionService not available, trying alternative methods")

            try:
                # 方案2: 使用简单的正则提取
                entities = await self._extract_entities_simple(doc_id, chunks)
            except Exception as e:
                logger.error(f"Simple entity extraction failed: {e}")
                entities = []
        except Exception as e:
            logger.warning(f"EntityExtractionService failed: {e}, falling back to simple extraction")
            try:
                entities = await self._extract_entities_simple(doc_id, chunks)
            except Exception as e2:
                logger.error(f"Simple entity extraction failed: {e2}")
                entities = []

        # 保存实体到数据库并创建关系
        saved_entities = []
        for entity in entities:
            try:
                # 检查实体是否已存在（基于text+type的唯一约束）
                existing = (
                    self.db.query(Entity)
                    .filter(Entity.text == entity.text, Entity.type == entity.type)
                    .first()
                )

                if existing:
                    # 使用已存在的实体
                    entity_id = existing.id
                else:
                    # 保存新实体
                    self.db.add(entity)
                    self.db.flush()  # 获取entity.id
                    entity_id = entity.id
                    saved_entities.append(entity)

                # 检查文档-实体关系是否已存在
                existing_relation = (
                    self.db.query(DocumentEntity)
                    .filter(
                        DocumentEntity.document_id == doc_id,
                        DocumentEntity.entity_id == entity_id
                    )
                    .first()
                )

                if not existing_relation:
                    # 获取下一个可用的ID
                    from sqlalchemy import func
                    max_id = self.db.query(func.max(DocumentEntity.id)).scalar() or 0
                    next_id = max_id + 1

                    # 创建文档-实体关系（手动设置ID）
                    doc_entity = DocumentEntity(
                        id=next_id,
                        document_id=doc_id,
                        entity_id=entity_id,
                        mentions=1
                    )
                    self.db.add(doc_entity)

            except Exception as e:
                logger.error(f"Failed to save entity {entity.text}: {e}")
                self.db.rollback()  # 回滚失败的事务

        self.db.commit()
        logger.info(f"Extracted {len(saved_entities)} entities from document {doc_id}")

        return saved_entities

    async def _extract_entities_simple(
        self,
        doc_id: str,
        chunks: List[DocumentChunk]
    ) -> List[Entity]:
        """
        简单的实体提取（基于规则和模式）

        Args:
            doc_id: 文档ID
            chunks: 文档块列表

        Returns:
            List[Entity]: 提取的实体
        """
        import re
        entities = []

        # 合并所有块的文本
        full_text = "\n".join([chunk.content for chunk in chunks if chunk.content])

        # 简单的中文人名提取（姓氏+名字模式）
        chinese_surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤"
        name_pattern = f"[{chinese_surnames}][\\u4e00-\\u9fa5]{{1,2}}"

        names = re.findall(name_pattern, full_text)
        for name in set(names[:50]):  # 限制数量
            entity = Entity(
                text=name,
                type="PERSON",
                confidence=0.6,
                metadata_json={"extraction_method": "regex"}
            )
            entities.append(entity)

        # 提取地名（带"村"、"镇"、"市"、"省"等）
        place_pattern = "[\\u4e00-\\u9fa5]{2,8}(村|镇|市|省|县|区|乡|街道)"
        places = re.findall(place_pattern, full_text)
        for place in set(places[:50]):
            entity = Entity(
                text=place,
                type="LOCATION",
                confidence=0.7,
                metadata_json={"extraction_method": "regex"}
            )
            entities.append(entity)

        # 提取组织名（带"公司"、"学校"、"协会"等）
        org_pattern = "[\\u4e00-\\u9fa5]{2,12}(公司|学校|大学|协会|组织|机构|委员会|研究所|中心)"
        orgs = re.findall(org_pattern, full_text)
        for org in set(orgs[:50]):
            entity = Entity(
                text=org,
                type="ORG",
                confidence=0.7,
                metadata_json={"extraction_method": "regex"}
            )
            entities.append(entity)

        logger.info(f"Simple extraction found {len(entities)} entities in document {doc_id}")
        return entities

    def get_document_entities(
        self,
        doc_id: str,
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """
        获取文档的实体列表

        Args:
            doc_id: 文档ID
            entity_type: 实体类型过滤

        Returns:
            List[Entity]: 实体列表
        """
        query = (
            self.db.query(Entity)
            .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
            .filter(DocumentEntity.document_id == doc_id)
        )

        if entity_type:
            query = query.filter(Entity.type == entity_type)

        return query.all()

    def get_entity_stats(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档实体统计

        Args:
            doc_id: 文档ID

        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import func

        stats = (
            self.db.query(
                Entity.type,
                func.count(Entity.id).label('count')
            )
            .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
            .filter(DocumentEntity.document_id == doc_id)
            .group_by(Entity.type)
            .all()
        )

        return {
            "total": sum(s.count for s in stats),
            "by_type": {s.type: s.count for s in stats}
        }
