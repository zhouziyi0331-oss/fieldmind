"""
文档化规则层 - API接口

提供三个核心接口：
1. POST /api/v1/files/{file_id}/normalize - 触发文档化
2. GET /api/v1/files/{file_id}/normalized - 获取文档化结果
3. GET /api/v1/files/{file_id}/dirty-data-report - 获取脏数据处理报告
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.project import ProjectDocument
from app.services.document_normalization.normalization_rules import (
    DocumentNormalizer,
    FileType,
    NormalizationResult
)
from app.services.document_normalization.normalization_service import (
    save_normalization_result,
    get_normalized_content,
    get_dirty_data_report
)

router = APIRouter(prefix="/api/v1/files", tags=["document-normalization"])
logger = logging.getLogger(__name__)


# =====================================================
# Schemas
# =====================================================

class NormalizeRequest(BaseModel):
    """规范化请求"""
    force: bool = False  # 是否强制重新处理
    rules: Optional[List[str]] = None  # 指定使用的规则


class NormalizeResponse(BaseModel):
    """规范化响应"""
    file_id: int
    status: str  # processing/completed/failed
    message: str
    result: Optional[Dict[str, Any]] = None


class NormalizedContentResponse(BaseModel):
    """规范化内容响应"""
    file_id: int
    file_type: str
    text_content: str
    word_count: int
    structure_info: Dict[str, Any]
    metadata: Dict[str, Any]
    completeness: Dict[str, Any]
    confidence: float
    normalized_at: str


class DirtyDataItem(BaseModel):
    """脏数据项"""
    type: str
    action: str
    location: str
    original: Optional[str]
    processed: Optional[str]
    timestamp: str


class DirtyDataReportResponse(BaseModel):
    """脏数据报告响应"""
    file_id: int
    file_name: str
    total_dirty_data: int
    dirty_data_by_type: Dict[str, int]
    dirty_data_details: List[DirtyDataItem]
    recommendations: List[str]


class CompletenessCheckResponse(BaseModel):
    """完整性检查响应"""
    file_id: int
    is_complete: bool
    score: float
    issues: List[str]
    checks: List[Dict[str, Any]]


# =====================================================
# API 1: 触发文档化
# =====================================================

@router.post("/{file_id}/normalize", response_model=NormalizeResponse)
async def normalize_document(
    file_id: int,
    request: NormalizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    触发文档规范化处理

    Args:
        file_id: 文件ID
        request: 规范化请求
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        处理状态
    """
    # 1. 检查文件是否存在
    document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    # 2. 检查是否已经规范化过
    extra_data = document.extra_data or {}
    if "normalization" in extra_data and not request.force:
        return NormalizeResponse(
            file_id=file_id,
            status="completed",
            message="文件已规范化，使用 force=true 可重新处理",
            result=extra_data["normalization"]
        )

    # 3. 提交后台任务
    background_tasks.add_task(
        normalize_document_task,
        file_id=file_id,
        db=db
    )

    logger.info(f"📝 文档规范化任务已提交: file_id={file_id}")

    return NormalizeResponse(
        file_id=file_id,
        status="processing",
        message="规范化处理中，请稍后查询结果",
        result=None
    )


def normalize_document_task(file_id: int, db: Session):
    """后台任务：规范化文档"""
    try:
        logger.info(f"🚀 开始规范化文档: file_id={file_id}")

        # 1. 加载文档
        document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
        if not document:
            logger.error(f"文件 {file_id} 不存在")
            return

        # 2. 读取文件内容
        file_path = document.local_file_path
        with open(file_path, "rb") as f:
            file_content = f.read()

        # 3. 确定文件类型
        file_type = _determine_file_type(document.file_type)

        # 4. 调用规范化器
        normalizer = DocumentNormalizer()
        result = normalizer.normalize(
            file_content=file_content,
            file_type=file_type,
            metadata={
                "file_id": file_id,
                "filename": document.original_filename,
                "file_size": document.file_size
            }
        )

        # 5. 保存结果到数据库
        save_normalization_result(db, file_id, file_type.value, result)

        # 6. 更新文档状态
        extra_data = document.extra_data or {}
        extra_data["normalization"] = {
            "status": "completed",
            "completeness": result.completeness["score"],
            "confidence": result.confidence,
            "normalized_at": datetime.utcnow().isoformat()
        }
        document.extra_data = extra_data
        db.commit()

        logger.info(f"✅ 文档规范化完成: file_id={file_id}, 完整性={result.completeness['score']:.1%}")

    except Exception as e:
        logger.error(f"❌ 文档规范化失败: file_id={file_id}, error={e}", exc_info=True)

        # 标记失败
        document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
        if document:
            extra_data = document.extra_data or {}
            extra_data["normalization"] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
            document.extra_data = extra_data
            db.commit()


