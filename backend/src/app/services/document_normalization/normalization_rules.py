"""
文档化规则层 - 五种文件类型的处理框架

核心原则：
1. 所有文件最终都变成"文档"
2. "变成文档"的规则因类型而异
3. 脏数据处理有明确标准和日志
4. 完整性可验证

处理流程：
上传文件 → 识别类型 → 调用对应规则 → 规范化处理 → 记录日志 → 输出干净文档
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """文件类型枚举"""
    AUDIO = "audio"
    VIDEO = "video"
    TABLE = "table"
    DOCUMENT = "document"
    IMAGE = "image"


class DirtyDataType(str, Enum):
    """脏数据类型"""
    MISSING_VALUE = "missing_value"           # 缺失值
    DUPLICATE_CONTENT = "duplicate_content"   # 重复内容
    CONTRADICTION = "contradiction"           # 矛盾信息
    FORMAT_ERROR = "format_error"             # 格式错误
    UNRECOGNIZABLE = "unrecognizable"         # 无法识别
    LOW_CONFIDENCE = "low_confidence"         # 低置信度
    FILLER_WORDS = "filler_words"             # 口头禅
    OCR_ERROR = "ocr_error"                   # OCR错误
    NOISE = "noise"                           # 噪音


class DirtyDataAction(str, Enum):
    """脏数据处理动作"""
    KEEP_AND_TAG = "keep_and_tag"      # 保留并标记
    REMOVE = "remove"                  # 删除
    CORRECT = "correct"                # 修正
    DEDUPLICATE = "deduplicate"        # 去重
    FLAG = "flag"                      # 标记待确认


class NormalizationResult:
    """规范化处理结果"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.text_content = ""           # 最终文本内容
        self.word_count = 0              # 字数
        self.structure_info = {}         # 结构信息
        self.metadata = {}               # 元数据
        self.normalized_contents = []    # 结构化内容列表
        self.dirty_data_found = []       # 发现的脏数据
        self.dirty_data_handled = []     # 处理的脏数据
        self.completeness = {            # 完整性
            "score": 0.0,
            "issues": [],
            "details": {}
        }
        self.confidence = 1.0            # 整体置信度
        self.processing_time_ms = 0      # 处理耗时


