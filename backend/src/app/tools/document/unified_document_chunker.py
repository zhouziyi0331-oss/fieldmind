"""
文档分块器 - 统一整合版 (v1 + v2 → Unified)

核心改进：
1. 双模式输出 - Dict模式（向后兼容）+ 强类型ChunkMetadata模式
2. 完整时间戳支持 - 音频时间戳映射 + 文档元数据继承
3. 智能overlap策略 - 真正实现chunk间重叠，保持上下文连贯
4. 分块质量评分 - 评估每个chunk的语义完整性（0-100分）
5. 多种分块策略 - 语义边界、固定大小、句子级、滑动窗口
"""

import re
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============== Enums ==============

class ChunkStrategy(str, Enum):
    """分块策略枚举"""
    SEMANTIC = "semantic"  # 语义边界切分（默认，按段落和句子）
    FIXED = "fixed"  # 固定大小切分
    SENTENCE = "sentence"  # 句子级切分（每个chunk是完整句子的集合）
    SLIDING = "sliding"  # 滑动窗口切分（固定窗口大小，固定步长）


class ChunkQuality(str, Enum):
    """Chunk质量等级"""
    EXCELLENT = "excellent"  # 90-100分：完整段落，边界清晰
    GOOD = "good"  # 70-89分：句子完整，语义连贯
    FAIR = "fair"  # 50-69分：有断句，但可用
    POOR = "poor"  # <50分：强制切分，语义不完整


# ============== Data Classes ==============

