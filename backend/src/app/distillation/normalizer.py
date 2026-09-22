"""
来源规范化器

负责将各种输入格式转换为统一的规范化文档结构
"""

import os
import uuid
import hashlib
import asyncio
from typing import Optional, List, Tuple
from pathlib import Path

from app.distillation.types import (
    SourceMetadata,
    NormalizedSource,
    NormalizedChapter,
    InputMode,
    SourceKind,
)


class SourceNormalizer:
    """生产者角色：来源规范化器"""

    def __init__(self):
        self.version = "fieldmind-normalizer-1.0.0"

    async def normalize(self, metadata: SourceMetadata) -> NormalizedSource:
        """
        规范化处理流程：
        1. 根据 input_mode 获取原始内容
        2. 格式转换（EPUB/PDF/DOCX → UTF-8 文本）
        3. 音频转写（调用 Whisper）
        4. 章节切分与排序
        5. 计算字节偏移量
        6. 质量检查（缺页/乱码/空段）
        7. 生成 SHA-256 基线
        """
        generation_id = f"gen-{uuid.uuid4()}"

        # 1. 获取原始内容
        if metadata.input_mode == InputMode.FILE:
            raw_content = await self._load_from_file(metadata)
        elif metadata.input_mode == InputMode.URL:
            raw_content = await self._load_from_url(metadata)
        elif metadata.input_mode == InputMode.AUDIO:
            raw_content = await self._transcribe_audio(metadata)
        else:
            raise ValueError(f"Unsupported input mode: {metadata.input_mode}")

        # 2. 格式转换
        text_content = await self._convert_to_text(raw_content, metadata)

        # 3. 章节切分
        chapters = await self._split_chapters(text_content, metadata)

        # 4. 计算字节偏移量
        chapters_with_offsets = self._compute_byte_offsets(chapters)

        # 5. 拼接全文
        full_text = "\n\n".join([ch.content for ch in chapters_with_offsets])

        # 6. 质量检查
        quality_flags = self._check_quality(full_text, chapters_with_offsets)

        # 7. 计算 SHA-256
        full_text_sha256 = self._compute_sha256(full_text)

        return NormalizedSource(
            generation_id=generation_id,
            source_metadata=metadata,
            chapters=chapters_with_offsets,
            full_text=full_text,
            full_text_sha256=full_text_sha256,
            has_missing_pages=quality_flags["has_missing_pages"],
            has_encoding_errors=quality_flags["has_encoding_errors"],
            has_ocr_uncertainty=quality_flags["has_ocr_uncertainty"],
            normalizer_version=self.version,
        )

    async def _load_from_file(self, metadata: SourceMetadata) -> bytes:
        """从文件加载内容"""
        if not metadata.file_path or not os.path.exists(metadata.file_path):
            raise FileNotFoundError(f"File not found: {metadata.file_path}")

        with open(metadata.file_path, "rb") as f:
            return f.read()

    async def _load_from_url(self, metadata: SourceMetadata) -> str:
        """从 URL 加载内容"""
        if not metadata.original_url:
            raise ValueError("original_url is required for URL mode")

        # 根据 source_kind 选择不同策略
        if metadata.source_kind == SourceKind.VIDEO:
            # 视频：提取字幕或转写音频
            return await self._extract_video_content(metadata.original_url)
        elif metadata.source_kind in [SourceKind.BLOG, SourceKind.DOCUMENT]:
            # 网页：使用 Jina Reader API
            return await self._extract_webpage_content(metadata.original_url)
        else:
            raise ValueError(f"Unsupported source_kind for URL: {metadata.source_kind}")

    async def _transcribe_audio(self, metadata: SourceMetadata) -> str:
        """转写音频"""
        if not metadata.file_path:
            raise ValueError("file_path is required for audio mode")

        # 调用 FieldMind 现有的 Whisper 集成
        from app.audio import AudioTranscriber

        transcriber = AudioTranscriber()
        result = await transcriber.transcribe(metadata.file_path)

        # 更新元数据
        metadata.transcription_performed = True
        metadata.transcription_model = result.get("model", "whisper-large-v3")

        return result["text"]

    async def _extract_video_content(self, url: str) -> str:
        """提取视频内容（字幕或转写）"""
        # TODO: 实现视频字幕提取
        # 1. 尝试下载官方字幕（bilibili/youtube API）
        # 2. 如果没有字幕，下载音频并转写
        raise NotImplementedError("Video extraction not yet implemented")

    async def _extract_webpage_content(self, url: str) -> str:
        """提取网页内容"""
        import aiohttp

        # 使用 Jina Reader API
        jina_url = f"https://r.jina.ai/{url}"

        async with aiohttp.ClientSession() as session:
            async with session.get(jina_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch URL: {response.status}")
                return await response.text()

    async def _convert_to_text(
        self, raw_content: bytes | str, metadata: SourceMetadata
    ) -> str:
        """格式转换为纯文本"""
        if isinstance(raw_content, str):
            return raw_content

        # 根据文件格式选择转换器
        file_format = metadata.file_format or self._detect_format(raw_content)

        if file_format == "txt":
            return raw_content.decode("utf-8")

        elif file_format == "pdf":
            return await self._convert_pdf(raw_content)

        elif file_format == "epub":
            return await self._convert_epub(raw_content)

        elif file_format == "docx":
            return await self._convert_docx(raw_content)

        elif file_format == "md":
            return raw_content.decode("utf-8")

        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _detect_format(self, content: bytes) -> str:
        """检测文件格式"""
        if content.startswith(b"%PDF"):
            return "pdf"
        elif content.startswith(b"PK\x03\x04"):
            # ZIP 格式（EPUB 或 DOCX）
            if b"mimetype" in content[:100]:
                return "epub"
            else:
                return "docx"
        else:
            # 尝试作为文本
            try:
                content.decode("utf-8")
                return "txt"
            except UnicodeDecodeError:
                raise ValueError("Unknown file format")

    async def _convert_pdf(self, content: bytes) -> str:
        """转换 PDF"""
        import io
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(content))
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        full_text = "\n\n".join(text_parts)

        # 检查是否需要 OCR
        if len(full_text.strip()) < 100:
            # 可能是扫描版 PDF
            raise ValueError(
                "PDF appears to be scanned. OCR required but not implemented yet."
            )

        return full_text

    async def _convert_epub(self, content: bytes) -> str:
        """转换 EPUB"""
        import io
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup

        book = epub.read_epub(io.BytesIO(content))
        text_parts = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text()
                if text.strip():
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    async def _convert_docx(self, content: bytes) -> str:
        """转换 DOCX"""
        import io
        from docx import Document

        doc = Document(io.BytesIO(content))
        text_parts = []

        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        return "\n\n".join(text_parts)

    async def _split_chapters(
        self, text: str, metadata: SourceMetadata
    ) -> List[NormalizedChapter]:
        """
        章节切分

        策略：
        1. 检测标题模式（第一章、Chapter 1、1.、等）
        2. 如果检测失败，按固定长度切分（每 10000 字）
        3. 为每个章节生成 ID 和计算 SHA-256
        """
        chapters = []

        # 尝试智能检测章节
        detected_chapters = self._detect_chapters(text)

        if detected_chapters:
            # 使用检测到的章节
            for i, (label, content) in enumerate(detected_chapters):
                chapter = NormalizedChapter(
                    chapter_id=f"ch-{i+1:03d}",
                    label=label,
                    order=i,
                    content=content,
                    sha256=self._compute_sha256(content),
                    byte_offset_start=0,  # 稍后计算
                    byte_offset_end=0,
                )
                chapters.append(chapter)
        else:
            # 回退：按固定长度切分
            chunk_size = 10000
            for i in range(0, len(text), chunk_size):
                chunk = text[i : i + chunk_size]
                chapter = NormalizedChapter(
                    chapter_id=f"ch-{i//chunk_size+1:03d}",
                    label=f"第 {i//chunk_size+1} 部分",
                    order=i // chunk_size,
                    content=chunk,
                    sha256=self._compute_sha256(chunk),
                    byte_offset_start=0,
                    byte_offset_end=0,
                )
                chapters.append(chapter)

        return chapters

    def _detect_chapters(self, text: str) -> Optional[List[Tuple[str, str]]]:
        """检测章节边界"""
        import re

        # 常见章节标题模式
        patterns = [
            r"^第[一二三四五六七八九十百千\d]+章[：:\s].*$",
            r"^Chapter\s+\d+[：:\s].*$",
            r"^\d+\.\s+.*$",
            r"^[一二三四五六七八九十]+、.*$",
        ]

        lines = text.split("\n")
        chapter_indices = []

        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in patterns:
                if re.match(pattern, line, re.MULTILINE):
                    chapter_indices.append((i, line))
                    break

        if len(chapter_indices) < 2:
            # 检测失败
            return None

        # 提取章节内容
        chapters = []
        for i in range(len(chapter_indices)):
            start_idx, label = chapter_indices[i]
            end_idx = (
                chapter_indices[i + 1][0] if i + 1 < len(chapter_indices) else len(lines)
            )

            content_lines = lines[start_idx + 1 : end_idx]
            content = "\n".join(content_lines).strip()

            if content:
                chapters.append((label, content))

        return chapters if chapters else None

    def _compute_byte_offsets(
        self, chapters: List[NormalizedChapter]
    ) -> List[NormalizedChapter]:
        """计算字节偏移量"""
        offset = 0

        for chapter in chapters:
            content_bytes = chapter.content.encode("utf-8")
            chapter.byte_offset_start = offset
            chapter.byte_offset_end = offset + len(content_bytes)
            offset = chapter.byte_offset_end + 2  # +2 for "\n\n"

        return chapters

    def _check_quality(
        self, full_text: str, chapters: List[NormalizedChapter]
    ) -> dict:
        """质量检查"""
        flags = {
            "has_missing_pages": False,
            "has_encoding_errors": False,
            "has_ocr_uncertainty": False,
        }

        # 检查乱码字符
        if "�" in full_text or "�" in full_text:
            flags["has_encoding_errors"] = True

        # 检查空章节
        empty_chapters = sum(1 for ch in chapters if len(ch.content.strip()) < 50)
        if empty_chapters > len(chapters) * 0.1:
            flags["has_missing_pages"] = True

        # 检查 OCR 常见错误字符
        ocr_indicators = ["Ⅰ", "Ⅱ", "╳", "□", "■"]
        if any(indicator in full_text for indicator in ocr_indicators):
            flags["has_ocr_uncertainty"] = True

        return flags

    def _compute_sha256(self, text: str) -> str:
        """计算 SHA-256"""
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        return f"sha256:{hash_obj.hexdigest()}"
