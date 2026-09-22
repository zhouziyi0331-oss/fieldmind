"""
批量文档处理API - 集成WebSocket实时通知

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
from app.services.background_tasks import submit_task
from app.services.websocket_manager import ConnectionManager
from app.schemas.response import success_response, error_response

router = APIRouter(tags=["batch"])
logger = logging.getLogger(__name__)

# 全局WebSocket连接管理器
connection_manager = ConnectionManager()


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


def _process_batch_sync(
    document_ids: List[int],
    project_id: int,
    force_reprocess: bool
):
    """批量处理文档（同步方法，在后台线程运行）"""
    import asyncio
    from app.core.database import SessionLocal

    # 创建新的数据库会话（后台任务专用）
    db = SessionLocal()

    # 创建事件循环用于WebSocket通知
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # 发送开始通知
        loop.run_until_complete(
            connection_manager.broadcast({
                "type": "batch_processing_start",
                "data": {
                    "project_id": project_id,
                    "total_documents": len(document_ids),
                    "status": "started"
                }
            })
        )

        # 批量查询文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(document_ids)
        ).all()

        total = len(documents)
        processed = 0
        failed = 0

        for idx, doc in enumerate(documents, 1):
            try:
                # 跳过已完成的文档（除非强制重新处理）
                if doc.status == 'completed' and not force_reprocess:
                    logger.info(f"跳过已完成文档: {doc.id}")
                    continue

                # 重置状态
                if force_reprocess and doc.status == 'completed':
                    doc.status = 'pending'
                    doc.extra_data = {}
                    db.commit()

                # 统一进入线程池；submit_task 会拦截重复任务
                submit_task(doc.id, force=force_reprocess)
                processed += 1

                # 发送进度通知
                loop.run_until_complete(
                    connection_manager.broadcast({
                        "type": "batch_processing_progress",
                        "data": {
                            "project_id": project_id,
                            "current": idx,
                            "total": total,
                            "processed": processed,
                            "failed": failed,
                            "progress": round((idx / total) * 100, 2)
                        }
                    })
                )

            except Exception as e:
                failed += 1
                logger.error(f"处理文档 {doc.id} 失败: {e}")

                loop.run_until_complete(
                    connection_manager.broadcast({
                        "type": "batch_processing_error",
                        "data": {
                            "project_id": project_id,
                            "document_id": doc.id,
                            "error": str(e)
                        }
                    })
                )

        # 发送完成通知
        loop.run_until_complete(
            connection_manager.broadcast({
                "type": "batch_processing_complete",
                "data": {
                    "project_id": project_id,
                    "total": total,
                    "processed": processed,
                    "failed": failed,
                    "status": "completed"
                }
            })
        )

    except Exception as e:
        logger.error(f"批量处理失败: {e}", exc_info=True)
        loop.run_until_complete(
            connection_manager.broadcast({
                "type": "batch_processing_error",
                "data": {
                    "project_id": project_id,
                    "error": str(e),
                    "status": "failed"
                }
            })
        )
    finally:
        loop.close()
        db.close()


@router.post("/process", response_model=BatchProcessResponse)
async def batch_process_documents(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    project_id: Optional[int] = None
):
    """
    批量处理文档 - 异步处理 + WebSocket实时通知

    性能优化：
    - 异步后台处理
    - 跳过已完成的文档（除非force_reprocess=True）
    - 批量查询减少数据库往返
    - WebSocket实时进度推送
    """
    try:
        logger.info(f"批量处理请求: {len(request.document_ids)} 个文档")

        # 批量查询文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(request.document_ids)
        ).all()

        if not documents:
            return error_response(
                code="DOCUMENTS_NOT_FOUND",
                message="No documents found"
            )

        # 获取project_id（从第一个文档）
        if not project_id and documents:
            project_id = documents[0].project_id

        # 后台处理 + 通知
        background_tasks.add_task(
            _process_batch_sync,
            request.document_ids,
            project_id,
            request.force_reprocess
        )

        return success_response(
            data={
                "total": len(documents),
                "queued": len(documents),
                "skipped": 0
            },
            message=f"已将{len(documents)}个文档提交到处理队列，实时进度将通过WebSocket推送"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理失败: {e}", exc_info=True)
        return error_response(
            code="BATCH_PROCESS_FAILED",
            message=str(e)
        )


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

        return success_response(
            data={
                "total_documents": total,
                "status_breakdown": result,
                "progress_percent": progress,
                "is_processing": result["processing"] > 0 or result["pending"] > 0
            }
        )

    except Exception as e:
        logger.error(f"获取批量状态失败: {e}")
        return error_response(
            code="GET_STATUS_FAILED",
            message=str(e)
        )


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
            return success_response(
                data={
                    "count": 0
                },
                message="没有失败的文档需要重新处理"
            )

        # 重置状态并重新提交
        for doc in failed_docs:
            doc.status = 'pending'
            doc.extra_data = {}
            background_tasks.add_task(submit_task, doc.id, True)

        db.commit()

        logger.info(f"重新处理{len(failed_docs)}个失败文档")

        return success_response(
            data={
                "count": len(failed_docs)
            },
            message=f"已将{len(failed_docs)}个失败文档重新提交处理"
        )

    except Exception as e:
        logger.error(f"重新处理失败文档失败: {e}")
        return error_response(
            code="REPROCESS_FAILED",
            message=str(e)
        )


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
            return success_response(
                data={
                    "total": 0,
                    "queued": 0
                },
                message="没有需要处理的文档"
            )

        # 批量提交
        for doc in documents:
            if force_reprocess:
                doc.status = 'pending'
                doc.extra_data = {}

            background_tasks.add_task(submit_task, doc.id, force_reprocess)

        if force_reprocess:
            db.commit()

        logger.info(f"已提交{len(documents)}个文档到处理队列")

        return success_response(
            data={
                "total": len(documents),
                "queued": len(documents)
            },
            message=f"已将{len(documents)}个文档提交到处理队列"
        )

    except Exception as e:
        logger.error(f"处理整个项目失败: {e}")
        return error_response(
            code="PROCESS_PROJECT_FAILED",
            message=str(e)
        )
