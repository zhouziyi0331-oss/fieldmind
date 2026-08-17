"""
语义切分器 - Semantic Chunker
按语义边界切分，而不是机械按字数

原则：
1. 音频：按Whisper的segments（天然语义单元）
2. 文档：按自然段落（\n\n）
3. 保持完整性：不破坏语义
"""

import re
from typing import List, Dict, Any


class SemanticChunker:
    """语义切分器 - 按语义边界切分"""

    @staticmethod
    def chunk_audio_transcript(segments: List[Dict], max_words: int = 500) -> List[Dict]:
        """
        按Whisper segments切分音频转写

        Args:
            segments: Whisper返回的segments列表
            max_words: 单个chunk最大字数

        Returns:
            切分后的chunks，每个包含完整的语义单元
        """
        if not segments:
            return []

        chunks = []
        current_chunk = {
            'text': '',
            'start_sec': None,
            'end_sec': None,
            'segments': []
        }
        current_words = 0

        for segment in segments:
            segment_text = segment.get('text', '').strip()
            segment_words = len(segment_text)

            # 如果是第一个segment
            if current_chunk['start_sec'] is None:
                current_chunk['start_sec'] = segment.get('start', 0)

            # 如果加入这个segment会超过max_words，且当前chunk不为空
            if current_words + segment_words > max_words and current_chunk['text']:
                # 结束当前chunk
                current_chunk['end_sec'] = current_chunk['segments'][-1].get('end', 0)
                chunks.append(current_chunk)

                # 开始新chunk
                current_chunk = {
                    'text': segment_text,
                    'start_sec': segment.get('start', 0),
                    'end_sec': segment.get('end', 0),
                    'segments': [segment]
                }
                current_words = segment_words
            else:
                # 继续累加到当前chunk
                if current_chunk['text']:
                    current_chunk['text'] += ' '
                current_chunk['text'] += segment_text
                current_chunk['segments'].append(segment)
                current_words += segment_words

        # 添加最后一个chunk
        if current_chunk['text']:
            current_chunk['end_sec'] = current_chunk['segments'][-1].get('end', 0)
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def chunk_document_text(text: str, max_words: int = 500) -> List[Dict]:
        """
        按自然段落切分文档文本

        Args:
            text: 文档文本
            max_words: 单个chunk最大字数

        Returns:
            切分后的chunks
        """
        if not text:
            return []

        # 按双换行符切分为段落
        paragraphs = re.split(r'\n\n+', text)

        chunks = []
        current_chunk = ''
        current_words = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_words = len(para)

            # 如果单个段落就超过max_words，按句子切分
            if para_words > max_words:
                sentences = re.split(r'([。！？.!?])', para)
                # 重组句子（保留标点）
                reconstructed = []
                for i in range(0, len(sentences)-1, 2):
                    if i+1 < len(sentences):
                        reconstructed.append(sentences[i] + sentences[i+1])

                for sentence in reconstructed:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    sentence_words = len(sentence)

                    if current_words + sentence_words > max_words and current_chunk:
                        # 结束当前chunk
                        chunks.append({'text': current_chunk})
                        current_chunk = sentence
                        current_words = sentence_words
                    else:
                        if current_chunk:
                            current_chunk += '\n'
                        current_chunk += sentence
                        current_words += sentence_words

            # 如果加入这个段落会超过max_words，且当前chunk不为空
            elif current_words + para_words > max_words and current_chunk:
                # 结束当前chunk
                chunks.append({'text': current_chunk})
                current_chunk = para
                current_words = para_words
            else:
                # 继续累加到当前chunk
                if current_chunk:
                    current_chunk += '\n\n'
                current_chunk += para
                current_words += para_words

        # 添加最后一个chunk
        if current_chunk:
            chunks.append({'text': current_chunk})

        return chunks


class TextCleaner:
    """文本清洗器 - 去除口语填充词、重复句"""

    # 口语填充词
    FILLER_WORDS = [
        '嗯', '啊', '呃', '哦', '诶', '唉',
        '那个', '这个', '就是说', '然后呢', '对吧',
        '你知道', '怎么说呢', '其实吧', '我觉得',
        '基本上', '大概', '可能',
    ]

    @staticmethod
    def clean_filler_words(text: str) -> str:
        """去除填充词"""
        for word in TextCleaner.FILLER_WORDS:
            text = text.replace(word, '')
        return text

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """标点归一化"""
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def remove_excessive_spaces(text: str) -> str:
        """去除多余空格"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def clean(text: str) -> str:
        """完整清洗"""
        if not text:
            return ""

        text = TextCleaner.clean_filler_words(text)
        text = TextCleaner.normalize_punctuation(text)
        text = TextCleaner.remove_excessive_spaces(text)

        return text

    @staticmethod
    def detect_duplicates(texts: List[str], threshold: float = 0.9) -> List[int]:
        """
        检测重复句子

        Returns:
            重复句子的索引列表
        """
        from difflib import SequenceMatcher

        duplicates = []

        for i in range(len(texts)):
            if i in duplicates:
                continue

            for j in range(i+1, len(texts)):
                if j in duplicates:
                    continue

                similarity = SequenceMatcher(None, texts[i], texts[j]).ratio()
                if similarity > threshold:
                    duplicates.append(j)

        return duplicates


if __name__ == "__main__":
    print("=" * 70)
    print("🧩 语义切分器测试")
    print("=" * 70)

    # 测试音频切分
    print("\n[测试1] 音频转写切分")
    test_segments = [
        {'text': '王大爷说杀猪菜是传统美食', 'start': 0.0, 'end': 3.2},
        {'text': '它需要很多道工序', 'start': 3.5, 'end': 6.1},
        {'text': '李婶补充说现在年轻人都不会做了', 'start': 6.5, 'end': 10.2},
    ]

    chunks = SemanticChunker.chunk_audio_transcript(test_segments, max_words=20)
    print(f"原始segments: {len(test_segments)}个")
    print(f"切分后chunks: {len(chunks)}个")
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i+1}:")
        print(f"    文本: {chunk['text']}")
        print(f"    时间: {chunk['start_sec']:.1f}s - {chunk['end_sec']:.1f}s")

    # 测试文档切分
    print("\n[测试2] 文档文本切分")
    test_text = """第一段内容，讲述村里的历史。

第二段内容，介绍传统习俗。

第三段内容，描述现代变化。"""

    chunks = SemanticChunker.chunk_document_text(test_text, max_words=30)
    print(f"切分后chunks: {len(chunks)}个")
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i+1}: {chunk['text'][:50]}...")

    # 测试文本清洗
    print("\n[测试3] 文本清洗")
    dirty_text = "嗯，那个，我觉得这个杀猪菜啊，就是说，是我们村的传统美食，你知道吗？"
    clean_text = TextCleaner.clean(dirty_text)
    print(f"原文: {dirty_text}")
    print(f"清洗后: {clean_text}")

    print("\n" + "=" * 70)
    print("✅ 语义切分器测试完成")
    print("=" * 70)
