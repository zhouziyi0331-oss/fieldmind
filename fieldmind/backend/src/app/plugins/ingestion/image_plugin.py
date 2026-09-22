"""
图片采集插件

核心功能：
1. OCR 文字识别（使用 PaddleOCR，支持中英文）
2. 图片元数据提取
3. 支持多种图片格式

技术栈：
- PaddleOCR：文字识别（优先）
- Tesseract：降级方案
- PIL：图片元数据
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class ImagePlugin(IngestionPlugin):
    """图片采集插件（OCR）"""

    @property
    def plugin_name(self) -> str:
        return "ImagePlugin"

    @property
    def supported_formats(self) -> list:
        return ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        采集图片文件（OCR 文字识别）

        优先使用 PaddleOCR，如果不可用则降级到 Tesseract
        """
        try:
            # 提取图片元数据
            image_metadata = self._extract_image_metadata(file_path)

            # OCR 识别（优先使用 PaddleOCR）
            ocr_result = self._ocr_with_paddleocr(file_path)

            # OCRService 已统一负责 PaddleOCR -> RapidOCR；最后才尝试 Tesseract。
            if not ocr_result.get("text") and ocr_result.get("method") in {"none", "rapidocr_onnxruntime"}:
                logger.info("⚠️ 主 OCR 未识别到文字，尝试 Tesseract...")
                tesseract_result = self._ocr_with_tesseract(file_path)
                if tesseract_result.get("text"):
                    ocr_result = tesseract_result

            # 合并元数据
            structured_metadata = {
                **image_metadata,
                "ocr_method": ocr_result.get("method"),
                "ocr_confidence": ocr_result.get("statistics", {}).get("avg_confidence"),
                "line_count": ocr_result.get("statistics", {}).get("line_count", 0),
                "total_words": len(ocr_result.get("text", "").replace(" ", "")),
                "language": self._detect_language(ocr_result.get("text", ""))
            }

            return {
                "raw_text": ocr_result.get("text", "").strip(),
                "structured_metadata": structured_metadata,
                "content_type": "image",
                "extraction_method": ocr_result.get("method"),
                "confidence": ocr_result.get("statistics", {}).get("avg_confidence", 0.0),
                # ⭐ 保存 OCR 的详细结果（用于调试和后续处理）
                "ocr_lines": ocr_result.get("lines", [])
            }

        except Exception as e:
            logger.error(f"图片采集失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise

    def _ocr_with_paddleocr(self, file_path: str) -> Dict[str, Any]:
        """使用 PaddleOCR 识别图片"""
        try:
            from app.services.ocr_service import get_ocr_service

            ocr_service = get_ocr_service()

            logger.info("📷 使用 PaddleOCR 识别图片...")
            result = ocr_service.extract_text_from_image(
                file_path,
                return_confidence=True,
                return_boxes=False
            )

            logger.info(f"✅ PaddleOCR 识别完成: {len(result.get('lines', []))} 行")

            return result

        except ImportError:
            logger.warning("PaddleOCR 未安装")
            return {"text": "", "lines": [], "method": "none"}
        except Exception as e:
            logger.error(f"PaddleOCR 识别失败: {e}")
            return {"text": "", "lines": [], "method": "none", "error": str(e)}

    def _ocr_with_tesseract(self, file_path: str) -> Dict[str, Any]:
        """使用 Tesseract OCR（降级方案）"""
        try:
            import pytesseract
            from PIL import Image

            logger.info("📷 使用 Tesseract 识别图片...")

            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')

            logger.info(f"✅ Tesseract 识别完成")

            return {
                "text": text,
                "method": "tesseract",
                "statistics": {
                    "line_count": text.count('\n'),
                    "char_count": len(text),
                    "avg_confidence": 0.75  # Tesseract 默认置信度估计
                }
            }

        except ImportError:
            logger.warning("Tesseract 未安装")
            return {"text": "", "method": "none"}
        except Exception as e:
            logger.error(f"Tesseract 识别失败: {e}")
            return {"text": "", "method": "none", "error": str(e)}

    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取图片元数据"""
        try:
            from PIL import Image

            img = Image.open(file_path)

            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size_pixels": img.width * img.height,
                "dpi": img.info.get('dpi', (72, 72)),  # 分辨率
            }

        except Exception as e:
            logger.error(f"图片元数据提取失败: {e}")
            return {
                "format": "unknown",
                "error": str(e)
            }

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        if not text:
            return "unknown"

        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text.replace(" ", "").replace("\n", ""))

        if total_chars == 0:
            return "unknown"

        if chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
