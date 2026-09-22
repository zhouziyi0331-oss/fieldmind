"""
溯源追踪服务 - 句子级精确溯源
记录每段内容的准确出处：文件、页码、段落、句子、时间戳
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class SourceTracker:
    """溯源追踪器 - 句子级精确定位"""

    def __init__(self):
        self.name = "SourceTracker"

    def split_into_sentences(self, text: str, language: str = "zh") -> List[str]:
        """
        将文本分割为句子

        Args:
            text: 原始文本
            language: 'zh' (中文) | 'en' (英文)

        Returns:
            句子列表
        """
        if not text or len(text.strip()) == 0:
            return []

        if language == "zh":
            # 中文句子分割：按句号、问号、感叹号、分号
            sentences = re.split(r'[。！？；\n]+', text)
        else:
            # 英文句子分割：按. ? ! ;
            sentences = re.split(r'[.!?;]\s+', text)

        # 过滤空句子，保留非空白
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def create_document_sources(
        self,
        text: str,
        file_name: str,
        file_type: str,
        language: str = "zh",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        为文档内容创建句子级溯源

        Args:
            text: 文档内容
            file_name: 文件名
            file_type: 文件类型 (pdf, docx, etc.)
            language: 语言
            metadata: 额外元数据（如页码信息）

        Returns:
            [
                {
                    "sentence": "这是第一句话",
                    "sentence_index": 0,
                    "source": {
                        "file": "报告.pdf",
                        "file_type": "pdf",
                        "page": 1,
                        "paragraph": 1,
                        "sentence": 1
                    }
                },
                ...
            ]
        """
        sentences = self.split_into_sentences(text, language)

        sourced_sentences = []
        current_paragraph = 1

        # 检测段落分隔（连续两个换行）
        paragraphs = text.split('\n\n')

        sentence_counter = 0
        for para_idx, para in enumerate(paragraphs):
            if not para.strip():
                continue

            para_sentences = self.split_into_sentences(para, language)

            for sent_idx, sentence in enumerate(para_sentences):
                # 构建溯源信息
                source_info = {
                    "file": file_name,
                    "file_type": file_type,
                    "paragraph": para_idx + 1,
                    "sentence": sent_idx + 1
                }

                # 如果有页码信息（PDF等），尝试估算
                if metadata and "pages" in metadata:
                    # 简单估算：按字符数平均分配页码
                    estimated_page = min(
                        int((sentence_counter / len(sentences)) * metadata["pages"]) + 1,
                        metadata["pages"]
                    )
                    source_info["page"] = estimated_page

                sourced_sentences.append({
                    "sentence": sentence,
                    "sentence_index": sentence_counter,
                    "source": source_info
                })

                sentence_counter += 1

        logger.info(f"✅ 创建文档溯源: {len(sourced_sentences)} 个句子")
        return sourced_sentences

    def create_audio_sources(
        self,
        segments: List[Dict[str, Any]],
        file_name: str,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        为音频转录创建时间戳级溯源

        Args:
            segments: Whisper返回的详细片段
                [{"text": "...", "start": 0.0, "end": 5.2}, ...]
            file_name: 音频文件名
            chunks: 如果音频被切片，chunk信息

        Returns:
            [
                {
                    "sentence": "这是音频的一句话",
                    "sentence_index": 0,
                    "source": {
                        "file": "会议录音.mp3",
                        "file_type": "audio",
                        "timestamp": "00:00:00-00:00:05",
                        "start_time": 0.0,
                        "end_time": 5.2,
                        "chunk_index": 0  # 如果有切片
                    }
                },
                ...
            ]
        """
        sourced_sentences = []

        for idx, segment in enumerate(segments):
            text = segment.get("text", "").strip()
            if not text:
                continue

            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", 0.0)

            # 格式化时间戳
            timestamp = f"{self._format_time(start_time)}-{self._format_time(end_time)}"

            # 构建溯源信息
            source_info = {
                "file": file_name,
                "file_type": "audio",
                "timestamp": timestamp,
                "start_time": start_time,
                "end_time": end_time
            }

            # 如果有切片信息，添加chunk_index
            if chunks:
                # 找到属于哪个chunk
                for chunk in chunks:
                    if chunk["start_time"] <= start_time < chunk["end_time"]:
                        source_info["chunk_index"] = chunk.get("chunk_index", 0)
                        source_info["chunk_timestamp"] = chunk.get("timestamp", "")
                        break

            sourced_sentences.append({
                "sentence": text,
                "sentence_index": idx,
                "source": source_info
            })

        logger.info(f"✅ 创建音频溯源: {len(sourced_sentences)} 个片段")
        return sourced_sentences

    def create_table_sources(
        self,
        sheets: Dict[str, Any],
        file_name: str
    ) -> List[Dict[str, Any]]:
        """
        为表格内容创建单元格级溯源

        Args:
            sheets: Excel的sheets数据
            file_name: 文件名

        Returns:
            [
                {
                    "sentence": "A1单元格内容",
                    "sentence_index": 0,
                    "source": {
                        "file": "数据.xlsx",
                        "file_type": "excel",
                        "sheet": "Sheet1",
                        "cell": "A1",
                        "row": 1,
                        "col": 1,
                        "formula": "=SUM(A1:A10)"  # 如果有公式
                    }
                },
                ...
            ]
        """
        sourced_items = []
        item_index = 0

        for sheet_name, sheet_data in sheets.items():
            data = sheet_data.get("data", [])
            formulas = sheet_data.get("formulas", {})

            for row_idx, row in enumerate(data):
                for col_idx, cell_value in enumerate(row):
                    if cell_value is None or cell_value == "":
                        continue

                    # 单元格引用（A1格式）
                    from openpyxl.utils import get_column_letter
                    cell_ref = f"{get_column_letter(col_idx + 1)}{row_idx + 1}"

                    # 构建溯源信息
                    source_info = {
                        "file": file_name,
                        "file_type": "excel",
                        "sheet": sheet_name,
                        "cell": cell_ref,
                        "row": row_idx + 1,
                        "col": col_idx + 1
                    }

                    # 如果是公式单元格
                    if cell_ref in formulas:
                        source_info["formula"] = formulas[cell_ref]

                    sourced_items.append({
                        "sentence": str(cell_value),
                        "sentence_index": item_index,
                        "source": source_info
                    })

                    item_index += 1

        logger.info(f"✅ 创建表格溯源: {len(sourced_items)} 个单元格")
        return sourced_items

    def format_citation(self, source: Dict[str, Any]) -> str:
        """
        格式化引用文本（给用户看的引用格式）

        Args:
            source: 溯源信息

        Returns:
            格式化的引用字符串
            例如：
            - "来自 报告.pdf 第3页 第2段 第5句"
            - "来自 会议录音.mp3 00:15:30-00:16:45"
            - "来自 数据.xlsx Sheet1 单元格C5 (公式: =SUM(A1:A4))"
        """
        file_type = source.get("file_type", "unknown")
        file_name = source.get("file", "未知文件")

        if file_type == "audio" or file_type == "video":
            # 音频/视频：显示时间戳
            timestamp = source.get("timestamp", "")
            return f"来自 {file_name} {timestamp}"

        elif file_type == "excel" or file_type == "csv":
            # 表格：显示sheet和单元格
            sheet = source.get("sheet", "")
            cell = source.get("cell", "")
            formula = source.get("formula", "")

            citation = f"来自 {file_name}"
            if sheet:
                citation += f" {sheet}"
            if cell:
                citation += f" 单元格{cell}"
            if formula:
                citation += f" (公式: {formula})"

            return citation

        else:
            # 文档：显示页码、段落、句子
            parts = [f"来自 {file_name}"]

            if "page" in source:
                parts.append(f"第{source['page']}页")
            if "paragraph" in source:
                parts.append(f"第{source['paragraph']}段")
            if "sentence" in source:
                parts.append(f"第{source['sentence']}句")

            return " ".join(parts)

    def merge_sources(self, sources_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        合并多个溯源列表（例如多个文件的溯源）

        Args:
            sources_list: [file1_sources, file2_sources, ...]

        Returns:
            合并后的溯源列表，重新编号sentence_index
        """
        merged = []
        index = 0

        for sources in sources_list:
            for item in sources:
                merged.append({
                    **item,
                    "sentence_index": index
                })
                index += 1

        return merged

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间为 HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
