"""
文本采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class TextPlugin(IngestionPlugin):
    """纯文本采集插件"""

    @property
    def plugin_name(self) -> str:
        return "TextPlugin"

    @property
    def supported_formats(self) -> list:
        return ["txt"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集文本文件"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            text = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                raise ValueError("无法识别文件编码")

            # 统计
            structured_metadata = {
                "encoding": used_encoding,
                "total_words": len(text.replace(" ", "")),
                "total_sentences": text.count('。') + text.count('.'),
                "total_paragraphs": len([p for p in text.split('\n') if p.strip()]),
                "language": self._detect_language(text)
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "text_read",
                "confidence": 1.0
            }

        except Exception as e:
            logger.error(f"文本采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"


class MarkdownPlugin(IngestionPlugin):
    """Markdown 采集插件"""

    @property
    def plugin_name(self) -> str:
        return "MarkdownPlugin"

    @property
    def supported_formats(self) -> list:
        return ["md", "markdown"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 Markdown 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()

            # 提取标题
            lines = markdown_text.split('\n')
            title = ""
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            # 转换为纯文本（移除 Markdown 标记）
            import re
            text = re.sub(r'```[\s\S]*?```', '', markdown_text)
            text = re.sub(r'`[^`]+`', '', text)
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
            text = re.sub(r'[#*_~]', '', text)

            structured_metadata = {
                "title": title,
                "total_words": len(text.replace(" ", "")),
                "total_sentences": text.count('。') + text.count('.'),
                "language": self._detect_language(text)
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "markdown_parse",
                "confidence": 0.95
            }

        except Exception as e:
            logger.error(f"Markdown 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
