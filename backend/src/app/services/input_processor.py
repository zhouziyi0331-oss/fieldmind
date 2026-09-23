"""
多格式输入处理服务

支持格式：
- PDF
- DOCX
- TXT
- MD
- EPUB
- 网页URL
- 视频URL (字幕提取)
"""
from typing import Dict, Any, Optional, List
import hashlib
import logging
from pathlib import Path
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class InputProcessor:
    """
    多格式输入处理器

    功能：
    1. 文件格式检测和验证
    2. 文本提取和规范化
    3. 元信息提取
    4. 章节识别
    """

    SUPPORTED_FORMATS = {
        "pdf": [".pdf"],
        "docx": [".docx", ".doc"],
        "text": [".txt", ".md", ".markdown"],
        "ebook": [".epub", ".mobi"],
        "url": ["http://", "https://"]
    }

    def __init__(self):
        self.normalized_text = ""
        self.metadata = {}
        self.chapters = []

    def process(self, input_source: str, source_type: Optional[str] = None) -> Dict[str, Any]:
        """
        处理输入源

        参数:
            input_source: 文件路径或URL
            source_type: 可选，指定类型

        返回:
            处理结果
        """
        logger.info(f"开始处理输入: {input_source}")

        # 1. 检测输入类型
        if not source_type:
            source_type = self._detect_type(input_source)

        # 2. 根据类型处理
        if source_type == "pdf":
            result = self._process_pdf(input_source)
        elif source_type == "docx":
            result = self._process_docx(input_source)
        elif source_type == "text":
            result = self._process_text(input_source)
        elif source_type == "epub":
            result = self._process_epub(input_source)
        elif source_type == "url":
            result = self._process_url(input_source)
        elif source_type == "video_url":
            result = self._process_video_url(input_source)
        else:
            raise ValueError(f"不支持的输入类型: {source_type}")

        # 3. 规范化文本
        self.normalized_text = self._normalize_text(result["raw_text"])

        # 4. 提取元信息
        self.metadata = self._extract_metadata(result)

        # 5. 识别章节
        self.chapters = self._detect_chapters(self.normalized_text)

        # 6. 计算SHA-256
        text_hash = hashlib.sha256(self.normalized_text.encode()).hexdigest()

        return {
            "success": True,
            "source_type": source_type,
            "normalized_text": self.normalized_text,
            "text_hash": text_hash,
            "metadata": self.metadata,
            "chapters": self.chapters,
            "text_length": len(self.normalized_text),
            "chapter_count": len(self.chapters)
        }

    def _detect_type(self, input_source: str) -> str:
        """检测输入类型"""
        # URL检测
        if input_source.startswith("http://") or input_source.startswith("https://"):
            # 检查是否是视频平台
            video_platforms = ["youtube.com", "youtu.be", "bilibili.com", "vimeo.com"]
            if any(platform in input_source for platform in video_platforms):
                return "video_url"
            return "url"

        # 文件扩展名检测
        path = Path(input_source)
        suffix = path.suffix.lower()

        for format_type, extensions in self.SUPPORTED_FORMATS.items():
            if suffix in extensions:
                return format_type

        return "text"  # 默认作为文本处理

    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """处理PDF文件"""
        try:
            import PyPDF2

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)

                text_parts = []
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    text_parts.append(text)

                raw_text = "\n\n".join(text_parts)

                # 提取PDF元信息
                info = reader.metadata
                metadata = {
                    "title": info.get("/Title", ""),
                    "author": info.get("/Author", ""),
                    "pages": num_pages,
                    "format": "PDF"
                }

                return {
                    "raw_text": raw_text,
                    "metadata": metadata
                }

        except ImportError:
            logger.warning("PyPDF2未安装，使用pdfplumber")
            return self._process_pdf_with_pdfplumber(file_path)
        except Exception as e:
            logger.error(f"PDF处理失败: {str(e)}")
            raise

    def _process_pdf_with_pdfplumber(self, file_path: str) -> Dict[str, Any]:
        """使用pdfplumber处理PDF"""
        try:
            import pdfplumber

            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                raw_text = "\n\n".join(text_parts)

                metadata = {
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "pages": len(pdf.pages),
                    "format": "PDF"
                }

                return {
                    "raw_text": raw_text,
                    "metadata": metadata
                }

        except Exception as e:
            logger.error(f"pdfplumber处理失败: {str(e)}")
            raise

    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """处理DOCX文件"""
        try:
            from docx import Document

            doc = Document(file_path)

            # 提取所有段落
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            raw_text = "\n\n".join(paragraphs)

            # 提取元信息
            core_properties = doc.core_properties
            metadata = {
                "title": core_properties.title or "",
                "author": core_properties.author or "",
                "format": "DOCX"
            }

            return {
                "raw_text": raw_text,
                "metadata": metadata
            }

        except ImportError:
            raise ImportError("请安装python-docx: pip install python-docx")
        except Exception as e:
            logger.error(f"DOCX处理失败: {str(e)}")
            raise

    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """处理纯文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            # 从文件名提取标题
            path = Path(file_path)
            title = path.stem

            metadata = {
                "title": title,
                "format": path.suffix.upper().lstrip(".")
            }

            return {
                "raw_text": raw_text,
                "metadata": metadata
            }

        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                raw_text = f.read()

            path = Path(file_path)
            metadata = {
                "title": path.stem,
                "format": path.suffix.upper().lstrip(".")
            }

            return {
                "raw_text": raw_text,
                "metadata": metadata
            }

    def _process_epub(self, file_path: str) -> Dict[str, Any]:
        """处理EPUB文件"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(file_path)

            # 提取文本
            text_parts = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    if text.strip():
                        text_parts.append(text)

            raw_text = "\n\n".join(text_parts)

            # 提取元信息
            metadata = {
                "title": book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "",
                "author": book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "",
                "format": "EPUB"
            }

            return {
                "raw_text": raw_text,
                "metadata": metadata
            }

        except ImportError:
            raise ImportError("请安装ebooklib和beautifulsoup4: pip install ebooklib beautifulsoup4")
        except Exception as e:
            logger.error(f"EPUB处理失败: {str(e)}")
            raise

    def _process_url(self, url: str) -> Dict[str, Any]:
        """处理网页URL"""
        try:
            from bs4 import BeautifulSoup

            # 获取网页内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()

            # 提取标题
            title = soup.title.string if soup.title else ""

            # 提取正文
            # 优先尝试article标签
            article = soup.find('article')
            if article:
                text = article.get_text()
            else:
                # 否则使用body
                text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            raw_text = '\n'.join(chunk for chunk in chunks if chunk)

            metadata = {
                "title": title.strip(),
                "url": url,
                "format": "网页",
                "fetched_at": datetime.utcnow().isoformat()
            }

            return {
                "raw_text": raw_text,
                "metadata": metadata
            }

        except ImportError:
            raise ImportError("请安装beautifulsoup4和requests: pip install beautifulsoup4 requests")
        except Exception as e:
            logger.error(f"网页处理失败: {str(e)}")
            raise

    def _process_video_url(self, url: str) -> Dict[str, Any]:
        """处理视频URL（提取字幕）"""
        logger.info(f"处理视频URL: {url}")

        # 这里需要集成字幕提取工具
        # 可以使用youtube-dl或yt-dlp提取字幕
        try:
            import yt_dlp

            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['zh-Hans', 'zh-CN', 'en'],
                'skip_download': True,
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                title = info.get('title', '')
                description = info.get('description', '')

                # 提取字幕文本
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                subtitle_text = self._extract_subtitle_text(subtitles or automatic_captions)

                raw_text = f"{title}\n\n{description}\n\n{subtitle_text}"

                metadata = {
                    "title": title,
                    "url": url,
                    "format": "视频",
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', ''),
                    "upload_date": info.get('upload_date', ''),
                    "fetched_at": datetime.utcnow().isoformat()
                }

                return {
                    "raw_text": raw_text,
                    "metadata": metadata
                }

        except ImportError:
            raise ImportError("请安装yt-dlp: pip install yt-dlp")
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            raise

    def _extract_subtitle_text(self, subtitles: Dict[str, Any]) -> str:
        """从字幕数据中提取文本"""
        # 简化版实现
        # 实际需要下载和解析字幕文件
        return "字幕文本提取功能待实现"

    def _normalize_text(self, raw_text: str) -> str:
        """规范化文本"""
        # 1. 统一换行符
        text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. 移除多余空白
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)

        # 3. 合并过短的行（可能是分页导致的）
        normalized_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # 如果行很短且不是标题，尝试与下一行合并
            if len(line) < 50 and i + 1 < len(lines) and not self._is_heading(line):
                line = line + " " + lines[i + 1]
                i += 2
            else:
                i += 1
            normalized_lines.append(line)

        return '\n\n'.join(normalized_lines)

    def _is_heading(self, line: str) -> bool:
        """判断是否是标题"""
        # 简单启发式判断
        if len(line) < 5:
            return False

        # 章节标记
        heading_patterns = [
            "第", "章", "节", "部分",
            "Chapter", "Section", "Part",
            "#"
        ]

        return any(pattern in line for pattern in heading_patterns)

    def _extract_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """提取元信息"""
        metadata = result.get("metadata", {})

        # 确保必需字段存在
        metadata.setdefault("title", "未命名")
        metadata.setdefault("author", "未知")
        metadata.setdefault("format", "未知")

        return metadata

    def _detect_chapters(self, text: str) -> List[Dict[str, Any]]:
        """识别章节"""
        chapters = []

        lines = text.split('\n\n')
        current_chapter = None
        chapter_content = []

        for i, line in enumerate(lines):
            # 检测章节标题
            if self._is_chapter_heading(line):
                # 保存之前的章节
                if current_chapter:
                    chapters.append({
                        "title": current_chapter,
                        "content": '\n\n'.join(chapter_content),
                        "start_line": current_chapter_start
                    })

                # 开始新章节
                current_chapter = line
                current_chapter_start = i
                chapter_content = []
            else:
                # 添加到当前章节
                if current_chapter:
                    chapter_content.append(line)

        # 保存最后一个章节
        if current_chapter:
            chapters.append({
                "title": current_chapter,
                "content": '\n\n'.join(chapter_content),
                "start_line": current_chapter_start
            })

        return chapters

    def _is_chapter_heading(self, line: str) -> bool:
        """判断是否是章节标题"""
        # 中文章节标记
        chinese_patterns = [
            "第.*章", "第.*节", "第.*部分",
            "章节", "序言", "前言", "导言", "结语", "附录"
        ]

        # 英文章节标记
        english_patterns = [
            "Chapter", "Section", "Part",
            "Introduction", "Preface", "Conclusion", "Appendix"
        ]

        import re

        for pattern in chinese_patterns + english_patterns:
            if re.search(pattern, line):
                return True

        # Markdown标题
        if line.startswith("#"):
            return True

        return False
