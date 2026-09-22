"""
蒸馏系统 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.distillation_service import DistillationService
from app.models.distillation import DistillationStatus
from app.distillation.types import SourceKind, InputMode
from app.services.llm_adapter import get_llm_adapter


router = APIRouter(tags=["distillation"])


def get_llm_service():
    """获取LLM服务依赖"""
    try:
        adapter = get_llm_adapter(strategy="cost_optimized")
        if adapter.anthropic_llm:
            return adapter.anthropic_llm
        elif adapter.openai_llm:
            return adapter.openai_llm
        else:
            return None
    except Exception:
        return None


# ============== Pydantic Schemas ==============

class DistillationJobCreate(BaseModel):
    """创建蒸馏任务"""
    title: str = Field(..., description="文档标题")
    author: Optional[str] = Field(None, description="作者")
    source_kind: SourceKind = Field(..., description="来源类型")
    language: str = Field("zh-CN", description="语言")
    publisher: Optional[str] = None
    publish_date: Optional[str] = None


class DistillationJobCreateFromURL(BaseModel):
    """从 URL 创建蒸馏任务"""
    url: str = Field(..., description="URL 地址")
    source_kind: SourceKind = Field(..., description="来源类型")
    title: Optional[str] = Field(None, description="标题（可选）")


class DistillationJobResponse(BaseModel):
    """蒸馏任务响应"""
    id: str
    generation_id: str
    status: str
    current_stage: Optional[str]
    progress: Optional[dict]
    knowledge_count: int
    method_count: int
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


class KnowledgeUnitResponse(BaseModel):
    """知识单元响应"""
    id: str
    type: str
    title: str
    statement: str
    explanation: str
    evidence_anchors: List[dict]
    tags: List[str]


class MethodUnitResponse(BaseModel):
    """方法单元响应"""
    id: str
    name: str
    display_name: str
    description: str
    trigger_scenarios: List[str]
    execution_steps: List[dict]
    tags: List[str]


# ============== API Endpoints ==============

@router.post("/upload", response_model=dict)
async def upload_and_distill(
    file: UploadFile = File(...),
    metadata: str = Body(...),
    db: Session = Depends(get_db),
):
    """
    上传文件并创建蒸馏任务

    Args:
        file: 上传的文件
        metadata: 元数据（JSON 字符串）
        db: 数据库会话

    Returns:
        dict: 创建的任务信息
    """
    import json
    import tempfile
    import os

    # 解析元数据
    try:
        metadata_dict = json.loads(metadata)
        job_metadata = DistillationJobCreate(**metadata_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata: {e}")

    # 保存上传的文件到临时位置
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 创建蒸馏任务
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)
    job = await service.create_job_from_file(
        file_path=file_path,
        source_kind=job_metadata.source_kind,
        title=job_metadata.title,
        author=job_metadata.author,
        additional_metadata={
            "language": job_metadata.language,
            "publisher": job_metadata.publisher,
            "publish_date": job_metadata.publish_date,
        },
    )

    # 启动蒸馏
    await service.start_distillation(job.id)

    return {
        "job_id": job.id,
        "generation_id": job.generation_id,
        "status": job.status.value,
        "message": "蒸馏任务已创建并启动",
    }


@router.post("/url", response_model=dict)
async def distill_from_url(
    request: DistillationJobCreateFromURL,
    db: Session = Depends(get_db),
):
    """
    从 URL 创建蒸馏任务

    Args:
        request: 请求体
        db: 数据库会话

    Returns:
        dict: 创建的任务信息
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    # 创建任务
    job = await service.create_job_from_url(
        url=request.url,
        source_kind=request.source_kind,
        title=request.title,
    )

    # 启动蒸馏
    await service.start_distillation(job.id)

    return {
        "job_id": job.id,
        "generation_id": job.generation_id,
        "status": job.status.value,
        "message": "蒸馏任务已创建并启动",
    }


