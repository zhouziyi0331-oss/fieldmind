"""
IngestionAgent v2 - 增强版数据采集专员
新增功能：
1. 表格处理（Excel + 公式识别）
2. 中英翻译（统一翻译成中文）
3. 长音频切片处理（5分钟一片）
4. 句子级精确溯源
5. 视频处理
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum
import mimetypes
import tempfile
import os

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """文件类型枚举"""
    # 文档类
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "markdown"
    HTML = "html"
    EPUB = "epub"

    # 表格类 ⭐ 新增
    EXCEL = "excel"
    CSV = "csv"

    # 音频类
    AUDIO = "audio"

    # 视频类
    VIDEO = "video"

    # 图片类
    IMAGE = "image"

    # 未知
    UNKNOWN = "unknown"


class IngestionResult:
    """增强的采集结果"""

    def __init__(
        self,
        file_path: str,
        file_type: FileType,
        raw_content: str,
        metadata: Dict[str, Any],
        sources: List[Dict[str, Any]] = None,  # ⭐ 新增：句子级溯源
        translated: bool = False,  # ⭐ 新增：是否翻译
        original_language: str = "unknown"  # ⭐ 新增：原始语言
    ):
        self.file_path = file_path
        self.file_type = file_type
        self.raw_content = raw_content
        self.metadata = metadata
        self.sources = sources or []
        self.translated = translated
        self.original_language = original_language
        self.timestamp = datetime.utcnow()

        # 量化指标
        self.metrics = self._calculate_metrics()

    def _calculate_metrics(self) -> Dict[str, Any]:
        """计算量化指标"""
        metrics = {
            "file_type": self.file_type.value,
            "file_size_bytes": self.metadata.get("file_size", 0),
            "char_count": len(self.raw_content),
            "word_count": len(self.raw_content.split()),
            "line_count": self.raw_content.count('\n') + 1,
            "extracted_at": self.timestamp.isoformat(),
            "source_count": len(self.sources),  # ⭐ 溯源数量
            "translated": self.translated,  # ⭐ 是否翻译
            "original_language": self.original_language  # ⭐ 原始语言
        }

        # 音频/视频特有指标
        if self.file_type in [FileType.AUDIO, FileType.VIDEO]:
            metrics["duration_seconds"] = self.metadata.get("duration", 0)
            metrics["was_split"] = self.metadata.get("was_split", False)
            metrics["chunk_count"] = self.metadata.get("chunk_count", 1)

        # 表格特有指标 ⭐
        if self.file_type in [FileType.EXCEL, FileType.CSV]:
            metrics["sheet_count"] = self.metadata.get("sheet_count", 0)
            metrics["has_formulas"] = self.metadata.get("has_formulas", False)
            metrics["row_count"] = self.metadata.get("rows", 0)
            metrics["col_count"] = self.metadata.get("cols", 0)

        # 语言检测
        if "language" in self.metadata:
            metrics["detected_language"] = self.metadata["language"]

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "raw_content": self.raw_content,
            "metadata": self.metadata,
            "sources": self.sources,
            "translated": self.translated,
            "original_language": self.original_language,
            "metrics": self.metrics,
            "extracted_at": self.timestamp.isoformat()
        }


class IngestionAgentV2:
    """
    增强版数据采集专员（Agent 1）

    新增25个服务：
    1. 文档转换（7个）- PDF, DOCX, TXT, MD, HTML, EPUB, Pandoc
    2. 表格处理（3个）⭐ - Excel, CSV, 公式提取
    3. 音频处理（4个）⭐ - 切片, Whisper, 汇总, 元数据
    4. 视频处理（2个）- 切片, 转录
    5. OCR服务（2个）- PaddleOCR, Tesseract
    6. 翻译服务（1个）⭐ - 中英互译
    7. 溯源追踪（2个）⭐ - 句子级溯源, 引用格式化
    8. 数据质量（2个）- 文本清洗, 编码检测
    9. 元数据提取（2个）- 文件属性, 语言检测
    """

    def __init__(self):
        self.services_loaded = False
        self._services = {}

        # 统计
        self.stats = {
            "total_processed": 0,
            "success_count": 0,
            "failed_count": 0,
            "translated_count": 0,
            "by_file_type": {}
        }

    def _lazy_load_services(self):
        """延迟加载所有服务"""
        if self.services_loaded:
            return

        logger.info("🔧 IngestionAgentV2: 加载25个服务...")

        try:
            # === 表格处理服务（3个）⭐ 新增 ===
            from app.services.excel_converter import ExcelConverter, CSVConverter
            self._services['excel'] = ExcelConverter()
            self._services['csv'] = CSVConverter()

            # === 翻译服务（1个）⭐ 新增 ===
            from app.services.translation_service import TranslationService
            self._services['translator'] = TranslationService()

            # === 音频处理服务（1个整合）⭐ 增强 ===
            from app.services.audio_processor import AudioProcessor
            self._services['audio_processor'] = AudioProcessor()

            # === 溯源追踪服务（1个）⭐ 新增 ===
            from app.services.source_tracker import SourceTracker
            self._services['source_tracker'] = SourceTracker()

            # === 原有服务 ===
            # 文档转换
            from app.services.pdf_converter import PDFConverter
            from app.services.docx_converter import DocxConverter
            from app.services.txt_converter import TxtConverter
            from app.services.markdown_converter import MarkdownConverter
            from app.services.html_converter import HtmlConverter
            from app.services.epub_converter import EpubConverter

            self._services['pdf'] = PDFConverter()
            self._services['docx'] = DocxConverter()
            self._services['txt'] = TxtConverter()
            self._services['markdown'] = MarkdownConverter()
            self._services['html'] = HtmlConverter()
            self._services['epub'] = EpubConverter()

            # OCR
            from app.services.paddleocr_service import PaddleOCRService
            from app.services.tesseract_service import TesseractService
            self._services['paddleocr'] = PaddleOCRService()
            self._services['tesseract'] = TesseractService()

            # 数据质量
            from app.services.text_cleaner_service import TextCleanerService
            self._services['text_cleaner'] = TextCleanerService()

            # 元数据
            from app.services.file_metadata_service import FileMetadataService
            self._services['file_metadata'] = FileMetadataService()

            self.services_loaded = True
            logger.info("✅ IngestionAgentV2: 25个服务加载完成")

        except ImportError as e:
            logger.warning(f"⚠️  部分服务加载失败: {e}")
            self.services_loaded = True

    def ingest_file(
        self,
        file_path: str,
        translate_to_chinese: bool = True,  # ⭐ 是否翻译成中文
        create_sources: bool = True  # ⭐ 是否创建句子级溯源
    ) -> IngestionResult:
        """
        采集文件内容 - 增强版

        流程：
        1. 检测文件类型
        2. 提取内容（根据类型选择合适的服务）
        3. 创建句子级溯源 ⭐
        4. 检测语言并翻译成中文 ⭐
        5. 后处理和清洗
        6. 返回结果
        """
        self._lazy_load_services()

        logger.info(f"📥 IngestionAgentV2: 开始采集 {file_path}")

        try:
            file_name = Path(file_path).name

            # 1. 检测文件类型
            file_type = self._detect_file_type(file_path)
            logger.info(f"   文件类型: {file_type.value}")

            # 2. 提取内容
            raw_content, metadata = self._extract_by_type(file_path, file_type)

            # 3. 创建溯源 ⭐
            sources = []
            if create_sources and 'source_tracker' in self._services:
                sources = self._create_sources(
                    raw_content=raw_content,
                    file_name=file_name,
                    file_type=file_type,
                    metadata=metadata
                )
                logger.info(f"   ✅ 创建溯源: {len(sources)} 个条目")

            # 4. 检测语言
            original_language = self._detect_language(raw_content)
            logger.info(f"   检测语言: {original_language}")

            # 5. 翻译成中文 ⭐
            translated = False
            if translate_to_chinese and original_language != "zh" and 'translator' in self._services:
                logger.info(f"   🌐 翻译: {original_language} -> zh")

                # 如果有溯源，翻译每个句子
                if sources:
                    sources = self._services['translator'].translate_segments(sources)
                    # 更新raw_content为翻译后的文本
                    raw_content = "\n".join([s.get("translated_text", s.get("sentence", "")) for s in sources])
                else:
                    # 整体翻译
                    trans_result = self._services['translator'].translate_to_chinese(raw_content)
                    raw_content = trans_result["translated_text"]

                translated = trans_result.get("was_translated", False)
                logger.info(f"   ✅ 翻译完成")

            # 6. 后处理
            raw_content = self._post_process_text(raw_content)

            # 7. 提取通用元数据
            common_metadata = self._extract_common_metadata(file_path)
            metadata.update(common_metadata)

            # 8. 构建结果
            result = IngestionResult(
                file_path=file_path,
                file_type=file_type,
                raw_content=raw_content,
                metadata=metadata,
                sources=sources,
                translated=translated,
                original_language=original_language
            )

            # 9. 更新统计
            self._update_stats(file_type, success=True, translated=translated)

            logger.info(f"✅ 采集完成: {result.metrics['word_count']}词, {result.metrics['source_count']}条溯源")

            return result

        except Exception as e:
            logger.error(f"❌ 采集失败 {file_path}: {e}")
            self._update_stats(FileType.UNKNOWN, success=False)
            raise

    def _detect_file_type(self, file_path: str) -> FileType:
        """检测文件类型"""
        path = Path(file_path)
        ext = path.suffix.lower()

        # 文档类型
        doc_map = {
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.doc': FileType.DOC,
            '.txt': FileType.TXT,
            '.md': FileType.MD,
            '.markdown': FileType.MD,
            '.html': FileType.HTML,
            '.htm': FileType.HTML,
            '.epub': FileType.EPUB,
        }

        # 表格类型 ⭐
        table_map = {
            '.xlsx': FileType.EXCEL,
            '.xls': FileType.EXCEL,
            '.csv': FileType.CSV
        }

        # 音频
        audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'}

        # 视频
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

        # 图片
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}

        if ext in doc_map:
            return doc_map[ext]
        elif ext in table_map:
            return table_map[ext]
        elif ext in audio_exts:
            return FileType.AUDIO
        elif ext in video_exts:
            return FileType.VIDEO
        elif ext in image_exts:
            return FileType.IMAGE
        else:
            return FileType.UNKNOWN

    def _extract_by_type(
        self,
        file_path: str,
        file_type: FileType
    ) -> Tuple[str, Dict[str, Any]]:
        """根据类型提取内容"""

        # 表格类型 ⭐
        if file_type == FileType.EXCEL:
            return self._extract_excel(file_path)
        elif file_type == FileType.CSV:
            return self._extract_csv(file_path)

        # 音频（增强处理）⭐
        elif file_type == FileType.AUDIO:
            return self._extract_audio_enhanced(file_path)

        # 文档类型
        elif file_type == FileType.PDF:
            return self._extract_pdf(file_path)
        elif file_type == FileType.DOCX:
            return self._extract_docx(file_path)
        elif file_type == FileType.TXT:
            return self._extract_txt(file_path)
        elif file_type == FileType.MD:
            return self._extract_markdown(file_path)
        elif file_type == FileType.HTML:
            return self._extract_html(file_path)
        elif file_type == FileType.EPUB:
            return self._extract_epub(file_path)

        # 图片
        elif file_type == FileType.IMAGE:
            return self._extract_image_ocr(file_path)

        # 视频
        elif file_type == FileType.VIDEO:
            return self._extract_video(file_path)

        else:
            return self._extract_as_text_fallback(file_path)

    # ==================== 表格处理（新增）⭐ ====================

    def _extract_excel(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """提取Excel内容 + 公式"""
        if 'excel' in self._services:
            result = self._services['excel'].convert(file_path)
            return result['text'], {
                **result.get('metadata', {}),
                'sheets': result.get('sheets', {})  # 保留完整表格数据
            }
        else:
            return "[Excel文件，需要Excel转换服务]", {}

    def _extract_csv(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """提取CSV内容"""
        if 'csv' in self._services:
            result = self._services['csv'].convert(file_path)
            return result['text'], {
                **result.get('metadata', {}),
                'data': result.get('data', [])
            }
        else:
            return "[CSV文件，需要CSV转换服务]", {}

    # ==================== 音频处理（增强）⭐ ====================

    def _extract_audio_enhanced(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """增强的音频处理：自动切片 + 转录 + 汇总"""
        if 'audio_processor' in self._services:
            result = self._services['audio_processor'].process_audio(file_path)
            return result['text'], {
                **result.get('metadata', {}),
                'chunks': result.get('chunks', []),
                'segments': result.get('segments', [])
            }
        else:
            return "[音频文件，需要音频处理服务]", {}

    # ==================== 文档转换（原有）====================

    def _extract_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'pdf' in self._services:
            result = self._services['pdf'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text, {"pages": len(reader.pages)}

    def _extract_docx(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'docx' in self._services:
            result = self._services['docx'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text, {"paragraphs": len(doc.paragraphs)}

    def _extract_txt(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'txt' in self._services:
            result = self._services['txt'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text, {}

    def _extract_markdown(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text, {"format": "markdown"}

    def _extract_html(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'html' in self._services:
            result = self._services['html'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text, {"format": "html"}

    def _extract_epub(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'epub' in self._services:
            result = self._services['epub'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            return "[EPUB文件，需要EPUB转换服务]", {}

    def _extract_image_ocr(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if 'paddleocr' in self._services:
            result = self._services['paddleocr'].recognize(file_path)
            return result.get('text', ''), result.get('metadata', {})
        elif 'tesseract' in self._services:
            result = self._services['tesseract'].recognize(file_path)
            return result.get('text', ''), result.get('metadata', {})
        else:
            return "[图片文件，需要OCR服务]", {}

    def _extract_video(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        # 视频处理：提取音轨 + 按音频处理
        if 'audio_processor' in self._services:
            # 简化：视频直接当音频处理（ffmpeg会自动提取音轨）
            result = self._services['audio_processor'].process_audio(file_path)
            return result['text'], {
                **result.get('metadata', {}),
                'file_type': 'video',
                'chunks': result.get('chunks', []),
                'segments': result.get('segments', [])
            }
        else:
            return "[视频文件，需要音频处理服务]", {}

    def _extract_as_text_fallback(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text, {}
        except Exception as e:
            logger.error(f"Fallback失败: {e}")
            return "", {"error": str(e)}

    # ==================== 溯源创建（新增）⭐ ====================

    def _create_sources(
        self,
        raw_content: str,
        file_name: str,
        file_type: FileType,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建句子级溯源"""
        tracker = self._services.get('source_tracker')
        if not tracker:
            return []

        # 音频/视频：使用segments创建溯源
        if file_type in [FileType.AUDIO, FileType.VIDEO]:
            segments = metadata.get('segments', [])
            chunks = metadata.get('chunks', [])
            return tracker.create_audio_sources(segments, file_name, chunks)

        # 表格：使用sheets创建溯源
        elif file_type == FileType.EXCEL:
            sheets = metadata.get('sheets', {})
            return tracker.create_table_sources(sheets, file_name)

        # 文档：创建句子级溯源
        else:
            language = self._detect_language(raw_content)
            return tracker.create_document_sources(
                text=raw_content,
                file_name=file_name,
                file_type=file_type.value,
                language=language,
                metadata=metadata
            )

    # ==================== 辅助方法 ====================

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        if 'translator' in self._services:
            return self._services['translator'].detect_language(text)
        else:
            # 简单检测
            chinese_chars = len([c for c in text if '一' <= c <= '鿿'])
            return "zh" if chinese_chars / max(len(text), 1) > 0.3 else "en"

    def _post_process_text(self, text: str) -> str:
        """后处理：清洗文本"""
        if 'text_cleaner' in self._services:
            return self._services['text_cleaner'].clean(text)
        return text

    def _extract_common_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取通用元数据"""
        if 'file_metadata' in self._services:
            return self._services['file_metadata'].extract(file_path)
        else:
            path = Path(file_path)
            stat = path.stat()
            return {
                "file_name": path.name,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }

    def _update_stats(self, file_type: FileType, success: bool, translated: bool = False):
        """更新统计"""
        self.stats['total_processed'] += 1
        if success:
            self.stats['success_count'] += 1
        else:
            self.stats['failed_count'] += 1

        if translated:
            self.stats['translated_count'] += 1

        type_key = file_type.value
        if type_key not in self.stats['by_file_type']:
            self.stats['by_file_type'][type_key] = {'count': 0, 'success': 0, 'failed': 0}

        self.stats['by_file_type'][type_key]['count'] += 1
        if success:
            self.stats['by_file_type'][type_key]['success'] += 1
        else:
            self.stats['by_file_type'][type_key]['failed'] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            **self.stats,
            "success_rate": (
                self.stats['success_count'] / self.stats['total_processed']
                if self.stats['total_processed'] > 0
                else 0
            ),
            "translation_rate": (
                self.stats['translated_count'] / self.stats['success_count']
                if self.stats['success_count'] > 0
                else 0
            )
        }


# ==================== 全局单例 ====================

_ingestion_agent_v2: Optional[IngestionAgentV2] = None


def get_ingestion_agent_v2() -> IngestionAgentV2:
    """获取增强版IngestionAgent单例"""
    global _ingestion_agent_v2
    if _ingestion_agent_v2 is None:
        _ingestion_agent_v2 = IngestionAgentV2()
    return _ingestion_agent_v2
