"""文档管理API - 支持项目隔离的文档上传和处理"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.project import Project, ProjectDocument
from app.models.batch_operation import BatchOperation
from app.schemas.document import DocumentResponse
from app.schemas.project import ProjectDocumentResponse
from app.schemas.batch import (
    BatchUploadResponse, BatchStatusResponse, BatchOperationRequest,
    BatchDeleteRequest, BatchReprocessRequest, BatchQualityCheckRequest,
    BatchOperationResponse, BatchListResponse
)
from app.services.background_tasks import submit_task
from app.services.batch_processing import batch_service
from app.services.project_document_upload import upload_project_document, prepare_document_retry
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    上传文档到项目（简化版，用于桌面应用）

    支持14种格式：PDF, DOCX, PPTX, XLSX, HTML, TXT, MD, CSV, JSON, XML等
    自动转换为Markdown并提取记忆
    """
    try:
        content = await file.read()
        original_filename = os.path.basename(file.filename or "unnamed")
        doc, created = upload_project_document(
            db,
            project_id=project_id,
            original_filename=original_filename,
            content=content,
            mime_type=file.content_type,
            status="pending" if auto_process else "uploaded",
        )

        # 提交到后台处理（如果需要自动处理）
        if auto_process and created:
            logger.info(f"提交文档 {doc.id} 到后台处理队列")
            submit_task(doc.id)
        elif auto_process and not created and doc.status in {"failed", "review_needed"}:
            prepare_document_retry(db, doc)
            submit_task(doc.id, force=True)

        # 返回简化数据，避免复杂嵌套对象
        return success_response(
            data={
                "id": doc.id,
                "project_id": doc.project_id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/documents/")
def list_project_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目的所有文档"""
    try:
        query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

        if status:
            query = query.filter(ProjectDocument.status == status)

        total = query.count()
        documents = query.order_by(ProjectDocument.created_at.desc()).offset(skip).limit(limit).all()

        return success_response(
            data={
                "total": total,
                "documents": [DocumentResponse.model_validate(doc) for doc in documents]
            }
        )

    except Exception as e:
        logger.error(f"Failed to list documents for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    try:
        logger.info(f"🔍 查询文档 {document_id}")
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            logger.warning(f"❌ 文档 {document_id} 不存在")
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info(f"✅ 找到文档 {document_id}: {doc.filename}")
        return DocumentResponse.model_validate(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}/")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """删除文档"""
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 删除文件
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # 删除数据库记录
        db.delete(doc)
        db.commit()

        logger.info(f"Deleted document {document_id}")

        return success_response(message="Document deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/status")
def get_knowledge_base_status(db: Session = Depends(get_db)):
    """
    获取知识库状态

    返回：
    - 总文档数
    - 各状态文档数（pending, processing, completed, failed）
    - 总分块数（从metadata中统计）
    - 向量化完成的文档数
    """
    try:
        from sqlalchemy import func

        # 统计各状态文档数
        status_counts = db.query(
            ProjectDocument.status,
            func.count(ProjectDocument.id)
        ).group_by(ProjectDocument.status).all()

        status_map = {status: count for status, count in status_counts}

        # 统计完成向量化的文档
        vectorized_count = 0
        total_chunks = 0

        # 获取所有已完成的文档
        completed_docs = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        ).all()

        for doc in completed_docs:
            # extra_data是JSON字段
            meta = doc.extra_data if doc.extra_data else {}

            # 检查是否完成pipeline
            if meta.get('pipeline_completed'):
                vectorized_count += 1

            # 统计分块数
            if 'chunks_count' in meta:
                total_chunks += meta.get('chunks_count', 0)

        return success_response(
            data={
                "total_documents": sum(status_map.values()),
                "status_breakdown": {
                    "pending": status_map.get("pending", 0),
                    "processing": status_map.get("processing", 0),
                    "completed": status_map.get("completed", 0),
                    "failed": status_map.get("failed", 0)
                },
                "vectorized_documents": vectorized_count,
                "total_chunks": total_chunks,
                "ready_for_query": vectorized_count > 0
            }
        )

    except Exception as e:
        logger.error(f"Failed to get knowledge base status: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/list/status")
def get_documents_status(
    project_id: int,  # 强制必填，不再是Optional
    db: Session = Depends(get_db)
):
    """
    获取文档处理状态列表（用于前端轮询）

    **项目隔离：强制要求project_id参数**

    返回每个文档的：id, filename, status, chunk_count, created_at
    """
    try:
        from sqlalchemy import text

        # 强制按project_id过滤
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).order_by(ProjectDocument.created_at.desc()).all()

        result = []
        for doc in documents:
            meta = doc.extra_data if doc.extra_data else {}

            # 使用原生SQL查询chunk数量（避免模型导入冲突）
            chunk_count_result = db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id"),
                {"doc_id": doc.id}
            ).scalar()
            actual_chunk_count = chunk_count_result or 0

            result.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "chunk_count": actual_chunk_count,  # 使用实际查询的chunk数量
                "vectorized": actual_chunk_count > 0,  # 有chunks就表示已向量化
                "skills_completed": meta.get('skills_completed', False),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "word_count": doc.word_count,
                "file_type": doc.file_type,
                "error_message": doc.error_message  # 添加错误信息
            })

        from app.core.responses import success_response
        return success_response(
            data=result,
            message=f"获取到{len(result)}个文档"
        )

    except Exception as e:
        logger.error(f"Failed to get documents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate/keywords")
def get_aggregated_keywords(
    project_id: int,  # 强制必填
    top_n: int = 50,
    db: Session = Depends(get_db)
):
    """
    聚合所有文档的关键词（按词频排序）

    **项目隔离：强制要求project_id参数**

    返回：[{keyword, count, weight}]
    """
    try:
        # 强制按project_id过滤
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        # 聚合关键词
        keyword_stats = {}

        for doc in documents:
            if not doc.extra_data:
                continue
                
            keywords = doc.extra_data.get('keywords', [])
            
            for kw in keywords:
                if isinstance(kw, dict):
                    word = kw.get('word')
                    weight = kw.get('weight', 1.0)
                else:
                    word = str(kw)
                    weight = 1.0
                
                if not word:
                    continue
                
                if word not in keyword_stats:
                    keyword_stats[word] = {
                        'keyword': word,
                        'count': 0,
                        'total_weight': 0.0,
                        'documents': []
                    }
                
                keyword_stats[word]['count'] += 1
                keyword_stats[word]['total_weight'] += weight
                keyword_stats[word]['documents'].append(doc.id)

        # 转换为列表并排序
        result = [
            {
                'keyword': stats['keyword'],
                'count': stats['count'],
                'weight': round(stats['total_weight'], 2),
                'document_ids': list(set(stats['documents']))
            }
            for word, stats in keyword_stats.items()
        ]

        # 按count排序
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return result[:top_n]

    except Exception as e:
        logger.error(f"Failed to aggregate keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skill/analysis/{document_id}/")
def get_skill_analysis(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档的Skill分析结果

    返回：skill_results字典
    """
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if not doc.extra_data:
            return success_response(data={"skill_results": {}})

        return success_response(
            data={
                "document_id": document_id,
                "filename": doc.filename,
                "skill_results": doc.extra_data.get('skill_results', {}),
                "skills_completed": doc.extra_data.get('skills_completed', False)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skill analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate/skills")
def get_aggregated_skills(
    project_id: int,  # 强制必填
    db: Session = Depends(get_db)
):
    """
    聚合所有文档的Skill分析结果

    **项目隔离：强制要求project_id参数**

    返回：{skill_name: {dimension: {matched_count, contexts[]}}}
    """
    try:
        # 强制按project_id过滤
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        # 聚合Skill分析结果
        aggregated = {}

        for doc in documents:
            if not doc.extra_data:
                continue

            skill_results = doc.extra_data.get('skill_results', {})

            for skill_name, skill_data in skill_results.items():
                if skill_name not in aggregated:
                    aggregated[skill_name] = {}

                dimensions = skill_data.get('dimensions', {})

                for dim_name, dim_data in dimensions.items():
                    if dim_name not in aggregated[skill_name]:
                        aggregated[skill_name][dim_name] = {
                            'matched_count': 0,
                            'contexts': [],
                            'document_ids': []
                        }

                    aggregated[skill_name][dim_name]['matched_count'] += dim_data.get('matched_count', 0)
                    aggregated[skill_name][dim_name]['contexts'].extend(dim_data.get('contexts', []))
                    aggregated[skill_name][dim_name]['document_ids'].append(doc.id)

        return aggregated

    except Exception as e:
        logger.error(f"Failed to aggregate skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/fact-statements/")
def get_document_fact_statements(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档的所有fact_statements（带时间戳）

    返回：[{statement, start_sec, end_sec, confidence_score, speaker}]
    """
    try:
        # 验证文档存在
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 从SQLite数据库查询fact_statements
        import sqlite3
        db_path = settings.DATABASE_URL.replace("sqlite:///", "", 1)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT statement_text, start_sec, end_sec, confidence_score, NULL
            FROM fact_statements
            WHERE document_id = ?
            ORDER BY start_sec ASC
        """, (document_id,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "statement": row[0],
                "start_sec": row[1],
                "end_sec": row[2],
                "confidence_score": row[3],
                "speaker": row[4]
            })

        # 检查是否有音频文件
        audio_url = None
        if doc.file_type in ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'audio'] and doc.file_path:
            # 返回相对路径，前端通过/api/documents/{id}/audio访问
            audio_url = f"/api/documents/{document_id}/audio"

        return success_response(
            data={
                "document_id": document_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "audio_url": audio_url,
                "total_statements": len(results),
                "statements_with_timestamps": sum(1 for s in results if s["start_sec"] is not None),
                "timestamp_coverage": round(sum(1 for s in results if s["start_sec"] is not None) / len(results) * 100, 2) if results else 0,
                "fact_statements": results
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fact statements for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/audio/")
async def get_document_audio(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档的音频文件

    返回音频文件流，支持浏览器播放
    """
    from fastapi.responses import FileResponse

    try:
        # 查询文档
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 检查文件类型
        if doc.file_type not in ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'audio']:
            raise HTTPException(status_code=400, detail="This document is not an audio file")

        # 检查文件是否存在
        if not doc.file_path or not os.path.exists(doc.file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")

        # 返回音频文件
        return FileResponse(
            path=doc.file_path,
            media_type=f"audio/{doc.file_type}",
            filename=doc.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audio for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 批量处理API ====================

@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    project_id: int = Form(...),
    files: List[UploadFile] = File(...),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    批量上传文档

    支持:
    - 一次上传多个文件 (最多50个)
    - 返回批次ID用于追踪
    - 自动处理所有文档

    限制:
    - 单次最多50个文件
    - 单个文件最大100MB
    """
    try:
        # 验证文件数量
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 files per batch")

        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")

        # 创建批次ID
        batch_id = str(uuid.uuid4())

        document_ids = []
        failures = []
        successful_uploads = 0

        for file in files:
            try:
                # 保存文件
                original_filename = os.path.basename(file.filename or "unnamed")
                content = await file.read()
                file_size = len(content)

                # 验证文件大小
                if file_size > 100 * 1024 * 1024:  # 100MB
                    failures.append({
                        "filename": original_filename,
                        "error": "File size exceeds 100MB"
                    })
                    continue

                doc, created = upload_project_document(
                    db,
                    project_id=project_id,
                    original_filename=original_filename,
                    content=content,
                    mime_type=file.content_type,
                    status="pending" if auto_process else "uploaded",
                )
                document_ids.append(doc.id)
                successful_uploads += 1
                if auto_process and (created or doc.status in {"failed", "review_needed"}):
                    if not created:
                        prepare_document_retry(db, doc)
                    submit_task(doc.id, force=not created)

            except Exception as e:
                logger.error(f"Failed to upload file {file.filename}: {e}")
                failures.append({
                    "filename": os.path.basename(file.filename or "unnamed"),
                    "error": str(e)
                })

        # 创建批次操作记录
        if document_ids:
            batch_op = batch_service.create_batch_operation(
                db=db,
                project_id=project_id,
                operation_type="upload",
                total_items=len(document_ids),
                metadata={
                    "batch_id": batch_id,
                    "document_ids": document_ids,
                    "auto_process": auto_process
                }
            )

        logger.info(
            f"批量上传完成: 批次={batch_id}, "
            f"成功={successful_uploads}, 失败={len(failures)}"
        )

        return BatchUploadResponse(
            batch_id=batch_id,
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=len(failures),
            document_ids=document_ids,
            failures=failures,
            message=f"Uploaded {successful_uploads} files successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Batch upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    获取批次操作状态

    返回:
    - 总文档数
    - 已完成数
    - 失败数
    - 进度百分比
    """
    try:
        batch_op = batch_service.get_batch_status(db, batch_id)

        if not batch_op:
            raise HTTPException(status_code=404, detail="Batch operation not found")

        return BatchStatusResponse(
            batch_id=batch_op.batch_id,
            project_id=batch_op.project_id,
            operation_type=batch_op.operation_type,
            total_items=batch_op.total_items,
            completed_items=batch_op.completed_items,
            failed_items=batch_op.failed_items,
            status=batch_op.status,
            progress_percentage=batch_op.progress_percentage,
            created_at=batch_op.created_at,
            completed_at=batch_op.completed_at,
            metadata=batch_op.extra_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch", response_model=BatchOperationResponse)
async def delete_documents_batch(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    批量删除文档

    限制:
    - 单次最多100个文档
    """
    try:
        if len(request.document_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 documents per batch")

        if len(request.document_ids) == 0:
            raise HTTPException(status_code=400, detail="No document IDs provided")

        # 验证项目ID（从第一个文档获取）
        first_doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == request.document_ids[0]
        ).first()

        if not first_doc:
            raise HTTPException(status_code=404, detail="First document not found")

        project_id = first_doc.project_id

        # 执行批量删除
        result = batch_service.batch_delete_documents(
            db=db,
            document_ids=request.document_ids,
            project_id=project_id
        )

        return BatchOperationResponse(
            batch_id=result["batch_id"],
            operation_type="delete",
            total_items=result["total"],
            message=f"Deleted {result['successful']} documents, {result['failed']} failed",
            status="completed"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/reprocess", response_model=BatchOperationResponse)
async def reprocess_documents_batch(
    request: BatchReprocessRequest,
    db: Session = Depends(get_db)
):
    """
    批量重新处理文档

    用于重新处理失败的文档或更新处理结果

    限制:
    - 单次最多100个文档
    """
    try:
        if len(request.document_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 documents per batch")

        if len(request.document_ids) == 0:
            raise HTTPException(status_code=400, detail="No document IDs provided")

        # 验证项目ID
        first_doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == request.document_ids[0]
        ).first()

        if not first_doc:
            raise HTTPException(status_code=404, detail="First document not found")

        project_id = first_doc.project_id

        # 过滤文档：只处理失败的或强制重处理
        valid_doc_ids = []

        for doc_id in request.document_ids:
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.id == doc_id,
                ProjectDocument.project_id == project_id
            ).first()

            if not doc:
                continue

            # 如果force=True或状态为failed，添加到处理列表
            if request.force or doc.status == "failed":
                doc.status = "pending"
                valid_doc_ids.append(doc_id)

        db.commit()

        if not valid_doc_ids:
            raise HTTPException(
                status_code=400,
                detail="No documents need reprocessing. Use force=true to reprocess all."
            )

        # 创建批次记录
        batch_op = batch_service.create_batch_operation(
            db=db,
            project_id=project_id,
            operation_type="reprocess",
            total_items=len(valid_doc_ids),
            metadata={"document_ids": valid_doc_ids}
        )

        # 提交到后台处理
        for doc_id in valid_doc_ids:
            try:
                submit_task(doc_id)
                batch_service.update_batch_progress(db, batch_op.batch_id, completed=1)
            except Exception as e:
                logger.error(f"Failed to submit task for document {doc_id}: {e}")
                batch_service.update_batch_progress(db, batch_op.batch_id, failed=1)

        return BatchOperationResponse(
            batch_id=batch_op.batch_id,
            operation_type="reprocess",
            total_items=len(valid_doc_ids),
            message=f"Reprocessing {len(valid_doc_ids)} documents",
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch reprocess failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/quality-check", response_model=BatchOperationResponse)
async def quality_check_batch(
    request: BatchQualityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    批量运行质量检查

    对指定文档重新运行质量控制Agent

    限制:
    - 单次最多100个文档
    """
    try:
        if len(request.document_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 documents per batch")

        if len(request.document_ids) == 0:
            raise HTTPException(status_code=400, detail="No document IDs provided")

        # 验证项目ID
        first_doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == request.document_ids[0]
        ).first()

        if not first_doc:
            raise HTTPException(status_code=404, detail="First document not found")

        project_id = first_doc.project_id

        # 创建批次记录
        batch_op = batch_service.create_batch_operation(
            db=db,
            project_id=project_id,
            operation_type="quality_check",
            total_items=len(request.document_ids),
            metadata={"document_ids": request.document_ids}
        )

        batch_op.status = "processing"
        db.commit()

        # 执行质量检查
        from app.agents.quality_control_agent import quality_agent

        successful = 0
        failed = 0

        for doc_id in request.document_ids:
            try:
                doc = db.query(ProjectDocument).filter(
                    ProjectDocument.id == doc_id,
                    ProjectDocument.project_id == project_id
                ).first()

                if not doc:
                    failed += 1
                    continue

                # 运行完整质量检查
                report = quality_agent.validate_all(doc, db)

                # 更新文档的质量检查结果
                doc.extra_data = doc.extra_data or {}
                doc.extra_data['quality_check'] = {
                    "score": report.overall_score,
                    "passed": report.passed,
                    "quality_level": report.quality_level.value,
                    "issues_count": len(report.issues),
                    "checked_at": datetime.utcnow().isoformat()
                }

                db.commit()
                successful += 1

            except Exception as e:
                logger.error(f"Quality check failed for document {doc_id}: {e}")
                failed += 1

        # 更新批次状态
        batch_op.completed_items = successful
        batch_op.failed_items = failed
        batch_op.status = "completed"
        batch_op.completed_at = datetime.utcnow()
        db.commit()

        return BatchOperationResponse(
            batch_id=batch_op.batch_id,
            operation_type="quality_check",
            total_items=len(request.document_ids),
            message=f"Quality check completed: {successful} passed, {failed} failed",
            status="completed"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch quality check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch", response_model=BatchListResponse)
async def list_batch_operations(
    project_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    列出批次操作

    查询参数:
    - project_id: 按项目过滤
    - operation_type: 按操作类型过滤 (upload, delete, reprocess, quality_check)
    - status: 按状态过滤 (pending, processing, completed, failed, cancelled)
    - limit: 返回数量限制
    - offset: 偏移量
    """
    try:
        batches = batch_service.list_batch_operations(
            db=db,
            project_id=project_id,
            operation_type=operation_type,
            status=status,
            limit=limit,
            offset=offset
        )

        # 统计总数
        query = db.query(BatchOperation)
        if project_id:
            query = query.filter(BatchOperation.project_id == project_id)
        if operation_type:
            query = query.filter(BatchOperation.operation_type == operation_type)
        if status:
            query = query.filter(BatchOperation.status == status)

        total = query.count()

        batch_responses = [
            BatchStatusResponse(
                batch_id=b.batch_id,
                project_id=b.project_id,
                operation_type=b.operation_type,
                total_items=b.total_items,
                completed_items=b.completed_items,
                failed_items=b.failed_items,
                status=b.status,
                progress_percentage=b.progress_percentage,
                created_at=b.created_at,
                completed_at=b.completed_at,
                metadata=b.extra_data
            )
            for b in batches
        ]

        return BatchListResponse(
            total=total,
            batches=batch_responses
        )

    except Exception as e:
        logger.error(f"Failed to list batch operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch/{batch_id}/cancel/")
async def cancel_batch_operation(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    取消批次操作

    只能取消pending或processing状态的批次
    """
    try:
        success = batch_service.cancel_batch_operation(db, batch_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel batch operation (not found or already completed)"
            )

        return success_response(message="Batch operation cancelled successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel batch operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
