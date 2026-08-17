"""报告生成API路由 - 完整实现和增强"""
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from pathlib import Path

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundException, ValidationException, FileException
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.schemas.report import (
    ReportGenerateRequest, ReportResponse,
    SummaryDocumentRequest, SummaryDocumentResponse
)
from app.middleware.auth import get_current_user
# from app.tasks.report_tasks import generate_report

router = APIRouter(tags=["Reports"])

# 报告存储目录 - 使用环境变量
REPORTS_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", "./reports"))
REPORTS_DIR.mkdir(exist_ok=True)


@router.post("/generate", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    report_data: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成报告（异步任务）"""
    # 创建报告记录
    new_report = Report(
        title=report_data.title,
        report_type=report_data.report_type,
        status=ReportStatus.PROCESSING,
        config={
            "time_range": report_data.time_range.dict() if report_data.time_range else None,
            "include": report_data.include.dict(),
            "format": report_data.format
        },
        data_sources=report_data.data_sources.dict(),
        file_format=report_data.format
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # 启动异步任务
    task = generate_report.delay(
        report_id=new_report.id,
        title=report_data.title,
        report_type=report_data.report_type.value,
        time_range=report_data.time_range.dict() if report_data.time_range else None,
        include=report_data.include.dict(),
        data_sources=report_data.data_sources.dict(),
        output_format=report_data.format
    )

    # 更新task_id
    new_report.task_id = task.id
    db.commit()

    return {
        "report_id": new_report.id,
        "task_id": task.id,
        "status": "processing",
        "message": "Report generation started"
    }


@router.get("", response_model=list)
async def list_reports(
    status: Optional[ReportStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告列表"""
    query = db.query(Report)

    if status:
        query = query.filter(Report.status == status)

    query = query.order_by(Report.created_at.desc())

    offset = (page - 1) * limit
    reports = query.offset(offset).limit(limit).all()

    return [ReportResponse.from_orm(report) for report in reports]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报告详情"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ResourceNotFoundException(
            resource_type="Report",
            resource_id=report_id
        )

    return ReportResponse.from_orm(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("docx", pattern="^(docx|pdf|html)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载报告文件"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ResourceNotFoundException(
            resource_type="Report",
            resource_id=report_id
        )

    if report.status != ReportStatus.COMPLETED:
        raise ValidationException(
            message=f"Report is not ready for download. Current status: {report.status}",
            field="status"
        )

    if not report.file_path or not os.path.exists(report.file_path):
        raise FileException(
            message="Report file not found",
            operation="download",
            details={"file_path": report.file_path}
        )

    # 确定MIME类型
    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "html": "text/html"
    }

    filename = f"{report.title}.{format}"
    media_type = media_types.get(format, "application/octet-stream")

    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=filename
    )


@router.delete("/{report_id}", response_model=dict)
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除报告"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ResourceNotFoundException(
            resource_type="Report",
            resource_id=report_id
        )

    # 删除文件
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {report.file_path}: {e}")

    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully"}


@router.post("/summary-document", response_model=SummaryDocumentResponse)
async def generate_summary_document(
    summary_data: SummaryDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成总结文档"""
    # TODO: 集成实际的RAG系统和LLM生成摘要
    # 这里提供示例实现

    if not summary_data.document_ids:
        raise ValidationException(
            message="At least one document ID is required",
            field="document_ids"
        )

    # 示例摘要
    summary = f"本文档综合分析了{len(summary_data.document_ids)}份相关文档。"

    sections = [
        {
            "title": "概述",
            "content": "这是一个综合分析报告，涵盖了多个方面的调研结果。"
        },
        {
            "title": "主要发现",
            "content": "通过深入分析，我们发现了以下关键信息..."
        },
        {
            "title": "结论与建议",
            "content": "基于以上分析，我们提出以下建议..."
        }
    ]

    citations = []
    if summary_data.include_citations:
        citations = [
            {"document_id": doc_id, "reference": f"[{i+1}]"}
            for i, doc_id in enumerate(summary_data.document_ids)
        ]

    word_count = len(summary) + sum(len(s["content"]) for s in sections)

    return SummaryDocumentResponse(
        summary=summary,
        sections=sections,
        citations=citations,
        word_count=word_count
    )
