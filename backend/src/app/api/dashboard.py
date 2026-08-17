"""
Dashboard统计API

提供项目的综合统计数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundException, DatabaseException
from app.models.project import Project, ProjectDocument, ProjectChatSession, ProjectChatMessage

router = APIRouter(tags=["dashboard"])
logger = logging.getLogger(__name__)


class DashboardStats(BaseModel):
    """Dashboard统计数据"""
    # 文档统计
    total_documents: int
    completed_documents: int
    processing_documents: int
    failed_documents: int
    total_words: int
    total_chunks: int

    # Skill分析统计
    skills_analyzed: int
    total_dimensions: int

    # 关键词统计
    total_keywords: int
    top_keywords: List[Dict]

    # 向量检索统计
    vectorized_documents: int
    vector_count: int

    # 对话统计
    chat_sessions: int
    chat_messages: int

    # 报告统计
    reports_generated: int

    # 活跃度统计
    last_activity: Optional[str]
    documents_this_week: int

    # 项目信息
    project_name: str
    project_created: str


@router.get("/stats/{project_id}", response_model=DashboardStats)
def get_dashboard_stats(
    project_id: int,
    db: Session = Depends(get_db)
) -> DashboardStats:
    """
    获取项目的Dashboard统计数据
    """
    try:
        # 获取项目
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise ResourceNotFoundException("Project", project_id)

        # 1. 文档统计
        total_documents = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        completed_documents = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).scalar() or 0

        processing_documents = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status.in_(['pending', 'processing'])
        ).scalar() or 0

        failed_documents = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'failed'
        ).scalar() or 0

        # 总字数
        total_words = db.query(func.sum(ProjectDocument.word_count)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).scalar() or 0

        # 2. 向量化统计
        vectorized_documents = 0
        total_chunks = 0

        completed_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        from app.services.pipeline_status import is_pipeline_completed

        for doc in completed_docs:
            if is_pipeline_completed(doc):
                vectorized_documents += 1
                chunks = doc.extra_data.get('chunks_count', 0) if doc.extra_data else 0
                if chunks:
                    total_chunks += chunks

        # 从ChromaDB获取向量数量
        vector_count = 0
        try:
            from app.core.rag_engine import rag_engine
            if rag_engine and rag_engine.collection:
                vector_count = rag_engine.collection.count()
        except ImportError:
            logger.debug("RAG引擎未初始化")
        except Exception as e:
            logger.warning(f"获取向量数量失败: {e}")

        # 3. Skill分析统计
        skills_analyzed = 0
        total_dimensions = 0

        for doc in completed_docs:
            if doc.extra_data and doc.extra_data.get('skills_completed'):
                skills_analyzed += 1
                skill_results = doc.extra_data.get('skill_results', {})
                for skill_name, skill_data in skill_results.items():
                    dimensions = skill_data.get('dimensions', {})
                    for dim_name, dim_data in dimensions.items():
                        if dim_data.get('matched_count', 0) > 0:
                            total_dimensions += 1

        # 4. 关键词统计
        keyword_freq = {}

        for doc in completed_docs:
            if doc.extra_data and doc.extra_data.get('keywords'):
                for kw in doc.extra_data['keywords']:
                    word = kw.get('word') if isinstance(kw, dict) else str(kw)
                    weight = kw.get('weight', 1.0) if isinstance(kw, dict) else 1.0
                    keyword_freq[word] = keyword_freq.get(word, 0) + weight

        total_keywords = len(keyword_freq)

        # Top 10关键词
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = [
            {"keyword": word, "weight": round(freq, 2)}
            for word, freq in sorted_keywords
        ]

        # 5. 对话统计
        chat_sessions = db.query(func.count(ProjectChatSession.id)).filter(
            ProjectChatSession.project_id == project_id
        ).scalar() or 0

        chat_messages = db.query(func.count(ProjectChatMessage.id)).join(
            ProjectChatSession
        ).filter(
            ProjectChatSession.project_id == project_id
        ).scalar() or 0

        # 6. 报告统计（暂时使用完成文档数作为近似）
        reports_generated = completed_documents

        # 7. 活跃度统计
        last_activity = project.last_activity_at.strftime('%Y-%m-%d %H:%M:%S') if project.last_activity_at else None

        # 本周新增文档
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        documents_this_week = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.created_at >= one_week_ago
        ).scalar() or 0

        # 8. 项目信息
        project_name = project.name
        project_created = project.created_at.strftime('%Y-%m-%d') if project.created_at else "未知"

        return DashboardStats(
            total_documents=total_documents,
            completed_documents=completed_documents,
            processing_documents=processing_documents,
            failed_documents=failed_documents,
            total_words=total_words,
            total_chunks=total_chunks,
            skills_analyzed=skills_analyzed,
            total_dimensions=total_dimensions,
            total_keywords=total_keywords,
            top_keywords=top_keywords,
            vectorized_documents=vectorized_documents,
            vector_count=vector_count,
            chat_sessions=chat_sessions,
            chat_messages=chat_messages,
            reports_generated=reports_generated,
            last_activity=last_activity,
            documents_this_week=documents_this_week,
            project_name=project_name,
            project_created=project_created
        )

    except (ResourceNotFoundException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}", exc_info=True)
        raise DatabaseException(message=str(e), operation="dashboard", cause=e)


@router.get("/timeline/{project_id}")
def get_project_timeline(
    project_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取项目的时间线数据（最近N天的活动）
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # 按日期分组统计文档
        documents_by_date = {}

        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.created_at >= start_date
        ).all()

        for doc in docs:
            date_key = doc.created_at.strftime('%Y-%m-%d')
            if date_key not in documents_by_date:
                documents_by_date[date_key] = 0
            documents_by_date[date_key] += 1

        # 生成完整的日期序列
        timeline = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
            timeline.append({
                "date": date,
                "documents": documents_by_date.get(date, 0)
            })

        return {
            "timeline": timeline,
            "total_days": days
        }

    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        raise DatabaseException(message=str(e), operation="dashboard", cause=e)


@router.get("/progress/{project_id}")
def get_project_progress(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取项目的整体进度指标
    """
    try:
        total_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        if total_docs == 0:
            return {
                "upload_progress": 0,
                "processing_progress": 0,
                "analysis_progress": 0,
                "overall_progress": 0
            }

        completed_docs = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).scalar() or 0

        # 向量化完成数
        vectorized = 0
        # Skill分析完成数
        analyzed = 0

        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        for doc in docs:
            if is_pipeline_completed(doc):
                vectorized += 1
            if doc.extra_data and doc.extra_data.get('skills_completed'):
                analyzed += 1

        return {
            "upload_progress": 100,  # 假设已上传
            "processing_progress": int((completed_docs / total_docs) * 100),
            "vectorization_progress": int((vectorized / total_docs) * 100),
            "analysis_progress": int((analyzed / total_docs) * 100),
            "overall_progress": int((analyzed / total_docs) * 100)
        }

    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        raise DatabaseException(message=str(e), operation="dashboard", cause=e)
