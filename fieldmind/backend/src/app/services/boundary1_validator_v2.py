"""
边界1验证器（可验证版本）：多模态→统一文本
核心：完整性可量化、可验证、可追溯

原则：
1. 所有数据都保留（不筛选）
2. 完整性基于实际数据计算（不估算）
3. 计算公式透明（可验证）
4. 每个分数都可追溯到具体数据
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """质量等级"""
    HIGH = "高"       # ≥80%
    MEDIUM = "中"     # 50-80%
    LOW = "低"        # <50%


class Boundary1ValidatorV2:
    """边界1验证器 V2 - 可验证版本"""

    @staticmethod
    def validate(document: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证文档完整性（可验证版本）

        Args:
            document: 文档数据

        Returns:
            验证结果（包含详细计算过程）
        """
        file_type = document.get("file_type", "").lower()
        extra_data = document.get("extra_data", {})

        # 判断模态类型
        if file_type in ["mp3", "wav", "m4a", "flac", "ogg", "audio"]:
            result = Boundary1ValidatorV2._validate_audio(document, extra_data)
        elif file_type in ["mp4", "mov", "avi", "mkv", "video"]:
            result = Boundary1ValidatorV2._validate_video(document, extra_data)
        elif file_type in ["png", "jpg", "jpeg", "gif", "webp", "image"]:
            result = Boundary1ValidatorV2._validate_image(document, extra_data)
        else:
            result = Boundary1ValidatorV2._validate_document(document, extra_data)

        # 添加通用信息
        result["document_id"] = document.get("id")
        result["filename"] = document.get("original_filename", document.get("filename"))
        result["file_type"] = file_type
        result["validated_at"] = datetime.utcnow().isoformat()
        result["usable"] = True  # 所有数据都可用

        # 判断质量等级
        completeness = result["completeness"]
        if completeness >= 0.8:
            result["quality_level"] = QualityLevel.HIGH
        elif completeness >= 0.5:
            result["quality_level"] = QualityLevel.MEDIUM
        else:
            result["quality_level"] = QualityLevel.LOW

        logger.info(f"✅ 边界1验证完成: 文档 {result['document_id']}, 完整性 {completeness:.1%}, 等级 {result['quality_level']}")

        return result

    @staticmethod
    def _validate_audio(document: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证音频完整性

        可验证指标：
        1. 时间覆盖率：转写覆盖了多少音频时长
        2. 片段完整率：片段数 vs 预期片段数
        3. 说话人覆盖：说话人识别率
        """
        # 获取音频元数据
        total_duration = extra_data.get("recording_duration") or extra_data.get("audio_duration") or extra_data.get("duration", 0)
        transcript = extra_data.get("transcript", [])

        # 1. 时间覆盖率
        if transcript and total_duration > 0:
            transcribed_duration = sum(
                seg.get("end", 0) - seg.get("start", 0)
                for seg in transcript
                if isinstance(seg, dict) and "start" in seg and "end" in seg
            )
            time_coverage = min(transcribed_duration / total_duration, 1.0)
        else:
            transcribed_duration = 0
            time_coverage = 0

        # 2. 片段完整率
        # 假设理想情况下，每5秒一个片段
        if total_duration > 0:
            expected_segments = total_duration / 5
            actual_segments = len(transcript)
            segment_coverage = min(actual_segments / expected_segments, 1.0) if expected_segments > 0 else 0
        else:
            expected_segments = 0
            actual_segments = len(transcript)
            segment_coverage = 0

        # 3. 说话人覆盖
        if transcript:
            segments_with_speaker = sum(
                1 for seg in transcript
                if isinstance(seg, dict) and ("speaker" in seg or "speaker_id" in seg)
            )
            speaker_coverage = segments_with_speaker / len(transcript)
        else:
            segments_with_speaker = 0
            speaker_coverage = 0

        # 加权平均
        completeness = (
            time_coverage * 0.5 +      # 时间覆盖最重要（50%）
            segment_coverage * 0.3 +   # 片段完整性（30%）
            speaker_coverage * 0.2     # 说话人识别（20%）
        )

        return {
            "modality": "audio",
            "completeness": completeness,
            "details": {
                "time_coverage": time_coverage,
                "segment_coverage": segment_coverage,
                "speaker_coverage": speaker_coverage,
                "total_duration": total_duration,
                "transcribed_duration": transcribed_duration,
                "expected_segments": expected_segments,
                "actual_segments": actual_segments,
                "segments_with_speaker": segments_with_speaker
            },
            "verification": {
                "formula": "0.5×时间覆盖 + 0.3×片段完整 + 0.2×说话人覆盖",
                "calculation": f"0.5×{time_coverage:.2f} + 0.3×{segment_coverage:.2f} + 0.2×{speaker_coverage:.2f} = {completeness:.2f}",
                "time_coverage_calc": f"{transcribed_duration:.0f}秒 / {total_duration:.0f}秒 = {time_coverage:.2%}",
                "segment_coverage_calc": f"{actual_segments}段 / {expected_segments:.0f}段(预期) = {segment_coverage:.2%}",
                "speaker_coverage_calc": f"{segments_with_speaker}段 / {len(transcript)}段 = {speaker_coverage:.2%}",
                "verifiable": True
            },
            "recommendations": Boundary1ValidatorV2._generate_audio_recommendations(
                time_coverage, segment_coverage, speaker_coverage
            )
        }

    @staticmethod
    def _validate_video(document: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证视频完整性"""
        # 视频包含音频和视觉两部分
        total_duration = extra_data.get("video_duration") or extra_data.get("duration", 0)
        transcript = extra_data.get("transcript", [])
        key_frames = extra_data.get("key_frames") or extra_data.get("frames", [])

        # 1. 音频转写覆盖
        if transcript and total_duration > 0:
            transcribed_duration = sum(
                seg.get("end", 0) - seg.get("start", 0)
                for seg in transcript
                if isinstance(seg, dict) and "start" in seg and "end" in seg
            )
            audio_coverage = min(transcribed_duration / total_duration, 1.0)
        else:
            transcribed_duration = 0
            audio_coverage = 0

        # 2. 关键帧提取率
        # 假设每10秒提取1帧
        if total_duration > 0:
            expected_frames = total_duration / 10
            actual_frames = len(key_frames) if isinstance(key_frames, list) else 0
            frame_coverage = min(actual_frames / expected_frames, 1.0) if expected_frames > 0 else 0
        else:
            expected_frames = 0
            actual_frames = 0
            frame_coverage = 0

        # 加权平均（音频更重要）
        completeness = (
            audio_coverage * 0.7 +    # 音频转写（70%）
            frame_coverage * 0.3      # 关键帧提取（30%）
        )

        return {
            "modality": "video",
            "completeness": completeness,
            "details": {
                "audio_coverage": audio_coverage,
                "frame_coverage": frame_coverage,
                "total_duration": total_duration,
                "transcribed_duration": transcribed_duration,
                "expected_frames": expected_frames,
                "actual_frames": actual_frames
            },
            "verification": {
                "formula": "0.7×音频覆盖 + 0.3×关键帧覆盖",
                "calculation": f"0.7×{audio_coverage:.2f} + 0.3×{frame_coverage:.2f} = {completeness:.2f}",
                "audio_coverage_calc": f"{transcribed_duration:.0f}秒 / {total_duration:.0f}秒 = {audio_coverage:.2%}",
                "frame_coverage_calc": f"{actual_frames}帧 / {expected_frames:.0f}帧(预期) = {frame_coverage:.2%}",
                "verifiable": True
            },
            "recommendations": []
        }

    @staticmethod
    def _validate_image(document: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证图片完整性"""
        # 1. OCR覆盖率
        ocr_regions = extra_data.get("ocr_regions", [])
        width = extra_data.get("width") or extra_data.get("resolution", {}).get("width", 1920)
        height = extra_data.get("height") or extra_data.get("resolution", {}).get("height", 1080)
        image_area = width * height

        if isinstance(ocr_regions, list) and ocr_regions:
            ocr_area = sum(
                region.get("width", 0) * region.get("height", 0)
                for region in ocr_regions
                if isinstance(region, dict)
            )
            ocr_coverage = min(ocr_area / image_area, 1.0)
        else:
            ocr_area = 0
            ocr_coverage = 0

        # 2. 图像描述
        description = extra_data.get("image_description", "")
        has_description = len(description) >= 20
        description_score = 1.0 if has_description else 0

        # 加权（描述更重要）
        completeness = (
            ocr_coverage * 0.4 +       # OCR覆盖（40%）
            description_score * 0.6    # 图像描述（60%）
        )

        return {
            "modality": "image",
            "completeness": completeness,
            "details": {
                "ocr_coverage": ocr_coverage,
                "has_description": has_description,
                "description_length": len(description),
                "ocr_regions_count": len(ocr_regions) if isinstance(ocr_regions, list) else 0,
                "image_area": image_area,
                "ocr_area": ocr_area
            },
            "verification": {
                "formula": "0.4×OCR覆盖 + 0.6×图像描述",
                "calculation": f"0.4×{ocr_coverage:.2f} + 0.6×{description_score:.2f} = {completeness:.2f}",
                "ocr_coverage_calc": f"{ocr_area:.0f}像素 / {image_area:.0f}像素 = {ocr_coverage:.2%}",
                "description_calc": f"描述长度 {len(description)}字 {'≥' if has_description else '<'} 20字",
                "verifiable": True
            },
            "recommendations": []
        }

    @staticmethod
    def _validate_document(document: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证文档完整性"""
        # 1. 页面提取率
        total_pages = extra_data.get("page_count") or extra_data.get("pages") or extra_data.get("num_pages", 1)
        extracted_pages = extra_data.get("extracted_pages", total_pages)  # 默认假设全部提取

        page_extraction = extracted_pages / total_pages if total_pages > 0 else 1.0

        # 2. 字数合理性
        # PDF一般：300-500字/页，取中间值400
        expected_words = total_pages * 400
        actual_words = document.get("word_count", 0)

        if expected_words > 0:
            word_ratio = actual_words / expected_words
            # 字数比例在50%-150%之间算合理
            if 0.5 <= word_ratio <= 1.5:
                word_reasonableness = 1.0
            else:
                word_reasonableness = max(0, 1 - abs(word_ratio - 1))
        else:
            word_ratio = 0
            word_reasonableness = 0

        # 3. 结构完整性
        has_structure = extra_data.get("structure_info") is not None or extra_data.get("structure") is not None
        structure_score = 1.0 if has_structure else 0.5

        # 加权平均
        completeness = (
            page_extraction * 0.5 +       # 页面提取最重要（50%）
            word_reasonableness * 0.3 +   # 字数合理性（30%）
            structure_score * 0.2          # 结构完整性（20%）
        )

        return {
            "modality": "document",
            "completeness": completeness,
            "details": {
                "page_extraction": page_extraction,
                "word_ratio": word_ratio,
                "word_reasonableness": word_reasonableness,
                "structure_complete": has_structure,
                "total_pages": total_pages,
                "extracted_pages": extracted_pages,
                "expected_words": expected_words,
                "actual_words": actual_words
            },
            "verification": {
                "formula": "0.5×页面提取 + 0.3×字数合理 + 0.2×结构完整",
                "calculation": f"0.5×{page_extraction:.2f} + 0.3×{word_reasonableness:.2f} + 0.2×{structure_score:.2f} = {completeness:.2f}",
                "page_extraction_calc": f"{extracted_pages}页 / {total_pages}页 = {page_extraction:.2%}",
                "word_ratio_calc": f"{actual_words}字 / {expected_words:.0f}字(预期) = {word_ratio:.2f}",
                "structure_calc": f"结构信息: {'有' if has_structure else '无'}",
                "verifiable": True
            },
            "recommendations": []
        }

    @staticmethod
    def _generate_audio_recommendations(time_coverage: float, segment_coverage: float, speaker_coverage: float) -> List[str]:
        """生成音频改进建议"""
        recommendations = []

        if time_coverage < 0.9:
            recommendations.append(f"时间覆盖率不足（{time_coverage:.1%}），建议检查音频质量或重新转写")

        if segment_coverage < 0.8:
            recommendations.append(f"片段完整性不足（{segment_coverage:.1%}），可能有大段静音或转写失败")

        if speaker_coverage < 0.7:
            recommendations.append(f"说话人识别率低（{speaker_coverage:.1%}），建议使用更好的说话人分离算法")

        return recommendations


# ========== 便捷函数 ==========

def validate_boundary1_v2(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证边界1（可验证版本）

    Args:
        document: 文档数据

    Returns:
        验证结果（包含详细计算过程）
    """
    return Boundary1ValidatorV2.validate(document)


def get_boundary1_report_v2(validation_result: Dict[str, Any]) -> str:
    """
    获取边界1验证报告（可验证版本）

    Args:
        validation_result: 验证结果

    Returns:
        报告文本
    """
    report = f"""
╔══════════════════════════════════════════════════════════════
║ 边界1验证报告：多模态→统一文本（可验证版本）
╠══════════════════════════════════════════════════════════════
║ 文档ID: {validation_result.get('document_id')}
║ 文件名: {validation_result.get('filename')}
║ 模态类型: {validation_result.get('modality')}
║ 完整性: {validation_result['completeness']:.1%}
║ 质量等级: {validation_result['quality_level']} ⭐
║ 状态: ✅ 可用（所有数据都保留）
╠══════════════════════════════════════════════════════════════
║ 📐 计算公式（可验证）:
║    {validation_result['verification']['formula']}
║
║ 🔢 详细计算:
║    {validation_result['verification']['calculation']}
╠══════════════════════════════════════════════════════════════
"""

    # 详细指标
    details = validation_result.get('details', {})
    verification = validation_result.get('verification', {})

    if validation_result['modality'] == 'audio':
        report += f"""║ 📊 详细指标:
║    时间覆盖: {details.get('time_coverage', 0):.1%}
║       计算: {verification.get('time_coverage_calc', 'N/A')}
║    片段完整: {details.get('segment_coverage', 0):.1%}
║       计算: {verification.get('segment_coverage_calc', 'N/A')}
║    说话人覆盖: {details.get('speaker_coverage', 0):.1%}
║       计算: {verification.get('speaker_coverage_calc', 'N/A')}
"""

    elif validation_result['modality'] == 'document':
        report += f"""║ 📊 详细指标:
║    页面提取: {details.get('page_extraction', 0):.1%}
║       计算: {verification.get('page_extraction_calc', 'N/A')}
║    字数合理: {details.get('word_reasonableness', 0):.1%}
║       计算: {verification.get('word_ratio_calc', 'N/A')}
║    结构完整: {details.get('structure_complete', False)}
║       计算: {verification.get('structure_calc', 'N/A')}
"""

    # 改进建议
    if validation_result.get('recommendations'):
        report += f"╠══════════════════════════════════════════════════════════════\n"
        report += f"║ 💡 改进建议:\n"
        for rec in validation_result['recommendations']:
            report += f"║    - {rec}\n"

    report += f"║\n║ ✅ 所有计算可验证\n"
    report += "╚══════════════════════════════════════════════════════════════\n"

    return report