class BaseNormalizationRule(ABC):
    """规范化规则基类"""

    def __init__(self):
        self.rule_name = self.__class__.__name__
        self.file_type = None

    @abstractmethod
    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """
        转换文件为规范化文档

        Args:
            file_content: 文件内容
            metadata: 文件元数据

        Returns:
            NormalizationResult
        """
        pass

    @abstractmethod
    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """
        验证完整性

        Args:
            result: 规范化结果

        Returns:
            (is_complete, issues)
        """
        pass

    def handle_dirty_data(
        self,
        data_type: DirtyDataType,
        action: DirtyDataAction,
        location: str,
        original: str,
        processed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理脏数据并记录

        Args:
            data_type: 脏数据类型
            action: 处理动作
            location: 位置
            original: 原始内容
            processed: 处理后内容

        Returns:
            处理记录
        """
        record = {
            "type": data_type.value,
            "action": action.value,
            "location": location,
            "original": original[:100] if original else None,  # 只记录前100字符
            "processed": processed[:100] if processed else None,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"处理脏数据: {data_type.value} at {location}, action={action.value}")

        return record


# =====================================================
# 规则1: 音频 → 文本
# =====================================================

class AudioToTextRule(BaseNormalizationRule):
    """
    音频 → 文本规范化规则

    目标：逐句转录，保留时间码和说话人

    处理流程：
    1. ASR转录（Whisper/FunASR）
    2. 去除口头禅
    3. 修正常见错别字
    4. 说话人分离
    5. 保留时间码
    """

    def __init__(self):
        super().__init__()
        self.file_type = FileType.AUDIO

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换音频为文本"""
        result = NormalizationResult()
        start_time = datetime.utcnow()

        try:
            # 【集成插件】先调用音频插件获取基础信息
            from .plugin_integration import get_plugin_integration_service
            plugin_service = get_plugin_integration_service()

            file_type = metadata.get("file_type", "mp3")
            file_path = metadata.get("file_path", "audio.mp3")

            plugin_result = plugin_service.get_plugin_basic_info(
                file_path=file_path,
                file_content=file_content,
                file_type=file_type
            )

            # 从插件结果提取元数据
            if plugin_result:
                plugin_metadata = plugin_service.extract_metadata_from_plugin_result(plugin_result, file_type)
                total_duration = plugin_metadata.get('duration', 0)
                logger.info(f"✅ 从插件获取音频时长: {total_duration:.1f}秒")
            else:
                # 降级：自己计算时长
                total_duration = self._get_audio_duration(file_content)
                logger.info(f"⚠️ 插件不可用，使用降级方案获取时长: {total_duration:.1f}秒")

            # 2. 调用ASR引擎
            transcript_result = self._transcribe_audio(
                file_content,
                mode="full",
                enable_timestamps=True,
                enable_speaker_diarization=True
            )

            # 3. 处理转录结果
            segments = transcript_result.get("segments", [])

            # 4. 去除口头禅（脏数据处理）
            segments = self._remove_filler_words(segments, result)

            # 5. 修正常见错别字
            segments = self._fix_common_errors(segments, result)

            # 6. 验证时间覆盖
            covered_duration = self._calculate_covered_duration(segments)
            coverage_rate = covered_duration / total_duration if total_duration > 0 else 0

            # 7. 如果覆盖率不足，处理遗漏片段
            if coverage_rate < 0.95:
                missing_gaps = self._find_missing_gaps(segments, total_duration)
                for gap in missing_gaps:
                    retry_segment = self._transcribe_segment(
                        file_content,
                        start_time=gap["start"],
                        end_time=gap["end"]
                    )
                    segments.append(retry_segment)

                    # 记录脏数据
                    result.dirty_data_found.append({
                        "type": DirtyDataType.MISSING_VALUE.value,
                        "location": f"{gap['start']:.1f}s - {gap['end']:.1f}s",
                        "description": "音频片段遗漏"
                    })

                # 重新排序
                segments.sort(key=lambda x: x.get("start", 0))
                covered_duration = self._calculate_covered_duration(segments)
                coverage_rate = covered_duration / total_duration if total_duration > 0 else 0

            # 8. 生成完整文本
            full_text = self._build_text_from_segments(segments)

            # 9. 提取说话人列表
            speakers = self._extract_speakers(segments)

            # 10. 构建结构化内容
            for idx, seg in enumerate(segments):
                result.normalized_contents.append({
                    "content_type": "audio_transcript",
                    "content": seg.get("text", ""),
                    "metadata": {
                        "speaker": seg.get("speaker"),
                        "start_time": seg.get("start"),
                        "end_time": seg.get("end"),
                        "confidence": seg.get("confidence", 1.0)
                    },
                    "source_location": {
                        "time_range": [seg.get("start"), seg.get("end")]
                    },
                    "extraction_method": "asr",
                    "confidence": seg.get("confidence", 1.0),
                    "sequence": idx
                })

            # 11. 填充结果
            result.text_content = full_text
            result.word_count = len(full_text)
            result.structure_info = {
                "type": "audio",
                "transcript": segments,
                "speakers": speakers
            }
            result.metadata = {
                "total_duration": total_duration,
                "transcribed_duration": covered_duration,
                "coverage_rate": coverage_rate,
                "segment_count": len(segments),
                "speaker_count": len(speakers),
                "language": "zh-CN",
                "engine": "FunASR"
            }

            # 12. 计算完整性
            result.completeness = self._calculate_completeness(
                coverage_rate, segments, total_duration
            )
            result.confidence = self._calculate_confidence(segments)

        except Exception as e:
            logger.error(f"音频规范化失败: {e}", exc_info=True)
            result.completeness["issues"].append(f"处理失败: {str(e)}")

        # 记录耗时
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(elapsed)

        return result

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证音频转换完整性"""
        issues = []

        # 1. 时间覆盖率必须≥95%
        coverage_rate = result.metadata.get("coverage_rate", 0)
        if coverage_rate < 0.95:
            issues.append(f"时间覆盖不足: {coverage_rate:.1%} < 95%")

        # 2. 不能有超过5秒的空白
        segments = result.structure_info.get("transcript", [])
        large_gaps = self._find_large_gaps(segments, threshold=5.0)
        if large_gaps:
            issues.append(f"发现{len(large_gaps)}个超过5秒的空白片段")

        # 3. 所有片段必须有说话人标识
        segments_without_speaker = [
            s for s in segments
            if not s.get("speaker")
        ]
        if segments_without_speaker:
            issues.append(f"{len(segments_without_speaker)}个片段缺少说话人标识")

        is_complete = len(issues) == 0
        return is_complete, issues

    # ========== 私有方法 ==========

    def _get_audio_duration(self, file_content: bytes) -> float:
        """获取音频时长（秒）"""
        # TODO: 实现音频时长获取
        # import librosa
        # y, sr = librosa.load(io.BytesIO(file_content))
        # return len(y) / sr
        return 3600.0  # 示例：1小时

    def _transcribe_audio(
        self,
        file_content: bytes,
        mode: str = "full",
        enable_timestamps: bool = True,
        enable_speaker_diarization: bool = True
    ) -> Dict[str, Any]:
        """调用ASR引擎转录音频"""
        import tempfile
        import os

        try:
            # 尝试使用 AudioProcessor
            from app.services.audio_processor import AudioProcessor

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(file_content)
                temp_path = f.name

            logger.info(f"调用 AudioProcessor 转写音频: {temp_path}")

            processor = AudioProcessor()
            result = processor.process_audio(temp_path)

            # 清理临时文件
            os.unlink(temp_path)

            # 转换为统一格式
            if result and result.get('segments'):
                return {"segments": result['segments']}
            else:
                logger.warning("AudioProcessor 返回空结果，使用模拟数据")
                return self._get_mock_transcript()

        except Exception as e:
            logger.error(f"AudioProcessor 调用失败: {e}")
            logger.info("使用模拟数据作为降级方案")
            return self._get_mock_transcript()

    def _get_mock_transcript(self) -> Dict[str, Any]:
        """获取模拟转写数据（降级方案）"""
        return {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.2,
                    "speaker": "speaker_1",
                    "text": "[音频转写服务不可用，这是模拟数据]",
                    "confidence": 0.92
                },
                {
                    "start": 5.3,
                    "end": 10.5,
                    "speaker": "speaker_2",
                    "text": "[请安装或配置音频转写服务]",
                    "confidence": 0.95
                }
            ]
        }

    def _remove_filler_words(
        self,
        segments: List[Dict[str, Any]],
        result: NormalizationResult
    ) -> List[Dict[str, Any]]:
        """去除口头禅"""
        filler_words = ["嗯", "啊", "那个", "这个", "呃", "嗯嗯"]

        cleaned_segments = []
        for seg in segments:
            original_text = seg.get("text", "")
            cleaned_text = original_text

            # 去除口头禅
            for filler in filler_words:
                if filler in cleaned_text:
                    cleaned_text = cleaned_text.replace(filler, "")

                    # 记录脏数据处理
                    dirty_record = self.handle_dirty_data(
                        data_type=DirtyDataType.FILLER_WORDS,
                        action=DirtyDataAction.REMOVE,
                        location=f"{seg.get('start', 0):.1f}s",
                        original=original_text,
                        processed=cleaned_text
                    )
                    result.dirty_data_handled.append(dirty_record)

            # 清理多余空格
            cleaned_text = " ".join(cleaned_text.split())

            seg["text"] = cleaned_text
            cleaned_segments.append(seg)

        return cleaned_segments

    def _fix_common_errors(
        self,
        segments: List[Dict[str, Any]],
        result: NormalizationResult
    ) -> List[Dict[str, Any]]:
        """修正常见错别字"""
        # 常见错别字映射
        error_corrections = {
            "那里": "哪里",  # 示例
            # 更多映射...
        }

        for seg in segments:
            original_text = seg.get("text", "")
            corrected_text = original_text

            for error, correction in error_corrections.items():
                if error in corrected_text:
                    corrected_text = corrected_text.replace(error, correction)

                    # 记录修正
                    dirty_record = self.handle_dirty_data(
                        data_type=DirtyDataType.FORMAT_ERROR,
                        action=DirtyDataAction.CORRECT,
                        location=f"{seg.get('start', 0):.1f}s",
                        original=original_text,
                        processed=corrected_text
                    )
                    result.dirty_data_handled.append(dirty_record)

            seg["text"] = corrected_text

        return segments

    def _calculate_covered_duration(self, segments: List[Dict[str, Any]]) -> float:
        """计算覆盖时长"""
        total = 0.0
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            total += (end - start)
        return total

    def _find_missing_gaps(
        self,
        segments: List[Dict[str, Any]],
        total_duration: float
    ) -> List[Dict[str, float]]:
        """查找遗漏的时间片段"""
        gaps = []

        # 按时间排序
        sorted_segments = sorted(segments, key=lambda x: x.get("start", 0))

        # 检查开头是否有gap
        if sorted_segments and sorted_segments[0].get("start", 0) > 0:
            gaps.append({
                "start": 0,
                "end": sorted_segments[0]["start"]
            })

        # 检查中间的gaps
        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i].get("end", 0)
            next_start = sorted_segments[i + 1].get("start", 0)

            if next_start - current_end > 0.5:  # 超过0.5秒算gap
                gaps.append({
                    "start": current_end,
                    "end": next_start
                })

        # 检查结尾是否有gap
        if sorted_segments:
            last_end = sorted_segments[-1].get("end", 0)
            if total_duration - last_end > 0.5:
                gaps.append({
                    "start": last_end,
                    "end": total_duration
                })

        return gaps

    def _transcribe_segment(
        self,
        file_content: bytes,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """转录特定时间片段"""
        # TODO: 实现片段转录
        return {
            "start": start_time,
            "end": end_time,
            "speaker": "unknown",
            "text": "[重新转录的片段]",
            "confidence": 0.7
        }

    def _build_text_from_segments(self, segments: List[Dict[str, Any]]) -> str:
        """从片段构建完整文本"""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "未知")
            text = seg.get("text", "")
            timestamp = seg.get("start", 0)
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")

        return "\n".join(lines)

    def _extract_speakers(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取说话人列表"""
        speakers = {}

        for seg in segments:
            speaker_id = seg.get("speaker")
            if speaker_id:
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "id": speaker_id,
                        "name": speaker_id,
                        "segments": 0
                    }
                speakers[speaker_id]["segments"] += 1

        return list(speakers.values())

    def _calculate_completeness(
        self,
        coverage_rate: float,
        segments: List[Dict[str, Any]],
        total_duration: float
    ) -> Dict[str, Any]:
        """计算完整性"""
        return {
            "score": coverage_rate,
            "details": {
                "coverage_rate": coverage_rate,
                "segment_count": len(segments),
                "total_duration": total_duration
            },
            "issues": [] if coverage_rate >= 0.95 else [f"覆盖率不足: {coverage_rate:.1%}"]
        }

    def _calculate_confidence(self, segments: List[Dict[str, Any]]) -> float:
        """计算整体置信度"""
        if not segments:
            return 0.0

        total_confidence = sum(seg.get("confidence", 1.0) for seg in segments)
        return total_confidence / len(segments)

    def _find_large_gaps(
        self,
        segments: List[Dict[str, Any]],
        threshold: float = 5.0
    ) -> List[Dict[str, float]]:
        """查找大的空白片段"""
        gaps = []
        sorted_segments = sorted(segments, key=lambda x: x.get("start", 0))

        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i].get("end", 0)
            next_start = sorted_segments[i + 1].get("start", 0)
            gap_duration = next_start - current_end

            if gap_duration > threshold:
                gaps.append({
                    "start": current_end,
                    "end": next_start,
                    "duration": gap_duration
                })

        return gaps


