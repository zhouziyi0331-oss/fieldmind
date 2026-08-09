"""
文档处理API - 提供文档处理状态查询和控制
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.services.document_processing_pipeline import DocumentProcessingPipeline
from app.services.vectorization_service_complete import VectorizationService
from app.models.project import ProjectDocument
from app.tasks.document_tasks import process_document as celery_process_document

router = APIRouter(tags=["文档处理"])
logger = logging.getLogger(__name__)


@router.get("/documents/{document_id}/status")
async def get_processing_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档处理状态

    返回5个阶段的完成情况：
    - extract: 内容提取
    - clean: 数据清洗
    - chunk: 文档切分
    - vectorize: 向量化
    - index: 入库索引
    """
    pipeline = DocumentProcessingPipeline()
    status = pipeline.get_processing_status(document_id, db)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重新处理文档

    会删除旧的chunks，重新走完整流程
    """
    doc = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 添加到后台任务
    background_tasks.add_task(
        celery_process_document.delay,
        document_id
    )

    return {
        "message": "文档已加入重新处理队列",
        "document_id": document_id
    }


@router.get("/documents/{document_id}/chunks/preview")
async def get_chunks_preview(
    document_id: int,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    获取文档的chunks预览

    返回前N个chunks的信息（用于UI展示）
    """
    from app.services.vectorization_service_complete import DocumentChunk

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).limit(limit).all()

    if not chunks:
        raise HTTPException(status_code=404, detail="文档尚未切分或不存在")

    preview = []
    for chunk in chunks:
        preview_text = chunk.text
        if len(preview_text) > 100:
            preview_text = preview_text[:100] + "..."

        preview.append({
            "chunk_id": str(chunk.chunk_id) if chunk.chunk_id else "",
            "chunk_index": int(chunk.chunk_index) if chunk.chunk_index is not None else 0,
            "text_preview": preview_text,
            "text_length": int(chunk.text_length) if chunk.text_length else 0,
            "position": f"{chunk.start_pos}-{chunk.end_pos}",
            "has_embedding": bool(chunk.embedding is not None)
        })

    total_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()

    return {
        "document_id": document_id,
        "total_chunks": total_chunks,
        "preview_chunks": preview,
        "showing": len(preview)
    }


@router.get("/projects/{project_id}/chunks/statistics")
async def get_project_chunks_statistics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的chunks统计信息
    """
    vectorizer = VectorizationService()
    stats = vectorizer.get_chunk_statistics(project_id, db)

    return stats


@router.post("/projects/{project_id}/semantic-search")
async def semantic_search(
    project_id: int,
    query: str,
    top_k: int = 10,
    threshold: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    语义搜索 - 基于向量相似度

    Args:
        query: 查询文本
        top_k: 返回前K个结果
        threshold: 相似度阈值（0-1）

    Returns:
        匹配的chunks列表，按相似度排序
    """
    vectorizer = VectorizationService()

    # 使用project_id作为过滤条件
    filter_metadata = {"project_id": project_id} if project_id else None

    results = vectorizer.query_similar(
        query_text=query,
        top_k=top_k,
        filter_metadata=filter_metadata
    )

    # 过滤低于阈值的结果（distance越小越相似，转换为score）
    filtered_results = []
    for result in results:
        # ChromaDB返回的是距离，转换为相似度分数(0-1)
        score = 1 / (1 + result["distance"])
        if score >= threshold:
            filtered_results.append({
                "chunk_id": result["chunk_id"],
                "text": result["text"],
                "metadata": result["metadata"],
                "score": score
            })

    return {
        "query": query,
        "project_id": project_id,
        "total_results": len(filtered_results),
        "results": filtered_results
    }
