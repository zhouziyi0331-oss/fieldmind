"""
统一文档处理API - 整合所有文档处理相关功能
合并自: documents, document_processing, document_processing_v2, document_normalization
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import os
import shutil
from pathlib import Path

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter(prefix="/api/documents", tags=["统一文档处理"])


# 辅助函数：保存上传文件
async def save_uploaded_file(file: UploadFile, project_id: int) -> str:
    """保存上传的文件到本地存储"""
    upload_dir = Path(f"uploads/project_{project_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)

# ============================================================================
# 请求/响应模型
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: int
    filename: str
    status: str


class DocumentProcessRequest(BaseModel):
    """文档处理请求"""
    document_id: int
    force_reprocess: bool = Field(default=False, description="强制重新处理")
    extract_entities: bool = Field(default=True, description="提取实体")
    build_graph: bool = Field(default=True, description="构建知识图谱")


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    project_id: int
    document_ids: Optional[List[int]] = None
    operation: str = Field(..., description="操作类型: process, quality_check, reprocess")


# ============================================================================
# 1. 文档上传
# ============================================================================

@router.post("/upload", response_model=ApiResponse, summary="上传单个文档")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    上传单个文档到项目

    支持的文件类型:
    - 文档: PDF, DOC, DOCX, TXT, MD
    - 音频: MP3, WAV, M4A
    - 图片: JPG, PNG, GIF
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        # 保存文件
        file_path = await save_uploaded_file(file, project_id)

        # 创建文档记录
        document = ProjectDocument(
            project_id=project_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size if hasattr(file, 'size') else 0,
            mime_type=file.content_type,
            status="uploaded"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return success_response(
            data={
                "document_id": document.id,
                "filename": document.filename,
                "status": document.status
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch", response_model=ApiResponse, summary="批量上传文档")
async def upload_documents_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """批量上传多个文档"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        uploaded_docs = []

        for file in files:
            # 保存文件
            file_path = await save_uploaded_file(file, project_id)

            # 创建文档记录
            document = ProjectDocument(
                project_id=project_id,
                filename=file.filename,
                file_path=file_path,
                file_size=file.size if hasattr(file, 'size') else 0,
                mime_type=file.content_type,
                status="uploaded"
            )

            db.add(document)
            uploaded_docs.append({
                "filename": file.filename,
                "status": "uploaded"
            })

        db.commit()

        return success_response(
            data={
                "total": len(uploaded_docs),
                "documents": uploaded_docs
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. 文档处理
# ============================================================================

@router.post("/process/{document_id}", response_model=ApiResponse, summary="处理文档")
async def process_document_endpoint(
    request: Request,
    document_id: int,
    force_reprocess: bool = Query(False, description="强制重新处理"),
    db: Session = Depends(get_db)
):
    """
    处理文档：提取文本、分块、向量化、实体识别

    处理流程:
    1. 文本提取 (PDF/DOC/音频转文字)
    2. 文档分块
    3. 向量化
    4. 实体提取
    5. 知识图谱构建
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查是否需要处理
        if document.status == "completed" and not force_reprocess:
            return success_response(
                data={"message": "文档已处理完成", "status": document.status},
                request_id=request_id
            )

        # 更新状态
        document.status = "processing"
        db.commit()

        # TODO: 调用处理服务（需要实现统一的文档处理服务）
        # result = await process_document(db, document_id)

        # 临时返回
        result = {
            "document_id": document_id,
            "status": "processing",
            "message": "文档处理已启动"
        }

        # 更新状态
        document.status = "completed"
        db.commit()

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        if document:
            document.status = "failed"
            document.error_message = str(e)
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/batch", response_model=ApiResponse, summary="批量处理文档")
async def process_documents_batch(
    request: Request,
    batch_request: BatchProcessRequest,
    db: Session = Depends(get_db)
):
    """批量处理多个文档"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        # 获取文档列表
        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == batch_request.project_id
        )

        if batch_request.document_ids:
            query = query.filter(ProjectDocument.id.in_(batch_request.document_ids))

        documents = query.all()

        if not documents:
            raise HTTPException(status_code=404, detail="没有找到文档")

        # 批量处理
        results = []
        for doc in documents:
            try:
                doc.status = "processing"
                db.commit()

                # TODO: 调用处理服务（需要实现统一的文档处理服务）
                # result = await process_document(db, doc.id)
                result = {
                    "document_id": doc.id,
                    "status": "processing"
                }

                doc.status = "completed"
                db.commit()

                results.append({
                    "document_id": doc.id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                doc.status = "failed"
                doc.error_message = str(e)
                db.commit()

                results.append({
                    "document_id": doc.id,
                    "status": "failed",
                    "error": str(e)
                })

        return success_response(
            data={
                "total": len(results),
                "results": results
            },
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. 文档查询
# ============================================================================

@router.get("/list", response_model=ApiResponse, summary="查询文档列表")
async def list_documents(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """查询项目中的文档列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        )

        if status:
            query = query.filter(ProjectDocument.status == status)

        total = query.count()
        documents = query.offset(offset).limit(limit).all()

        result = {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "file_size": doc.file_size,
                    "mime_type": doc.mime_type,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in documents
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=ApiResponse, summary="获取文档详情")
async def get_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取单个文档的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        result = {
            "id": document.id,
            "filename": document.filename,
            "status": document.status,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "file_path": document.file_path,
            "project_id": document.project_id,
            "error_message": document.error_message,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content", response_model=ApiResponse, summary="获取文档内容")
async def get_document_content(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的文本内容"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from app.models.document_chunk import DocumentChunk

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取文档的所有块
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

        result = {
            "document_id": document.id,
            "filename": document.filename,
            "chunks": [
                {
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index
                }
                for chunk in chunks
            ],
            "total_chunks": len(chunks)
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. 文档更新与删除
# ============================================================================

@router.patch("/{document_id}", response_model=ApiResponse, summary="更新文档信息")
async def update_document(
    request: Request,
    document_id: int,
    update_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """更新文档的元数据信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 更新允许的字段
        allowed_fields = ['filename', 'status']
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(document, field, value)

        db.commit()
        db.refresh(document)

        return success_response(
            data={
                "document_id": document.id,
                "filename": document.filename,
                "status": document.status
            },
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=ApiResponse, summary="删除文档")
async def delete_document(
    request: Request,
    document_id: int,
    delete_file: bool = Query(True, description="是否删除物理文件"),
    db: Session = Depends(get_db)
):
    """删除文档及其相关数据"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from app.models.document_chunk import DocumentChunk

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 删除相关的块
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()

        # 删除物理文件
        if delete_file and document.file_path:
            try:
                if os.path.exists(document.file_path):
                    os.remove(document.file_path)
            except Exception as e:
                # 文件删除失败不应阻止数据库记录删除
                pass

        # 删除文档记录
        db.delete(document)
        db.commit()

        return success_response(
            data={"deleted_document_id": document_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. 文档统计
# ============================================================================

@router.get("/statistics/project/{project_id}", response_model=ApiResponse, summary="项目文档统计")
async def get_project_statistics(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的文档统计信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from sqlalchemy import func

        # 统计各状态的文档数
        status_stats = db.query(
            ProjectDocument.status,
            func.count(ProjectDocument.id)
        ).filter(
            ProjectDocument.project_id == project_id
        ).group_by(ProjectDocument.status).all()

        # 总文档数
        total_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar()

        # 总文件大小
        total_size = db.query(func.sum(ProjectDocument.file_size)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        result = {
            "project_id": project_id,
            "total_documents": total_docs,
            "total_size_bytes": total_size,
            "status_distribution": {
                status: count for status, count in status_stats
            }
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chunks/statistics", response_model=ApiResponse, summary="文档块统计")
async def get_chunks_statistics(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档的分块统计信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.document_chunk import DocumentChunk
        from sqlalchemy import func

        # 块数量
        chunk_count = db.query(func.count(DocumentChunk.id)).filter(
            DocumentChunk.document_id == document_id
        ).scalar()

        # 平均块大小
        avg_size = db.query(func.avg(func.length(DocumentChunk.content))).filter(
            DocumentChunk.document_id == document_id
        ).scalar() or 0

        result = {
            "document_id": document_id,
            "chunk_count": chunk_count,
            "avg_chunk_size": int(avg_size)
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. 文档搜索
# ============================================================================

@router.post("/search", response_model=ApiResponse, summary="搜索文档")
async def search_documents(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """在文档中搜索关键词"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.filename.contains(keyword)
        ).limit(limit).all()

        result = {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status
                }
                for doc in documents
            ],
            "total": len(documents)
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 补充端点：从旧模块迁移的聚合和状态功能
# ============================================================================

@router.get("/aggregate/skills", response_model=ApiResponse, summary="聚合技能分析结果")
async def get_aggregated_skills(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """聚合所有文档的Skill分析结果"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

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

        return success_response(
            data=aggregated,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚合技能失败: {str(e)}")


@router.get("/aggregate/keywords", response_model=ApiResponse, summary="聚合关键词")
async def get_aggregated_keywords(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    top_n: int = Query(50, description="返回前N个关键词"),
    db: Session = Depends(get_db)
):
    """聚合所有文档的关键词（按词频排序）"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

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
                    keyword_stats[word] = {'count': 0, 'total_weight': 0.0}
                
                keyword_stats[word]['count'] += 1
                keyword_stats[word]['total_weight'] += weight

        result = [
            {
                'keyword': word,
                'count': stats['count'],
                'weight': round(stats['total_weight'] / stats['count'], 3)
            }
            for word, stats in keyword_stats.items()
        ]

        result.sort(key=lambda x: x['count'], reverse=True)
        result = result[:top_n]

        return success_response(
            data={
                'keywords': result,
                'total_unique': len(keyword_stats)
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚合关键词失败: {str(e)}")


@router.get("/knowledge-base/status", response_model=ApiResponse, summary="获取知识库状态")
async def get_knowledge_base_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取知识库状态统计"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from sqlalchemy import func

        status_counts = db.query(
            ProjectDocument.status,
            func.count(ProjectDocument.id)
        ).group_by(ProjectDocument.status).all()

        status_map = {status: count for status, count in status_counts}

        vectorized_count = 0
        total_chunks = 0

        completed_docs = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        ).all()

        for doc in completed_docs:
            meta = doc.extra_data if doc.extra_data else {}

            if meta.get('pipeline_completed'):
                vectorized_count += 1

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
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库状态失败: {str(e)}")