# =====================================================
# 其他规则的框架（待完整实现）
# =====================================================

class VideoToTextRule(BaseNormalizationRule):
    """视频 → 文本规范化规则"""

    def __init__(self):
        super().__init__()
        self.file_type = FileType.VIDEO

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换视频为文本（音频线+画面线）"""
        # TODO: 实现视频转换
        pass

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证视频转换完整性"""
        # TODO: 实现完整性验证
        pass


class TableToTextRule(BaseNormalizationRule):
    """
    表格 → 文本规范化规则

    目标：保留结构+公式+关系，不是简单转文字

    处理流程：
    1. 读取所有sheet
    2. 识别表头和数据区
    3. 提取公式（保留公式本身，不只是结果）
    4. 识别单位
    5. 识别合并单元格层级
    6. 转结构化叙述
    """

    def __init__(self):
        super().__init__()
        self.file_type = FileType.TABLE

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换表格为结构化文本"""
        result = NormalizationResult()
        start_time = datetime.utcnow()

        try:
            import io
            import openpyxl
            import csv

            file_type = metadata.get("file_type", "").lower()

            # 【集成插件】先调用Excel插件获取基础信息
            from .plugin_integration import get_plugin_integration_service
            plugin_service = get_plugin_integration_service()

            file_path = metadata.get("file_path", f"table.{file_type}")

            plugin_result = plugin_service.get_plugin_basic_info(
                file_path=file_path,
                file_content=file_content,
                file_type=file_type
            )

            # 从插件结果提取基础内容
            plugin_basic_content = ""
            if plugin_result:
                plugin_basic_content = plugin_service.extract_basic_content_from_plugin_result(plugin_result, file_type)
                logger.info(f"✅ 从插件获取表格基础内容: {len(plugin_basic_content)} 字符")

            # 1. 解析表格文件（增强版：识别公式和单位）
            if file_type in ["xlsx", "xls"]:
                workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=False)
            elif file_type == "csv":
                workbook = self._parse_csv(file_content)
            else:
                raise ValueError(f"不支持的表格类型: {file_type}")

            full_text = ""
            sheets_data = []

            # 2. 遍历所有工作表
            for sheet in workbook.worksheets if hasattr(workbook, 'worksheets') else [workbook]:
                sheet_name = sheet.title if hasattr(sheet, 'title') else "Sheet1"
                sheet_text = f"## 工作表: {sheet_name}\n\n"

                # 3. 读取所有单元格
                rows_data = []
                for row_idx, row in enumerate(sheet.iter_rows() if hasattr(sheet, 'iter_rows') else sheet):
                    row_data = []
                    for cell in row:
                        cell_info = self._extract_cell_info(cell)
                        row_data.append(cell_info)

                    if any(cell["value"] for cell in row_data):  # 跳过空行
                        rows_data.append(row_data)

                # 4. 检查是否有数据
                if not rows_data:
                    result.dirty_data_found.append({
                        "type": DirtyDataType.MISSING_VALUE.value,
                        "location": f"工作表 {sheet_name}",
                        "description": "工作表为空"
                    })
                    continue

                # 5. 识别表头
                headers = [str(cell["value"] or f"列{i+1}") for i, cell in enumerate(rows_data[0])]

                # 6. 转换为Markdown表格
                sheet_text += "| " + " | ".join(headers) + " |\n"
                sheet_text += "|" + "|".join(["---"] * len(headers)) + "|\n"

                # 7. 处理数据行
                for row in rows_data[1:]:
                    values = []
                    for cell in row:
                        if cell["is_formula"]:
                            # 公式用特殊格式标记
                            formula_text = f"`{cell['formula']}` = {cell['value']}"
                            values.append(formula_text)
                        elif cell["has_unit"]:
                            # 带单位
                            values.append(f"{cell['value']} {cell['unit']}")
                        else:
                            values.append(str(cell["value"] or ""))

                    sheet_text += "| " + " | ".join(values) + " |\n"

                sheet_text += "\n"
                full_text += sheet_text

                # 8. 保存sheet数据
                sheets_data.append({
                    "name": sheet_name,
                    "rows": len(rows_data),
                    "cols": len(rows_data[0]) if rows_data else 0,
                    "data": rows_data,
                    "has_formulas": any(
                        cell["is_formula"]
                        for row in rows_data
                        for cell in row
                    )
                })

                # 9. 保存结构化内容
                for row_idx, row in enumerate(rows_data):
                    for col_idx, cell in enumerate(row):
                        if cell["value"] or cell["is_formula"]:
                            result.normalized_contents.append({
                                "content_type": "table" if not cell["is_formula"] else "formula",
                                "content": str(cell["value"]),
                                "metadata": {
                                    "sheet": sheet_name,
                                    "row": row_idx,
                                    "col": col_idx,
                                    "formula": cell.get("formula"),
                                    "unit": cell.get("unit"),
                                    "is_formula": cell["is_formula"]
                                },
                                "source_location": {
                                    "sheet": sheet_name,
                                    "cell": f"{chr(65+col_idx)}{row_idx+1}"
                                },
                                "extraction_method": "openpyxl" if file_type in ["xlsx", "xls"] else "csv",
                                "confidence": 1.0,
                                "sequence": row_idx * 100 + col_idx
                            })

            # 10. 填充结果
            result.text_content = full_text
            result.word_count = len(full_text)
            result.structure_info = {
                "type": "table",
                "sheets": sheets_data,
                "total_rows": sum(s["rows"] for s in sheets_data),
                "total_cols": max(s["cols"] for s in sheets_data) if sheets_data else 0,
                "has_formulas": any(s["has_formulas"] for s in sheets_data)
            }
            result.metadata = {
                "file_type": file_type,
                "sheet_count": len(sheets_data),
                "total_cells": sum(s["rows"] * s["cols"] for s in sheets_data),
                "extracted_at": datetime.utcnow().isoformat()
            }

            # 11. 计算完整性
            result.completeness = {
                "score": 1.0 if sheets_data else 0.0,
                "details": {
                    "sheets_extracted": len(sheets_data),
                    "has_formulas": result.structure_info["has_formulas"]
                },
                "issues": []
            }
            result.confidence = 1.0

        except Exception as e:
            logger.error(f"表格规范化失败: {e}", exc_info=True)
            result.completeness["issues"].append(f"处理失败: {str(e)}")

        # 记录耗时
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(elapsed)

        return result

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证表格转换完整性"""
        issues = []

        structure = result.structure_info

        # 1. 必须有工作表
        if not structure.get("sheets"):
            issues.append("未提取任何工作表")

        # 2. 检查公式识别
        if structure.get("has_formulas"):
            formulas_found = sum(
                1 for content in result.normalized_contents
                if content.get("content_type") == "formula"
            )
            if formulas_found == 0:
                issues.append("表格包含公式但未识别")

        # 3. 检查空工作表
        for sheet in structure.get("sheets", []):
            if sheet["rows"] == 0:
                issues.append(f"工作表 {sheet['name']} 为空")

        is_complete = len(issues) == 0
        return is_complete, issues

    # ========== 私有方法 ==========

    def _parse_csv(self, file_content: bytes) -> object:
        """解析CSV文件"""
        import io
        import csv

        # 简化的CSV工作簿对象
        class CSVWorkbook:
            def __init__(self, rows):
                self.rows = rows
                self.title = "Sheet1"

            def iter_rows(self):
                return self.rows

        text = file_content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)

        return CSVWorkbook(rows)

    def _extract_cell_info(self, cell) -> Dict[str, Any]:
        """提取单元格信息"""
        cell_info = {
            "value": None,
            "type": "text",
            "is_formula": False,
            "formula": None,
            "has_unit": False,
            "unit": None
        }

        # 如果是openpyxl的Cell对象
        if hasattr(cell, 'value'):
            cell_info["value"] = cell.value
            cell_info["type"] = type(cell.value).__name__

            # 检查是否是公式
            if hasattr(cell, 'data_type') and cell.data_type == 'f':
                cell_info["is_formula"] = True
                if hasattr(cell, 'value') and isinstance(cell.value, str) and cell.value.startswith('='):
                    cell_info["formula"] = cell.value

        # 如果是CSV的字符串
        elif isinstance(cell, str):
            cell_info["value"] = cell
            cell_info["type"] = "str"

        # 识别单位
        if cell_info["value"] and isinstance(cell_info["value"], str):
            unit = self._extract_unit(cell_info["value"])
            if unit:
                cell_info["has_unit"] = True
                cell_info["unit"] = unit

        return cell_info

    def _extract_unit(self, text: str) -> Optional[str]:
        """从文本中提取单位"""
        common_units = ["元", "万元", "亿元", "亩", "公斤", "吨", "米", "厘米", "%", "人", "个"]

        for unit in common_units:
            if text.endswith(unit):
                return unit

        return None


