"""
数据质量监控 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter()


@router.get("/data-quality/{project_id}/overview", response_model=ApiResponse)
async def get_project_quality_overview(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取项目数据质量概览

    返回：
    - 文档总数和状态分布
    - 处理进度
    - 质量分数
    - 数据覆盖度
    - 缺口分析
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.data_quality_service import data_quality_service

        overview = data_quality_service.get_project_status(db, project_id)

        return success_response(
            data=overview,
            request_id=request_id,
            message="数据质量概览获取成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-quality/document/{document_id}", response_model=ApiResponse)
async def get_document_quality_detail(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    获取单个文档的质量详情

    返回：
    - 处理步骤和状态
    - 错误日志
    - 质量指标
    - 是否可重试
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.data_quality_service import data_quality_service

        detail = data_quality_service.get_document_detail(db, document_id)

        if "error" in detail:
            raise HTTPException(status_code=404, detail=detail["error"])

        return success_response(
            data=detail,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-quality/document/{document_id}/retry", response_model=ApiResponse)
async def retry_document_processing(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    重试文档处理

    适用于处理失败的文档
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from app.services.background_tasks import process_document_async

        # 获取文档
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查是否可以重试
        if doc.status not in ["error", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"文档状态为 {doc.status}，无法重试"
            )

        # 重置状态
        doc.status = "pending"
        doc.error_message = None

        # 清除错误标记
        if doc.extra_data:
            extra_data = dict(doc.extra_data)
            extra_data.pop("extraction_error", None)
            extra_data["retry_count"] = extra_data.get("retry_count", 0) + 1
            doc.extra_data = extra_data

        db.commit()

        # 触发重新处理
        try:
            process_document_async.delay(document_id)
        except Exception as e:
            # 如果 Celery 不可用，记录但不阻塞
            import logging
            logging.warning(f"无法触发后台任务: {e}")

        return success_response(
            data={
                "document_id": document_id,
                "status": "retry_triggered",
                "message": "已加入处理队列"
            },
            request_id=request_id,
            message="文档重试已启动"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-quality/{project_id}/gaps", response_model=ApiResponse)
async def get_project_data_gaps(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取项目数据缺口分析

    返回需要补充的数据类型和建议
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.data_quality_service import data_quality_service
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        gaps = data_quality_service._identify_gaps(db, project_id, documents)

        return success_response(
            data={
                "project_id": project_id,
                "gaps": gaps,
                "total_gaps": len(gaps),
                "high_severity": sum(1 for g in gaps if g.get("severity") == "high"),
                "medium_severity": sum(1 for g in gaps if g.get("severity") == "medium")
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-quality/{project_id}/dashboard", response_model=ApiResponse)
async def get_quality_dashboard(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    数据治理看板（综合视图）

    返回：
    - 质量概览
    - 数据覆盖度
    - 缺口分析
    - 处理错误列表
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.data_quality_service import data_quality_service
        from app.models.project import ProjectDocument

        # 获取概览
        overview = data_quality_service.get_project_status(db, project_id)

        # 获取错误文档列表
        error_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status.in_(["error", "failed"])
        ).all()

        error_list = [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "error": doc.error_message,
                "can_retry": True
            }
            for doc in error_docs
        ]

        dashboard = {
            "overview": overview,
            "error_documents": error_list,
            "recommendations": []
        }

        # 生成建议
        if overview["quality_score"] < 60:
            dashboard["recommendations"].append({
                "type": "quality_improvement",
                "message": "数据质量较低，建议检查处理错误并补充数据"
            })

        if overview["processing_progress"] < 0.8:
            dashboard["recommendations"].append({
                "type": "processing_incomplete",
                "message": "部分文档尚未完成处理，请等待或检查错误"
            })

        if len(overview.get("gaps", [])) > 0:
            dashboard["recommendations"].append({
                "type": "data_gaps",
                "message": f"发现 {len(overview['gaps'])} 个数据缺口，建议补充相关材料"
            })

        return success_response(
            data=dashboard,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
