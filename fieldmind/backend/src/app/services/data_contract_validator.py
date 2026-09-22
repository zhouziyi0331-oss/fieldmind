"""
数据契约验证器
定义脏数据→干净数据的转换标准和验证规则
"""

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SourceLevel(str, Enum):
    """数据来源层级"""
    RAW_MATERIAL = "原始材料"      # 田野笔记、录音原始文本
    FIRST_HAND = "一度报告"        # 访谈记录、调研日志
    SECOND_HAND = "二度报告"       # 整理后的报告
    THIRD_HAND = "三度报告"        # 学术论文、出版物


class DataQualityLevel(str, Enum):
    """数据质量等级"""
    DIRTY = "脏数据"    # 原始上传，未处理
    CLEAN = "干净数据"   # 已清洗，可进入知识流水线
    ENRICHED = "富化数据" # 经过知识流水线处理


class CleanDataContract:
    """干净数据契约 - 定义进入知识流水线的标准"""

    # 必需字段
    REQUIRED_FIELDS = [
        "document_id",
        "text_content",
        "word_count",
        "file_type",
        "created_at",
        "metadata"
    ]

    # 支持的文件类型
    SUPPORTED_FILE_TYPES = [
        "pdf", "docx", "txt", "md", "markdown",
        "audio", "video", "image"
    ]

    # 最小字数要求
    MIN_WORD_COUNT = 10

    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证数据是否符合干净数据标准

        Args:
            data: 待验证的数据

        Returns:
            (is_valid, errors): 验证结果和错误列表
        """
        errors = []

        # 1. 检查必需字段
        for field in CleanDataContract.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                errors.append(f"缺少必需字段: {field}")

        # 2. 检查文本内容
        text_content = data.get("text_content")
        if text_content:
            if not isinstance(text_content, str):
                errors.append("text_content 必须是字符串类型")
            elif len(text_content.strip()) == 0:
                errors.append("text_content 不能为空")

        # 3. 检查字数
        word_count = data.get("word_count", 0)
        if word_count < CleanDataContract.MIN_WORD_COUNT:
            errors.append(f"文档字数不足（最少{CleanDataContract.MIN_WORD_COUNT}字，当前{word_count}字）")

        # 4. 检查文件类型
        file_type = data.get("file_type", "").lower()
        if file_type not in CleanDataContract.SUPPORTED_FILE_TYPES:
            errors.append(f"不支持的文件类型: {file_type}")

        # 5. 检查时间戳
        created_at = data.get("created_at")
        if created_at and not isinstance(created_at, (datetime, str)):
            errors.append("created_at 必须是 datetime 或 ISO 格式字符串")

        # 6. 检查元数据
        metadata = data.get("metadata")
        if metadata:
            if not isinstance(metadata, dict):
                errors.append("metadata 必须是字典类型")
            else:
                # 检查元数据必需字段
                if "source_level" not in metadata:
                    errors.append("metadata 缺少 source_level 字段")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"✅ 数据契约验证通过: document_id={data.get('document_id')}")
        else:
            logger.warning(f"❌ 数据契约验证失败: document_id={data.get('document_id')}, errors={errors}")

        return is_valid, errors

    @staticmethod
    def create_clean_data_template(
        document_id: int,
        text_content: str,
        filename: str,
        file_type: str,
        source_level: SourceLevel = SourceLevel.RAW_MATERIAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建符合契约标准的干净数据模板

        Args:
            document_id: 文档ID
            text_content: 文本内容
            filename: 文件名
            file_type: 文件类型
            source_level: 来源层级
            metadata: 额外元数据

        Returns:
            符合契约的数据字典
        """
        word_count = len(text_content.split())

        base_metadata = {
            "source_level": source_level.value,
            "filename": filename,
            "document_date": datetime.now(),
            "tags": [],
            "confidence": 1.0
        }

        if metadata:
            base_metadata.update(metadata)

        return {
            "document_id": document_id,
            "text_content": text_content,
            "word_count": word_count,
            "file_type": file_type.lower(),
            "created_at": datetime.now(),
            "metadata": base_metadata,
            "quality_level": DataQualityLevel.CLEAN.value
        }


