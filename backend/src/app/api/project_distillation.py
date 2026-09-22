"""
项目级知识蒸馏 API
支持对整个项目的文档批量执行知识蒸馏
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.services.distillation_service import DistillationService
from app.models.document import Document
from app.distillation.types import SourceKind

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/projects", tags=["项目蒸馏"])


class ProjectDistillationRequest(BaseModel):
    """项目蒸馏请求"""
    mode: str = Field("incremental", description="蒸馏模式: full(完整) 或 incremental(增量)")
    document_ids: Optional[List[str]] = Field(None, description="指定文档ID列表，为空则处理所有文档")
    description: Optional[str] = Field(None, description="任务描述")


@router.post("/{project_id}/distill", response_model=dict)
async def distill_project(
    project_id: int,
    request: ProjectDistillationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    对项目执行知识蒸馏

    Args:
        project_id: 项目ID
        request: 蒸馏请求参数
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        dict: 蒸馏任务信息
    """
    # 获取项目文档
    if request.document_ids:
        documents = (
            db.query(Document)
            .filter(
                Document.project_id == project_id,
                Document.id.in_(request.document_ids)
            )
            .all()
        )
    else:
        documents = db.query(Document).filter_by(project_id=project_id).all()

    if not documents:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found in project {project_id}"
        )

    service = DistillationService(db)
    jobs = []

    # 为每个文档创建蒸馏任务
    for doc in documents:
        try:
            # 检查文档是否有内容文件
            if not doc.file_path:
                logger.warning(f"Document {doc.id} has no file_path, skipping")
                continue

            # 创建蒸馏任务
            job = await service.create_job_from_file(
                file_path=doc.file_path,
                source_kind=SourceKind.ACADEMIC_PAPER,  # 默认学术论文类型
                title=doc.name or doc.id,
                author=None,
                additional_metadata={
                    "project_id": project_id,
                    "document_id": doc.id,
                    "mode": request.mode,
                    "description": request.description or f"项目 {project_id} 文档蒸馏",
                }
            )

            # 在后台启动蒸馏
            background_tasks.add_task(service.start_distillation, job.id)

            jobs.append({
                "job_id": job.id,
                "document_id": doc.id,
                "document_name": doc.name,
                "status": job.status.value,
            })

        except Exception as e:
            logger.error(f"Failed to create distillation job for document {doc.id}: {e}")
            jobs.append({
                "document_id": doc.id,
                "document_name": doc.name,
                "status": "failed",
                "error": str(e),
            })

    return {
        "project_id": project_id,
        "mode": request.mode,
        "total_documents": len(documents),
        "jobs_created": len([j for j in jobs if "error" not in j]),
        "jobs_failed": len([j for j in jobs if "error" in j]),
        "jobs": jobs,
        "message": f"Created {len(jobs)} distillation jobs for project {project_id}",
    }


@router.get("/{project_id}/distillation-status", response_model=dict)
async def get_project_distillation_status(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取项目的蒸馏状态

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        dict: 蒸馏状态统计
    """
    from app.models.distillation import DistillationJob, DistillationStatus
    from sqlalchemy import func, and_

    # 查询项目相关的蒸馏任务
    jobs = (
        db.query(DistillationJob)
        .filter(DistillationJob.metadata.contains(f'"project_id": {project_id}'))
        .all()
    )

    if not jobs:
        return {
            "project_id": project_id,
            "total_jobs": 0,
            "status_breakdown": {},
            "knowledge_units": 0,
            "method_units": 0,
            "message": "No distillation jobs found for this project",
        }

    # 统计状态
    status_counts = {}
    for job in jobs:
        status = job.status.value
        status_counts[status] = status_counts.get(status, 0) + 1

    # 统计知识和方法单元
    from app.models.distillation import ExtractedKnowledge, ExtractedMethod

    job_ids = [job.id for job in jobs]
    knowledge_count = (
        db.query(func.count(ExtractedKnowledge.id))
        .filter(ExtractedKnowledge.distillation_job_id.in_(job_ids))
        .scalar()
    )
    method_count = (
        db.query(func.count(ExtractedMethod.id))
        .filter(ExtractedMethod.distillation_job_id.in_(job_ids))
        .scalar()
    )

    return {
        "project_id": project_id,
        "total_jobs": len(jobs),
        "status_breakdown": status_counts,
        "knowledge_units": knowledge_count,
        "method_units": method_count,
        "jobs": [
            {
                "job_id": job.id,
                "generation_id": job.generation_id,
                "status": job.status.value,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs
        ],
    }