@router.get("/jobs", response_model=List[dict])
async def list_jobs(
    status: Optional[str] = Query(None, description="过滤状态"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    列出蒸馏任务

    Args:
        status: 过滤状态
        limit: 限制数量
        offset: 偏移量
        db: 数据库会话

    Returns:
        List[dict]: 任务列表
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    # 转换状态
    filter_status = None
    if status:
        try:
            filter_status = DistillationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    jobs = await service.list_jobs(status=filter_status, limit=limit, offset=offset)

    return jobs


@router.get("/jobs/{job_id}", response_model=dict)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    获取任务状态

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        dict: 任务状态
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    try:
        status = await service.get_job_status(job_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/knowledge", response_model=List[dict])
async def get_job_knowledge(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    获取任务提取的知识单元

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        List[dict]: 知识单元列表
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    try:
        knowledge = await service.get_extracted_knowledge(job_id)
        return knowledge
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/methods", response_model=List[dict])
async def get_job_methods(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    获取任务提取的方法单元

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        List[dict]: 方法单元列表
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    try:
        methods = await service.get_extracted_methods(job_id)
        return methods
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/jobs/{job_id}", response_model=dict)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    删除蒸馏任务

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        dict: 删除结果
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    success = await service.delete_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {"message": "Job deleted successfully"}


@router.post("/jobs/{job_id}/start", response_model=dict)
async def start_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    启动蒸馏任务

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        dict: 启动结果
    """
    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)

    try:
        await service.start_distillation(job_id)
        return {"message": "Job started successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{job_id}/package", response_class=FileResponse)
async def download_package(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    下载生成的 SBPACK

    Args:
        job_id: 任务 ID
        db: 数据库会话

    Returns:
        FileResponse: SBPACK 文件
    """
    from app.models.distillation import DistillationJob

    job = db.query(DistillationJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if not job.package_path or not os.path.exists(job.package_path):
        raise HTTPException(status_code=404, detail="Package not found")

    return FileResponse(
        job.package_path,
        media_type="application/zip",
        filename=f"{job.generation_id}.sbpack",
    )


@router.post("/projects/{project_id}/distill", response_model=dict)
async def distill_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    对整个项目执行知识蒸馏

    为项目中的所有文档创建蒸馏任务并执行批量蒸馏

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        dict: 批量蒸馏任务信息
    """
    from app.models.project import ProjectDocument

    # 获取项目文档
    documents = db.query(ProjectDocument).filter_by(project_id=project_id).all()

    if not documents:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} has no documents"
        )

    llm_service = get_llm_service()
    service = DistillationService(db, llm_service=llm_service)
    created_jobs = []

    # 为每个文档创建蒸馏任务
    for doc in documents:
        try:
            # 检查文件是否存在
            import os
            if not os.path.exists(doc.file_path):
                raise FileNotFoundError(f"文件不存在: {doc.file_path}")

            job = await service.create_job_from_file(
                file_path=doc.file_path,
                source_kind=SourceKind.FIELDWORK_NOTE,  # 默认类型
                title=doc.filename,
                author=None,
                additional_metadata={
                    "project_id": project_id,
                    "document_id": doc.id,
                }
            )

            # 启动蒸馏
            await service.start_distillation(job.id)

            created_jobs.append({
                "job_id": job.id,
                "document_id": doc.id,
                "filename": doc.filename,
                "status": job.status.value
            })
        except Exception as e:
            import traceback
            created_jobs.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    return {
        "project_id": project_id,
        "total_documents": len(documents),
        "jobs_created": len([j for j in created_jobs if "job_id" in j]),
        "jobs": created_jobs,
        "message": f"已为项目 {project_id} 创建 {len(created_jobs)} 个蒸馏任务"
    }


@router.get("/stats", response_model=dict)
async def get_stats(
    db: Session = Depends(get_db),
):
    """
    获取蒸馏系统统计信息

    Args:
        db: 数据库会话

    Returns:
        dict: 统计信息
    """
    from app.models.distillation import DistillationJob, ExtractedKnowledge, ExtractedMethod
    from sqlalchemy import func

    # 任务统计
    total_jobs = db.query(func.count(DistillationJob.id)).scalar()
    completed_jobs = (
        db.query(func.count(DistillationJob.id))
        .filter(DistillationJob.status == DistillationStatus.COMPLETED)
        .scalar()
    )
    failed_jobs = (
        db.query(func.count(DistillationJob.id))
        .filter(DistillationJob.status == DistillationStatus.FAILED)
        .scalar()
    )
    running_jobs = (
        db.query(func.count(DistillationJob.id))
        .filter(
            DistillationJob.status.notin_(
                [DistillationStatus.COMPLETED, DistillationStatus.FAILED]
            )
        )
        .scalar()
    )

    # 知识和方法统计
    total_knowledge = db.query(func.count(ExtractedKnowledge.id)).scalar()
    total_methods = db.query(func.count(ExtractedMethod.id)).scalar()

    return {
        "jobs": {
            "total": total_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "running": running_jobs,
        },
        "knowledge_units": total_knowledge,
        "method_units": total_methods,
    }