class DirtyToCleanConverter:
    """脏数据到干净数据的转换器"""

    @staticmethod
    def convert(
        raw_data: Dict[str, Any],
        extracted_text: str,
        document_id: int
    ) -> Dict[str, Any]:
        """
        将脏数据转换为干净数据

        Args:
            raw_data: 原始上传数据（脏数据）
            extracted_text: 提取的文本内容
            document_id: 文档ID

        Returns:
            符合契约的干净数据
        """
        filename = raw_data.get("filename", "unknown")
        file_type = raw_data.get("file_type", "txt")
        mime_type = raw_data.get("mime_type", "")

        # 推断来源层级
        source_level = DirtyToCleanConverter._infer_source_level(filename, mime_type)

        # 提取元数据
        metadata = {
            "source_level": source_level.value,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": raw_data.get("file_size", 0),
            "upload_time": datetime.now(),
            "tags": raw_data.get("tags", []),
            "confidence": 1.0
        }

        # 如果有额外元数据，合并
        if "metadata" in raw_data:
            metadata.update(raw_data["metadata"])

        clean_data = CleanDataContract.create_clean_data_template(
            document_id=document_id,
            text_content=extracted_text,
            filename=filename,
            file_type=file_type,
            source_level=source_level,
            metadata=metadata
        )

        logger.info(f"🔄 脏数据转换完成: {filename} → clean_data (words={clean_data['word_count']})")

        return clean_data

    @staticmethod
    def _infer_source_level(filename: str, mime_type: str) -> SourceLevel:
        """推断数据来源层级"""
        filename_lower = filename.lower()

        # 根据文件名关键词推断
        if any(kw in filename_lower for kw in ["笔记", "录音", "原始", "raw", "audio"]):
            return SourceLevel.RAW_MATERIAL
        elif any(kw in filename_lower for kw in ["访谈", "调研", "interview", "fieldwork"]):
            return SourceLevel.FIRST_HAND
        elif any(kw in filename_lower for kw in ["报告", "整理", "report", "summary"]):
            return SourceLevel.SECOND_HAND
        elif any(kw in filename_lower for kw in ["论文", "paper", "article", "publication"]):
            return SourceLevel.THIRD_HAND

        # 根据MIME类型推断
        if "audio" in mime_type or "video" in mime_type:
            return SourceLevel.RAW_MATERIAL

        # 默认为原始材料
        return SourceLevel.RAW_MATERIAL


class PipelineGate:
    """流水线门控 - 决定数据能否进入下一阶段"""

    @staticmethod
    def can_enter_knowledge_pipeline(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查数据是否可以进入知识流水线（九步）

        Args:
            data: 待检查的数据

        Returns:
            (can_enter, reason): 是否可以进入和原因
        """
        # 1. 验证契约
        is_valid, errors = CleanDataContract.validate(data)

        if not is_valid:
            reason = f"数据契约验证失败: {'; '.join(errors)}"
            logger.warning(f"🚫 拒绝进入知识流水线: {reason}")
            return False, reason

        # 2. 检查质量等级
        quality_level = data.get("quality_level")
        if quality_level != DataQualityLevel.CLEAN.value:
            reason = f"数据质量等级不符（需要CLEAN，当前{quality_level}）"
            logger.warning(f"🚫 拒绝进入知识流水线: {reason}")
            return False, reason

        # 3. 检查文本长度
        text_length = len(data.get("text_content", ""))
        if text_length < 50:  # 至少50个字符
            reason = f"文本过短（{text_length}字符）"
            logger.warning(f"🚫 拒绝进入知识流水线: {reason}")
            return False, reason

        logger.info(f"✅ 通过门控检查，可进入知识流水线: document_id={data.get('document_id')}")
        return True, "通过所有检查"


# 导出便捷函数
def validate_clean_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证干净数据"""
    return CleanDataContract.validate(data)


def convert_dirty_to_clean(
    raw_data: Dict[str, Any],
    extracted_text: str,
    document_id: int
) -> Dict[str, Any]:
    """脏数据转干净数据"""
    return DirtyToCleanConverter.convert(raw_data, extracted_text, document_id)


def check_pipeline_gate(data: Dict[str, Any]) -> Tuple[bool, str]:
    """检查流水线门控"""
    return PipelineGate.can_enter_knowledge_pipeline(data)