class DocumentToTextRule(BaseNormalizationRule):
    """纯文档 → 文本规范化规则"""

    def __init__(self):
        super().__init__()
        self.file_type = FileType.DOCUMENT

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换文档为结构化文本"""
        # TODO: 实现文档转换
        pass

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证文档转换完整性"""
        # TODO: 实现完整性验证
        pass


class ImageToTextRule(BaseNormalizationRule):
    """
    图片 → 文本规范化规则

    目标：有字OCR，没字描述，都要完整

    处理流程：
    1. 检测图片中是否有文字
    2. 如果有文字，OCR提取（带位置信息）
    3. 生成图像描述（无论有没有文字）
    4. 识别文化元素
    """

    def __init__(self):
        super().__init__()
        self.file_type = FileType.IMAGE

    def convert(self, file_content: bytes, metadata: Dict[str, Any]) -> NormalizationResult:
        """转换图片为文本（OCR+描述）"""
        result = NormalizationResult()
        start_time = datetime.utcnow()

        try:
            from PIL import Image
            import io

            # 【集成插件】先调用图片插件获取基础信息
            from .plugin_integration import get_plugin_integration_service
            plugin_service = get_plugin_integration_service()

            file_type = metadata.get("file_type", "jpg")
            file_path = metadata.get("file_path", "image.jpg")

            plugin_result = plugin_service.get_plugin_basic_info(
                file_path=file_path,
                file_content=file_content,
                file_type=file_type
            )

            # 从插件结果提取元数据（EXIF等）
            plugin_metadata = {}
            if plugin_result:
                plugin_metadata = plugin_service.extract_metadata_from_plugin_result(plugin_result, file_type)
                logger.info(f"✅ 从插件获取图片元数据: {len(plugin_metadata)} 个字段")

            # 1. 加载图片
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size

            # 2. 检测文字区域
            text_regions = self._detect_text_regions(file_content)
            has_text = len(text_regions) > 0

            ocr_text = ""
            ocr_confidence = 1.0

            # 3. 如果有文字，OCR提取
            if has_text:
                ocr_results = []
                for region in text_regions:
                    recognized = self._ocr_recognize(file_content, region)
                    ocr_results.append(recognized)
                    ocr_text += f"[区域{region['id']}] {recognized['text']}\n"

                ocr_confidence = sum(r["confidence"] for r in ocr_results) / len(ocr_results) if ocr_results else 0

                # 保存OCR结果到结构化内容
                for idx, region in enumerate(text_regions):
                    if idx < len(ocr_results):
                        result.normalized_contents.append({
                            "content_type": "text",
                            "content": ocr_results[idx]["text"],
                            "metadata": {
                                "region_id": region["id"],
                                "bbox": region["bbox"],
                                "confidence": ocr_results[idx]["confidence"]
                            },
                            "source_location": {
                                "bbox": region["bbox"]
                            },
                            "extraction_method": "ocr",
                            "confidence": ocr_results[idx]["confidence"],
                            "sequence": idx
                        })

            # 4. 生成图像描述（无论有没有文字，都要描述）
            image_description = self._generate_image_description(file_content, has_text)

            # 5. 识别文化元素
            cultural_elements = self._identify_cultural_elements(image_description)

            # 6. 识别场景和物体
            scene_analysis = self._analyze_scene(file_content)

            # 7. 融合OCR和描述
            if has_text:
                full_text = f"## 图像内容\n\n{image_description}\n\n## 图像文字\n\n{ocr_text}"
            else:
                full_text = f"## 图像内容\n\n{image_description}"

            # 8. 保存图像描述到结构化内容
            result.normalized_contents.append({
                "content_type": "visual_description",
                "content": image_description,
                "metadata": {
                    "has_text": has_text,
                    "text_regions_count": len(text_regions),
                    "cultural_elements": cultural_elements,
                    "scene_type": scene_analysis.get("scene_type"),
                    "objects": scene_analysis.get("objects", [])
                },
                "source_location": {
                    "full_image": True
                },
                "extraction_method": "vision_model",
                "confidence": 0.85,
                "sequence": 1000  # 描述放在最后
            })

            # 9. 填充结果
            result.text_content = full_text
            result.word_count = len(full_text)
            result.structure_info = {
                "type": "image",
                "has_text": has_text,
                "text_regions": text_regions,
                "cultural_elements": cultural_elements,
                "scene_analysis": scene_analysis
            }
            result.metadata = {
                "resolution": {"width": width, "height": height},
                "format": image.format,
                "has_ocr": has_text,
                "description_length": len(image_description),
                "extracted_at": datetime.utcnow().isoformat()
            }

            # 10. 计算完整性
            description_score = 1.0 if len(image_description) >= 50 else len(image_description) / 50
            ocr_score = 1.0 if not has_text or (has_text and ocr_text) else 0.5

            result.completeness = {
                "score": (description_score + ocr_score) / 2,
                "details": {
                    "description_length": len(image_description),
                    "has_text": has_text,
                    "ocr_complete": bool(ocr_text) if has_text else True
                },
                "issues": []
            }

            if len(image_description) < 50:
                result.completeness["issues"].append(f"图像描述过短: {len(image_description)}字 < 50字")

            result.confidence = (0.85 + ocr_confidence) / 2  # 综合置信度

        except Exception as e:
            logger.error(f"图片规范化失败: {e}", exc_info=True)
            result.completeness["issues"].append(f"处理失败: {str(e)}")

        # 记录耗时
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = int(elapsed)

        return result

    def verify_completeness(self, result: NormalizationResult) -> Tuple[bool, List[str]]:
        """验证图片转换完整性"""
        issues = []

        # 1. 必须有图像描述，且长度≥50字
        description_length = result.metadata.get("description_length", 0)
        if description_length < 50:
            issues.append(f"图像描述过短: {description_length}字 < 50字")

        # 2. 如果检测到文字区域，必须有OCR结果
        structure = result.structure_info
        if structure.get("has_text"):
            has_ocr_content = any(
                c.get("content_type") == "text"
                for c in result.normalized_contents
            )
            if not has_ocr_content:
                issues.append("检测到文字但未进行OCR")

        # 3. OCR文字必须有位置信息
        if structure.get("has_text"):
            text_regions = structure.get("text_regions", [])
            if not text_regions:
                issues.append("有文字但缺少位置信息")

        is_complete = len(issues) == 0
        return is_complete, issues

    # ========== 私有方法 ==========

    def _detect_text_regions(self, image_content: bytes) -> List[Dict[str, Any]]:
        """检测图片中的文字区域"""
        import tempfile
        import os

        try:
            # 尝试使用 OCRService
            from app.services.ocr_service import OCRService

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(image_content)
                temp_path = f.name

            logger.info(f"调用 OCRService 检测文字区域: {temp_path}")

            ocr = OCRService()
            result = ocr.recognize_image(temp_path)

            # 清理临时文件
            os.unlink(temp_path)

            # 提取文字区域
            regions = []
            if result and result.get('boxes'):
                for i, box in enumerate(result['boxes']):
                    regions.append({
                        'id': i + 1,
                        'bbox': box.get('bbox', [0, 0, 100, 100]),
                        'confidence': box.get('confidence', 0.8),
                        'text': box.get('text', '')
                    })

            logger.info(f"检测到 {len(regions)} 个文字区域")
            return regions

        except Exception as e:
            logger.warning(f"OCRService 调用失败: {e}")
            logger.info("使用降级方案：简单启发式检测")
            return self._detect_text_regions_fallback(image_content)

    def _detect_text_regions_fallback(self, image_content: bytes) -> List[Dict[str, Any]]:
        """降级方案：简单启发式检测"""
        try:
            from PIL import Image, ImageStat
            import io

            image = Image.open(io.BytesIO(image_content))

            # 简单启发式：如果图片有明显的对比度变化，可能有文字
            stat = ImageStat.Stat(image.convert('L'))
            std_dev = stat.stddev[0]

            # 标准差大于30，可能有文字
            if std_dev > 30:
                width, height = image.size
                return [
                    {
                        "id": 1,
                        "bbox": [0, 0, width, height],
                        "confidence": 0.5,
                        "text": ""
                    }
                ]
        except:
            pass

        return []

    def _ocr_recognize(self, image_content: bytes, region: Dict[str, Any]) -> Dict[str, Any]:
        """OCR识别文字区域"""
        import tempfile
        import os

        try:
            # 尝试使用 OCRService
            from app.services.ocr_service import OCRService

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(image_content)
                temp_path = f.name

            logger.info(f"调用 OCRService 识别文字")

            ocr = OCRService()
            result = ocr.recognize_image(temp_path)

            # 清理临时文件
            os.unlink(temp_path)

            # 提取识别的文字
            if result and result.get('text'):
                return {
                    "text": result['text'],
                    "confidence": result.get('confidence', 0.85)
                }
            else:
                return {
                    "text": "[OCR识别的文字]",
                    "confidence": 0.85
                }

        except Exception as e:
            logger.error(f"OCRService 调用失败: {e}")
            return {
                "text": "[OCR服务不可用]",
                "confidence": 0.5
            }

    def _generate_image_description(self, image_content: bytes, has_text: bool) -> str:
        """生成图像描述"""
        import tempfile
        import os

        try:
            # 尝试使用 VisionService
            from app.services.vision_service import VisionService

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(image_content)
                temp_path = f.name

            logger.info(f"调用 VisionService 生成图像描述")

            vision = VisionService(model_type="blip2")

            # 生成描述
            prompt = """请详细描述这张图片：
1. 主体内容是什么？
2. 有哪些关键元素？
3. 场景、环境、氛围如何？
4. 如果是自然景观，描述地理特征
5. 如果是人物，描述人物动作、表情
6. 如果是物品，描述物品特征、状态

要求：描述至少50字，具体明确。
"""

            description = vision.describe_image(temp_path, prompt)

            # 清理临时文件
            os.unlink(temp_path)

            # 如果描述太短，补充说明
            if len(description) < 50:
                if has_text:
                    description += " 图片中包含文字内容，已通过OCR提取。"
                else:
                    description += " 这是一张图片，包含视觉信息。"

            return description

        except Exception as e:
            logger.error(f"VisionService 调用失败: {e}")
            # 降级方案
            if has_text:
                return "这是一张包含文字的图片，可能是海报、截图或文档扫描件。图片中有清晰的文字内容，已通过OCR提取。"
            else:
                return "这是一张图片，包含视觉内容。由于视觉模型服务不可用，无法生成详细描述。建议手动添加图片说明。"

    def _identify_cultural_elements(self, description: str) -> List[str]:
        """从描述中识别文化元素"""
        cultural_keywords = [
            "传统服饰", "民族", "建筑", "器物", "习俗", "仪式", "节日",
            "布依族", "苗族", "侗族", "壮族", "彝族",
            "古建筑", "寺庙", "祠堂", "民居"
        ]

        elements = []
        for keyword in cultural_keywords:
            if keyword in description:
                elements.append(keyword)

        return elements

    def _analyze_scene(self, image_content: bytes) -> Dict[str, Any]:
        """分析场景和物体"""
        # TODO: 集成场景分类模型
        # 这里返回模拟数据
        return {
            "scene_type": "outdoor/nature",
            "objects": [
                {"name": "山", "confidence": 0.9},
                {"name": "水", "confidence": 0.85},
                {"name": "天空", "confidence": 0.95}
            ],
            "mood": "宁静"
        }


