"""
统一工具API - 整合所有工具相关功能
合并自: ocr, audio等工具模块
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter(prefix="/api/tools", tags=["统一工具"])

# ============================================================================
# 请求/响应模型
# ============================================================================

class OCRRequest(BaseModel):
    """OCR识别请求"""
    language: str = Field(default="zh", description="识别语言")
    enhance: bool = Field(default=True, description="是否增强图像")


# ============================================================================
# 1. OCR文字识别
# ============================================================================

@router.post("/ocr/recognize", response_model=ApiResponse, summary="OCR识别")
async def ocr_recognize(
    request: Request,
    file: UploadFile = File(...),
    language: str = Query("zh", description="识别语言"),
    enhance: bool = Query(True, description="是否增强图像"),
    db: Session = Depends(get_db)
):
    """
    OCR文字识别

    支持的语言:
    - zh: 中文
    - en: 英文
    - zh-en: 中英文混合
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 实现OCR识别
        result = {
            "text": "识别的文字内容",
            "language": language,
            "confidence": 0.95
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/recognize-pdf", response_model=ApiResponse, summary="PDF OCR识别")
async def ocr_recognize_pdf(
    request: Request,
    file: UploadFile = File(...),
    language: str = Query("zh", description="识别语言"),
    db: Session = Depends(get_db)
):
    """对PDF文件进行OCR识别"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 实现PDF OCR
        result = {
            "pages": [],
            "total_pages": 0,
            "language": language
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/recognize-batch", response_model=ApiResponse, summary="批量OCR识别")
async def ocr_recognize_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    language: str = Query("zh", description="识别语言"),
    db: Session = Depends(get_db)
):
    """批量OCR识别"""
    request_id = getattr(request.state, "request_id", None)

    try:
        results = []
        for file in files:
            # TODO: 批量处理
            results.append({
                "filename": file.filename,
                "text": "识别内容",
                "confidence": 0.95
            })

        return success_response(
            data={
                "results": results,
                "total": len(results)
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/quality-check", response_model=ApiResponse, summary="OCR质量检查")
async def ocr_quality_check(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """检查图像质量是否适合OCR"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 质量检查
        quality = {
            "suitable": True,
            "quality_score": 0.85,
            "issues": []
        }

        return success_response(data=quality, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/supported-languages", response_model=ApiResponse, summary="获取支持的语言")
async def get_supported_languages(request: Request):
    """获取OCR支持的语言列表"""
    request_id = getattr(request.state, "request_id", None)

    languages = [
        {"code": "zh", "name": "中文"},
        {"code": "en", "name": "英文"},
        {"code": "zh-en", "name": "中英文混合"}
    ]

    return success_response(data={"languages": languages}, request_id=request_id)


@router.get("/ocr/statistics", response_model=ApiResponse, summary="OCR统计")
async def get_ocr_statistics(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取OCR使用统计"""
    request_id = getattr(request.state, "request_id", None)

    try:
        stats = {
            "total_recognitions": 0,
            "total_pages": 0,
            "avg_confidence": 0.0
        }

        return success_response(data=stats, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. 健康检查
# ============================================================================

@router.get("/health", response_model=ApiResponse, summary="工具健康检查")
async def health_check(request: Request):
    """检查工具服务的健康状态"""
    request_id = getattr(request.state, "request_id", None)

    health = {
        "status": "healthy",
        "services": {
            "ocr": "available",
        }
    }

    return success_response(data=health, request_id=request_id)


# ============================================================================
# 补充端点：从旧模块迁移的导出功能
# ============================================================================

@router.get("/documents/{document_id}/pdf", summary="导出文档为PDF")
async def export_document_pdf(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """导出单个文档摘要为PDF格式"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from fastapi.responses import FileResponse
        from sqlalchemy import text
        import json

        # 查询文档摘要
        result = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.document_id = :document_id
        """), {'document_id': document_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="文档摘要不存在")

        # 解析数据
        summary = {
            'document_title': result[-1] if result[-1] else f"文档{document_id}",
            'one_line_summary': result[3] if len(result) > 3 else '',
            'full_summary': result[4] if len(result) > 4 else '',
            'top_keywords': json.loads(result[5]) if len(result) > 5 and result[5] else [],
            'generated_at': result[21] if len(result) > 21 else None
        }

        # 简化版PDF生成（返回JSON，实际PDF生成需要额外的库）
        # 这里返回一个占位响应，实际实现需要使用reportlab或类似库
        return success_response(
            data={
                "message": "PDF导出功能",
                "document_id": document_id,
                "title": summary['document_title'],
                "note": "完整PDF生成需要配置reportlab库"
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


@router.get("/documents/{document_id}/word", summary="导出文档为Word")
async def export_document_word(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """导出单个文档摘要为Word格式"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from sqlalchemy import text
        import json

        # 查询文档摘要
        result = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.document_id = :document_id
        """), {'document_id': document_id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="文档摘要不存在")

        # 解析数据
        summary = {
            'document_title': result[-1] if result[-1] else f"文档{document_id}",
            'one_line_summary': result[3] if len(result) > 3 else '',
            'full_summary': result[4] if len(result) > 4 else '',
            'top_keywords': json.loads(result[5]) if len(result) > 5 and result[5] else [],
            'generated_at': result[21] if len(result) > 21 else None
        }

        # 简化版Word生成（返回JSON，实际Word生成需要额外的库）
        # 实际实现需要使用python-docx库
        return success_response(
            data={
                "message": "Word导出功能",
                "document_id": document_id,
                "title": summary['document_title'],
                "note": "完整Word生成需要配置python-docx库"
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Word失败: {str(e)}")


@router.get("/projects/{project_id}/pdf", summary="导出项目为PDF")
async def export_project_pdf(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """批量导出项目所有文档摘要为PDF"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from sqlalchemy import text
        import json

        # 查询所有文档摘要
        results = db.execute(text("""
            SELECT s.*, d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.project_id = :project_id AND s.status = 'done'
            ORDER BY s.created_at DESC
        """), {'project_id': project_id}).fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="项目中没有可用的摘要")

        # 解析数据
        summaries = []
        for row in results:
            summaries.append({
                'document_title': row[-1] if row[-1] else f"文档{row[2]}",
                'one_line_summary': row[3] if len(row) > 3 else '',
                'full_summary': row[4] if len(row) > 4 else '',
            })

        # 简化版批量PDF生成
        return success_response(
            data={
                "message": "项目PDF导出功能",
                "project_id": project_id,
                "document_count": len(summaries),
                "note": "完整PDF生成需要配置reportlab库"
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出项目PDF失败: {str(e)}")
