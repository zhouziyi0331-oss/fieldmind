"""
文本分块器
将长文本分割成合适大小的块
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class TextChunk:
    """文本块"""
    content: str
    sequence: int
    token_count: int
    start_index: int
    end_index: int
    metadata: Dict[str, Any]

    # 添加属性别名，兼容旧代码
    @property
    def chunk_index(self):
        return self.sequence


class TextChunker:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        初始化分块器

        Args:
            chunk_size: 块大小（token数）
            chunk_overlap: 块重叠（token数）
            separators: 分隔符列表（优先级从高到低）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 行
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            ".",     # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 分号
            ",",     # 逗号
            " ",     # 空格
            ""       # 字符
        ]

    def chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        分块文本

        Args:
            text: 文本内容
            metadata: 额外元数据

        Returns:
            List[TextChunk]: 文本块列表
        """
        if not text or not text.strip():
            return []

        logger.info(f"开始分块: 文本长度={len(text)}, 块大小={self.chunk_size}")

        # 清理文本
        text = self._clean_text(text)

        # 递归分块
        chunks = self._split_text(text, self.separators)

        # 创建 TextChunk 对象
        result = []
        current_position = 0

        for i, chunk_text in enumerate(chunks):
            # 估算 token 数（简单方法：中文按字符数，英文按词数）
            token_count = self._estimate_tokens(chunk_text)

            # 查找在原文本中的位置
            start_index = text.find(chunk_text, current_position)
            end_index = start_index + len(chunk_text) if start_index != -1 else -1

            chunk = TextChunk(
                content=chunk_text,
                sequence=i,
                token_count=token_count,
                start_index=start_index,
                end_index=end_index,
                metadata=metadata or {}
            )

            result.append(chunk)

            if start_index != -1:
                current_position = start_index + 1

        logger.info(f"分块完成: 生成 {len(result)} 个块")

        return result

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)

        # 移除首尾空白
        text = text.strip()

        return text

    def _split_text(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """
        递归分割文本

        Args:
            text: 文本内容
            separators: 分隔符列表

        Returns:
            List[str]: 文本块列表
        """
        if not separators:
            # 没有分隔符了，按固定大小切分
            return self._split_by_size(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if not separator:
            # 空分隔符，按字符切分
            return self._split_by_size(text)

        # 按当前分隔符切分
        splits = text.split(separator)

        # 重新组合，保持分隔符
        result = []
        current_chunk = ""

        for i, split in enumerate(splits):
            # 添加分隔符（除了最后一个）
            if i < len(splits) - 1:
                split = split + separator

            # 检查是否需要进一步切分
            if self._estimate_tokens(split) > self.chunk_size:
                # 太大，需要继续切分
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = ""

                # 递归切分
                sub_chunks = self._split_text(split, remaining_separators)
                result.extend(sub_chunks)

            else:
                # 尝试合并
                test_chunk = current_chunk + split

                if self._estimate_tokens(test_chunk) <= self.chunk_size:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        result.append(current_chunk)
                    current_chunk = split

        # 添加最后一个块
        if current_chunk:
            result.append(current_chunk)

        return result

    def _split_by_size(self, text: str) -> List[str]:
        """
        按固定大小切分文本

        Args:
            text: 文本内容

        Returns:
            List[str]: 文本块列表
        """
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # 计算结束位置（考虑重叠）
            end_pos = current_pos + self.chunk_size

            if end_pos >= len(text):
                # 最后一块
                chunks.append(text[current_pos:])
                break
            else:
                chunks.append(text[current_pos:end_pos])
                # 下一块的起始位置（考虑重叠）
                current_pos = end_pos - self.chunk_overlap

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """
        估算 token 数量

        简单方法：
        - 中文：每个字符算1个 token
        - 英文：每个词算1个 token

        Args:
            text: 文本内容

        Returns:
            int: token 数量
        """
        # 统计中文字符
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')

        # 统计英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

        # 总 token 数
        return chinese_chars + english_words


class SemanticChunker:
    """
    语义分块器

    基于语义相似度进行分块，保持语义连贯性
    """

    def __init__(
        self,
        chunk_size: int = 500,
        similarity_threshold: float = 0.7
    ):
        """
        初始化语义分块器

        Args:
            chunk_size: 块大小
            similarity_threshold: 相似度阈值
        """
        self.chunk_size = chunk_size
        self.similarity_threshold = similarity_threshold

    def chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        语义分块

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            List[TextChunk]: 文本块列表
        """
        # TODO: 实现基于语义的分块
        # 1. 将文本分割成句子
        # 2. 为每个句子生成向量
        # 3. 计算句子间的相似度
        # 4. 根据相似度合并句子成块

        # 暂时使用简单的分块器
        simple_chunker = TextChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=50
        )

        return simple_chunker.chunk(text, metadata)


class MarkdownChunker:
    """
    Markdown 分块器

    基于 Markdown 结构（标题、段落）进行分块
    """

    def __init__(self, chunk_size: int = 500):
        """
        初始化 Markdown 分块器

        Args:
            chunk_size: 块大小
        """
        self.chunk_size = chunk_size

    def chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        按 Markdown 结构分块

        Args:
            text: Markdown 文本
            metadata: 元数据

        Returns:
            List[TextChunk]: 文本块列表
        """
        chunks = []
        current_chunk = ""
        current_heading = ""
        sequence = 0

        lines = text.split('\n')

        for line in lines:
            # 检查是否是标题
            if line.startswith('#'):
                # 保存当前块
                if current_chunk.strip():
                    token_count = self._estimate_tokens(current_chunk)
                    chunks.append(TextChunk(
                        content=current_chunk.strip(),
                        sequence=sequence,
                        token_count=token_count,
                        start_index=-1,
                        end_index=-1,
                        metadata={
                            **(metadata or {}),
                            "heading": current_heading
                        }
                    ))
                    sequence += 1
                    current_chunk = ""

                # 更新当前标题
                current_heading = line.strip()
                current_chunk = line + "\n"

            else:
                current_chunk += line + "\n"

                # 检查是否超过大小限制
                if self._estimate_tokens(current_chunk) >= self.chunk_size:
                    token_count = self._estimate_tokens(current_chunk)
                    chunks.append(TextChunk(
                        content=current_chunk.strip(),
                        sequence=sequence,
                        token_count=token_count,
                        start_index=-1,
                        end_index=-1,
                        metadata={
                            **(metadata or {}),
                            "heading": current_heading
                        }
                    ))
                    sequence += 1
                    current_chunk = ""

        # 添加最后一块
        if current_chunk.strip():
            token_count = self._estimate_tokens(current_chunk)
            chunks.append(TextChunk(
                content=current_chunk.strip(),
                sequence=sequence,
                token_count=token_count,
                start_index=-1,
                end_index=-1,
                metadata={
                    **(metadata or {}),
                    "heading": current_heading
                }
            ))

        logger.info(f"Markdown 分块完成: 生成 {len(chunks)} 个块")

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """估算 token 数量"""
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return chinese_chars + english_words
