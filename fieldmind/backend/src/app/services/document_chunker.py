"""
文档切分服务 - 按语义边界切分长文本
核心：不是硬切字数，而是保持语义完整性
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentChunker:
    """文档切分器 - 智能切分长文本"""

    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        target_chunk_size: int = 350,
        overlap_size: int = 50
    ):
        """
        Args:
            min_chunk_size: 最小chunk大小（字符数）
            max_chunk_size: 最大chunk大小（字符数）
            target_chunk_size: 目标chunk大小
            overlap_size: chunk之间的重叠大小（保持上下文连贯）
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None  # ⭐⭐⭐ 新增 sources 参数
    ) -> List[Dict[str, Any]]:
        """
        切分文档为多个语义块

        Args:
            text: 文档文本
            metadata: 元数据
            sources: 结构化数据源（表格行、音频 segments 等）⭐ 新增

        Returns:
            List of chunks: [
                {
                    "chunk_id": "chunk_001",
                    "text": "chunk内容",
                    "metadata": {
                        "start_pos": 0,
                        "end_pos": 350,
                        "paragraph_index": 1,
                        "start_sec": 0.0,  # 音频时间戳（如果有）
                        "end_sec": 4.8,
                        "structured_data": {...},  # ⭐ 表格结构化数据
                        ...原始metadata
                    },
                    "prev_chunk_id": "chunk_000",
                    "next_chunk_id": "chunk_002"
                }
            ]
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        sources = sources or []  # ⭐ 确保 sources 不为 None

        # ⭐⭐⭐ 新增：如果有 sources，使用结构化切块
        if sources:
            logger.info(f"🔍 检测到 {len(sources)} 个 sources，使用结构化切块")
            from app.services.document_chunker_sources import chunk_with_sources
            return chunk_with_sources(text, metadata, sources)

        # 原有逻辑：普通文本切块
        # 第一步：按段落分割
        paragraphs = self._split_into_paragraphs(text)

        # 第二步：处理段落，生成chunks
        chunks = []
        current_pos = 0

        for para_idx, paragraph in enumerate(paragraphs):
            para_chunks = self._process_paragraph(
                paragraph,
                para_idx,
                current_pos,
                metadata
            )
            chunks.extend(para_chunks)
            current_pos += len(paragraph) + 1  # +1 for newline

        # 第三步：添加chunk间的链接关系
        chunks = self._add_chunk_links(chunks)

        # ===== 新增：第四步：映射音频时间戳 =====
        if metadata.get('transcript'):
            logger.info(f"检测到transcript数据，开始映射时间戳到chunks")
            chunks = self._map_timestamps_to_chunks(chunks, text, metadata['transcript'])
        # ===== 结束 =====

        # 第五步：限制chunk总数（防止超大文档）
        if len(chunks) > 500:
            logger.warning(f"文档切分产生{len(chunks)}个chunks，超过限制，进行合并")
            chunks = self._merge_chunks_to_limit(chunks, max_chunks=500)

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本
        段落边界：连续的换行符
        """
        # 先标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 按双换行或以上分割段落
        paragraphs = re.split(r'\n\s*\n', text)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _process_paragraph(
        self,
        paragraph: str,
        para_idx: int,
        start_pos: int,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        处理单个段落，返回切分后的chunks
        """
        para_len = len(paragraph)

        # 情况1：段落太短，直接作为一个chunk
        if para_len < self.min_chunk_size:
            return [{
                "text": paragraph,
                "metadata": {
                    **base_metadata,
                    "start_pos": start_pos,
                    "end_pos": start_pos + para_len,
                    "paragraph_index": para_idx,
                    "chunk_type": "short_paragraph"
                }
            }]

        # 情况2：段落在目标范围内，直接作为一个chunk
        if self.min_chunk_size <= para_len <= self.max_chunk_size:
            return [{
                "text": paragraph,
                "metadata": {
                    **base_metadata,
                    "start_pos": start_pos,
                    "end_pos": start_pos + para_len,
                    "paragraph_index": para_idx,
                    "chunk_type": "normal_paragraph"
                }
            }]

        # 情况3：段落太长，需要按句子边界切分
        return self._split_long_paragraph(
            paragraph,
            para_idx,
            start_pos,
            base_metadata
        )

    def _split_long_paragraph(
        self,
        paragraph: str,
        para_idx: int,
        start_pos: int,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        切分长段落 - 按句子边界切分
        """
        # 按句子边界分割（中文和英文句子结束符）
        sentences = re.split(r'([。！？.!?\n])', paragraph)

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

        # 合并句子为chunks
        chunks = []
        current_chunk = ""
        current_start = start_pos

        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 如果添加这句话不会超过max_chunk_size，就继续添加
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                # 当前chunk已满，保存并开始新chunk
                if current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "metadata": {
                            **base_metadata,
                            "start_pos": current_start,
                            "end_pos": current_start + len(current_chunk),
                            "paragraph_index": para_idx,
                            "chunk_type": "split_paragraph"
                        }
                    })
                    current_start += len(current_chunk)

                # 如果单个句子就超过max_chunk_size，强制切分
                if len(sentence) > self.max_chunk_size:
                    # 按字数硬切（最后手段）
                    for i in range(0, len(sentence), self.target_chunk_size):
                        sub_chunk = sentence[i:i + self.target_chunk_size]
                        chunks.append({
                            "text": sub_chunk,
                            "metadata": {
                                **base_metadata,
                                "start_pos": current_start + i,
                                "end_pos": current_start + i + len(sub_chunk),
                                "paragraph_index": para_idx,
                                "chunk_type": "forced_split"
                            }
                        })
                    current_chunk = ""
                    current_start += len(sentence)
                else:
                    current_chunk = sentence

        # 保存最后一个chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "metadata": {
                    **base_metadata,
                    "start_pos": current_start,
                    "end_pos": current_start + len(current_chunk),
                    "paragraph_index": para_idx,
                    "chunk_type": "split_paragraph"
                }
            })

        return chunks

    def _add_chunk_links(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为每个chunk添加前后链接
        """
        for i, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"chunk_{i:04d}"
            chunk["chunk_index"] = i
            chunk["total_chunks"] = len(chunks)

            # 添加前后chunk的ID
            if i > 0:
                chunk["prev_chunk_id"] = f"chunk_{i-1:04d}"
            else:
                chunk["prev_chunk_id"] = None

            if i < len(chunks) - 1:
                chunk["next_chunk_id"] = f"chunk_{i+1:04d}"
            else:
                chunk["next_chunk_id"] = None

        return chunks

    def _merge_chunks_to_limit(
        self,
        chunks: List[Dict[str, Any]],
        max_chunks: int = 500
    ) -> List[Dict[str, Any]]:
        """
        如果chunks超过限制，进行合并
        """
        if len(chunks) <= max_chunks:
            return chunks

        # 计算合并比例
        merge_ratio = len(chunks) / max_chunks

        merged_chunks = []
        current_merged = None

        for i, chunk in enumerate(chunks):
            if current_merged is None:
                current_merged = chunk.copy()
            else:
                # 合并文本
                current_merged["text"] += "\n" + chunk["text"]
                # 更新end_pos
                current_merged["metadata"]["end_pos"] = chunk["metadata"]["end_pos"]

            # 判断是否完成一个合并chunk
            if (i + 1) % int(merge_ratio) == 0 or i == len(chunks) - 1:
                merged_chunks.append(current_merged)
                current_merged = None

        return self._add_chunk_links(merged_chunks)

    def get_chunk_preview(
        self,
        chunks: List[Dict[str, Any]],
        preview_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取chunk预览（用于UI展示）
        """
        previews = []
        for chunk in chunks[:preview_count]:
            preview_text = chunk["text"]
            if len(preview_text) > 100:
                preview_text = preview_text[:100] + "..."

            previews.append({
                "chunk_id": chunk["chunk_id"],
                "preview": preview_text,
                "length": len(chunk["text"]),
                "position": f"{chunk['metadata']['start_pos']}-{chunk['metadata']['end_pos']}"
            })

        return previews

    def _map_timestamps_to_chunks(
        self,
        chunks: List[Dict[str, Any]],
        full_text: str,
        transcript: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        将Whisper转录的时间戳映射到chunks

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
            # Whisper的segments是按顺序的，每个segment有text、start、end
            position_to_time = []
            current_pos = 0

            for segment in transcript:
                seg_text = segment.get('text', '').strip()
                seg_start = segment.get('start', 0.0)
                seg_end = segment.get('end', 0.0)

                if not seg_text:
                    continue

                # 在full_text中查找这个segment的位置
                # 注意：Whisper的text可能和原文有细微差异
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
                    # 如果找不到精确匹配，记录警告但继续
                    logger.debug(f"未找到segment文本: {seg_text[:50]}...")

            logger.info(f"成功映射{len(position_to_time)}个transcript segments到文本位置")

            # 为每个chunk查找对应的时间戳范围
            for chunk in chunks:
                chunk_start_pos = chunk['metadata'].get('start_pos', 0)
                chunk_end_pos = chunk['metadata'].get('end_pos', 0)

                # 查找与这个chunk重叠的所有segments
                overlapping_segments = []
                for seg in position_to_time:
                    # 判断是否重叠
                    if not (seg['end_pos'] <= chunk_start_pos or seg['start_pos'] >= chunk_end_pos):
                        overlapping_segments.append(seg)

                if overlapping_segments:
                    # 使用第一个segment的start作为chunk的start_sec
                    # 使用最后一个segment的end作为chunk的end_sec
                    chunk['metadata']['start_sec'] = overlapping_segments[0]['start_sec']
                    chunk['metadata']['end_sec'] = overlapping_segments[-1]['end_sec']

                    logger.debug(f"Chunk {chunk.get('chunk_id')}: {chunk['metadata']['start_sec']:.2f}s - {chunk['metadata']['end_sec']:.2f}s")

            # 统计成功映射的chunk数量
            mapped_count = sum(1 for c in chunks if c['metadata'].get('start_sec') is not None)
            logger.info(f"✅ 成功为 {mapped_count}/{len(chunks)} 个chunks映射时间戳")

        except Exception as e:
            logger.error(f"❌ 时间戳映射失败: {e}", exc_info=True)

        return chunks

