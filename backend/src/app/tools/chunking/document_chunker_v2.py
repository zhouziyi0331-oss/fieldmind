"""
文档切分服务 v2 - 链路十四改造版
核心改进：每个chunk继承完整的父文档元数据，确保可精确溯源
"""

import re
from typing import List, Dict, Any, Optional
import logging

from app.schemas.document_metadata import DocumentMetadata, ChunkMetadata

logger = logging.getLogger(__name__)


class DocumentChunkerV2:
    """文档切分器 v2 - 元数据完整版"""

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
        document_metadata: DocumentMetadata
    ) -> List[ChunkMetadata]:
        """
        切分文档为多个语义块（链路十四核心方法）

        Args:
            text: 文档文本
            document_metadata: 父文档的完整元数据

        Returns:
            List[ChunkMetadata]: 每个chunk都继承了父文档的元数据
        """
        if not text or not text.strip():
            logger.warning(f"文档 {document_metadata.document_id} 文本为空")
            return []

        logger.info(f"📄 开始切分文档: {document_metadata.source_file} (type={document_metadata.document_type.value})")

        # 第一步：按段落分割
        paragraphs = self._split_into_paragraphs(text)
        logger.debug(f"  分割出 {len(paragraphs)} 个段落")

        # 第二步：处理段落，生成chunks
        chunks = []
        current_pos = 0

        for para_idx, paragraph in enumerate(paragraphs):
            para_chunks = self._process_paragraph(
                paragraph,
                para_idx,
                current_pos,
                document_metadata
            )
            chunks.extend(para_chunks)
            current_pos += len(paragraph) + 1  # +1 for newline

        # 第三步：添加chunk间的链接关系
        chunks = self._add_chunk_links(chunks)

        # 第四步：限制chunk总数（防止超大文档）
        if len(chunks) > 500:
            logger.warning(f"文档切分产生{len(chunks)}个chunks，超过限制，进行合并")
            chunks = self._merge_chunks_to_limit(chunks, max_chunks=500)

        logger.info(f"✅ 切分完成: {len(chunks)} 个chunks")

        # 第五步：验证元数据完整性
        self._validate_chunks(chunks)

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 标准化换行符
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
        document_metadata: DocumentMetadata
    ) -> List[ChunkMetadata]:
        """
        处理单个段落，返回切分后的chunks（带完整元数据）
        """
        para_len = len(paragraph)

        # 情况1：段落太短，直接作为一个chunk
        if para_len < self.min_chunk_size:
            return [self._create_chunk_metadata(
                text=paragraph,
                chunk_index=0,  # 临时索引，后续会重新分配
                start_pos=start_pos,
                end_pos=start_pos + para_len,
                para_idx=para_idx,
                chunk_type="short_paragraph",
                document_metadata=document_metadata
            )]

        # 情况2：段落在目标范围内，直接作为一个chunk
        if self.min_chunk_size <= para_len <= self.max_chunk_size:
            return [self._create_chunk_metadata(
                text=paragraph,
                chunk_index=0,
                start_pos=start_pos,
                end_pos=start_pos + para_len,
                para_idx=para_idx,
                chunk_type="normal_paragraph",
                document_metadata=document_metadata
            )]

        # 情况3：段落太长，需要按句子边界切分
        return self._split_long_paragraph(
            paragraph,
            para_idx,
            start_pos,
            document_metadata
        )

    def _split_long_paragraph(
        self,
        paragraph: str,
        para_idx: int,
        start_pos: int,
        document_metadata: DocumentMetadata
    ) -> List[ChunkMetadata]:
        """切分长段落 - 按句子边界切分"""
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
        current_chunk_text = ""
        current_start = start_pos

        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 如果添加这句话不会超过max_chunk_size，就继续添加
            if len(current_chunk_text) + len(sentence) <= self.max_chunk_size:
                current_chunk_text += sentence
            else:
                # 当前chunk已满，保存并开始新chunk
                if current_chunk_text:
                    chunks.append(self._create_chunk_metadata(
                        text=current_chunk_text,
                        chunk_index=len(chunks),
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk_text),
                        para_idx=para_idx,
                        chunk_type="split_paragraph",
                        document_metadata=document_metadata
                    ))
                    current_start += len(current_chunk_text)

                # 如果单个句子就超过max_chunk_size，强制切分
                if len(sentence) > self.max_chunk_size:
                    # 按字数硬切（最后手段）
                    for i in range(0, len(sentence), self.target_chunk_size):
                        sub_chunk = sentence[i:i + self.target_chunk_size]
                        chunks.append(self._create_chunk_metadata(
                            text=sub_chunk,
                            chunk_index=len(chunks),
                            start_pos=current_start + i,
                            end_pos=current_start + i + len(sub_chunk),
                            para_idx=para_idx,
                            chunk_type="forced_split",
                            document_metadata=document_metadata
                        ))
                    current_chunk_text = ""
                    current_start += len(sentence)
                else:
                    current_chunk_text = sentence

        # 保存最后一个chunk
        if current_chunk_text:
            chunks.append(self._create_chunk_metadata(
                text=current_chunk_text,
                chunk_index=len(chunks),
                start_pos=current_start,
                end_pos=current_start + len(current_chunk_text),
                para_idx=para_idx,
                chunk_type="split_paragraph",
                document_metadata=document_metadata
            ))

        return chunks

    def _create_chunk_metadata(
        self,
        text: str,
        chunk_index: int,
        start_pos: int,
        end_pos: int,
        para_idx: int,
        chunk_type: str,
        document_metadata: DocumentMetadata
    ) -> ChunkMetadata:
        """
        创建chunk元数据对象（链路十四核心：继承父文档元数据）

        这是确保引用溯源的关键：每个chunk都知道自己来自哪个文件、哪一页、哪个时间段
        """
        # 复制父文档元数据的所有字段
        chunk_meta = ChunkMetadata(
            # 继承父文档的必填字段
            document_id=document_metadata.document_id,
            source_file=document_metadata.source_file,
            document_type=document_metadata.document_type,
            source_level=document_metadata.source_level,

            # 继承位置信息
            page_number=document_metadata.page_number,
            page_range=document_metadata.page_range,
            timestamp_start=document_metadata.timestamp_start,
            timestamp_end=document_metadata.timestamp_end,
            timestamp_range=document_metadata.timestamp_range,
            speaker=document_metadata.speaker,
            speaker_confidence=document_metadata.speaker_confidence,

            # Chunk特有字段
            chunk_index=chunk_index,
            total_chunks=0,  # 暂时设为0，后续统一更新
            char_start=start_pos,
            char_end=end_pos,
            paragraph_index=para_idx,

            # 继承项目关联
            project_id=document_metadata.project_id,

            # 继承时间信息
            upload_time=document_metadata.upload_time,
            document_date=document_metadata.document_date,
            extracted_dates=document_metadata.extracted_dates.copy(),

            # 继承内容特征
            text_length=len(text),
            language=document_metadata.language,

            # 继承扩展字段
            tags=document_metadata.tags.copy(),
            keywords=document_metadata.keywords.copy(),
            entities=document_metadata.entities.copy(),
            custom_fields={
                **document_metadata.custom_fields,
                "chunk_type": chunk_type,
                "text": text  # 存储文本内容
            }
        )

        return chunk_meta

    def _add_chunk_links(self, chunks: List[ChunkMetadata]) -> List[ChunkMetadata]:
        """
        为每个chunk添加前后链接，并更新total_chunks
        """
        total = len(chunks)

        for i, chunk in enumerate(chunks):
            # 更新chunk索引和总数
            chunk.chunk_index = i
            chunk.total_chunks = total
            chunk.chunk_id = f"doc{chunk.document_id}_chunk{i:04d}"

            # 添加前后chunk的ID
            if i > 0:
                chunk.prev_chunk_id = f"doc{chunk.document_id}_chunk{i-1:04d}"
            else:
                chunk.prev_chunk_id = None

            if i < total - 1:
                chunk.next_chunk_id = f"doc{chunk.document_id}_chunk{i+1:04d}"
            else:
                chunk.next_chunk_id = None

        return chunks

    def _merge_chunks_to_limit(
        self,
        chunks: List[ChunkMetadata],
        max_chunks: int = 500
    ) -> List[ChunkMetadata]:
        """
        如果chunks超过限制，进行合并（保持元数据完整性）
        """
        if len(chunks) <= max_chunks:
            return chunks

        logger.warning(f"⚠️ Chunks数量({len(chunks)})超过限制，合并至{max_chunks}个")

        # 计算合并比例
        merge_ratio = len(chunks) / max_chunks

        merged_chunks = []
        current_merged = None
        merge_buffer = []

        for i, chunk in enumerate(chunks):
            merge_buffer.append(chunk)

            # 判断是否完成一个合并chunk
            if len(merge_buffer) >= int(merge_ratio) or i == len(chunks) - 1:
                # 合并文本
                merged_text = "\n".join([c.custom_fields.get("text", "") for c in merge_buffer])

                # 使用第一个chunk的元数据作为基础
                first_chunk = merge_buffer[0]
                last_chunk = merge_buffer[-1]

                merged_meta = ChunkMetadata(
                    document_id=first_chunk.document_id,
                    source_file=first_chunk.source_file,
                    document_type=first_chunk.document_type,
                    source_level=first_chunk.source_level,
                    page_number=first_chunk.page_number,
                    timestamp_start=first_chunk.timestamp_start,
                    timestamp_end=last_chunk.timestamp_end,  # 使用最后一个的结束时间
                    speaker=first_chunk.speaker,
                    char_start=first_chunk.char_start,
                    char_end=last_chunk.char_end,
                    project_id=first_chunk.project_id,
                    text_length=len(merged_text),
                    custom_fields={
                        **first_chunk.custom_fields,
                        "text": merged_text,
                        "merged_from": [c.chunk_id for c in merge_buffer]
                    }
                )

                merged_chunks.append(merged_meta)
                merge_buffer = []

        return self._add_chunk_links(merged_chunks)

    def _validate_chunks(self, chunks: List[ChunkMetadata]):
        """验证所有chunks的元数据完整性"""
        for i, chunk in enumerate(chunks):
            errors = chunk.validate()
            if errors:
                logger.warning(f"⚠️ Chunk {i} 元数据不完整: {', '.join(errors)}")


def get_document_chunker_v2() -> DocumentChunkerV2:
    """获取文档切分器单例"""
    return DocumentChunkerV2()