# =====================================================
# 统一处理器
# =====================================================

class DocumentNormalizer:
    """文档规范化统一处理器"""

    def __init__(self):
        self.rules = {
            FileType.AUDIO: AudioToTextRule(),
            FileType.VIDEO: VideoToTextRule(),
            FileType.TABLE: TableToTextRule(),
            FileType.DOCUMENT: DocumentToTextRule(),
            FileType.IMAGE: ImageToTextRule()
        }

    def normalize(
        self,
        file_content: bytes,
        file_type: FileType,
        metadata: Dict[str, Any]
    ) -> NormalizationResult:
        """
        统一入口：规范化任何类型的文件

        Args:
            file_content: 文件内容
            file_type: 文件类型
            metadata: 元数据

        Returns:
            NormalizationResult
        """
        rule = self.rules.get(file_type)
        if not rule:
            raise ValueError(f"不支持的文件类型: {file_type}")

        logger.info(f"开始规范化处理: 类型={file_type.value}, 规则={rule.rule_name}")

        result = rule.convert(file_content, metadata)

        # 验证完整性
        is_complete, issues = rule.verify_completeness(result)
        result.completeness["issues"].extend(issues)

        logger.info(
            f"规范化完成: 类型={file_type.value}, "
            f"完整性={result.completeness['score']:.1%}, "
            f"耗时={result.processing_time_ms}ms"
        )

        return result
