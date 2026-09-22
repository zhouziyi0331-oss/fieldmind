"""
OCR API端点 - PaddleOCR文本识别接口
支持图像OCR、PDF OCR、批量处理、质量检查
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
import tempfile
import shutil
import time
from datetime import datetime

from app.schemas.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 请求/响应模型 ====================

class OCRRequest(BaseModel):
    """OCR识别请求"""
    language: str = Field(default="ch", description="识别语言 (ch/en/chinese_cht/japan/korean)")
    detect_direction: bool = Field(default=True, description="是否检测文字方向")
    enable_quality_check: bool = Field(default=True, description="是否启用质量检查")


class BatchOCRRequest(BaseModel):
    """批量OCR请求"""
    language: str = Field(default="ch", description="识别语言")
    max_workers: int = Field(default=4, ge=1, le=10, description="并发工作线程数")
    enable_quality_check: bool = Field(default=True, description="是否启用质量检查")


class PDFOCRRequest(BaseModel):
    """PDF OCR请求"""
    language: str = Field(default="ch", description="识别语言")
    start_page: Optional[int] = Field(default=None, ge=1, description="起始页码")
    end_page: Optional[int] = Field(default=None, ge=1, description="结束页码")
    enable_quality_check: bool = Field(default=True, description="是否启用质量检查")


class OCRResponse(BaseModel):
    """OCR识别响应"""
    success: bool
    text: str
    text_blocks: List[Dict[str, Any]]
    confidence: float
    language: str
    processing_time: float
    total_blocks: int
    quality_report: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class BatchOCRResponse(BaseModel):
    """批量OCR响应"""
    success: bool
    total_images: int
    results: List[OCRResponse]
    total_processing_time: float
    average_confidence: float
    failed_count: int


class PDFOCRResponse(BaseModel):
    """PDF OCR响应"""
    success: bool
    total_pages: int
    processed_pages: int
    pages: List[OCRResponse]
    full_text: str
    total_processing_time: float
    average_confidence: float


# ==================== OCR端点 ====================

@router.post("/recognize", response_model=OCRResponse)
async def recognize_image(
    file: UploadFile = File(..., description="图像文件"),
    language: str = Query(default="ch", description="识别语言"),
    detect_direction: bool = Query(default=True, description="是否检测文字方向"),
    enable_quality_check: bool = Query(default=True, description="是否启用质量检查")
):
    """
    识别单个图像中的文本

    支持格式: JPG, PNG, BMP, TIFF
    """
    start_time = time.time()
    temp_path = None

    try:
        # 验证文件类型
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"
            )

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        logger.info(f"📄 OCR请求: {file.filename}, 语言={language}")

        # 执行OCR
        from app.services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service(lang=language)
        result = ocr_service.recognize_image(temp_path, language=language, detect_direction=detect_direction)

        # 质量检查
        quality_report = None
        if enable_quality_check and result.text:
            from app.services.ocr_quality_checker import check_ocr_quality
            quality_check = check_ocr_quality(result)
            quality_report = quality_check.to_dict()

        # 构建响应
        response = OCRResponse(
            success=True,
            text=result.text,
            text_blocks=result.text_blocks,
            confidence=result.confidence,
            language=result.language,
            processing_time=result.processing_time,
            total_blocks=result.total_blocks,
            quality_report=quality_report,
            metadata={
                "filename": file.filename,
                "image_size": result.image_size,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"✅ OCR完成: {result.total_blocks}个文本块, 置信度{result.confidence:.2%}")

        return response

    except Exception as e:
        logger.error(f"❌ OCR识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"OCR识别失败: {str(e)}")

    finally:
        # 清理临时文件
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()
        if file.file:
            file.file.close()


@router.post("/recognize-pdf", response_model=PDFOCRResponse)
async def recognize_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    language: str = Query(default="ch", description="识别语言"),
    start_page: Optional[int] = Query(default=None, ge=1, description="起始页码"),
    end_page: Optional[int] = Query(default=None, ge=1, description="结束页码"),
    enable_quality_check: bool = Query(default=True, description="是否启用质量检查")
):
    """
    识别PDF文档中的文本

    支持指定页码范围，默认处理全部页
    """
    start_time = time.time()
    temp_path = None

    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="仅支持PDF文件")

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        logger.info(f"📚 PDF OCR请求: {file.filename}")

        # 执行PDF OCR
        from app.services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service(lang=language)

        page_range = None
        if start_page is not None:
            page_range = (start_page - 1, end_page if end_page else 999999)

        results = ocr_service.recognize_pdf(temp_path, page_range=page_range, language=language)

        # 构建页面响应
        page_responses = []
        full_text_parts = []
        total_confidence = 0.0

        for result in results:
            # 质量检查
            quality_report = None
            if enable_quality_check and result.text:
                from app.services.ocr_quality_checker import check_ocr_quality
                quality_check = check_ocr_quality(result)
                quality_report = quality_check.to_dict()

            page_response = OCRResponse(
                success=True,
                text=result.text,
                text_blocks=result.text_blocks,
                confidence=result.confidence,
                language=result.language,
                processing_time=result.processing_time,
                total_blocks=result.total_blocks,
                quality_report=quality_report,
                metadata=result.metadata
            )
            page_responses.append(page_response)
            full_text_parts.append(result.text)
            total_confidence += result.confidence

        # 构建响应
        total_time = time.time() - start_time
        avg_confidence = total_confidence / len(results) if results else 0.0

        response = PDFOCRResponse(
            success=True,
            total_pages=len(results),
            processed_pages=len(results),
            pages=page_responses,
            full_text="\n\n".join(full_text_parts),
            total_processing_time=total_time,
            average_confidence=avg_confidence
        )

        logger.info(f"✅ PDF OCR完成: {len(results)}页, 平均置信度{avg_confidence:.2%}")

        return response

    except Exception as e:
        logger.error(f"❌ PDF OCR失败: {e}")
        raise HTTPException(status_code=500, detail=f"PDF OCR失败: {str(e)}")

    finally:
        # 清理临时文件
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()
        if file.file:
            file.file.close()


@router.post("/recognize-batch", response_model=BatchOCRResponse)
async def recognize_batch(
    files: List[UploadFile] = File(..., description="图像文件列表"),
    language: str = Query(default="ch", description="识别语言"),
    max_workers: int = Query(default=4, ge=1, le=10, description="并发工作线程数"),
    enable_quality_check: bool = Query(default=True, description="是否启用质量检查")
):
    """
    批量识别多个图像

    支持并发处理，提高效率
    """
    start_time = time.time()
    temp_paths = []

    try:
        # 验证文件数量
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="单次最多处理50个文件")

        logger.info(f"🔄 批量OCR请求: {len(files)}个文件")

        # 保存临时文件
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

        for file in files:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file.filename}"
                )

            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_paths.append(temp_file.name)
            file.file.close()

        # 执行批量OCR
        from app.services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service(lang=language)
        results = ocr_service.recognize_batch(temp_paths, language=language, max_workers=max_workers)

        # 构建响应
        responses = []
        total_confidence = 0.0
        failed_count = 0

        for i, result in enumerate(results):
            # 质量检查
            quality_report = None
            if enable_quality_check and result.text:
                from app.services.ocr_quality_checker import check_ocr_quality
                quality_check = check_ocr_quality(result)
                quality_report = quality_check.to_dict()

            success = "error" not in result.metadata
            if not success:
                failed_count += 1

            response = OCRResponse(
                success=success,
                text=result.text,
                text_blocks=result.text_blocks,
                confidence=result.confidence,
                language=result.language,
                processing_time=result.processing_time,
                total_blocks=result.total_blocks,
                quality_report=quality_report,
                metadata={
                    **result.metadata,
                    "filename": files[i].filename,
                    "image_size": result.image_size
                }
            )
            responses.append(response)

            if success:
                total_confidence += result.confidence

        # 计算平均值
        total_time = time.time() - start_time
        success_count = len(results) - failed_count
        avg_confidence = total_confidence / success_count if success_count > 0 else 0.0

        batch_response = BatchOCRResponse(
            success=True,
            total_images=len(files),
            results=responses,
            total_processing_time=total_time,
            average_confidence=avg_confidence,
            failed_count=failed_count
        )

        logger.info(
            f"✅ 批量OCR完成: {success_count}/{len(files)}成功, "
            f"平均置信度{avg_confidence:.2%}, 耗时{total_time:.2f}秒"
        )

        return batch_response

    except Exception as e:
        logger.error(f"❌ 批量OCR失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量OCR失败: {str(e)}")

    finally:
        # 清理临时文件
        for temp_path in temp_paths:
            if Path(temp_path).exists():
                Path(temp_path).unlink()


@router.get("/statistics")
async def get_ocr_statistics():
    """
    获取OCR服务统计信息
    """
    try:
        from app.services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service()
        stats = ocr_service.get_statistics()

        return success_response(
            data={
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/supported-languages")
async def get_supported_languages():
    """
    获取支持的语言列表
    """
    languages = {
        "ch": "中英文混合",
        "en": "英文",
        "chinese_cht": "繁体中文",
        "japan": "日文",
        "korean": "韩文",
        "french": "法文",
        "german": "德文",
        "spanish": "西班牙文",
        "portuguese": "葡萄牙文",
        "russian": "俄文",
        "arabic": "阿拉伯文",
        "hindi": "印地文"
    }

    return success_response(
        data={
            "languages": languages,
            "default": "ch",
            "recommended_for_chinese": ["ch", "chinese_cht"]
        }
    )


@router.post("/quality-check")
async def check_ocr_quality_endpoint(
    file: UploadFile = File(..., description="图像文件"),
    language: str = Query(default="ch", description="识别语言")
):
    """
    执行OCR并返回详细的质量报告

    用于质量评估和调试
    """
    temp_path = None

    try:
        # 保存临时文件
        file_ext = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        # 执行OCR
        from app.services.ocr_service import get_ocr_service
        from app.services.ocr_quality_checker import check_ocr_quality

        ocr_service = get_ocr_service(lang=language)
        result = ocr_service.recognize_image(temp_path, language=language)

        # 质量检查
        quality_report = check_ocr_quality(result)

        return success_response(
            data={
                "filename": file.filename,
                "ocr_result": result.to_dict(),
                "quality_report": quality_report.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"❌ 质量检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"质量检查失败: {str(e)}")

    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()
        if file.file:
            file.file.close()


@router.get("/health")
async def ocr_health_check():
    """
    OCR服务健康检查
    """
    try:
        from app.services.ocr_service import get_ocr_service

        # 尝试初始化服务
        ocr_service = get_ocr_service()
        stats = ocr_service.get_statistics()

        return success_response(
            data={
                "status": "healthy",
                "service": "OCR (PaddleOCR)",
                "initialized": ocr_service.ocr_engine is not None,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"❌ OCR健康检查失败: {e}")
        return error_response(
            message="OCR service unhealthy",
            error=str(e),
            status_code=503
        )
