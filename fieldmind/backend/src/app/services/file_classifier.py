"""
文件分类器
智能识别文件类型和内容
"""

import os
import mimetypes
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path

from app.models.document import DocumentType
from app.core.logging import logger


class FileClassifier:
    """文件分类器"""

    # 扩展名映射
    EXTENSION_MAP = {
        # 文档
        ".pdf": DocumentType.DOCUMENT,
        ".doc": DocumentType.DOCUMENT,
        ".docx": DocumentType.DOCUMENT,
        ".txt": DocumentType.DOCUMENT,
        ".md": DocumentType.DOCUMENT,
        ".rtf": DocumentType.DOCUMENT,
        ".odt": DocumentType.DOCUMENT,

        # 图片
        ".jpg": DocumentType.IMAGE,
        ".jpeg": DocumentType.IMAGE,
        ".png": DocumentType.IMAGE,
        ".gif": DocumentType.IMAGE,
        ".bmp": DocumentType.IMAGE,
        ".webp": DocumentType.IMAGE,
        ".svg": DocumentType.IMAGE,
        ".tiff": DocumentType.IMAGE,

        # 音频
        ".mp3": DocumentType.AUDIO,
        ".wav": DocumentType.AUDIO,
        ".m4a": DocumentType.AUDIO,
        ".flac": DocumentType.AUDIO,
        ".ogg": DocumentType.AUDIO,
        ".aac": DocumentType.AUDIO,
        ".wma": DocumentType.AUDIO,

        # 视频
        ".mp4": DocumentType.VIDEO,
        ".avi": DocumentType.VIDEO,
        ".mov": DocumentType.VIDEO,
        ".wmv": DocumentType.VIDEO,
        ".flv": DocumentType.VIDEO,
        ".mkv": DocumentType.VIDEO,
        ".webm": DocumentType.VIDEO,

        # 表格
        ".xls": DocumentType.TABLE,
        ".xlsx": DocumentType.TABLE,
        ".csv": DocumentType.TABLE,
        ".tsv": DocumentType.TABLE,
        ".ods": DocumentType.TABLE,
    }

    # MIME类型映射
    MIME_TYPE_MAP = {
        # 文档
        "application/pdf": DocumentType.DOCUMENT,
        "application/msword": DocumentType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCUMENT,
        "text/plain": DocumentType.DOCUMENT,
        "text/markdown": DocumentType.DOCUMENT,
        "application/rtf": DocumentType.DOCUMENT,

        # 图片
        "image/jpeg": DocumentType.IMAGE,
        "image/png": DocumentType.IMAGE,
        "image/gif": DocumentType.IMAGE,
        "image/bmp": DocumentType.IMAGE,
        "image/webp": DocumentType.IMAGE,
        "image/svg+xml": DocumentType.IMAGE,
        "image/tiff": DocumentType.IMAGE,

        # 音频
        "audio/mpeg": DocumentType.AUDIO,
        "audio/wav": DocumentType.AUDIO,
        "audio/mp4": DocumentType.AUDIO,
        "audio/x-m4a": DocumentType.AUDIO,
        "audio/flac": DocumentType.AUDIO,
        "audio/ogg": DocumentType.AUDIO,
        "audio/aac": DocumentType.AUDIO,

        # 视频
        "video/mp4": DocumentType.VIDEO,
        "video/x-msvideo": DocumentType.VIDEO,
        "video/quicktime": DocumentType.VIDEO,
        "video/x-ms-wmv": DocumentType.VIDEO,
        "video/x-flv": DocumentType.VIDEO,
        "video/x-matroska": DocumentType.VIDEO,
        "video/webm": DocumentType.VIDEO,

        # 表格
        "application/vnd.ms-excel": DocumentType.TABLE,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.TABLE,
        "text/csv": DocumentType.TABLE,
        "text/tab-separated-values": DocumentType.TABLE,
    }

    # 魔数识别（文件头特征）
    MAGIC_NUMBERS = {
        # PDF
        b"%PDF": DocumentType.DOCUMENT,

        # 图片
        b"\xff\xd8\xff": DocumentType.IMAGE,  # JPEG
        b"\x89PNG\r\n\x1a\n": DocumentType.IMAGE,  # PNG
        b"GIF87a": DocumentType.IMAGE,  # GIF87a
        b"GIF89a": DocumentType.IMAGE,  # GIF89a
        b"BM": DocumentType.IMAGE,  # BMP

        # 音频
        b"ID3": DocumentType.AUDIO,  # MP3
        b"RIFF": DocumentType.AUDIO,  # WAV
        b"\xff\xfb": DocumentType.AUDIO,  # MP3

        # 视频
        b"\x00\x00\x00\x18ftypmp4": DocumentType.VIDEO,  # MP4
        b"\x00\x00\x00\x14ftypisom": DocumentType.VIDEO,  # MP4
        b"RIFF": DocumentType.VIDEO,  # AVI (需要进一步检查)
    }

    @classmethod
    def classify(
        cls,
        filename: str,
        mime_type: Optional[str] = None,
        file: Optional[BinaryIO] = None
    ) -> Dict[str, Any]:
        """
        分类文件

        Args:
            filename: 文件名
            mime_type: MIME类型
            file: 文件对象（用于内容检测）

        Returns:
            Dict: 分类结果
                {
                    "type": DocumentType,
                    "confidence": float,
                    "method": str,
                    "details": dict
                }
        """
        results = []

        # 方法1: 扩展名检测
        ext_result = cls._classify_by_extension(filename)
        if ext_result:
            results.append(ext_result)

        # 方法2: MIME类型检测
        if mime_type:
            mime_result = cls._classify_by_mime_type(mime_type)
            if mime_result:
                results.append(mime_result)

        # 方法3: 文件内容检测（魔数）
        if file:
            magic_result = cls._classify_by_magic_number(file)
            if magic_result:
                results.append(magic_result)

        # 综合判断
        return cls._aggregate_results(results, filename)

    @classmethod
    def _classify_by_extension(cls, filename: str) -> Optional[Dict[str, Any]]:
        """
        通过扩展名分类

        Args:
            filename: 文件名

        Returns:
            Optional[Dict]: 分类结果
        """
        ext = Path(filename).suffix.lower()

        if ext in cls.EXTENSION_MAP:
            return {
                "type": cls.EXTENSION_MAP[ext],
                "confidence": 0.7,
                "method": "extension",
                "details": {"extension": ext}
            }

        return None

    @classmethod
    def _classify_by_mime_type(cls, mime_type: str) -> Optional[Dict[str, Any]]:
        """
        通过MIME类型分类

        Args:
            mime_type: MIME类型

        Returns:
            Optional[Dict]: 分类结果
        """
        if mime_type in cls.MIME_TYPE_MAP:
            return {
                "type": cls.MIME_TYPE_MAP[mime_type],
                "confidence": 0.9,
                "method": "mime_type",
                "details": {"mime_type": mime_type}
            }

        return None

    @classmethod
    def _classify_by_magic_number(cls, file: BinaryIO) -> Optional[Dict[str, Any]]:
        """
        通过魔数（文件头）分类

        Args:
            file: 文件对象

        Returns:
            Optional[Dict]: 分类结果
        """
        # 读取文件头（前32字节）
        file.seek(0)
        header = file.read(32)
        file.seek(0)

        # 检查魔数
        for magic, doc_type in cls.MAGIC_NUMBERS.items():
            if header.startswith(magic):
                return {
                    "type": doc_type,
                    "confidence": 0.95,
                    "method": "magic_number",
                    "details": {"magic": magic.hex()}
                }

        return None

    @classmethod
    def _aggregate_results(
        cls,
        results: list,
        filename: str
    ) -> Dict[str, Any]:
        """
        聚合分类结果

        Args:
            results: 各种方法的结果
            filename: 文件名

        Returns:
            Dict: 最终分类结果
        """
        if not results:
            # 无法识别，返回默认类型
            return {
                "type": DocumentType.OTHER,
                "confidence": 0.0,
                "method": "default",
                "details": {"filename": filename}
            }

        # 按置信度排序
        results.sort(key=lambda x: x["confidence"], reverse=True)

        # 检查结果一致性
        top_result = results[0]

        # 如果多个方法结果一致，提高置信度
        consistent_count = sum(
            1 for r in results if r["type"] == top_result["type"]
        )

        if consistent_count > 1:
            top_result["confidence"] = min(
                top_result["confidence"] + 0.1 * (consistent_count - 1),
                1.0
            )
            top_result["method"] = f"{top_result['method']}+{consistent_count-1}"

        logger.debug(
            f"文件分类: {filename} -> {top_result['type'].value}",
            confidence=top_result["confidence"],
            method=top_result["method"]
        )

        return top_result

    @classmethod
    def is_supported(cls, filename: str, mime_type: Optional[str] = None) -> bool:
        """
        检查文件是否支持

        Args:
            filename: 文件名
            mime_type: MIME类型

        Returns:
            bool: 是否支持
        """
        result = cls.classify(filename, mime_type)
        return result["type"] != DocumentType.OTHER

    @classmethod
    def get_mime_type(cls, filename: str) -> Optional[str]:
        """
        推测MIME类型

        Args:
            filename: 文件名

        Returns:
            Optional[str]: MIME类型
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type

    @classmethod
    def validate_file_type(
        cls,
        filename: str,
        mime_type: str,
        expected_type: Optional[DocumentType] = None
    ) -> bool:
        """
        验证文件类型

        Args:
            filename: 文件名
            mime_type: MIME类型
            expected_type: 期望的文档类型

        Returns:
            bool: 是否匹配
        """
        result = cls.classify(filename, mime_type)

        if expected_type:
            return result["type"] == expected_type

        return result["type"] != DocumentType.OTHER
