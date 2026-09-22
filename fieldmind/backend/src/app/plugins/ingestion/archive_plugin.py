"""
电子书和压缩包采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class EPUBPlugin(IngestionPlugin):
    """EPUB 电子书采集插件"""

    @property
    def plugin_name(self) -> str:
        return "EPUBPlugin"

    @property
    def supported_formats(self) -> list:
        return ["epub"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 EPUB 文件"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(file_path)

            # 提取元数据
            structured_metadata = {
                "title": book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "",
                "author": book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "",
                "language": book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else "",
                "publisher": book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else "",
            }

            # 提取文本
            text_content = []
            chapter_count = 0

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    chapter_count += 1
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    if text.strip():
                        text_content.append(f"\n=== 章节 {chapter_count} ===\n")
                        text_content.append(text)

            full_text = "\n".join(text_content)

            # 统计
            structured_metadata["chapters"] = chapter_count
            structured_metadata["total_words"] = len(full_text.replace(" ", ""))
            structured_metadata["total_sentences"] = full_text.count('。') + full_text.count('.')

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "document",
                "extraction_method": "ebooklib",
                "confidence": 0.9
            }

        except Exception as e:
            logger.error(f"EPUB 采集失败: {e}")
            raise


class ZIPPlugin(IngestionPlugin):
    """ZIP 压缩包采集插件"""

    @property
    def plugin_name(self) -> str:
        return "ZIPPlugin"

    @property
    def supported_formats(self) -> list:
        return ["zip"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集 ZIP 文件（提取文件列表和元数据）"""
        try:
            import zipfile
            from pathlib import Path

            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 获取文件列表
                file_list = zip_file.namelist()

                # 统计
                total_files = len(file_list)
                total_size = sum(info.file_size for info in zip_file.infolist())

                # 按类型分类
                file_types = {}
                for filename in file_list:
                    ext = Path(filename).suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1

                # 生成文本描述
                text_lines = [
                    f"压缩包内容清单",
                    f"总文件数: {total_files}",
                    f"总大小: {total_size / 1024 / 1024:.2f} MB",
                    f"\n文件类型分布:",
                ]

                for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                    text_lines.append(f"  {ext or '(无扩展名)'}: {count} 个")

                text_lines.append("\n文件列表:")
                for filename in file_list[:100]:  # 只列出前100个
                    text_lines.append(f"  - {filename}")

                if total_files > 100:
                    text_lines.append(f"  ... 还有 {total_files - 100} 个文件")

                full_text = "\n".join(text_lines)

                # 元数据
                structured_metadata = {
                    "format": "zip",
                    "total_files": total_files,
                    "total_size": total_size,
                    "file_types": file_types,
                    "language": "unknown"
                }

                return {
                    "raw_text": full_text,
                    "structured_metadata": structured_metadata,
                    "content_type": "archive",
                    "extraction_method": "zipfile",
                    "confidence": 1.0
                }

        except Exception as e:
            logger.error(f"ZIP 采集失败: {e}")
            raise
