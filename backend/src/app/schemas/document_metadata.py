"""
文档元数据规范 - 链路十四核心模块
定义每个文档chunk必须携带的完整元数据字段
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """文档类型"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    REPORT_L1 = "report_level_1"  # 一度报告（原始材料整理）
    REPORT_L2 = "report_level_2"  # 二度报告（初步分析）
    REPORT_L3 = "report_level_3"  # 三度报告（深度洞察）


class SourceLevel(int, Enum):
    """来源层级（用于链路17的报告优先级）"""
    RAW_MATERIAL = 0      # 原始材料（音频、PDF等）
    REPORT_LEVEL_1 = 1    # 一度报告
    REPORT_LEVEL_2 = 2    # 二度报告
    REPORT_LEVEL_3 = 3    # 三度报告（最高优先级）


@dataclass
class DocumentMetadata:
    """
    文档元数据完整规范

    这是链路十四的核心：确保每个chunk都能精确溯源
    """
    # ========== 必填字段 ==========
    document_id: int                    # 文档ID
    source_file: str                    # 源文件名（如"访谈老张_20240801.mp3"）
    document_type: DocumentType         # 文档类型
    source_level: SourceLevel           # 来源层级（用于检索权重）

    # ========== 位置信息（根据类型必填） ==========
    # PDF/DOCX必填
    page_number: Optional[int] = None   # 页码（从1开始）
    page_range: Optional[str] = None    # 页码范围（如"23-25"）

    # 音频/视频必填
    timestamp_start: Optional[float] = None  # 开始时间戳（秒）
    timestamp_end: Optional[float] = None    # 结束时间戳（秒）
    timestamp_range: Optional[str] = None    # 时间范围（如"12:30-12:45"）

    # 音频特有（链路14强化需求）
    speaker: Optional[str] = None       # 说话人标识（如"speaker_1"或"老张"）
    speaker_confidence: Optional[float] = None  # 说话人识别置信度

    # ========== Chunk位置信息 ==========
    chunk_index: int = 0                # 当前chunk在文档中的索引
    total_chunks: int = 1               # 文档总chunk数
    char_start: int = 0                 # 字符起始位置
    char_end: int = 0                   # 字符结束位置

    # ========== 项目关联 ==========
    project_id: Optional[int] = None    # 所属项目ID

    # ========== 时间信息（链路15需要） ==========
    upload_time: Optional[datetime] = None      # 上传时间
    document_date: Optional[datetime] = None    # 文档日期（如会议日期、录音日期）
    extracted_dates: List[str] = field(default_factory=list)  # 文档中提到的日期（ISO格式）

    # ========== 内容特征 ==========
    text_length: int = 0                # 文本长度
    language: str = "zh"                # 语言（zh/en）

    # ========== 扩展字段 ==========
    tags: List[str] = field(default_factory=list)           # 标签
    keywords: List[str] = field(default_factory=list)        # 关键词
    entities: List[str] = field(default_factory=list)        # 提取的实体
    custom_fields: Dict[str, Any] = field(default_factory=dict)  # 自定义字段

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于存入ChromaDB）"""
        data = asdict(self)

        # 枚举类型转换为字符串
        if isinstance(data['document_type'], DocumentType):
            data['document_type'] = data['document_type'].value
        if isinstance(data['source_level'], SourceLevel):
            data['source_level'] = data['source_level'].value

        # datetime转换为ISO字符串
        if data['upload_time']:
            data['upload_time'] = data['upload_time'].isoformat()
        if data['document_date']:
            data['document_date'] = data['document_date'].isoformat()

        # 过滤None值（ChromaDB不接受None）
        return {k: v for k, v in data.items() if v is not None and v != [] and v != {}}

    def format_citation(self) -> str:
        """
        格式化引用文本（用于UI显示）

        Returns:
            格式化的引用字符串，如：
            - "[来源：访谈老张 12:30-12:45]"
            - "[来源：二度报告 P23]"
            - "[来源：会议记录.pdf P5]"
        """
        source_type = self.document_type.value

        # 音频/视频引用
        if source_type in ['audio', 'video']:
            if self.timestamp_range:
                time_str = self.timestamp_range
            elif self.timestamp_start is not None:
                time_str = self._format_timestamp(self.timestamp_start)
                if self.timestamp_end:
                    time_str += f"-{self._format_timestamp(self.timestamp_end)}"
            else:
                time_str = "未知时间"

            speaker_str = f" {self.speaker}" if self.speaker else ""
            return f"[来源：{self.source_file}{speaker_str} {time_str}]"

        # PDF/DOCX引用
        elif source_type in ['pdf', 'docx']:
            if self.page_range:
                page_str = f"P{self.page_range}"
            elif self.page_number:
                page_str = f"P{self.page_number}"
            else:
                page_str = "页码未知"
            return f"[来源：{self.source_file} {page_str}]"

        # 报告引用（标注报告层级）
        elif source_type.startswith('report_level_'):
            level_name = {
                'report_level_1': '一度报告',
                'report_level_2': '二度报告',
                'report_level_3': '三度报告'
            }.get(source_type, '报告')

            page_str = f"P{self.page_number}" if self.page_number else ""
            return f"[来源：{level_name} {self.source_file} {page_str}]"

        # 其他类型
        else:
            return f"[来源：{self.source_file}]"

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """将秒数转换为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def validate(self) -> List[str]:
        """
        验证元数据完整性

        Returns:
            错误列表，空列表表示验证通过
        """
        errors = []

        # 验证必填字段
        if not self.source_file:
            errors.append("缺少必填字段: source_file")

        # 根据文档类型验证特定字段
        if self.document_type in [DocumentType.PDF, DocumentType.DOCX]:
            if self.page_number is None and self.page_range is None:
                errors.append(f"{self.document_type.value}类型文档必须提供page_number或page_range")

        if self.document_type in [DocumentType.AUDIO, DocumentType.VIDEO]:
            if self.timestamp_start is None and self.timestamp_range is None:
                errors.append(f"{self.document_type.value}类型文档必须提供timestamp_start或timestamp_range")

        return errors