@dataclass
class ChunkResult:
    """分块结果（轻量版，Dict模式）"""
    chunk_id: str
    text: str
    chunk_index: int
    total_chunks: int

    # 位置信息
    start_pos: int
    end_pos: int
    paragraph_index: Optional[int] = None

    # 链接信息
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None

    # 时间戳（音频/视频）
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None

    # 质量信息
    chunk_type: str = "semantic"
    quality_score: float = 0.0
    quality_level: ChunkQuality = ChunkQuality.GOOD

    # 元数据
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（向后兼容v1格式）"""
        result = {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "prev_chunk_id": self.prev_chunk_id,
            "next_chunk_id": self.next_chunk_id,
            "metadata": {
                **self.metadata,
                "start_pos": self.start_pos,
                "end_pos": self.end_pos,
                "paragraph_index": self.paragraph_index,
                "chunk_type": self.chunk_type,
                "quality_score": self.quality_score,
                "quality_level": self.quality_level.value,
            }
        }

        # 添加时间戳（如果有）
        if self.start_sec is not None:
            result["metadata"]["start_sec"] = self.start_sec
        if self.end_sec is not None:
            result["metadata"]["end_sec"] = self.end_sec

        return result


# ============== Main Chunker Class ==============

class UnifiedDocumentChunker:
    """
    统一文档分块器

    整合了v1和v2的所有功能，并新增5个增强特性：
    1. 双模式输出
    2. 完整时间戳支持
    3. 智能overlap
    4. 质量评分
    5. 多种策略
    """

    def __init__(
        self,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        target_chunk_size: int = 350,
        overlap_size: int = 50,
        enable_overlap: bool = False,
        enable_quality_scoring: bool = True,
        max_chunks_limit: int = 500
    ):
        """
        Args:
            strategy: 分块策略（semantic/fixed/sentence/sliding）
            min_chunk_size: 最小chunk大小（字符数）
            max_chunk_size: 最大chunk大小（字符数）
            target_chunk_size: 目标chunk大小
            overlap_size: chunk之间的重叠大小（保持上下文连贯）
            enable_overlap: 是否启用overlap（新增功能）
            enable_quality_scoring: 是否启用质量评分（新增功能）
            max_chunks_limit: 最大chunk数量限制（防止超大文档）
        """
        self.strategy = strategy
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.enable_overlap = enable_overlap
        self.enable_quality_scoring = enable_quality_scoring
        self.max_chunks_limit = max_chunks_limit

        logger.info(
            f"📦 UnifiedDocumentChunker initialized: "
            f"strategy={strategy.value}, "
            f"size=[{min_chunk_size}, {max_chunk_size}], "
            f"overlap={'enabled' if enable_overlap else 'disabled'}"
        )

    # ============== Public API ==============

    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_metadata: Optional[Any] = None,
        output_mode: str = "dict",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Union[List[Dict[str, Any]], List[ChunkResult], List[Any]]:
        """
        切分文档为多个语义块（统一入口）

        Args:
            text: 文档文本
            metadata: 基础元数据（Dict格式，v1兼容）
            document_metadata: 强类型DocumentMetadata对象（v2兼容）
            output_mode: 输出模式 - "dict"（v1）/"result"（ChunkResult）/"metadata"（v2 ChunkMetadata）
            progress_callback: 进度回调函数 callback(current, total)

        Returns:
            根据output_mode返回不同格式：
            - "dict": List[Dict] - 向后兼容v1格式
            - "result": List[ChunkResult] - 新的强类型结果
            - "metadata": List[ChunkMetadata] - v2格式（需要document_metadata）
        """
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return []

        # 归一化metadata
        if metadata is None:
            metadata = {}

        # 根据策略执行分块
        if self.strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text, metadata, document_metadata)
        elif self.strategy == ChunkStrategy.FIXED:
            chunks = self._chunk_fixed(text, metadata, document_metadata)
        elif self.strategy == ChunkStrategy.SENTENCE:
            chunks = self._chunk_sentence(text, metadata, document_metadata)
        elif self.strategy == ChunkStrategy.SLIDING:
            chunks = self._chunk_sliding(text, metadata, document_metadata)
        else:
            logger.warning(f"未知策略 {self.strategy}，使用默认semantic")
            chunks = self._chunk_semantic(text, metadata, document_metadata)

        # 添加chunk链接
        chunks = self._add_chunk_links(chunks)

        # 映射音频时间戳（如果有）
        if metadata.get('transcript'):
            logger.info("检测到transcript数据，映射时间戳到chunks")
            chunks = self._map_timestamps_to_chunks(chunks, text, metadata['transcript'])

        # 应用overlap（如果启用）
        if self.enable_overlap and self.overlap_size > 0:
            chunks = self._apply_overlap(chunks, text)

        # 计算质量评分（如果启用）
        if self.enable_quality_scoring:
            chunks = self._score_chunk_quality(chunks)

        # 限制chunk总数
        if len(chunks) > self.max_chunks_limit:
            logger.warning(f"Chunks数量({len(chunks)})超过限制，合并至{self.max_chunks_limit}个")
            chunks = self._merge_chunks_to_limit(chunks, self.max_chunks_limit)

        # 进度回调
        if progress_callback:
            progress_callback(len(chunks), len(chunks))

        logger.info(f"✅ 分块完成: {len(chunks)} 个chunks")

        # 根据output_mode转换输出格式
        return self._convert_output_format(chunks, output_mode, document_metadata)

    def batch_chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        批量分块多个文档

        Args:
            documents: [{"text": "...", "metadata": {...}}, ...]
            progress_callback: callback(current, total)

        Returns:
            List of chunk lists
        """
        results = []
        total = len(documents)

        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})

            chunks = self.chunk_document(text, metadata, output_mode="dict")
            results.append(chunks)

            if progress_callback:
                progress_callback(i + 1, total)

        logger.info(f"✅ 批量分块完成: {total} 个文档")
        return results

    def get_chunk_preview(
        self,
        chunks: List[Union[Dict, ChunkResult]],
        preview_count: int = 3,
        preview_length: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取chunk预览（用于UI展示）

        Args:
            chunks: chunk列表（Dict或ChunkResult）
            preview_count: 预览数量
            preview_length: 每个预览的文本长度
        """
        previews = []

        for chunk in chunks[:preview_count]:
            # 统一处理Dict和ChunkResult
            if isinstance(chunk, ChunkResult):
                chunk_id = chunk.chunk_id
                text = chunk.text
                start_pos = chunk.start_pos
                end_pos = chunk.end_pos
            else:
                chunk_id = chunk.get("chunk_id", "")
                text = chunk.get("text", "")
                meta = chunk.get("metadata", {})
                start_pos = meta.get("start_pos", 0)
                end_pos = meta.get("end_pos", 0)

            # 截断文本
            preview_text = text if len(text) <= preview_length else text[:preview_length] + "..."

            previews.append({
                "chunk_id": chunk_id,
                "preview": preview_text,
                "length": len(text),
                "position": f"{start_pos}-{end_pos}"
            })

        return previews

    def get_chunking_stats(
        self,
        chunks: List[Union[Dict, ChunkResult]]
    ) -> Dict[str, Any]:
        """
        获取分块统计信息

        Returns:
            {
                "total_chunks": int,
                "avg_chunk_size": float,
                "min_chunk_size": int,
                "max_chunk_size": int,
                "avg_quality_score": float,
                "quality_distribution": {...}
            }
        """
        if not chunks:
            return {"total_chunks": 0}

        # 提取chunk大小
        sizes = []
        quality_scores = []
        quality_levels = []

        for chunk in chunks:
            if isinstance(chunk, ChunkResult):
                sizes.append(len(chunk.text))
                quality_scores.append(chunk.quality_score)
                quality_levels.append(chunk.quality_level.value)
            else:
                text = chunk.get("text", "")
                sizes.append(len(text))
                meta = chunk.get("metadata", {})
                quality_scores.append(meta.get("quality_score", 0))
                quality_levels.append(meta.get("quality_level", "good"))

        # 质量分布统计
        quality_dist = {}
        for level in quality_levels:
            quality_dist[level] = quality_dist.get(level, 0) + 1

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(sizes) / len(sizes) if sizes else 0,
            "min_chunk_size": min(sizes) if sizes else 0,
            "max_chunk_size": max(sizes) if sizes else 0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "quality_distribution": quality_dist
        }

    # ============== Chunking Strategies ==============

    def _chunk_semantic(
        self,
        text: str,
        metadata: Dict[str, Any],
        document_metadata: Optional[Any]
    ) -> List[ChunkResult]:
        """
        语义边界切分策略（默认，按段落和句子）
        这是最智能的策略，保持语义完整性
        """
        # 第一步：按段落分割
        paragraphs = self._split_into_paragraphs(text)
        logger.debug(f"  分割出 {len(paragraphs)} 个段落")

        # 第二步：处理段落，生成chunks
        chunks = []
        current_pos = 0

        for para_idx, paragraph in enumerate(paragraphs):
            para_chunks = self._process_paragraph_semantic(
                paragraph,
                para_idx,
                current_pos,
                metadata
            )
            chunks.extend(para_chunks)
            current_pos += len(paragraph) + 1  # +1 for newline

        return chunks

    def _chunk_fixed(
        self,
        text: str,
        metadata: Dict[str, Any],
        document_metadata: Optional[Any]
    ) -> List[ChunkResult]:
        """
        固定大小切分策略
        按目标大小硬切，不考虑语义边界
        """
        chunks = []
        chunk_size = self.target_chunk_size

        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]
            chunks.append(ChunkResult(
                chunk_id=f"chunk_{len(chunks):04d}",
                text=chunk_text,
                chunk_index=len(chunks),
                total_chunks=0,  # 稍后更新
                start_pos=i,
                end_pos=i + len(chunk_text),
                chunk_type="fixed",
                metadata=metadata.copy()
            ))

        return chunks

    def _chunk_sentence(
        self,
        text: str,
        metadata: Dict[str, Any],
        document_metadata: Optional[Any]
    ) -> List[ChunkResult]:
        """
        句子级切分策略
        每个chunk是完整句子的集合
        """
        # 分割句子
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk_text = ""
        current_start = 0

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 如果添加这句话不超过max_chunk_size
            if len(current_chunk_text) + len(sentence) <= self.max_chunk_size:
                current_chunk_text += sentence
            else:
                # 保存当前chunk
                if current_chunk_text:
                    chunks.append(ChunkResult(
                        chunk_id=f"chunk_{len(chunks):04d}",
                        text=current_chunk_text,
                        chunk_index=len(chunks),
                        total_chunks=0,
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk_text),
                        chunk_type="sentence",
                        metadata=metadata.copy()
                    ))
                    current_start += len(current_chunk_text)

                # 开始新chunk
                current_chunk_text = sentence

        # 保存最后一个chunk
        if current_chunk_text:
            chunks.append(ChunkResult(
                chunk_id=f"chunk_{len(chunks):04d}",
                text=current_chunk_text,
                chunk_index=len(chunks),
                total_chunks=0,
                start_pos=current_start,
                end_pos=current_start + len(current_chunk_text),
                chunk_type="sentence",
                metadata=metadata.copy()
            ))

        return chunks

    def _chunk_sliding(
        self,
        text: str,
        metadata: Dict[str, Any],
        document_metadata: Optional[Any]
    ) -> List[ChunkResult]:
        """
        滑动窗口切分策略
        固定窗口大小，固定步长
        """
        window_size = self.target_chunk_size
        step_size = window_size - self.overlap_size  # 步长 = 窗口 - 重叠

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + window_size, len(text))
            chunk_text = text[start:end]

            chunks.append(ChunkResult(
                chunk_id=f"chunk_{len(chunks):04d}",
                text=chunk_text,
                chunk_index=len(chunks),
                total_chunks=0,
                start_pos=start,
                end_pos=end,
                chunk_type="sliding",
                metadata=metadata.copy()
            ))

            start += step_size

            # 如果剩余文本太短，直接结束
            if len(text) - start < self.min_chunk_size:
                break

        return chunks

    # ============== Helper Methods ==============

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 按双换行或以上分割段落
        paragraphs = re.split(r'\n\s*\n', text)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _split_into_sentences(self, text: str) -> List[str]:
        """按句子分割文本（中文和英文）"""
        # 按句子边界分割（中文和英文句子结束符）
        sentences = re.split(r'([。！？.!?\n])', text)

        # 重新组合句子和标点
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])

        # 如果最后一个元素不是标点，也加上
        if len(sentences) % 2 == 1:
            combined_sentences.append(sentences[-1])

        return [s.strip() for s in combined_sentences if s.strip()]

    def _process_paragraph_semantic(
        self,
        paragraph: str,
        para_idx: int,
        start_pos: int,
        metadata: Dict[str, Any]
    ) -> List[ChunkResult]:
        """
        处理单个段落（语义模式）
        """
        para_len = len(paragraph)

        # 情况1：段落太短，直接作为一个chunk
        if para_len < self.min_chunk_size:
            return [ChunkResult(
                chunk_id="",  # 稍后统一分配
                text=paragraph,
                chunk_index=0,
                total_chunks=0,
                start_pos=start_pos,
                end_pos=start_pos + para_len,
                paragraph_index=para_idx,
                chunk_type="short_paragraph",
                metadata=metadata.copy()
            )]

        # 情况2：段落在目标范围内，直接作为一个chunk
        if self.min_chunk_size <= para_len <= self.max_chunk_size:
            return [ChunkResult(
                chunk_id="",
                text=paragraph,
                chunk_index=0,
                total_chunks=0,
                start_pos=start_pos,
                end_pos=start_pos + para_len,
                paragraph_index=para_idx,
                chunk_type="normal_paragraph",
                metadata=metadata.copy()
            )]

        # 情况3：段落太长，需要按句子边界切分
        return self._split_long_paragraph(paragraph, para_idx, start_pos, metadata)

    def _split_long_paragraph(
        self,
        paragraph: str,
        para_idx: int,
        start_pos: int,
        metadata: Dict[str, Any]
    ) -> List[ChunkResult]:
        """切分长段落 - 按句子边界切分"""
        sentences = self._split_into_sentences(paragraph)

        chunks = []
        current_chunk_text = ""
        current_start = start_pos

        for sentence in sentences:
            # 如果添加这句话不会超过max_chunk_size
            if len(current_chunk_text) + len(sentence) <= self.max_chunk_size:
                current_chunk_text += sentence
            else:
                # 保存当前chunk
                if current_chunk_text:
                    chunks.append(ChunkResult(
                        chunk_id="",
                        text=current_chunk_text,
                        chunk_index=0,
                        total_chunks=0,
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk_text),
                        paragraph_index=para_idx,
                        chunk_type="split_paragraph",
                        metadata=metadata.copy()
                    ))
                    current_start += len(current_chunk_text)

                # 如果单个句子就超过max_chunk_size，强制切分
                if len(sentence) > self.max_chunk_size:
                    # 按字数硬切（最后手段）
                    for i in range(0, len(sentence), self.target_chunk_size):
                        sub_chunk = sentence[i:i + self.target_chunk_size]
                        chunks.append(ChunkResult(
                            chunk_id="",
                            text=sub_chunk,
                            chunk_index=0,
                            total_chunks=0,
                            start_pos=current_start + i,
                            end_pos=current_start + i + len(sub_chunk),
                            paragraph_index=para_idx,
                            chunk_type="forced_split",
                            metadata=metadata.copy()
                        ))
                    current_chunk_text = ""
                    current_start += len(sentence)
                else:
                    current_chunk_text = sentence

        # 保存最后一个chunk
        if current_chunk_text:
            chunks.append(ChunkResult(
                chunk_id="",
                text=current_chunk_text,
                chunk_index=0,
                total_chunks=0,
                start_pos=current_start,
                end_pos=current_start + len(current_chunk_text),
                paragraph_index=para_idx,
                chunk_type="split_paragraph",
                metadata=metadata.copy()
            ))

        return chunks

    def _add_chunk_links(self, chunks: List[ChunkResult]) -> List[ChunkResult]:
        """为每个chunk添加前后链接"""
        total = len(chunks)

        for i, chunk in enumerate(chunks):
            chunk.chunk_id = f"chunk_{i:04d}"
            chunk.chunk_index = i
            chunk.total_chunks = total

            # 添加前后chunk的ID
            chunk.prev_chunk_id = f"chunk_{i-1:04d}" if i > 0 else None
            chunk.next_chunk_id = f"chunk_{i+1:04d}" if i < total - 1 else None

        return chunks

    def _apply_overlap(
        self,
        chunks: List[ChunkResult],
        full_text: str
    ) -> List[ChunkResult]:
        """
        应用chunk overlap（新增功能）
        在每个chunk的开头添加上一个chunk的结尾部分
        """
        if len(chunks) <= 1 or self.overlap_size <= 0:
            return chunks

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # 从上一个chunk的结尾提取overlap文本
            overlap_text = prev_chunk.text[-self.overlap_size:]

            # 添加到当前chunk的开头
            current_chunk.text = overlap_text + current_chunk.text
            current_chunk.start_pos -= len(overlap_text)

            # 在metadata中标记overlap
            current_chunk.metadata["has_overlap"] = True
            current_chunk.metadata["overlap_size"] = len(overlap_text)

        logger.debug(f"  应用overlap: {self.overlap_size}字符，影响{len(chunks)-1}个chunks")
        return chunks

    def _map_timestamps_to_chunks(
        self,
        chunks: List[ChunkResult],
        full_text: str,
        transcript: List[Dict[str, Any]]
    ) -> List[ChunkResult]:
        """
        将Whisper转录的时间戳映射到chunks（v1功能）

        Args:
            chunks: 已切分的chunk列表
            full_text: 完整文本
            transcript: Whisper转录结果 [{"text": "...", "start": 0.0, "end": 4.8}, ...]

        Returns:
            添加了start_sec和end_sec的chunks
        """
        if not transcript:
            return chunks

        try:
            # 构建文本位置到时间戳的映射
            position_to_time = []
            current_pos = 0

            for segment in transcript:
                seg_text = segment.get('text', '').strip()
                seg_start = segment.get('start', 0.0)
                seg_end = segment.get('end', 0.0)

                if not seg_text:
                    continue

                # 在full_text中查找这个segment的位置
                idx = full_text.find(seg_text, current_pos)

                if idx != -1:
                    position_to_time.append({
                        'start_pos': idx,
                        'end_pos': idx + len(seg_text),
                        'start_sec': seg_start,
                        'end_sec': seg_end,
                        'text': seg_text
                    })
                    current_pos = idx + len(seg_text)
                else:
                    logger.debug(f"未找到segment文本: {seg_text[:50]}...")

            logger.info(f"成功映射{len(position_to_time)}个transcript segments到文本位置")

            # 为每个chunk查找对应的时间戳范围
            for chunk in chunks:
                chunk_start_pos = chunk.start_pos
                chunk_end_pos = chunk.end_pos

                # 查找与这个chunk重叠的所有segments
                overlapping_segments = []
                for seg in position_to_time:
                    # 判断是否重叠
                    if not (seg['end_pos'] <= chunk_start_pos or seg['start_pos'] >= chunk_end_pos):
                        overlapping_segments.append(seg)

                if overlapping_segments:
                    # 使用第一个segment的start作为chunk的start_sec
                    # 使用最后一个segment的end作为chunk的end_sec
                    chunk.start_sec = overlapping_segments[0]['start_sec']
                    chunk.end_sec = overlapping_segments[-1]['end_sec']

                    logger.debug(f"Chunk {chunk.chunk_id}: {chunk.start_sec:.2f}s - {chunk.end_sec:.2f}s")

            # 统计成功映射的chunk数量
            mapped_count = sum(1 for c in chunks if c.start_sec is not None)
            logger.info(f"✅ 成功为 {mapped_count}/{len(chunks)} 个chunks映射时间戳")

        except Exception as e:
            logger.error(f"❌ 时间戳映射失败: {e}", exc_info=True)

        return chunks

    def _score_chunk_quality(self, chunks: List[ChunkResult]) -> List[ChunkResult]:
        """
        计算每个chunk的质量评分（新增功能）

        评分维度：
        1. 大小合理性 (30分) - 在目标范围内得高分
        2. 语义完整性 (40分) - 完整段落/句子得高分
        3. 边界清晰度 (20分) - 在自然边界得高分
        4. 文本密度 (10分) - 非空白字符占比

        总分: 0-100
        """
        for chunk in chunks:
            score = 0.0

            # 1. 大小合理性 (30分)
            chunk_len = len(chunk.text)
            if self.min_chunk_size <= chunk_len <= self.max_chunk_size:
                # 在范围内，根据接近target程度评分
                distance = abs(chunk_len - self.target_chunk_size)
                max_distance = max(
                    self.target_chunk_size - self.min_chunk_size,
                    self.max_chunk_size - self.target_chunk_size
                )
                score += 30 * (1 - distance / max_distance)
            elif chunk_len < self.min_chunk_size:
                # 太短，按比例扣分
                score += 30 * (chunk_len / self.min_chunk_size) * 0.6
            else:
                # 太长，固定给低分
                score += 10

            # 2. 语义完整性 (40分)
            chunk_type = chunk.chunk_type
            if chunk_type == "normal_paragraph":
                score += 40  # 完整段落，满分
            elif chunk_type == "short_paragraph":
                score += 35  # 短段落，稍微扣分
            elif chunk_type == "split_paragraph":
                score += 30  # 分割段落，语义可能不完整
            elif chunk_type in ["sentence", "semantic"]:
                score += 35  # 句子级切分，较好
            elif chunk_type == "forced_split":
                score += 15  # 强制切分，语义破坏严重
            else:
                score += 25  # 其他类型，中等分

            # 3. 边界清晰度 (20分)
            text = chunk.text.strip()
            # 检查是否以自然边界开始/结束
            starts_natural = text[0] in '。！？.!?\n' or text[0].isupper() or len(text) < self.min_chunk_size
            ends_natural = text[-1] in '。！？.!?\n'

            if starts_natural and ends_natural:
                score += 20
            elif starts_natural or ends_natural:
                score += 12
            else:
                score += 5

            # 4. 文本密度 (10分)
            non_whitespace = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
            density = non_whitespace / len(text) if len(text) > 0 else 0
            score += 10 * density

            # 限制分数范围
            chunk.quality_score = min(100.0, max(0.0, score))

            # 映射到质量等级
            if chunk.quality_score >= 90:
                chunk.quality_level = ChunkQuality.EXCELLENT
            elif chunk.quality_score >= 70:
                chunk.quality_level = ChunkQuality.GOOD
            elif chunk.quality_score >= 50:
                chunk.quality_level = ChunkQuality.FAIR
            else:
                chunk.quality_level = ChunkQuality.POOR

        return chunks

    def _merge_chunks_to_limit(
        self,
        chunks: List[ChunkResult],
        max_chunks: int
    ) -> List[ChunkResult]:
        """
        如果chunks超过限制，进行合并
        """
        if len(chunks) <= max_chunks:
            return chunks

        # 计算合并比例
        merge_ratio = len(chunks) / max_chunks

        merged_chunks = []
        merge_buffer = []

        for i, chunk in enumerate(chunks):
            merge_buffer.append(chunk)

            # 判断是否完成一个合并chunk
            if len(merge_buffer) >= int(merge_ratio) or i == len(chunks) - 1:
                # 合并文本
                merged_text = "\n".join([c.text for c in merge_buffer])

                # 使用第一个chunk的元数据作为基础
                first_chunk = merge_buffer[0]
                last_chunk = merge_buffer[-1]

                merged = ChunkResult(
                    chunk_id=f"chunk_{len(merged_chunks):04d}",
                    text=merged_text,
                    chunk_index=len(merged_chunks),
                    total_chunks=0,
                    start_pos=first_chunk.start_pos,
                    end_pos=last_chunk.end_pos,
                    paragraph_index=first_chunk.paragraph_index,
                    chunk_type="merged",
                    metadata={
                        **first_chunk.metadata,
                        "merged_from": [c.chunk_id for c in merge_buffer],
                        "merged_count": len(merge_buffer)
                    }
                )

                # 合并时间戳
                if first_chunk.start_sec is not None:
                    merged.start_sec = first_chunk.start_sec
                if last_chunk.end_sec is not None:
                    merged.end_sec = last_chunk.end_sec

                merged_chunks.append(merged)
                merge_buffer = []

        return self._add_chunk_links(merged_chunks)

    def _convert_output_format(
        self,
        chunks: List[ChunkResult],
        output_mode: str,
        document_metadata: Optional[Any]
    ) -> Union[List[Dict[str, Any]], List[ChunkResult], List[Any]]:
        """
        转换输出格式

        Args:
            chunks: ChunkResult列表
            output_mode: "dict" / "result" / "metadata"
            document_metadata: DocumentMetadata对象（metadata模式需要）

        Returns:
            根据模式返回不同格式
        """
        if output_mode == "result":
            # 返回ChunkResult对象
            return chunks

        elif output_mode == "dict":
            # 返回Dict（v1兼容格式）
            return [chunk.to_dict() for chunk in chunks]

        elif output_mode == "metadata":
            # 返回ChunkMetadata对象（v2格式）
            if document_metadata is None:
                logger.warning("output_mode='metadata' 需要document_metadata参数，降级为dict模式")
                return [chunk.to_dict() for chunk in chunks]

            # 需要导入ChunkMetadata
            try:
                from app.schemas.document_metadata import ChunkMetadata

                chunk_metadatas = []
                for chunk in chunks:
                    chunk_meta = ChunkMetadata(
                        document_id=document_metadata.document_id,
                        source_file=document_metadata.source_file,
                        document_type=document_metadata.document_type,
                        source_level=document_metadata.source_level,
                        page_number=document_metadata.page_number,
                        page_range=document_metadata.page_range,
                        timestamp_start=chunk.start_sec if chunk.start_sec is not None else document_metadata.timestamp_start,
                        timestamp_end=chunk.end_sec if chunk.end_sec is not None else document_metadata.timestamp_end,
                        speaker=document_metadata.speaker,
                        chunk_index=chunk.chunk_index,
                        total_chunks=chunk.total_chunks,
                        chunk_id=chunk.chunk_id,
                        prev_chunk_id=chunk.prev_chunk_id,
                        next_chunk_id=chunk.next_chunk_id,
                        char_start=chunk.start_pos,
                        char_end=chunk.end_pos,
                        paragraph_index=chunk.paragraph_index,
                        project_id=document_metadata.project_id,
                        upload_time=document_metadata.upload_time,
                        document_date=document_metadata.document_date,
                        extracted_dates=document_metadata.extracted_dates.copy() if hasattr(document_metadata.extracted_dates, 'copy') else [],
                        text_length=len(chunk.text),
                        language=document_metadata.language,
                        tags=document_metadata.tags.copy() if hasattr(document_metadata.tags, 'copy') else [],
                        keywords=document_metadata.keywords.copy() if hasattr(document_metadata.keywords, 'copy') else [],
                        entities=document_metadata.entities.copy() if hasattr(document_metadata.entities, 'copy') else [],
                        custom_fields={
                            **document_metadata.custom_fields,
                            "text": chunk.text,
                            "chunk_type": chunk.chunk_type,
                            "quality_score": chunk.quality_score,
                            "quality_level": chunk.quality_level.value
                        }
                    )
                    chunk_metadatas.append(chunk_meta)

                return chunk_metadatas

            except ImportError:
                logger.warning("无法导入ChunkMetadata，降级为dict模式")
                return [chunk.to_dict() for chunk in chunks]

        else:
            logger.warning(f"未知output_mode: {output_mode}，使用默认dict模式")
            return [chunk.to_dict() for chunk in chunks]


# ============== Convenience Functions ==============

def create_chunker(
    strategy: Union[str, ChunkStrategy] = ChunkStrategy.SEMANTIC,
    **kwargs
) -> UnifiedDocumentChunker:
    """
    创建文档分块器（工厂函数）

    Args:
        strategy: 分块策略 - "semantic"/"fixed"/"sentence"/"sliding"
        **kwargs: 其他参数传递给UnifiedDocumentChunker

    Returns:
        UnifiedDocumentChunker实例
    """
    if isinstance(strategy, str):
        strategy = ChunkStrategy(strategy)

    return UnifiedDocumentChunker(strategy=strategy, **kwargs)


def chunk_document(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    strategy: str = "semantic",
    min_size: int = 200,
    max_size: int = 500,
    enable_overlap: bool = False,
    overlap_size: int = 50
) -> List[Dict[str, Any]]:
    """
    快捷分块函数（单次使用）

    Args:
        text: 文档文本
        metadata: 元数据
        strategy: 分块策略
        min_size: 最小chunk大小
        max_size: 最大chunk大小
        enable_overlap: 是否启用overlap
        overlap_size: overlap大小

    Returns:
        List[Dict]: chunk列表（Dict格式）
    """
    chunker = create_chunker(
        strategy=strategy,
        min_chunk_size=min_size,
        max_chunk_size=max_size,
        enable_overlap=enable_overlap,
        overlap_size=overlap_size
    )

    return chunker.chunk_document(text, metadata, output_mode="dict")


def batch_chunk_documents(
    documents: List[Dict[str, Any]],
    strategy: str = "semantic",
    **kwargs
) -> List[List[Dict[str, Any]]]:
    """
    批量分块快捷函数

    Args:
        documents: [{"text": "...", "metadata": {...}}, ...]
        strategy: 分块策略
        **kwargs: 其他参数

    Returns:
        List of chunk lists
    """
    chunker = create_chunker(strategy=strategy, **kwargs)
    return chunker.batch_chunk_documents(documents)

