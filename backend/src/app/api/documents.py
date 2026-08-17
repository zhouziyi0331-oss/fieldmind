"""文档管理API - 支持项目隔离的文档上传和处理"""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundException,
    DatabaseException,
    FileException,
    ValidationException,
    ErrorCode
)
from app.models.project import Project, ProjectDocument
from app.schemas.document import DocumentUploadResponse, DocumentResponse
from app.services.background_tasks import submit_task
from app.config import settings
from app.services.pipeline_status import is_pipeline_completed

router = APIRouter(tags=["documents"])
logger = logging.getLogger(__name__)

# 上传目录 - 使用配置
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    上传文档到项目

    支持14种格式：PDF, DOCX, PPTX, XLSX, HTML, TXT, MD, CSV, JSON, XML等
    自动转换为Markdown并提取记忆
    """
    try:
        # 验证项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ResourceNotFoundException("Project", project_id)

        # 保存文件
        project_upload_dir = os.path.join(UPLOAD_DIR, f"project_{project_id}")
        os.makedirs(project_upload_dir, exist_ok=True)

        file_path = os.path.join(project_upload_dir, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        file_size = len(content)

        # 检测文件类型
        file_ext = os.path.splitext(file.filename)[1].lower()
        file_type_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "doc",
            ".pptx": "pptx",
            ".xlsx": "xlsx",
            ".txt": "txt",
            ".md": "markdown",
            ".html": "html",
            ".csv": "csv",
            ".json": "json",
            ".xml": "xml",
            # 音频格式（链路14核心）
            ".mp3": "audio",
            ".wav": "audio",
            ".m4a": "audio",
            ".flac": "audio",
            ".ogg": "audio",
            # 视频格式
            ".mp4": "video",
            ".mov": "video",
            ".avi": "video",
            ".mkv": "video"
        }
        file_type = file_type_map.get(file_ext, "unknown")

        # 创建文档记录
        doc = ProjectDocument(
            project_id=project_id,
            filename=file.filename,
            original_filename=file.filename,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            status="pending" if auto_process else "uploaded"
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 提交到后台处理（如果需要自动处理）
        if auto_process:
            logger.info(f"提交文档 {doc.id} 到后台处理队列")
            submit_task(doc.id)

            return DocumentUploadResponse(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                status="processing",
                message="Document uploaded, processing in background"
            )

        # 如果不自动处理，直接返回
        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status="uploaded",
            message="Document uploaded successfully"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upload document: {e}")
        raise DatabaseException(
            message=f"文档上传失败: {str(e)}",
            operation="upload_document",
            cause=e
        )


@router.get("/projects/{project_id}/documents")
def list_project_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取项目的所有文档"""
    try:
        query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

        if status:
            query = query.filter(ProjectDocument.status == status)

        total = query.count()
        documents = query.order_by(ProjectDocument.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "documents": [DocumentResponse.model_validate(doc) for doc in documents]
        }

    except Exception as e:
        logger.error(f"Failed to list documents for project {project_id}: {e}")
        raise DatabaseException(
            message=f"获取项目文档列表失败: {str(e)}",
            operation="list_project_documents",
            cause=e
        )