@dataclass
class ChunkMetadata(DocumentMetadata):
    """
    Chunk级别的元数据（继承文档元数据）

    在切分时，每个chunk会继承父文档的所有元数据，
    并添加chunk特有的字段
    """
    # Chunk特有字段
    chunk_id: str = ""                  # Chunk唯一ID
    prev_chunk_id: Optional[str] = None # 前一个chunk的ID
    next_chunk_id: Optional[str] = None # 后一个chunk的ID
    paragraph_index: int = 0            # 所属段落索引

    def __post_init__(self):
        """Chunk ID自动生成"""
        if not self.chunk_id:
            self.chunk_id = f"doc{self.document_id}_chunk{self.chunk_index}"


def create_metadata_from_upload(
    document_id: int,
    filename: str,
    file_type: str,
    project_id: Optional[int] = None,
    page_number: Optional[int] = None,
    timestamp_start: Optional[float] = None,
    timestamp_end: Optional[float] = None,
    speaker: Optional[str] = None,
    document_date: Optional[datetime] = None,
    source_level: SourceLevel = SourceLevel.RAW_MATERIAL,
    **kwargs
) -> DocumentMetadata:
    """
    从上传信息创建元数据对象

    这是入口函数：在文档上传时立即创建完整元数据
    """
    # 确定文档类型
    if file_type.lower() == 'pdf':
        doc_type = DocumentType.PDF
    elif file_type.lower() in ['docx', 'doc']:
        doc_type = DocumentType.DOCX
    elif file_type.lower() in ['txt', 'md']:
        doc_type = DocumentType.TXT
    elif file_type.lower() in ['mp3', 'wav', 'flac', 'm4a']:
        doc_type = DocumentType.AUDIO
    elif file_type.lower() in ['mp4', 'avi', 'mov']:
        doc_type = DocumentType.VIDEO
    else:
        doc_type = DocumentType.TXT  # 默认

    # 格式化时间戳范围
    timestamp_range = None
    if timestamp_start is not None and timestamp_end is not None:
        start_str = DocumentMetadata._format_timestamp(timestamp_start)
        end_str = DocumentMetadata._format_timestamp(timestamp_end)
        timestamp_range = f"{start_str}-{end_str}"

    return DocumentMetadata(
        document_id=document_id,
        source_file=filename,
        document_type=doc_type,
        source_level=source_level,
        project_id=project_id,
        page_number=page_number,
        timestamp_start=timestamp_start,
        timestamp_end=timestamp_end,
        timestamp_range=timestamp_range,
        speaker=speaker,
        document_date=document_date,
        upload_time=datetime.utcnow(),
        **kwargs
    )
