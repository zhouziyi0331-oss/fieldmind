"""
Microsoft Markitdown 集成
支持更多文档格式的转换
"""

from markitdown import MarkItDown
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EnhancedDocumentConverter:
    """
    增强的文档转换器
    使用 Microsoft Markitdown 支持更多格式
    """

    def __init__(self):
        self.markitdown = MarkItDown()

    def convert(self, file_path: str, file_type: Optional[str] = None) -> Optional[str]:
        """
        转换文档为 Markdown 格式

        支持的格式:
        - PDF, Word, Excel, PowerPoint
        - 图片 (OCR)
        - 音频 (转写)
        - 视频 (提取字幕)
        - HTML, XML, JSON
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None

            # 使用 markitdown 转换
            result = self.markitdown.convert(file_path)

            if result and result.text_content:
                logger.info(
                    f"成功转换文档: {file_path} ({len(result.text_content)} 字符)"
                )
                return result.text_content
            else:
                logger.warning(f"文档转换为空: {file_path}")
                return None

        except Exception as e:
            logger.error(f"文档转换失败 {file_path}: {e}")
            return None

    def convert_with_metadata(self, file_path: str) -> dict:
        """
        转换文档并返回元数据

        Returns:
            {
                "content": str,
                "metadata": dict,
                "format": str
            }
        """
        try:
            result = self.markitdown.convert(file_path)

            return {
                "content": result.text_content if result else None,
                "metadata": {
                    "title": result.title if result else None,
                    "source": file_path,
                },
                "format": "markdown",
            }

        except Exception as e:
            logger.error(f"文档转换失败: {e}")
            return {
                "content": None,
                "metadata": {},
                "format": None,
                "error": str(e),
            }


# 全局实例
enhanced_converter = EnhancedDocumentConverter()
