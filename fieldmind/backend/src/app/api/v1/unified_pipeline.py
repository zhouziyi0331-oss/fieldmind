"""
统一管道API端点
测试脏数据通道 → 干净数据通道 → 9步骤知识管道的完整流程
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import logging

from app.core.database import get_db
from app.services.unified_pipeline_coordinator import UnifiedPipelineCoordinator
from app.models.unified_pipeline import (
    DirtyChannelDocument,
    CleanChannelEvent,
    CleanChannelEntity,
    UnifiedProcessingRoute
)

router = APIRouter(prefix="/api/v1/unified-pipeline", tags=["unified-pipeline"])
logger = logging.getLogger(__name__)


@router.post("/process/{document_id}")
async def process_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    处理一个文档，通过统一管道：
    1. 脏数据通道：完整性优先，无损转换
    2. 干净数据通道：精准提取1-3个核心事件
    3. 9步骤知识管道：深度处理
    """
    try:
        coordinator = UnifiedPipelineCoordinator(db)
        result = await coordinator.process_document(document_id)

        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))

        return {
            "success": True,
            "message": "统一管道处理完成",
            "data": result
        }

    except Exception as e:
        logger.error(f"统一管道处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{document_id}")
async def get_processing_status(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取文档的处理状态
    """
    route = db.query(UnifiedProcessingRoute).filter_by(document_id=document_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="处理路由未找到")

    return {
        "document_id": document_id,
        "overall_status": route.overall_status,
        "dirty_channel": {
            "status": route.dirty_channel_status,
            "started_at": route.dirty_started_at,
            "completed_at": route.dirty_completed_at
        },
        "clean_channel": {
            "status": route.clean_channel_status,
            "events_count": route.clean_events_count,
            "entities_count": route.clean_entities_count,
            "relations_count": route.clean_relations_count,
            "started_at": route.clean_started_at,
            "completed_at": route.clean_completed_at
        },
        "nine_step_pipeline": {
            "status": route.nine_step_status,
            "current_step": route.nine_step_current_step
        }
    }


@router.get("/dirty-doc/{document_id}")
async def get_dirty_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取脏数据通道的完整文本
    """
    route = db.query(UnifiedProcessingRoute).filter_by(document_id=document_id).first()
    if not route or not route.dirty_doc_id:
        raise HTTPException(status_code=404, detail="脏数据文档未找到")

    dirty_doc = db.query(DirtyChannelDocument).filter_by(id=route.dirty_doc_id).first()
    if not dirty_doc:
        raise HTTPException(status_code=404, detail="脏数据文档未找到")

    return {
        "document_id": document_id,
        "dirty_doc_id": dirty_doc.id,
        "source_type": dirty_doc.source_type,
        "word_count": dirty_doc.word_count,
        "completeness_score": dirty_doc.completeness_score,
        "full_text": dirty_doc.full_text,
        "metadata": dirty_doc.metadata,
        "created_at": dirty_doc.created_at
    }


@router.get("/clean-data/{document_id}")
async def get_clean_data(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取干净数据通道的核心事件、实体、关系
    """
    route = db.query(UnifiedProcessingRoute).filter_by(document_id=document_id).first()
    if not route or not route.dirty_doc_id:
        raise HTTPException(status_code=404, detail="处理路由未找到")

    # 获取核心事件
    events = db.query(CleanChannelEvent).filter_by(dirty_doc_id=route.dirty_doc_id).all()

    # 获取核心实体
    entities = db.query(CleanChannelEntity).filter_by(dirty_doc_id=route.dirty_doc_id).all()

    return {
        "document_id": document_id,
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "summary": e.event_summary,
                "who": e.who,
                "what": e.what,
                "when": e.when,
                "where": e.where,
                "why": e.why,
                "how": e.how,
                "importance": e.importance_score
            }
            for e in events
        ],
        "entities": [
            {
                "id": ent.id,
                "type": ent.entity_type,
                "name": ent.entity_name,
                "attributes": ent.attributes,
                "mention_count": ent.mention_count,
                "importance": ent.importance_score
            }
            for ent in entities
        ]
    }


@router.get("/comparison/{document_id}")
async def get_dirty_clean_comparison(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    对比脏数据和干净数据，展示数据压缩效果
    """
    route = db.query(UnifiedProcessingRoute).filter_by(document_id=document_id).first()
    if not route or not route.dirty_doc_id:
        raise HTTPException(status_code=404, detail="处理路由未找到")

    dirty_doc = db.query(DirtyChannelDocument).filter_by(id=route.dirty_doc_id).first()
    events = db.query(CleanChannelEvent).filter_by(dirty_doc_id=route.dirty_doc_id).all()
    entities = db.query(CleanChannelEntity).filter_by(dirty_doc_id=route.dirty_doc_id).all()

    # 计算压缩比
    dirty_length = len(dirty_doc.full_text) if dirty_doc else 0
    clean_length = sum(len(e.event_summary) for e in events)
    compression_ratio = (1 - clean_length / dirty_length) * 100 if dirty_length > 0 else 0

    return {
        "document_id": document_id,
        "dirty_channel": {
            "word_count": dirty_doc.word_count if dirty_doc else 0,
            "completeness_score": dirty_doc.completeness_score if dirty_doc else 0,
            "description": "完整性优先：所有多模态内容转为完整文档"
        },
        "clean_channel": {
            "events_count": len(events),
            "entities_count": len(entities),
            "total_summary_length": clean_length,
            "description": "精准提取：1-3个核心事件 + 核心实体"
        },
        "compression": {
            "original_length": dirty_length,
            "compressed_length": clean_length,
            "compression_ratio": f"{compression_ratio:.1f}%",
            "description": f"去除了 {compression_ratio:.1f}% 的冗余信息"
        }
    }
