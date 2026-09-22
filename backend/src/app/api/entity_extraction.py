"""
实体提取 API 端点
用于重新提取文档实体、修复实体关联
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging

from app.database import get_db
from app.services.entity_service import EntityService
from app.models.document import Document
from app.models.entity import Entity, DocumentEntity

logger = logging.getLogger(__name__)
router = APIRouter(tags=["实体提取"])


@router.post("/documents/{doc_id}/extract", response_model=dict)
async def extract_entities_from_document(
    doc_id: str,
    force: bool = Query(False, description="是否强制重新提取（覆盖已有实体）"),
    db: Session = Depends(get_db),
):
    """
    从文档重新提取实体

    Args:
        doc_id: 文档ID
        force: 是否强制重新提取
        db: 数据库会话

    Returns:
        dict: 提取结果统计
    """
    # 检查文档是否存在
    document = db.query(Document).filter_by(id=doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # 检查是否已有实体（通过关系表）
    existing_count = (
        db.query(Entity)
        .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
        .filter(DocumentEntity.document_id == doc_id)
        .count()
    )
    if existing_count > 0 and not force:
        return {
            "status": "skipped",
            "message": f"Document already has {existing_count} entities. Use force=true to re-extract.",
            "existing_entities": existing_count,
        }

    # 如果强制重新提取，删除旧实体关系
    if force and existing_count > 0:
        db.query(DocumentEntity).filter_by(document_id=doc_id).delete()
        db.commit()
        logger.info(f"Deleted {existing_count} existing entity relations for document {doc_id}")

    # 执行实体提取
    try:
        service = EntityService(db)
        entities = await service.extract_entities_from_document(doc_id)

        return {
            "status": "success",
            "message": f"Successfully extracted {len(entities)} entities",
            "document_id": doc_id,
            "document_name": document.name,
            "extracted_count": len(entities),
            "previous_count": existing_count if force else 0,
        }
    except Exception as e:
        logger.error(f"Failed to extract entities from document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@router.post("/projects/{project_id}/extract", response_model=dict)
async def extract_entities_from_project(
    project_id: int,
    force: bool = Query(False, description="是否强制重新提取"),
    db: Session = Depends(get_db),
):
    """
    从项目的所有文档提取实体

    Args:
        project_id: 项目ID
        force: 是否强制重新提取
        db: 数据库会话

    Returns:
        dict: 提取结果统计
    """
    # 获取项目所有文档
    documents = db.query(Document).filter_by(project_id=project_id).all()
    if not documents:
        raise HTTPException(status_code=404, detail=f"No documents found in project {project_id}")

    service = EntityService(db)
    results = {
        "project_id": project_id,
        "total_documents": len(documents),
        "processed": 0,
        "extracted_count": 0,
        "skipped": 0,
        "failed": 0,
        "details": [],
    }

    for doc in documents:
        try:
            # 检查是否已有实体（通过关系表）
            existing_count = (
                db.query(Entity)
                .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
                .filter(DocumentEntity.document_id == doc.id)
                .count()
            )
            if existing_count > 0 and not force:
                results["skipped"] += 1
                results["details"].append({
                    "document_id": doc.id,
                    "document_name": doc.name,
                    "status": "skipped",
                    "existing_entities": existing_count,
                })
                continue

            # 强制重新提取则删除旧数据
            if force and existing_count > 0:
                db.query(DocumentEntity).filter_by(document_id=doc.id).delete()
                db.commit()

            # 提取实体
            entities = await service.extract_entities_from_document(doc.id)
            results["processed"] += 1
            results["extracted_count"] += len(entities)
            results["details"].append({
                "document_id": doc.id,
                "document_name": doc.name,
                "status": "success",
                "extracted_count": len(entities),
            })
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "document_id": doc.id,
                "document_name": doc.name,
                "status": "failed",
                "error": str(e),
            })
            logger.error(f"Failed to extract entities from document {doc.id}: {e}")

    return results


@router.post("/documents/{doc_id}/extract", response_model=dict)
async def extract_document_entities(
    doc_id: str,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """
    重新提取文档实体

    Args:
        doc_id: 文档ID
        force: 是否强制重新提取（删除已有实体）
        db: 数据库会话

    Returns:
        dict: 提取结果
    """
    from app.services.entity_service import EntityExtractionService

    # 验证文档存在
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 检查是否已有实体
    from sqlalchemy import func
    existing_count = (
        db.query(func.count(Entity.id))
        .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
        .filter(DocumentEntity.document_id == doc_id)
        .scalar()
    )

    if existing_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Document already has {existing_count} entities. Use force=true to re-extract."
        )

    # 如果强制重新提取，删除已有实体关联
    if force and existing_count > 0:
        db.query(DocumentEntity).filter(DocumentEntity.document_id == doc_id).delete()
        db.commit()

    # 执行实体提取
    service = EntityExtractionService(db)
    try:
        entities = await service.extract_entities_from_document(doc_id)

        return {
            "document_id": doc_id,
            "document_name": doc.name,
            "entities_extracted": len(entities),
            "entities": [
                {
                    "id": e.id,
                    "text": e.text,
                    "type": e.type,
                    "metadata": e.metadata_json
                }
                for e in entities[:50]  # 只返回前50个实体
            ],
            "total_entities": len(entities)
        }
    except Exception as e:
        logger.error(f"Entity extraction failed for document {doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.get("/documents/{doc_id}/stats", response_model=dict)
async def get_document_entity_stats(
    doc_id: str,
    db: Session = Depends(get_db),
):
    """
    获取文档的实体统计信息

    Args:
        doc_id: 文档ID
        db: 数据库会话

    Returns:
        dict: 实体统计
    """
    document = db.query(Document).filter_by(id=doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # 统计实体（通过关系表）
    from sqlalchemy import func

    entity_stats = (
        db.query(Entity.type, func.count(Entity.id))
        .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
        .filter(DocumentEntity.document_id == doc_id)
        .group_by(Entity.type)
        .all()
    )

    total_entities = (
        db.query(func.count(Entity.id))
        .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
        .filter(DocumentEntity.document_id == doc_id)
        .scalar()
    )

    # 获取文档块数量
    from app.models.document_chunk import DocumentChunk
    chunk_count = db.query(func.count(DocumentChunk.id)).filter_by(document_id=doc_id).scalar()

    return {
        "document_id": doc_id,
        "document_name": document.name,
        "total_entities": total_entities,
        "total_chunks": chunk_count,
        "entity_types": {et: count for et, count in entity_stats},
        "has_entities": total_entities > 0,
        "needs_extraction": total_entities == 0 and chunk_count > 0,
    }
