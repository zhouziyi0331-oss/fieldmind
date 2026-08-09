"""
证据链提取服务 - 链路16核心

从ChromaDB的chunk中提取实体证据：
1. 识别chunk中的实体
2. 提取包含实体的句子作为证据
3. 绑定音频时间戳（如果是音频chunk）
4. 分类到衣食住行等维度
5. 存储到EntityEvidence表
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import re
import logging

from app.services.entity_extraction import get_entity_extraction_service
from app.services.entity_categorizer import get_entity_categorizer
from app.services.vectorization_service_v2 import get_vectorization_service_v2
from app.models.entity import Entity
from app.models.entity_evidence import EntityEvidence
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)


class EvidenceExtractor:
    """证据链提取器"""

    def __init__(self, db: Session):
        self.db = db
        self.entity_service = get_entity_extraction_service()
        self.categorizer = get_entity_categorizer()
        self.vectorizer = get_vectorization_service_v2()

    def extract_from_document(
        self,
        document_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        从文档提取证据链

        Args:
            document_id: 文档ID
            project_id: 项目ID

        Returns:
            统计信息
        """
        # 获取文档
        document = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise ValueError(f"文档 {document_id} 不存在")

        # 获取文档的所有chunks（从ChromaDB）
        chunks = self._get_document_chunks(document_id)

        if not chunks:
            logger.warning(f"文档 {document_id} 没有chunks")
            return {
                "document_id": document_id,
                "chunks_processed": 0,
                "entities_found": 0,
                "evidences_created": 0
            }

        # 逐chunk提取证据
        total_entities = set()
        total_evidences = 0

        for chunk in chunks:
            result = self._extract_from_chunk(
                chunk=chunk,
                document_id=document_id,
                project_id=project_id
            )
            total_entities.update(result["entity_ids"])
            total_evidences += result["evidences_created"]

        return {
            "document_id": document_id,
            "chunks_processed": len(chunks),
            "entities_found": len(total_entities),
            "evidences_created": total_evidences
        }

    def _get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """
        从ChromaDB获取文档的所有chunks

        Returns:
            [{"id": "doc1_chunk0", "text": "...", "metadata": {...}}]
        """
        try:
            # 查询ChromaDB
            results = self.vectorizer.collection.get(
                where={"document_id": str(document_id)},
                include=["metadatas", "documents"]
            )

            if not results or not results.get("ids"):
                return []

            chunks = []
            for i, chunk_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                text = results["documents"][i] if results.get("documents") else ""

                chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "metadata": metadata
                })

            return chunks

        except Exception as e:
            logger.error(f"获取chunks失败: {e}")
            return []

    def _extract_from_chunk(
        self,
        chunk: Dict[str, Any],
        document_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        从单个chunk提取证据

        Returns:
            {"entity_ids": [...], "evidences_created": 3}
        """
        chunk_id = chunk["id"]
        text = chunk["text"]
        metadata = chunk["metadata"]

        if not text or not text.strip():
            return {"entity_ids": [], "evidences_created": 0}

        # 1. 提取实体
        entities = self.entity_service.extract_entities(text, min_confidence=0.6)

        if not entities:
            return {"entity_ids": [], "evidences_created": 0}

        # 2. 对实体进行分类
        entity_categories = self.categorizer.categorize_batch(
            entities,
            context_map={e["name"]: text for e in entities}
        )

        # 3. 为每个实体创建或更新Entity记录
        entity_ids = []
        evidences_created = 0

        for entity_data in entities:
            entity_name = entity_data["name"]
            entity_type = entity_data["type"]
            confidence = entity_data["confidence"]

            # 获取或创建Entity
            entity = self._get_or_create_entity(
                name=entity_name,
                entity_type=entity_type,
                document_id=document_id,
                project_id=project_id,
                confidence=confidence
            )
            entity_ids.append(entity.id)

            # 4. 提取包含该实体的句子作为证据
            evidence_text = self._extract_evidence_sentence(text, entity_name)

            # 5. 创建Evidence记录
            evidence = EntityEvidence(
                entity_id=entity.id,
                document_id=document_id,
                chunk_id=chunk_id,
                text=evidence_text,
                context=text[:500],  # 保留最多500字的上下文
                confidence=confidence,
                category=entity_categories.get(entity_name),
                # 音频时间戳（如果有）
                media_type=metadata.get("media_type"),
                timestamp_start=metadata.get("timestamp_start"),
                timestamp_end=metadata.get("timestamp_end"),
                timestamp_display=metadata.get("timestamp_range") or metadata.get("timestamp_display"),
                speaker=metadata.get("speaker"),
                # PDF页码（如果有）
                page_number=metadata.get("page_number")
            )

            self.db.add(evidence)
            evidences_created += 1

        # 批量提交
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"提交证据失败: {e}")
            self.db.rollback()

        return {
            "entity_ids": entity_ids,
            "evidences_created": evidences_created
        }

    def _get_or_create_entity(
        self,
        name: str,
        entity_type: str,
        document_id: int,
        project_id: int,
        confidence: float
    ) -> Entity:
        """
        获取或创建Entity记录

        如果实体已存在，更新mention_count和document_ids
        """
        # 查找现有实体
        entity = self.db.query(Entity).filter(
            Entity.name == name,
            Entity.entity_type == entity_type
        ).first()

        if entity:
            # 更新统计信息
            entity.mention_count += 1

            # 添加document_id（去重）
            doc_ids = entity.document_ids or []
            if document_id not in doc_ids:
                doc_ids.append(document_id)
                entity.document_ids = doc_ids

            # 更新置信度（取最大值）
            if confidence > entity.confidence:
                entity.confidence = confidence

        else:
            # 创建新实体
            entity = Entity(
                name=name,
                entity_type=entity_type,
                document_ids=[document_id],
                first_mentioned_doc=str(document_id),
                confidence=confidence,
                mention_count=1
            )
            self.db.add(entity)
            self.db.flush()  # 立即刷新以获取entity.id

        return entity

    def _extract_evidence_sentence(self, text: str, entity_name: str) -> str:
        """
        提取包含实体的句子

        Args:
            text: 全文
            entity_name: 实体名称

        Returns:
            包含实体的句子（如果有多句，返回第一句）
        """
        # 按句子分割
        sentences = re.split(r'[。！？\n]', text)

        for sentence in sentences:
            if entity_name in sentence:
                return sentence.strip()

        # 如果没找到句子，返回整段文本（最多200字）
        return text[:200]

    def get_entity_evidences(
        self,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取实体的所有证据

        Args:
            entity_id: 实体ID
            limit: 返回数量限制

        Returns:
            证据列表（按时间排序）
        """
        evidences = self.db.query(EntityEvidence).filter(
            EntityEvidence.entity_id == entity_id
        ).order_by(
            EntityEvidence.timestamp_start.asc().nullslast(),
            EntityEvidence.created_at.desc()
        ).limit(limit).all()

        return [ev.to_dict() for ev in evidences]

    def search_evidences_by_category(
        self,
        category: str,
        project_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        按分类搜索证据

        Args:
            category: 分类（food/clothing/housing/transportation/folk_song）
            project_id: 项目ID
            limit: 返回数量

        Returns:
            证据列表
        """
        # 获取项目的所有文档ID
        doc_ids = [doc.id for doc in self.db.query(ProjectDocument.id).filter(
            ProjectDocument.project_id == project_id
        ).all()]

        if not doc_ids:
            return []

        # 查询证据
        evidences = self.db.query(EntityEvidence).filter(
            EntityEvidence.category == category,
            EntityEvidence.document_id.in_(doc_ids)
        ).limit(limit).all()

        return [ev.to_dict() for ev in evidences]


def get_evidence_extractor(db: Session) -> EvidenceExtractor:
    """获取证据提取器"""
    return EvidenceExtractor(db)
