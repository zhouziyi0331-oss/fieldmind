"""
音频分块服务 - 链路15重写版
核心：保留Whisper的时间边界，禁止重切分

解决问题：
- 用户问"老李在23分45秒说了什么" → AI能精确回答并跳转播放
- 每个向量块必须携带 start_sec、end_sec、timestamp_display
"""

from typing import List, Dict, Any
from datetime import datetime
import logging

from app.schemas.document_metadata import ChunkMetadata, DocumentMetadata

logger = logging.getLogger(__name__)


class AudioChunker:
    """音频分块器 - 严格保留Whisper时间边界"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """不需要chunk_size参数 - 以Whisper segment为准"""
        pass

    def chunk_audio_segments(
        self,
        segments: List[Dict[str, Any]],
        document_metadata: DocumentMetadata
    ) -> List[ChunkMetadata]:
        """
        将Whisper segments转换为带时间戳的chunks

        ⚠️ 绝对禁令：
        - 禁止合并多个segment（会破坏时间边界）
        - 禁止重切分segment文本（会丢失start/end）
        - 每个segment = 1个chunk，时间戳精度 ±1秒

        Args:
            segments: Whisper返回的segments列表
            每个segment格式：
            {
                "id": 0,
                "start": 1425.0,  # 开始时间（秒）
                "end": 1450.0,    # 结束时间（秒）
                "text": "祠堂再不修就要塌了，村里年轻人都不认祖宗了。"
            }

            document_metadata: 父文档元数据（音频文件）

        Returns:
            List[ChunkMetadata]: 每个chunk携带完整时间戳
        """
        if not segments:
            logger.warning(f"音频文件 {document_metadata.source_file} 没有segments")
            return []

        logger.info(f"🎤 处理音频segments: {len(segments)} 个片段")

        chunks = []

        for idx, segment in enumerate(segments):
            # 提取时间信息
            start_sec = segment.get("start", 0.0)
            end_sec = segment.get("end", 0.0)
            text = segment.get("text", "").strip()

            if not text:
                continue

            # 格式化时间显示（MM:SS格式）
            timestamp_display = self._format_timestamp(start_sec, end_sec)

            # 创建chunk元数据
            chunk = ChunkMetadata(
                # 继承父文档字段
                document_id=document_metadata.document_id,
                source_file=document_metadata.source_file,
                document_type=document_metadata.document_type,
                source_level=document_metadata.source_level,

                # 音频特有字段
                timestamp_start=start_sec,
                timestamp_end=end_sec,
                timestamp_range=timestamp_display,
                speaker=document_metadata.speaker or "Unknown",

                # Chunk位置
                chunk_index=idx,
                total_chunks=len(segments),  # 会在后面更新
                char_start=0,  # 音频没有字符位置
                char_end=len(text),

                # 文本内容
                text_length=len(text),
                language=document_metadata.language or "zh",

                # 项目关联
                project_id=document_metadata.project_id,

                # 自定义字段（存储文本和segment ID）
                custom_fields={
                    "text": text,
                    "segment_id": segment.get("id", idx),
                    "start_sec": start_sec,  # 冗余存储，方便前端使用
                    "end_sec": end_sec,
                    "timestamp_display": timestamp_display,
                    "media_type": "audio"  # 标记为音频类型
                }
            )

            # 生成chunk_id
            chunk.chunk_id = f"audio{document_metadata.document_id}_seg{idx:04d}"

            chunks.append(chunk)

        # 更新total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        # 添加chunk链接（前后关系）
        chunks = self._add_chunk_links(chunks)

        logger.info(f"✅ 音频分块完成: {len(chunks)} 个时间戳片段")

        return chunks

    def _format_timestamp(self, start_sec: float, end_sec: float) -> str:
        """
        格式化时间戳为可读格式

        Examples:
            (65.5, 78.2) → "01:05-01:18"
            (1425.0, 1450.0) → "23:45-24:10"
        """
        def sec_to_mmss(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        start_str = sec_to_mmss(start_sec)
        end_str = sec_to_mmss(end_sec)

        return f"{start_str}-{end_str}"

    def _add_chunk_links(self, chunks: List[ChunkMetadata]) -> List[ChunkMetadata]:
        """添加chunk前后链接"""
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_id = chunks[i - 1].chunk_id
            if i < len(chunks) - 1:
                chunk.next_chunk_id = chunks[i + 1].chunk_id

        return chunks


# 全局单例
_audio_chunker = None

def get_audio_chunker() -> AudioChunker:
    """获取音频分块器单例"""
    global _audio_chunker
    if _audio_chunker is None:
        _audio_chunker = AudioChunker()
    return _audio_chunker
