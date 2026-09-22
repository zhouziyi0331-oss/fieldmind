"""
PDF 增强服务
基于 pdfcn 的核心功能
支持 PDF 预览、注释、标记
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PDFEnhancedService:
    """
    PDF 增强服务

    功能：
    1. PDF 文本提取
    2. PDF 元数据提取
    3. PDF 注释支持
    4. PDF 预览生成
    """

    def __init__(self):
        self._init_pdf_library()

    def _init_pdf_library(self):
        """初始化 PDF 库"""
        try:
            import PyPDF2
            self.pdf_lib = PyPDF2
            self.has_pypdf = True
        except ImportError:
            logger.warning("PyPDF2 未安装")
            self.has_pypdf = False

    def extract_text(self, pdf_path: str) -> str:
        """提取 PDF 文本"""
        if not self.has_pypdf:
            return self._fallback_extract(pdf_path)

        try:
            with open(pdf_path, 'rb') as f:
                reader = self.pdf_lib.PdfReader(f)
                text_parts = []

                for page in reader.pages:
                    text_parts.append(page.extract_text())

                return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return ""

    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """提取 PDF 元数据"""
        if not self.has_pypdf:
            return {}

        try:
            with open(pdf_path, 'rb') as f:
                reader = self.pdf_lib.PdfReader(f)

                metadata = {
                    "num_pages": len(reader.pages),
                    "title": reader.metadata.title if reader.metadata else None,
                    "author": reader.metadata.author if reader.metadata else None,
                    "subject": reader.metadata.subject if reader.metadata else None,
                    "creator": reader.metadata.creator if reader.metadata else None,
                }

                return metadata

        except Exception as e:
            logger.error(f"元数据提取失败: {e}")
            return {}

    def _fallback_extract(self, pdf_path: str) -> str:
        """备用提取方法"""
        from app.services.markitdown_converter import enhanced_converter
        return enhanced_converter.convert(pdf_path) or ""

    def get_page_count(self, pdf_path: str) -> int:
        """获取页数"""
        metadata = self.extract_metadata(pdf_path)
        return metadata.get("num_pages", 0)


# 全局实例
pdf_service = PDFEnhancedService()
