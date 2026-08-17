"""
批量文档处理API

优化大批量文档的处理性能，支持legacy和v2架构
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.project import ProjectDocument
from app.services.background_tasks import process_document_async
from app.services.pipeline_status import mark_pipeline_completed, clear_pipeline_status

router = APIRouter(tags=["batch"])
logger = logging.getLogger(__name__)


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    document_ids: List[int]
    force_reprocess: bool = False  # 是否强制重新处理已完成的文档
    use_v2_architecture: bool = False  # 是否使用6-Agent v2架构


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
) -> BatchProcessResponse:
    """
    批量处理文档

    性能优化：
    - 异步后台处理
    - 跳过已完成的文档（除非force_reprocess=True）
    - 批量查询减少数据库往返
    - 支持v2架构（6-Agent WorkflowV2Adapter）
    """
    try:
        logger.info(f"批量处理请求: {len(request.document_ids)} 个文档, v2架构={request.use_v2_architecture}")

        # 批量查询文档
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(request.document_ids)
        ).all()

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")

        queued = 0
        skipped = 0

        # V2架构模式
        if request.use_v2_architecture:
            from app.agents.workflow_adapter import get_v2_adapter

            adapter = get_v2_adapter()

            for doc in documents:
                # 跳过已完成的文档（除非强制重新处理）
                if doc.status == 'completed' and not request.force_reprocess:
                    skipped += 1
                    logger.info(f"跳过已完成文档: {doc.id}")
                    continue

                # 重置状态
                if request.force_reprocess and doc.status == 'completed':
                    doc.status = 'pending'
                    clear_pipeline_status(doc)
                    db.commit()

                # V2架构批处理：直接同步执行（适合批量）
                try:
                    doc.status = 'processing'
                    db.commit()

                    # 执行完整6-Agent v2流程
                    # Ingestion
                    ingestion_result = adapter.execute_v2_agent(
                        'ingestion',
                        {'document_id': doc.id, 'project_id': doc.project_id},
                        doc.project_id
                    )

                    if not ingestion_result.success:
                        raise Exception(f"Ingestion失败: {ingestion_result.error}")

                    # Chunking
                    chunking_result = adapter.execute_v2_agent(
                        'chunking',
                        {'document_id': doc.id, 'text_content': ingestion_result.data.get('text_content')},
                        doc.project_id
                    )

                    if not chunking_result.success:
                        raise Exception(f"Chunking失败: {chunking_result.error}")

                    # Vectorization
                    vectorization_result = adapter.execute_v2_agent(
                        'vectorization',
                        {
                            'document_id': doc.id,
                            'project_id': doc.project_id,
                            'chunks': chunking_result.data.get('chunks')
                        },
                        doc.project_id
                    )

                    if not vectorization_result.success:
                        raise Exception(f"Vectorization失败: {vectorization_result.error}")

                    # Knowledge (包含Skills自动集成)
                    knowledge_result = adapter.execute_v2_agent(
                        'knowledge',
                        {
                            'document_id': doc.id,
                            'project_id': doc.project_id,
                            'enable_skills_analysis': True  # 自动执行Skills
                        },
                        doc.project_id
                    )

                    if not knowledge_result.success:
                        raise Exception(f"Knowledge失败: {knowledge_result.error}")

                    # 标记v2完成
                    processing_time = sum([
                        ingestion_result.metadata.get('processing_time', 0),
                        chunking_result.metadata.get('processing_time', 0),
                        vectorization_result.metadata.get('processing_time', 0),
                        knowledge_result.metadata.get('processing_time', 0)
                    ])

                    mark_pipeline_completed(doc, use_v2=True, processing_time=processing_time)
                    doc.status = 'completed'
                    db.commit()

                    queued += 1
                    logger.info(f"✅ 文档{doc.id} v2处理完成，耗时{processing_time:.2f}秒")

                except Exception as e:
                    logger.error(f"❌ 文档{doc.id} v2处理失败: {e}")
                    doc.status = 'failed'
                    doc.error_message = str(e)
                    db.commit()

        else:
            # Legacy架构模式（原有逻辑）
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
            message=f"已将{queued}个文档提交到处理队列 ({'v2架构' if request.use_v2_architecture else 'legacy架构'})"
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
    use_v2_architecture: bool = False,
    db: Session = Depends(get_db)
) -> BatchProcessResponse:
    """
    处理项目的所有文档

    性能优化版本，适合大批量文档
    支持v2架构（6-Agent WorkflowV2Adapter）
    """
    try:
        logger.info(f"处理项目{project_id}的所有文档, force_reprocess={force_reprocess}, v2={use_v2_architecture}")

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

        # V2架构模式
        if use_v2_architecture:
            from app.agents.workflow_adapter import get_v2_adapter

            adapter = get_v2_adapter()
            processed = 0
            failed = 0

            for doc in documents:
                if force_reprocess:
                    doc.status = 'pending'
                    clear_pipeline_status(doc)
                    db.commit()

                try:
                    doc.status = 'processing'
                    db.commit()

                    # 执行完整6-Agent v2流程
                    ingestion_result = adapter.execute_v2_agent(
                        'ingestion',
                        {'document_id': doc.id, 'project_id': doc.project_id},
                        doc.project_id
                    )

                    if not ingestion_result.success:
                        raise Exception(f"Ingestion失败: {ingestion_result.error}")

                    chunking_result = adapter.execute_v2_agent(
                        'chunking',
                        {'document_id': doc.id, 'text_content': ingestion_result.data.get('text_content')},
                        doc.project_id
                    )

                    if not chunking_result.success:
                        raise Exception(f"Chunking失败: {chunking_result.error}")

                    vectorization_result = adapter.execute_v2_agent(
                        'vectorization',
                        {
                            'document_id': doc.id,
                            'project_id': doc.project_id,
                            'chunks': chunking_result.data.get('chunks')
                        },
                        doc.project_id
                    )

                    if not vectorization_result.success:
                        raise Exception(f"Vectorization失败: {vectorization_result.error}")

                    knowledge_result = adapter.execute_v2_agent(
                        'knowledge',
                        {
                            'document_id': doc.id,
                            'project_id': doc.project_id,
                            'enable_skills_analysis': True
                        },
                        doc.project_id
                    )

                    if not knowledge_result.success:
                        raise Exception(f"Knowledge失败: {knowledge_result.error}")

                    processing_time = sum([
                        ingestion_result.metadata.get('processing_time', 0),
                        chunking_result.metadata.get('processing_time', 0),
                        vectorization_result.metadata.get('processing_time', 0),
                        knowledge_result.metadata.get('processing_time', 0)
                    ])

                    mark_pipeline_completed(doc, use_v2=True, processing_time=processing_time)
                    doc.status = 'completed'
                    db.commit()

                    processed += 1
                    logger.info(f"✅ 文档{doc.id} v2处理完成")

                except Exception as e:
                    logger.error(f"❌ 文档{doc.id} v2处理失败: {e}")
                    doc.status = 'failed'
                    doc.error_message = str(e)
                    db.commit()
                    failed += 1

            logger.info(f"项目{project_id} v2批处理完成: 成功={processed}, 失败={failed}")

            return {
                "success": True,
                "message": f"v2架构处理完成: {processed}个成功, {failed}个失败",
                "total": len(documents),
                "queued": processed,
                "failed": failed
            }

        else:
            # Legacy架构模式（原有逻辑）
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