@router.get("/status")
def get_documents_status(
    project_id: int,  # 强制必填，不再是Optional
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    获取文档处理状态列表（用于前端轮询）

    **项目隔离：强制要求project_id参数**

    返回每个文档的：id, filename, status, chunk_count, created_at
    """
    try:
        # 强制按project_id过滤
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).order_by(ProjectDocument.created_at.desc()).all()

        result = []
        for doc in documents:
            meta = doc.extra_data if doc.extra_data else {}

            result.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "chunk_count": meta.get('chunks_count', 0),
                "vectorized": is_pipeline_completed(doc),
                "skills_completed": meta.get('skills_completed', False),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "word_count": doc.word_count,
                "file_type": doc.file_type,
                "error_message": doc.error_message  # 添加错误信息
            })

        return result

    except Exception as e:
        logger.error(f"Failed to get documents status: {e}")
        raise DatabaseException(
            message=f"获取文档状态失败: {str(e)}",
            operation="get_documents_status",
            cause=e
        )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """获取文档详情"""
    try:
        logger.info(f"🔍 查询文档 {document_id}")
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            logger.warning(f"❌ 文档 {document_id} 不存在")
            raise ResourceNotFoundException("Document", document_id)

        logger.info(f"✅ 找到文档 {document_id}: {doc.filename}")
        return DocumentResponse.model_validate(doc)

    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        raise DatabaseException(
            message=f"获取文档详情失败: {str(e)}",
            operation="get_document",
            cause=e
        )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """删除文档"""
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            raise ResourceNotFoundException("Document", document_id)

        # 删除文件
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # 删除数据库记录
        db.delete(doc)
        db.commit()

        logger.info(f"Deleted document {document_id}")

        return {"message": "Document deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise DatabaseException(
            message=f"删除文档失败: {str(e)}",
            operation="delete_document",
            cause=e
        )


@router.get("/knowledge-base/status")
def get_knowledge_base_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
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
            if is_pipeline_completed(doc):
                vectorized_count += 1

            # 统计分块数
            if 'chunks_count' in meta:
                total_chunks += meta.get('chunks_count', 0)

        return {
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

    except Exception as e:
        logger.error(f"Failed to get knowledge base status: {e}")
        raise DatabaseException(
            message=f"获取知识库状态失败: {str(e)}",
            operation="get_knowledge_base_status",
            cause=e
        )




@router.get("/aggregate/keywords")
def get_aggregated_keywords(
    project_id: int,  # 强制必填
    top_n: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
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
        raise DatabaseException(
            message=f"聚合关键词失败: {str(e)}",
            operation="get_aggregated_keywords",
            cause=e
        )


@router.get("/skill/analysis/{document_id}")
def get_skill_analysis(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取文档的Skill分析结果
    
    返回：skill_results字典
    """
    try:
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            raise ResourceNotFoundException("Document", document_id)

        if not doc.extra_data:
            return {"skill_results": {}}

        return {
            "document_id": document_id,
            "filename": doc.filename,
            "skill_results": doc.extra_data.get('skill_results', {}),
            "skills_completed": doc.extra_data.get('skills_completed', False)
        }

    except Exception as e:
        logger.error(f"Failed to get skill analysis: {e}")
        raise DatabaseException(
            message=f"获取技能分析失败: {str(e)}",
            operation="get_skill_analysis",
            cause=e
        )


@router.get("/aggregate/skills")
def get_aggregated_skills(
    project_id: int,  # 强制必填
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
        raise DatabaseException(
            message=f"聚合技能分析失败: {str(e)}",
            operation="get_aggregated_skills",
            cause=e
        )


@router.get("/{document_id}/fact-statements")
def get_document_fact_statements(
    document_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    获取文档的所有fact_statements（带时间戳）

    返回：[{statement, start_sec, end_sec, confidence_score, speaker}]
    """
    try:
        # 验证文档存在
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not doc:
            raise ResourceNotFoundException("Document", document_id)

        # 从SQLite数据库查询fact_statements
        import sqlite3
        from app.config import settings

        # 使用配置中的数据库URL
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT clean_text, start_sec, end_sec, confidence_score, speaker
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

        return {
            "document_id": document_id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "audio_url": audio_url,
            "total_statements": len(results),
            "statements_with_timestamps": sum(1 for s in results if s["start_sec"] is not None),
            "timestamp_coverage": round(sum(1 for s in results if s["start_sec"] is not None) / len(results) * 100, 2) if results else 0,
            "fact_statements": results
        }

    except Exception as e:
        logger.error(f"Failed to get fact statements for document {document_id}: {e}")
        raise DatabaseException(
            message=f"获取文档事实陈述失败: {str(e)}",
            operation="get_document_fact_statements",
            cause=e
        )


@router.get("/{document_id}/audio")
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
            raise ResourceNotFoundException("Document", document_id)

        # 检查文件类型
        if doc.file_type not in ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'audio']:
            raise ValidationException(
                message="此文档不是音频文件",
                field="file_type"
            )

        # 检查文件是否存在
        if not doc.file_path or not os.path.exists(doc.file_path):
            raise FileException(
                error_code=ErrorCode.FILE_NOT_FOUND,
                message="音频文件不存在",
                filename=doc.filename
            )

        # 返回音频文件
        return FileResponse(
            path=doc.file_path,
            media_type=f"audio/{doc.file_type}",
            filename=doc.filename
        )

    except Exception as e:
        logger.error(f"Failed to get audio for document {document_id}: {e}")
        raise FileException(
            message=f"获取音频文件失败: {str(e)}",
            filename=doc.filename if 'doc' in locals() else None,
            cause=e
        )

