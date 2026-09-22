"""
HTML 采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class HTMLPlugin(IngestionPlugin):
    """HTML 网页采集插件"""

    @property
    def plugin_name(self) -> str:
        return "HTMLPlugin"

    @property
    def supported_formats(self) -> list:
        return ["html", "htm"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 HTML 文件"""
        try:
            from bs4 import BeautifulSoup

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # 提取元数据
            structured_metadata = {}

            # 标题
            title_tag = soup.find('title')
            if title_tag:
                structured_metadata["title"] = title_tag.get_text().strip()

            # meta 标签
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                structured_metadata["description"] = meta_description.get('content', '')

            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                structured_metadata["keywords"] = meta_keywords.get('content', '')

            # 移除script和style标签
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # 提取文本
            text = soup.get_text(separator='\n', strip=True)

            # 清理空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            full_text = '\n'.join(lines)

            # 统计
            structured_metadata["total_words"] = len(full_text.replace(" ", ""))
            structured_metadata["total_sentences"] = full_text.count('。') + full_text.count('.')
            structured_metadata["total_paragraphs"] = len(lines)
            structured_metadata["language"] = self._detect_language(full_text)

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "beautifulsoup4",
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"HTML 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"


class RTFPlugin(IngestionPlugin):
    """RTF 富文本采集插件"""

    @property
    def plugin_name(self) -> str:
        return "RTFPlugin"

    @property
    def supported_formats(self) -> list:
        return ["rtf"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 RTF 文件"""
        try:
            from striprtf.striprtf import rtf_to_text

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()

            # 转换为纯文本
            text = rtf_to_text(rtf_content)

            # 统计
            structured_metadata = {
                "format": "rtf",
                "total_words": len(text.replace(" ", "")),
                "total_sentences": text.count('。') + text.count('.'),
                "language": self._detect_language(text)
            }

            return {
                "raw_text": text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "striprtf",
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"RTF 采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
