"""
IngestionAgent（数据采集专员）- 第一阶段Agent
职责：负责所有类型文件的内容提取，输出统一的原始文本
整合18个后端服务插件进行多模态内容提取
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum
import mimetypes

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

    # 音频类
    AUDIO = "audio"  # mp3, wav, m4a, flac

    # 视频类
    VIDEO = "video"  # mp4, avi, mov

    # 图片类
    IMAGE = "image"  # png, jpg, jpeg

    # 未知类型
    UNKNOWN = "unknown"


class IngestionResult:
    """采集结果数据结构"""

    def __init__(
        self,
        file_path: str,
        file_type: FileType,
        raw_content: str,
        metadata: Dict[str, Any]
    ):
        self.file_path = file_path
        self.file_type = file_type
        self.raw_content = raw_content
        self.metadata = metadata
        self.timestamp = datetime.utcnow()

        # 量化指标
        self.metrics = self._calculate_metrics()

    def _calculate_metrics(self) -> Dict[str, Any]:
        """计算量化指标：时长、字数、文件类型、语言等硬指标"""
        metrics = {
            "file_type": self.file_type.value,
            "file_size_bytes": self.metadata.get("file_size", 0),
            "char_count": len(self.raw_content),
            "word_count": len(self.raw_content.split()),
            "line_count": self.raw_content.count('\n') + 1,
            "extracted_at": self.timestamp.isoformat(),
        }

        # 音频/视频特有指标
        if self.file_type in [FileType.AUDIO, FileType.VIDEO]:
            metrics["duration_seconds"] = self.metadata.get("duration", 0)
            metrics["duration_formatted"] = self._format_duration(
                self.metadata.get("duration", 0)
            )

        # 语言检测（如果有）
        if "language" in self.metadata:
            metrics["language"] = self.metadata["language"]
        elif "detected_language" in self.metadata:
            metrics["language"] = self.metadata["detected_language"]
        else:
            # 简单启发式判断
            metrics["language"] = self._detect_language_simple(self.raw_content)

        # OCR特有指标
        if "ocr_confidence" in self.metadata:
            metrics["ocr_confidence"] = self.metadata["ocr_confidence"]
            metrics["ocr_blocks_count"] = self.metadata.get("ocr_blocks", 0)

        return metrics

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    @staticmethod
    def _detect_language_simple(text: str) -> str:
        """简单的语言检测（启发式）"""
        if not text:
            return "unknown"

        # 统计中文字符
        chinese_chars = len([c for c in text if '一' <= c <= '鿿'])
        total_chars = len(text.strip())

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh"  # 中文
        else:
            return "en"  # 默认英文

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "raw_content": self.raw_content,
            "metadata": self.metadata,
            "metrics": self.metrics,
            "extracted_at": self.timestamp.isoformat()
        }


class IngestionAgent:
    """
    数据采集专员（Agent 1）

    职责边界：
    1. 负责所有类型文件的内容提取（不只是音频）
    2. 提取后输出统一的原始文本，不做分析
    3. 量化指标：时长、字数、文件类型、语言等硬指标

    整合的18个服务插件：
    - 文档转换服务 (7个): PDF, DOCX, TXT, Markdown, HTML, EPUB, Pandoc
    - 音频处理 (2个): Whisper转录, 音频元数据提取
    - 视频处理 (1个): 视频转录（提取音轨 + Whisper）
    - OCR服务 (2个): PaddleOCR, Tesseract
    - 数据质量 (2个): 文本清洗, 编码检测
    - 元数据提取 (4个): EXIF, 文件属性, MIME类型, 语言检测
    """

    def __init__(self):
        """初始化采集Agent，延迟加载所有服务"""
        self.services_loaded = False
        self._services = {}

        # 统计信息
        self.stats = {
            "total_processed": 0,
            "success_count": 0,
            "failed_count": 0,
            "by_file_type": {}
        }

    def _lazy_load_services(self):
        """延迟加载所有服务（避免启动时全部初始化）"""
        if self.services_loaded:
            return

        logger.info("🔧 IngestionAgent: 加载18个服务插件...")

        try:
            # === 文档转换服务 (7个) ===
            from app.services.pdf_converter import PDFConverter
            from app.services.docx_converter import DocxConverter
            from app.services.txt_converter import TxtConverter
            from app.services.markdown_converter import MarkdownConverter
            from app.services.html_converter import HtmlConverter
            from app.services.epub_converter import EpubConverter
            from app.services.pandoc_converter import PandocConverter

            self._services['pdf'] = PDFConverter()
            self._services['docx'] = DocxConverter()
            self._services['txt'] = TxtConverter()
            self._services['markdown'] = MarkdownConverter()
            self._services['html'] = HtmlConverter()
            self._services['epub'] = EpubConverter()
            self._services['pandoc'] = PandocConverter()

            # === 音频处理 (2个) ===
            from app.services.whisper_service import WhisperService
            from app.services.audio_metadata_service import AudioMetadataService

            self._services['whisper'] = WhisperService()
            self._services['audio_metadata'] = AudioMetadataService()

            # === 视频处理 (1个) ===
            from app.services.video_transcription_service import VideoTranscriptionService

            self._services['video'] = VideoTranscriptionService()

            # === OCR服务 (2个) ===
            from app.services.paddleocr_service import PaddleOCRService
            from app.services.tesseract_service import TesseractService

            self._services['paddleocr'] = PaddleOCRService()
            self._services['tesseract'] = TesseractService()

            # === 数据质量 (2个) ===
            from app.services.text_cleaner_service import TextCleanerService
            from app.services.encoding_detector_service import EncodingDetectorService

            self._services['text_cleaner'] = TextCleanerService()
            self._services['encoding_detector'] = EncodingDetectorService()

            # === 元数据提取 (4个) ===
            from app.services.exif_service import ExifService
            from app.services.file_metadata_service import FileMetadataService
            from app.services.mime_detector_service import MimeDetectorService
            from app.services.language_detector_service import LanguageDetectorService

            self._services['exif'] = ExifService()
            self._services['file_metadata'] = FileMetadataService()
            self._services['mime_detector'] = MimeDetectorService()
            self._services['language_detector'] = LanguageDetectorService()

            self.services_loaded = True
            logger.info("✅ IngestionAgent: 18个服务插件加载完成")

        except ImportError as e:
            logger.warning(f"⚠️  部分服务插件加载失败: {e}")
            logger.warning("将使用fallback实现")
            # 不阻断启动，使用fallback
            self.services_loaded = True

    def ingest_file(self, file_path: str) -> IngestionResult:
        """
        采集单个文件的内容

        Args:
            file_path: 文件路径

        Returns:
            IngestionResult: 采集结果（原始文本 + 元数据 + 量化指标）
        """
        self._lazy_load_services()

        logger.info(f"📥 IngestionAgent: 开始采集文件 {file_path}")

        try:
            # 1. 检测文件类型
            file_type = self._detect_file_type(file_path)
            logger.info(f"   文件类型: {file_type.value}")

            # 2. 根据文件类型选择合适的提取器
            raw_content, metadata = self._extract_by_type(file_path, file_type)

            # 3. 后处理：编码检测和文本清洗
            raw_content = self._post_process_text(raw_content)

            # 4. 提取通用元数据
            common_metadata = self._extract_common_metadata(file_path)
            metadata.update(common_metadata)

            # 5. 构建结果
            result = IngestionResult(
                file_path=file_path,
                file_type=file_type,
                raw_content=raw_content,
                metadata=metadata
            )

            # 6. 更新统计
            self._update_stats(file_type, success=True)

            logger.info(f"✅ 采集完成: {result.metrics['word_count']}词, {result.metrics['char_count']}字符")

            return result

        except Exception as e:
            logger.error(f"❌ 采集失败 {file_path}: {e}")
            self._update_stats(FileType.UNKNOWN, success=False)
            raise

    def _detect_file_type(self, file_path: str) -> FileType:
        """检测文件类型"""
        path = Path(file_path)
        ext = path.suffix.lower()

        # 文档类型映射
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

        # 音频类型
        audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}

        # 视频类型
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

        # 图片类型
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}

        if ext in doc_map:
            return doc_map[ext]
        elif ext in audio_exts:
            return FileType.AUDIO
        elif ext in video_exts:
            return FileType.VIDEO
        elif ext in image_exts:
            return FileType.IMAGE
        else:
            # 使用MIME类型检测
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('audio/'):
                    return FileType.AUDIO
                elif mime_type.startswith('video/'):
                    return FileType.VIDEO
                elif mime_type.startswith('image/'):
                    return FileType.IMAGE

            return FileType.UNKNOWN

    def _extract_by_type(
        self,
        file_path: str,
        file_type: FileType
    ) -> Tuple[str, Dict[str, Any]]:
        """
        根据文件类型调用相应的服务插件提取内容

        Returns:
            (原始文本, 元数据字典)
        """
        if file_type == FileType.PDF:
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
        elif file_type == FileType.AUDIO:
            return self._extract_audio(file_path)
        elif file_type == FileType.VIDEO:
            return self._extract_video(file_path)
        elif file_type == FileType.IMAGE:
            return self._extract_image_ocr(file_path)
        else:
            # 未知类型，尝试读取为文本
            return self._extract_as_text_fallback(file_path)

    # ==================== 文档转换服务 (7个) ====================

    def _extract_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用PDFConverter提取PDF内容"""
        if 'pdf' in self._services:
            result = self._services['pdf'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback: 使用PyPDF2
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text, {"pages": len(reader.pages)}

    def _extract_docx(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用DocxConverter提取DOCX内容"""
        if 'docx' in self._services:
            result = self._services['docx'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback: 使用python-docx
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text, {"paragraphs": len(doc.paragraphs)}

    def _extract_txt(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用TxtConverter提取TXT内容"""
        if 'txt' in self._services:
            result = self._services['txt'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback: 直接读取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text, {}

    def _extract_markdown(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用MarkdownConverter提取Markdown内容"""
        if 'markdown' in self._services:
            result = self._services['markdown'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text, {"format": "markdown"}

    def _extract_html(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用HtmlConverter提取HTML内容"""
        if 'html' in self._services:
            result = self._services['html'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback: 使用BeautifulSoup
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text, {"format": "html"}

    def _extract_epub(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用EpubConverter提取EPUB内容"""
        if 'epub' in self._services:
            result = self._services['epub'].convert(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback: 使用ebooklib
            import ebooklib
            from ebooklib import epub
            book = epub.read_epub(file_path)
            text = ""
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    text += item.get_content().decode('utf-8', errors='ignore')
            return text, {"format": "epub"}

    # ==================== 音频处理服务 (2个) ====================

    def _extract_audio(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用新的audio_transcript工具转录音频"""
        try:
            # 使用新的工具函数（从旧TranscriptAgent提取）
            from app.tools.transcript import transcribe_audio

            result = transcribe_audio(
                file_path=file_path,
                file_type='audio',
                language='auto',
                enable_metrics=True,
                enable_cleaning=True
            )

            # 提取文本和元数据
            text = result['transcript']['full_text']
            metadata = {
                'raw_text': result['transcript']['raw_text'],
                'segments': result['transcript']['segments'],
                'language': result['transcript']['language'],
                'duration': result['total']['时长'],
                'word_count': result['total']['清洗后字数']
            }

            # 如果有metrics，添加到metadata
            if 'metrics' in result:
                metadata['metrics'] = result['metrics']

            return text, metadata

        except Exception as e:
            logger.warning(f"audio_transcript工具失败，尝试使用旧服务: {e}")

            # Fallback: 使用旧的WhisperService
            metadata = {}

            # 1. 提取音频元数据
            if 'audio_metadata' in self._services:
                metadata = self._services['audio_metadata'].extract(file_path)

            # 2. Whisper转录
            if 'whisper' in self._services:
                transcription = self._services['whisper'].transcribe(file_path)
                text = transcription.get('text', '')
                metadata.update({
                    'segments': transcription.get('segments', []),
                    'language': transcription.get('language', 'unknown')
                })
            else:
                # Final fallback
                text = "[音频文件，需要Whisper服务转录]"

            return text, metadata

    # ==================== 视频处理服务 (1个) ====================

    def _extract_video(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用VideoTranscriptionService转录视频"""
        if 'video' in self._services:
            result = self._services['video'].transcribe(file_path)
            return result['text'], result.get('metadata', {})
        else:
            # Fallback
            return "[视频文件，需要视频转录服务]", {}

    # ==================== OCR服务 (2个) ====================

    def _extract_image_ocr(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """使用PaddleOCR识别图片文字"""
        metadata = {}

        # 优先使用PaddleOCR（中文效果好）
        if 'paddleocr' in self._services:
            result = self._services['paddleocr'].recognize(file_path)
            text = result.get('text', '')
            metadata = result.get('metadata', {})
        # Fallback: Tesseract
        elif 'tesseract' in self._services:
            result = self._services['tesseract'].recognize(file_path)
            text = result.get('text', '')
            metadata = result.get('metadata', {})
        else:
            text = "[图片文件，需要OCR服务识别]"

        # 提取EXIF元数据
        if 'exif' in self._services:
            exif_data = self._services['exif'].extract(file_path)
            metadata['exif'] = exif_data

        return text, metadata

    # ==================== 数据质量服务 (2个) ====================

    def _post_process_text(self, text: str) -> str:
        """后处理：编码检测和文本清洗"""
        if 'text_cleaner' in self._services:
            text = self._services['text_cleaner'].clean(text)
        return text

    # ==================== 元数据提取服务 (4个) ====================

    def _extract_common_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取通用文件元数据"""
        metadata = {}

        # 1. 文件基本属性
        if 'file_metadata' in self._services:
            metadata.update(self._services['file_metadata'].extract(file_path))
        else:
            # Fallback
            path = Path(file_path)
            stat = path.stat()
            metadata = {
                "file_name": path.name,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }

        # 2. MIME类型检测
        if 'mime_detector' in self._services:
            mime_info = self._services['mime_detector'].detect(file_path)
            metadata['mime_type'] = mime_info.get('mime_type')

        return metadata

    # ==================== Fallback ====================

    def _extract_as_text_fallback(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback: 尝试作为纯文本读取"""
        try:
            # 如果有编码检测服务，使用它
            encoding = 'utf-8'
            if 'encoding_detector' in self._services:
                encoding = self._services['encoding_detector'].detect(file_path)

            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                text = f.read()
            return text, {"encoding": encoding}
        except Exception as e:
            logger.error(f"Fallback读取失败: {e}")
            return "", {"error": str(e)}

    # ==================== 统计 ====================

    def _update_stats(self, file_type: FileType, success: bool):
        """更新统计信息"""
        self.stats['total_processed'] += 1
        if success:
            self.stats['success_count'] += 1
        else:
            self.stats['failed_count'] += 1

        # 按文件类型统计
        type_key = file_type.value
        if type_key not in self.stats['by_file_type']:
            self.stats['by_file_type'][type_key] = {
                'count': 0,
                'success': 0,
                'failed': 0
            }

        self.stats['by_file_type'][type_key]['count'] += 1
        if success:
            self.stats['by_file_type'][type_key]['success'] += 1
        else:
            self.stats['by_file_type'][type_key]['failed'] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "success_rate": (
                self.stats['success_count'] / self.stats['total_processed']
                if self.stats['total_processed'] > 0
                else 0
            )
        }

    def reset_statistics(self):
        """重置统计"""
        self.stats = {
            "total_processed": 0,
            "success_count": 0,
            "failed_count": 0,
            "by_file_type": {}
        }


# ==================== 全局单例 ====================

_ingestion_agent: Optional[IngestionAgent] = None


def get_ingestion_agent() -> IngestionAgent:
    """获取IngestionAgent单例"""
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent()
    return _ingestion_agent
