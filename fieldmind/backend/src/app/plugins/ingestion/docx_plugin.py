"""
DOCX 采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class DOCXPlugin(IngestionPlugin):
    """DOCX 文档采集插件"""

    @property
    def plugin_name(self) -> str:
        return "DOCXPlugin"

    @property
    def supported_formats(self) -> list:
        return ["docx", "doc"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 DOCX 文件"""
        try:
            import docx

            doc = docx.Document(file_path)

            # 提取元数据
            structured_metadata = {
                "title": doc.core_properties.title or "",
                "author": doc.core_properties.author or "",
                "subject": doc.core_properties.subject or "",
                "created": str(doc.core_properties.created) if doc.core_properties.created else "",
            }

            # 提取文本
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            # 提取表格内容
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        text_content.append(row_text)

            full_text = "\n".join(text_content)

            # 统计
            structured_metadata["total_words"] = len(full_text.replace(" ", ""))
            structured_metadata["total_sentences"] = full_text.count('。') + full_text.count('.')
            structured_metadata["total_paragraphs"] = len([p for p in doc.paragraphs if p.text.strip()])
            structured_metadata["language"] = self._detect_language(full_text)

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "python-docx",
                "confidence": 0.95
            }

        except Exception as e:
            logger.error(f"DOCX 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
