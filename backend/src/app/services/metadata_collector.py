"""
采集层增强 - 全量元数据捕获
修改 FileUploadService，在上传时捕获所有元数据
"""

import os
import hashlib
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime

from app.core.logging import logger
from app.core.database import generate_id


class MetadataCollector:
    """元数据收集器"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    @staticmethod
    def collect_file_metadata(
        file: BinaryIO,
        filename: str,
        mime_type: str,
        project_id: int,
        collection_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        收集文件的完整元数据

        Args:
            file: 文件对象
            filename: 文件名
            mime_type: MIME类型
            project_id: 项目ID
            collection_info: 采集信息（设备、地点、人员、批次）

        Returns:
            Dict: 完整的元数据
        """
        metadata = {}

        # 1. 文件基础信息
        file.seek(0, 2)  # 移到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到开头

        metadata['size'] = file_size
        metadata['name'] = filename
        metadata['mime_type'] = mime_type

        # 2. 计算文件哈希（MD5）
        file_hash = MetadataCollector._calculate_file_hash(file)
        metadata['file_hash'] = file_hash

        # 3. 采集环境信息
        if collection_info:
            metadata['collection_device'] = collection_info.get('device')
            metadata['collection_location'] = collection_info.get('location')
            metadata['collector_name'] = collection_info.get('collector')
            metadata['batch_id'] = collection_info.get('batch_id')
        else:
            # 默认值
            metadata['collection_device'] = 'web_upload'
            metadata['batch_id'] = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 4. 系统级元数据
        metadata['uploaded_at'] = datetime.utcnow()
        metadata['created_at'] = datetime.utcnow()
        metadata['updated_at'] = datetime.utcnow()

        logger.info(
            f"元数据收集完成: {filename}",
            file_size=file_size,
            file_hash=file_hash[:16]
        )

        return metadata

    @staticmethod
    def _calculate_file_hash(file: BinaryIO) -> str:
        """计算文件MD5哈希"""
        md5 = hashlib.md5()

        file.seek(0)
        while chunk := file.read(8192):
            md5.update(chunk)
        file.seek(0)

        return md5.hexdigest()

    @staticmethod
    def extract_content_metadata(
        text: str,
        doc_type: str
    ) -> Dict[str, Any]:
        """
        提取内容级元数据

        Args:
            text: 文本内容
            doc_type: 文档类型

        Returns:
            Dict: 内容元数据
        """
        import re

        metadata = {}

        # 1. 统计字数（不含标点和空格）
        words = [c for c in text if c.isalnum()]
        metadata['total_words'] = len(words)

        # 2. 统计句数
        sentences = re.split(r'[。！？!?.]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        metadata['total_sentences'] = len(sentences)

        # 3. 统计段落数
        paragraphs = text.split('\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        metadata['total_paragraphs'] = len(paragraphs)

        # 4. 语言检测
        metadata['language'] = MetadataCollector._detect_language(text)

        # 5. 音频特定：说话人数量（从文本内容推断，或由ASR结果提供）
        if doc_type in ['audio', 'video']:
            # 默认单说话人，可由外部ASR结果覆盖
            metadata['speaker_count'] = MetadataCollector._estimate_speaker_count(text)

        logger.info(
            f"内容元数据提取完成",
            words=metadata['total_words'],
            sentences=metadata['total_sentences'],
            language=metadata['language']
        )

        return metadata

    @staticmethod
    def _detect_language(text: str) -> str:
        """简单语言检测"""
        # 统计中文字符
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)

        if total_chars == 0:
            return 'unknown'

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return 'zh'
        elif chinese_ratio < 0.1:
            return 'en'
        else:
            return 'mixed'

    @staticmethod
    def _estimate_speaker_count(text: str) -> int:
        """从文本推断说话人数量（简单启发式方法）"""
        # 检测对话标记
        dialogue_markers = ['A:', 'B:', '甲:', '乙:', '问:', '答:', 'Q:', 'A:']
        marker_count = sum(1 for marker in dialogue_markers if marker in text)

        if marker_count >= 2:
            return min(marker_count, 10)  # 最多10个说话人

        # 检测引号对话
        quote_count = text.count('"') + text.count('"') + text.count('"')
        if quote_count >= 4:
            return 2  # 至少2人对话

        return 1  # 默认单说话人
