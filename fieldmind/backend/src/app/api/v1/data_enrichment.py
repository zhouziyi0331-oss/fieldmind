"""
数据增强API端点
自动为项目补充 NLP 处理后的数据
"""
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response
from app.services.knowledge_enhancement_service import KnowledgeEnhancementService

router = APIRouter()


@router.post("/projects/{project_id}/enrich")
async def enrich_project_data(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    为项目自动补充 NLP 增强数据

    - 自动分类到 6 个大脉络
    - 提取关键词和实体
    - 提取时空上下文
    - 计算情感极性
    """
    service = KnowledgeEnhancementService(db)

    # 如果没有数据，先创建示例数据
    created_count = service.create_sample_chunks_if_empty(project_id)

    # 增强现有数据
    stats = service.enrich_project_chunks(project_id)

    return success_response(data={
        "message": "数据增强完成",
        "created_chunks": created_count,
        "enrichment_stats": stats
    })


@router.get("/projects/{project_id}/enrichment-status")
async def get_enrichment_status(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取项目的数据增强状态

    返回：
    - 总 chunk 数
    - 已增强的 chunk 数
    - 未增强的 chunk 数
    """
    from app.models.document_chunk import DocumentChunk
    from sqlalchemy import func, or_

    total_chunks = db.query(func.count(DocumentChunk.id)).filter(
        DocumentChunk.project_id == project_id
    ).scalar() or 0

    enriched_chunks = db.query(func.count(DocumentChunk.id)).filter(
        DocumentChunk.project_id == project_id,
        DocumentChunk.domain_tags.isnot(None),
        DocumentChunk.key_entities.isnot(None)
    ).scalar() or 0

    unenriched_chunks = total_chunks - enriched_chunks

    return success_response(data={
        "total_chunks": total_chunks,
        "enriched_chunks": enriched_chunks,
        "unenriched_chunks": unenriched_chunks,
        "enrichment_percentage": round(enriched_chunks / total_chunks * 100, 1) if total_chunks > 0 else 0
    })
