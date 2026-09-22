"""
PDF 采集插件

核心功能：
1. 纯文本 PDF 提取（使用 PyPDF2）
2. 扫描 PDF OCR 识别（使用 PaddleOCR）
3. 自动检测 PDF 类型并选择合适的方法

技术栈：
- PyPDF2 / pdfplumber / PyMuPDF：文本提取
- OCR：扫描 PDF 识别
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class PDFPlugin(IngestionPlugin):
    """PDF 文档采集插件"""

    @property
    def plugin_name(self) -> str:
        return "PDFPlugin"

    @property
    def supported_formats(self) -> list:
        return ["pdf"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        采集 PDF 文件

        策略：
        1. 先尝试文本提取（PyPDF2）
        2. 如果提取失败或文本太少，使用 OCR（扫描 PDF）
        """
        try:
            # 尝试文本提取
            text_result = self._extract_text_with_pypdf2(file_path)

            # 检查是否是扫描 PDF（文本太少）
            text_length = len(text_result.get("text", "").strip())
            page_count = text_result.get("metadata", {}).get("pages", 0)

            # 判断标准：平均每页少于 100 字符，可能是扫描 PDF
            is_scanned = (page_count > 0 and text_length / page_count < 100)

            if is_scanned:
                logger.info("⚠️ 检测到扫描 PDF，使用 OCR...")
                ocr_result = self._extract_text_with_ocr(file_path)

                # 如果 OCR 成功，使用 OCR 结果
                if ocr_result.get("text") and len(ocr_result["text"]) > text_length:
                    logger.info("✅ 使用 OCR 结果")
                    return ocr_result

            # 使用文本提取结果
            return text_result

        except Exception as e:
            logger.error(f"PDF 采集失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise

    def _extract_text_with_pypdf2(self, file_path: str) -> Dict[str, Any]:
        """按可用性依次使用 PyPDF2、pdfplumber、PyMuPDF 提取文本。"""
        errors = []

        try:
            import PyPDF2
            logger.info("📄 使用 PyPDF2 提取文本...")

            text_content = []
            structured_metadata = {}

            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                if pdf_reader.metadata:
                    structured_metadata = {
                        "title": pdf_reader.metadata.get('/Title', ''),
                        "author": pdf_reader.metadata.get('/Author', ''),
                        "subject": pdf_reader.metadata.get('/Subject', ''),
                        "creator": pdf_reader.metadata.get('/Creator', ''),
                    }

                num_pages = len(pdf_reader.pages)
                structured_metadata["pages"] = num_pages

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text() or ""
                    if text.strip():
                        text_content.append(text)

            full_text = "\n\n".join(text_content)
            structured_metadata["total_words"] = len(full_text.replace(" ", ""))
            structured_metadata["total_sentences"] = full_text.count('。') + full_text.count('.')
            structured_metadata["language"] = self._detect_language(full_text)
            structured_metadata["extraction_method"] = "pypdf2"

            logger.info(f"✅ PyPDF2 提取完成: {len(full_text)} 字符")
            return {
                "text": full_text,
                "raw_text": full_text,
                "metadata": structured_metadata,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "pypdf2",
                "extraction_status": "success" if full_text.strip() else "empty",
                "confidence": 0.95
            }
        except Exception as e:
            errors.append(f"PyPDF2: {e}")
            logger.warning(f"PyPDF2 提取失败，尝试 pdfplumber: {e}")

        try:
            import pdfplumber
            logger.info("📄 使用 pdfplumber 提取文本...")
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    text = (page.extract_text() or "").strip()
                    if text:
                        text_content.append(text)

            full_text = "\n\n".join(text_content)
            structured_metadata = {
                "pages": page_count,
                "total_words": len(full_text.replace(" ", "")),
                "total_sentences": full_text.count('。') + full_text.count('.'),
                "language": self._detect_language(full_text),
                "extraction_method": "pdfplumber",
            }
            if full_text:
                logger.info(f"✅ pdfplumber 提取完成: {len(full_text)} 字符")
                return {
                    "text": full_text,
                    "raw_text": full_text,
                    "metadata": structured_metadata,
                    "structured_metadata": structured_metadata,
                    "content_type": "document",
                    "extraction_method": "pdfplumber",
                    "extraction_status": "success",
                    "confidence": 0.92
                }
            errors.append("pdfplumber: 未提取到文本")
        except Exception as e:
            errors.append(f"pdfplumber: {e}")
            logger.warning(f"pdfplumber 提取失败，尝试 PyMuPDF: {e}")

        try:
            import fitz
            logger.info("📄 使用 PyMuPDF 提取文本...")
            text_content = []
            with fitz.open(file_path) as pdf:
                page_count = pdf.page_count
                for page in pdf:
                    text = page.get_text("text").strip()
                    if text:
                        text_content.append(text)

            full_text = "\n\n".join(text_content)
            structured_metadata = {
                "pages": page_count,
                "total_words": len(full_text.replace(" ", "")),
                "total_sentences": full_text.count('。') + full_text.count('.'),
                "language": self._detect_language(full_text),
                "extraction_method": "pymupdf",
            }
            logger.info(f"✅ PyMuPDF 提取完成: {len(full_text)} 字符")
            return {
                "text": full_text,
                "raw_text": full_text,
                "metadata": structured_metadata,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "pymupdf",
                "extraction_status": "success" if full_text.strip() else "empty",
                "confidence": 0.9 if full_text.strip() else 0.0,
            }
        except Exception as e:
            errors.append(f"PyMuPDF: {e}")
            logger.error(f"所有 PDF 解析器均失败: {'; '.join(errors)}")
            return {
                "text": "",
                "raw_text": "",
                "metadata": {"error": "; ".join(errors)},
                "structured_metadata": {"extraction_errors": errors, "pages": 0},
                "content_type": "document",
                "extraction_method": "pdf_parsers_failed",
                "extraction_status": "failed"
            }

    def _extract_text_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """使用 OCR 提取扫描 PDF 的文本"""
        try:
            from app.services.ocr_service import get_ocr_service

            ocr_service = get_ocr_service()

            logger.info("📄 使用 OCR 识别扫描 PDF...")

            # 调用 OCR 服务
            ocr_result = ocr_service.extract_text_from_pdf(file_path)

            full_text = ocr_result.get("text", "")

            # 构建元数据
            structured_metadata = {
                "pages": len(ocr_result.get("pages", [])),
                "total_words": len(full_text.replace(" ", "")),
                "language": self._detect_language(full_text),
                "extraction_method": "paddleocr",
                "ocr_pages": ocr_result.get("pages", [])
            }

            logger.info(f"✅ OCR 提取完成: {len(full_text)} 字符")

            return {
                "text": full_text,
                "raw_text": full_text,
                "metadata": structured_metadata,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": ocr_result.get("method", "pdf_ocr"),
                "extraction_status": "success" if full_text.strip() else "empty",
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"OCR 提取失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "text": "",
                "raw_text": "",
                "metadata": {"error": str(e)},
                "extraction_method": "ocr_failed"
            }

    def _detect_language(self, text: str) -> str:
        """简单语言检测"""
        if not text:
            return "unknown"

        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text.replace(" ", "").replace("\n", ""))

        if total_chars == 0:
            return "unknown"

        if chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