def _determine_file_type(file_extension: str) -> FileType:
    """根据文件扩展名确定文件类型"""
    file_extension = file_extension.lower()

    if file_extension in ["mp3", "wav", "m4a", "flac", "ogg", "audio"]:
        return FileType.AUDIO
    elif file_extension in ["mp4", "mov", "avi", "mkv", "video"]:
        return FileType.VIDEO
    elif file_extension in ["xlsx", "xls", "csv"]:
        return FileType.TABLE
    elif file_extension in ["png", "jpg", "jpeg", "gif", "webp", "image"]:
        return FileType.IMAGE
    else:
        return FileType.DOCUMENT


# =====================================================
# API 2: 获取规范化结果
# =====================================================

@router.get("/{file_id}/normalized", response_model=NormalizedContentResponse)
async def get_normalized_document(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文档的规范化结果

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        规范化内容
    """
    # 1. 检查文件是否存在
    document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    # 2. 获取规范化内容
    normalized_content = get_normalized_content(db, file_id)
    if not normalized_content:
        raise HTTPException(
            status_code=404,
            detail=f"文件 {file_id} 尚未规范化，请先调用 /normalize 接口"
        )

    return normalized_content


# =====================================================
# API 3: 获取脏数据报告
# =====================================================

@router.get("/{file_id}/dirty-data-report", response_model=DirtyDataReportResponse)
async def get_file_dirty_data_report(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文件的脏数据处理报告

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        脏数据报告
    """
    # 1. 检查文件是否存在
    document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    # 2. 获取脏数据报告
    report = get_dirty_data_report(db, file_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"文件 {file_id} 没有脏数据处理记录"
        )

    return report


# =====================================================
# API 4: 获取完整性检查结果
# =====================================================

@router.get("/{file_id}/completeness-check", response_model=CompletenessCheckResponse)
async def get_completeness_check(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文件的完整性检查结果

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        完整性检查结果
    """
    from app.services.document_normalization.normalization_service import get_completeness_checks

    # 1. 检查文件是否存在
    document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    # 2. 获取完整性检查
    checks = get_completeness_checks(db, file_id)
    if not checks:
        raise HTTPException(
            status_code=404,
            detail=f"文件 {file_id} 没有完整性检查记录"
        )

    # 3. 汇总结果
    all_passed = all(check["is_passed"] for check in checks)
    total_score = sum(check["score"] for check in checks) / len(checks) if checks else 0
    all_issues = []
    for check in checks:
        all_issues.extend(check.get("issues", []))

    return CompletenessCheckResponse(
        file_id=file_id,
        is_complete=all_passed,
        score=total_score,
        issues=all_issues,
        checks=checks
    )


# =====================================================
# API 5: 批量规范化
# =====================================================

class BatchNormalizeRequest(BaseModel):
    """批量规范化请求"""
    file_ids: List[int]
    force: bool = False


class BatchNormalizeResponse(BaseModel):
    """批量规范化响应"""
    total: int
    submitted: int
    skipped: int
    failed: List[Dict[str, Any]]


@router.post("/batch-normalize", response_model=BatchNormalizeResponse)
async def batch_normalize_documents(
    request: BatchNormalizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量规范化文档

    Args:
        request: 批量请求
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        批量处理结果
    """
    total = len(request.file_ids)
    submitted = 0
    skipped = 0
    failed = []

    for file_id in request.file_ids:
        try:
            document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
            if not document:
                failed.append({"file_id": file_id, "reason": "文件不存在"})
                continue

            # 检查是否已规范化
            extra_data = document.extra_data or {}
            if "normalization" in extra_data and not request.force:
                skipped += 1
                continue

            # 提交任务
            background_tasks.add_task(normalize_document_task, file_id=file_id, db=db)
            submitted += 1

        except Exception as e:
            failed.append({"file_id": file_id, "reason": str(e)})

    return BatchNormalizeResponse(
        total=total,
        submitted=submitted,
        skipped=skipped,
        failed=failed
    )


# =====================================================
# API 6: 获取处理进度
# =====================================================

class ProcessingProgressResponse(BaseModel):
    """处理进度响应"""
    file_id: int
    status: str
    progress: float  # 0-1
    current_step: Optional[str]
    message: str


@router.get("/{file_id}/normalization-progress", response_model=ProcessingProgressResponse)
async def get_normalization_progress(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取规范化处理进度

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        处理进度
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == file_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    extra_data = document.extra_data or {}
    normalization = extra_data.get("normalization", {})

    status = normalization.get("status", "not_started")

    if status == "completed":
        return ProcessingProgressResponse(
            file_id=file_id,
            status="completed",
            progress=1.0,
            current_step="完成",
            message="规范化处理已完成"
        )
    elif status == "failed":
        return ProcessingProgressResponse(
            file_id=file_id,
            status="failed",
            progress=0.0,
            current_step="失败",
            message=f"规范化失败: {normalization.get('error', '未知错误')}"
        )
    elif status == "processing":
        return ProcessingProgressResponse(
            file_id=file_id,
            status="processing",
            progress=0.5,
            current_step="处理中",
            message="规范化处理中，请稍后"
        )
    else:
        return ProcessingProgressResponse(
            file_id=file_id,
            status="not_started",
            progress=0.0,
            current_step="未开始",
            message="尚未开始规范化"
        )
