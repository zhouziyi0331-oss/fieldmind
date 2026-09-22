"""
边界1验证器：多模态→统一文本（脏数据→干净数据）
核心：完整性保证，无损转换

验证标准：
1. 完整性 ≥ 90%（必需项都有）
2. 元数据完整
3. 无严重质量问题
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class ModalityType(str, Enum):
    """模态类型"""
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"


class Boundary1Validator:
    """边界1验证器：多模态→统一文本"""

    # 每种模态的必需项
    MODALITY_REQUIREMENTS = {
        "audio": {
            "must_have": [
                "text_content",          # 完整转写文本
                "transcript",            # 带时间戳的片段
                "speakers",              # 说话人标识
                "transcription_confidence"  # 置信度
            ],
            "metadata_required": [
                "recording_duration",    # 录音时长
                "language",              # 语言
                "transcription_engine"   # 转写引擎
            ],
            "quality_thresholds": {
                "text_coverage": 0.95,          # 至少95%音频被转写
                "min_confidence": 0.7,          # 最低置信度70%
                "timestamp_accuracy": 1.0,      # 时间戳误差<1秒
            }
        },

        "video": {
            "must_have": [
                "text_content",          # 音频转写
                "transcript",            # 带时间戳
                "key_frames",            # 关键帧
                "scenes"                 # 场景分割
            ],
            "metadata_required": [
                "video_duration",
                "resolution",
                "frame_count"
            ],
            "quality_thresholds": {
                "audio_transcribed": True,
                "frames_extracted": True,
                "min_confidence": 0.7
            }
        },

        "image": {
            "must_have": [
                "text_content",          # OCR文字（如有）
                "image_description",     # 图像描述
            ],
            "metadata_required": [
                "resolution",
                "capture_time"
            ],
            "quality_thresholds": {
                "description_length": 20  # 描述至少20字
            }
        },

        "document": {
            "must_have": [
                "text_content",          # 完整文本
                "structure_info",        # 结构信息
            ],
            "metadata_required": [
                "document_type",
                "page_count"
            ],
            "quality_thresholds": {
                "text_extracted": True,
                "structure_preserved": True
            }
        }
    }

    @staticmethod
    def validate(document: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        验证文档是否为"干净数据"

        Args:
            document: 文档数据（包含 extra_data）

        Returns:
            (is_clean, validation_result)
        """
        file_type = document.get("file_type", "").lower()

        # 判断模态类型
        if file_type in ["mp3", "wav", "m4a", "flac", "ogg", "audio"]:
            modality = "audio"
        elif file_type in ["mp4", "mov", "avi", "mkv", "video"]:
            modality = "video"
        elif file_type in ["png", "jpg", "jpeg", "gif", "webp", "image"]:
            modality = "image"
        else:
            modality = "document"

        validation_result = {
            "is_clean": False,
            "modality": modality,
            "completeness_score": 0.0,
            "missing_items": [],
            "quality_issues": [],
            "metadata_issues": [],
            "recommendations": []
        }

        requirements = Boundary1Validator.MODALITY_REQUIREMENTS.get(modality)
        if not requirements:
            validation_result["quality_issues"].append(f"不支持的模态类型: {modality}")
            return False, validation_result

        # 1. 检查必需项
        must_have = requirements["must_have"]
        complete_items = 0
        total_items = len(must_have)

        for item in must_have:
            if Boundary1Validator._has_item(document, item):
                complete_items += 1
            else:
                validation_result["missing_items"].append(item)

        # 2. 检查元数据
        metadata_required = requirements["metadata_required"]
        total_items += len(metadata_required)

        for meta_field in metadata_required:
            if Boundary1Validator._has_metadata(document, meta_field):
                complete_items += 1
            else:
                validation_result["metadata_issues"].append(meta_field)

        # 3. 计算完整性分数
        validation_result["completeness_score"] = complete_items / total_items if total_items > 0 else 0

        # 4. 检查质量指标
        quality_thresholds = requirements["quality_thresholds"]
        quality_check_result = Boundary1Validator._check_quality(document, modality, quality_thresholds)
        validation_result["quality_issues"] = quality_check_result["issues"]

        # 5. 判断是否为"干净数据"
        # 标准：完整性 ≥ 90% + 无严重质量问题
        if validation_result["completeness_score"] >= 0.9 and len(validation_result["quality_issues"]) == 0:
            validation_result["is_clean"] = True
            logger.info(f"✅ 边界1验证通过: 文档 {document.get('id')} 是干净数据（完整性: {validation_result['completeness_score']:.1%}）")
        else:
            # 生成改进建议
            validation_result["recommendations"] = Boundary1Validator._generate_recommendations(validation_result)
            logger.warning(f"❌ 边界1验证失败: 文档 {document.get('id')} 不是干净数据")
            logger.warning(f"   完整性: {validation_result['completeness_score']:.1%}")
            logger.warning(f"   缺失项: {validation_result['missing_items']}")
            logger.warning(f"   质量问题: {validation_result['quality_issues']}")

        return validation_result["is_clean"], validation_result

    @staticmethod
    def _has_item(document: Dict[str, Any], item: str) -> bool:
        """检查文档是否有指定项"""
        # 直接检查字段
        if item in document and document[item]:
            return True

        # 检查 extra_data
        extra_data = document.get("extra_data", {})
        if item in extra_data and extra_data[item]:
            return True

        # 特殊处理
        if item == "text_content":
            return bool(document.get("text_content")) or bool(extra_data.get("text_content"))
        elif item == "transcript":
            return bool(extra_data.get("transcript")) or bool(extra_data.get("has_transcript"))
        elif item == "speakers":
            transcript = extra_data.get("transcript", [])
            if isinstance(transcript, list) and len(transcript) > 0:
                return "speaker" in transcript[0] or "speaker_id" in transcript[0]
        elif item == "transcription_confidence":
            return "transcription_confidence" in extra_data or "avg_confidence" in extra_data.get("quality_metrics", {})

        return False

    @staticmethod
    def _has_metadata(document: Dict[str, Any], meta_field: str) -> bool:
        """检查元数据是否存在"""
        metadata = document.get("extra_data", {}).get("metadata", {})

        # 直接检查
        if meta_field in metadata and metadata[meta_field]:
            return True

        # 映射检查
        field_mappings = {
            "recording_duration": ["duration", "recording_duration", "audio_duration"],
            "language": ["language", "lang"],
            "transcription_engine": ["transcription_engine", "engine", "asr_engine"],
            "video_duration": ["duration", "video_duration"],
            "resolution": ["resolution", "width", "height"],
            "frame_count": ["frame_count", "frames"],
            "capture_time": ["capture_time", "taken_at", "created_at"],
            "document_type": ["document_type", "file_type", "type"],
            "page_count": ["page_count", "pages", "num_pages"]
        }

        possible_fields = field_mappings.get(meta_field, [meta_field])
        for field in possible_fields:
            if field in metadata and metadata[field]:
                return True
            # 也检查 extra_data 根级别
            if field in document.get("extra_data", {}) and document["extra_data"][field]:
                return True

        return False

    @staticmethod
    def _check_quality(document: Dict[str, Any], modality: str, thresholds: Dict[str, Any]) -> Dict[str, Any]:
        """检查质量指标"""
        result = {
            "passed": True,
            "issues": []
        }

        extra_data = document.get("extra_data", {})
        quality_metrics = extra_data.get("quality_metrics", {})

        if modality == "audio":
            # 检查文本覆盖率
            if "text_coverage" in thresholds:
                coverage = quality_metrics.get("text_coverage", 0)
                if coverage < thresholds["text_coverage"]:
                    result["issues"].append(f"文本覆盖率不足: {coverage:.1%} < {thresholds['text_coverage']:.1%}")

            # 检查最低置信度
            if "min_confidence" in thresholds:
                confidence = quality_metrics.get("avg_confidence") or extra_data.get("transcription_confidence", 0)
                if confidence < thresholds["min_confidence"]:
                    result["issues"].append(f"转写置信度过低: {confidence:.1%} < {thresholds['min_confidence']:.1%}")

        elif modality == "video":
            # 检查音频是否转写
            if thresholds.get("audio_transcribed"):
                if not document.get("text_content") and not extra_data.get("text_content"):
                    result["issues"].append("视频音频未转写")

            # 检查关键帧是否提取
            if thresholds.get("frames_extracted"):
                if not extra_data.get("key_frames") and not extra_data.get("frames"):
                    result["issues"].append("关键帧未提取")

        elif modality == "image":
            # 检查描述长度
            if "description_length" in thresholds:
                description = extra_data.get("image_description", "")
                if len(description) < thresholds["description_length"]:
                    result["issues"].append(f"图像描述过短: {len(description)}字 < {thresholds['description_length']}字")

        elif modality == "document":
            # 检查文本是否提取
            if thresholds.get("text_extracted"):
                if not document.get("text_content"):
                    result["issues"].append("文档文本未提取")

            # 检查结构是否保留
            if thresholds.get("structure_preserved"):
                if not extra_data.get("structure_info") and not extra_data.get("structure"):
                    result["issues"].append("文档结构未保留")

        result["passed"] = len(result["issues"]) == 0
        return result

    @staticmethod
    def _generate_recommendations(validation_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 缺失项建议
        if validation_result["missing_items"]:
            recommendations.append(f"请补充缺失项: {', '.join(validation_result['missing_items'])}")

        # 元数据建议
        if validation_result["metadata_issues"]:
            recommendations.append(f"请补充元数据: {', '.join(validation_result['metadata_issues'])}")

        # 质量问题建议
        if validation_result["quality_issues"]:
            recommendations.append("请改进质量问题后重新处理")

        # 完整性建议
        if validation_result["completeness_score"] < 0.9:
            recommendations.append(f"完整性不足（{validation_result['completeness_score']:.1%}），需要达到90%以上")

        return recommendations


# ========== 便捷函数 ==========

def validate_boundary1(document: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    验证边界1：多模态→统一文本

    Args:
        document: 文档数据

    Returns:
        (is_clean, validation_result)
    """
    return Boundary1Validator.validate(document)


def get_boundary1_report(document: Dict[str, Any]) -> str:
    """
    获取边界1验证报告（可读格式）

    Args:
        document: 文档数据

    Returns:
        报告文本
    """
    is_clean, result = validate_boundary1(document)

    report = f"""
╔══════════════════════════════════════════════════════════════
║ 边界1验证报告：多模态→统一文本
╠══════════════════════════════════════════════════════════════
║ 文档ID: {document.get('id')}
║ 文件名: {document.get('original_filename', document.get('filename'))}
║ 模态类型: {result['modality']}
║ 验证结果: {'✅ 通过（干净数据）' if is_clean else '❌ 未通过'}
║ 完整性: {result['completeness_score']:.1%}
╠══════════════════════════════════════════════════════════════
"""

    if result['missing_items']:
        report += f"║ ⚠️  缺失项:\n"
        for item in result['missing_items']:
            report += f"║    - {item}\n"

    if result['metadata_issues']:
        report += f"║ ⚠️  元数据缺失:\n"
        for item in result['metadata_issues']:
            report += f"║    - {item}\n"

    if result['quality_issues']:
        report += f"║ ⚠️  质量问题:\n"
        for issue in result['quality_issues']:
            report += f"║    - {issue}\n"

    if result['recommendations']:
        report += f"║ 💡 改进建议:\n"
        for rec in result['recommendations']:
            report += f"║    - {rec}\n"

    report += "╚══════════════════════════════════════════════════════════════\n"

    return report
