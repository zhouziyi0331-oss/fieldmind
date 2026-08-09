"""
批量文档处理API

优化大批量文档的处理性能
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.project import ProjectDocument
from app.services.background_tasks import process_document_async

router = APIRouter(tags=["batch"])
logger = logging.getLogger(__name__)


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    document_ids: List[int]
    force_reprocess: bool = False  # 是否强制重新处理已完成的文档


class BatchProcessResponse(BaseModel):
    """批量处理响应"""
    total: int
    queued: int
    skipped: int
    message: str


@router.post("/process", response_model=BatchProcessResponse)
def batch_process_documents(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量处理文档

    性能优化：
    - 异步后台处理
    - 跳过已完成的文档（除非force_reprocess=True）
    - 批量查询减少数据库往返
    """
    try:
        logger.info(f"批量处理请求: {len(request.document_ids)} 个文档")

        # 批量查询文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(request.document_ids)
        ).all()

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")

        queued = 0
        skipped = 0

        for doc in documents:
            # 跳过已完成的文档（除非强制重新处理）
            if doc.status == 'completed' and not request.force_reprocess:
                skipped += 1
                logger.info(f"跳过已完成文档: {doc.id}")
                continue

            # 重置状态
            if request.force_reprocess and doc.status == 'completed':
                doc.status = 'pending'
                doc.extra_data = {}
                db.commit()

            # 提交到后台队列
            background_tasks.add_task(process_document_async, doc.id)
            queued += 1

        logger.info(f"批量处理: {queued}个已入队, {skipped}个已跳过")

        return BatchProcessResponse(
            total=len(documents),
            queued=queued,
            skipped=skipped,
            message=f"已将{queued}个文档提交到处理队列"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_batch_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的批量处理状态

    返回各状态的文档数量
    """
    try:
        from sqlalchemy import func

        status_counts = db.query(
            ProjectDocument.status,
            func.count(ProjectDocument.id)
        ).filter(
            ProjectDocument.project_id == project_id
        ).group_by(ProjectDocument.status).all()

        result = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }

        for status, count in status_counts:
            result[status] = count

        total = sum(result.values())

        # 计算进度
        progress = 0
        if total > 0:
            progress = int((result["completed"] / total) * 100)

        return {
            "total_documents": total,
            "status_breakdown": result,
            "progress_percent": progress,
            "is_processing": result["processing"] > 0 or result["pending"] > 0
        }

    except Exception as e:
        logger.error(f"获取批量状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess-failed")
def reprocess_failed_documents(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重新处理所有失败的文档
    """
    try:
        failed_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'failed'
        ).all()

        if not failed_docs:
            return {
                "success": True,
                "message": "没有失败的文档需要重新处理",
                "count": 0
            }

        # 重置状态并重新提交
        for doc in failed_docs:
            doc.status = 'pending'
            doc.extra_data = {}
            background_tasks.add_task(process_document_async, doc.id)

        db.commit()

        logger.info(f"重新处理{len(failed_docs)}个失败文档")

        return {
            "success": True,
            "message": f"已将{len(failed_docs)}个失败文档重新提交处理",
            "count": len(failed_docs)
        }

    except Exception as e:
        logger.error(f"重新处理失败文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-project")
def process_entire_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    force_reprocess: bool = False,
    db: Session = Depends(get_db)
):
    """
    处理项目的所有文档

    性能优化版本，适合大批量文档
    """
    try:
        logger.info(f"处理项目{project_id}的所有文档, force_reprocess={force_reprocess}")

        # 查询需要处理的文档
        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        )

        if not force_reprocess:
            # 只处理未完成的
            query = query.filter(
                ProjectDocument.status.in_(['pending', 'failed'])
            )

        documents = query.all()

        if not documents:
            return {
                "success": True,
                "message": "没有需要处理的文档",
                "total": 0,
                "queued": 0
            }

        # 批量提交
        for doc in documents:
            if force_reprocess:
                doc.status = 'pending'
                doc.extra_data = {}

            background_tasks.add_task(process_document_async, doc.id)

        if force_reprocess:
            db.commit()

        logger.info(f"已提交{len(documents)}个文档到处理队列")

        return {
            "success": True,
            "message": f"已将{len(documents)}个文档提交到处理队列",
            "total": len(documents),
            "queued": len(documents)
        }

    except Exception as e:
        logger.error(f"处理整个项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
