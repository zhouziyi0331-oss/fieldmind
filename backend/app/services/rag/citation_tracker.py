"""
精确引用溯源系统 (Precision Citation Traceability System)

实现答案句子到源文档的精确映射、文档片段定位、引用置信度评分
"""
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DocumentFragment:
    """文档片段 - 精确定位源文档中的特定段落"""
    doc_id: str
    content: str
    start_char: int  # 在原文档中的起始字符位置
    end_char: int    # 在原文档中的结束字符位置
    paragraph_index: Optional[int] = None  # 段落索引
    sentence_index: Optional[int] = None   # 句子索引
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "paragraph_index": self.paragraph_index,
            "sentence_index": self.sentence_index,
            "metadata": self.metadata
        }


@dataclass
class Citation:
    """引用 - 答案句子与源文档片段的映射关系"""
    answer_sentence: str
    source_fragment: DocumentFragment
    confidence_score: float  # 0.0-1.0，引用置信度
    similarity_score: float  # 语义相似度
    match_type: str  # exact_match, paraphrase, inference, weak
    evidence_text: str  # 支持该引用的具体证据文本

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "answer_sentence": self.answer_sentence,
            "source_fragment": self.source_fragment.to_dict(),
            "confidence_score": self.confidence_score,
            "similarity_score": self.similarity_score,
            "match_type": self.match_type,
            "evidence_text": self.evidence_text
        }


@dataclass
class AnswerWithCitations:
    """带引用的答案"""
    query: str
    answer: str
    citations: List[Citation]
    overall_confidence: float  # 整体置信度
    coverage_ratio: float  # 答案被引用覆盖的比例
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "overall_confidence": self.overall_confidence,
            "coverage_ratio": self.coverage_ratio,
            "timestamp": self.timestamp.isoformat(),
            "citation_count": len(self.citations),
            "high_confidence_count": sum(1 for c in self.citations if c.confidence_score >= 0.8)
        }


class SentenceSplitter:
    """句子分割器 - 支持中英文"""

    # 中文句子结束标点
    CN_SENTENCE_DELIMITERS = r'[。！？；]'
    # 英文句子结束标点
    EN_SENTENCE_DELIMITERS = r'[.!?;]'

    @classmethod
    def split_sentences(cls, text: str) -> List[Tuple[str, int, int]]:
        """
        分割句子，返回 (句子内容, 起始位置, 结束位置)

        Args:
            text: 输入文本

        Returns:
            句子列表，每个元素为 (sentence, start_char, end_char)
        """
        sentences = []

        # 综合中英文分隔符
        pattern = f'({cls.CN_SENTENCE_DELIMITERS}|{cls.EN_SENTENCE_DELIMITERS})'

        # 使用正则分割，保留分隔符
        parts = re.split(pattern, text)

        current_pos = 0
        current_sentence = ""

        for i, part in enumerate(parts):
            if not part:
                continue

            current_sentence += part

            # 如果是分隔符，结束当前句子
            if re.match(pattern, part):
                sentence = current_sentence.strip()
                if sentence:
                    start = current_pos
                    end = current_pos + len(current_sentence)
                    sentences.append((sentence, start, end))
                    current_pos = end
                current_sentence = ""
            else:
                # 非分隔符部分，继续累积
                pass

        # 处理最后一个句子（可能没有结束标点）
        if current_sentence.strip():
            sentence = current_sentence.strip()
            sentences.append((sentence, current_pos, current_pos + len(current_sentence)))

        return sentences

    @classmethod
    def get_sentence_at_position(cls, text: str, position: int) -> Optional[Tuple[str, int, int]]:
        """
        获取指定位置所在的句子

        Args:
            text: 文本
            position: 字符位置

        Returns:
            (句子, 起始位置, 结束位置) 或 None
        """
        sentences = cls.split_sentences(text)
        for sentence, start, end in sentences:
            if start <= position < end:
                return (sentence, start, end)
        return None


class CitationMatcher:
    """引用匹配器 - 计算答案句子与源文档片段的匹配关系"""

    # 匹配类型阈值
    EXACT_MATCH_THRESHOLD = 0.95
    PARAPHRASE_THRESHOLD = 0.75
    INFERENCE_THRESHOLD = 0.50
    WEAK_THRESHOLD = 0.30

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        使用 SequenceMatcher + 关键词重叠

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0-1.0)
        """
        # 文本归一化
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # SequenceMatcher 相似度
        sequence_sim = SequenceMatcher(None, t1, t2).ratio()

        # 关键词重叠度
        words1 = set(re.findall(r'\w+', t1))
        words2 = set(re.findall(r'\w+', t2))

        if not words1 or not words2:
            return sequence_sim

        keyword_overlap = len(words1 & words2) / len(words1 | words2)

        # 加权平均
        return sequence_sim * 0.6 + keyword_overlap * 0.4

    @classmethod
    def determine_match_type(cls, similarity: float) -> str:
        """
        根据相似度确定匹配类型

        Args:
            similarity: 相似度分数

        Returns:
            匹配类型: exact_match, paraphrase, inference, weak
        """
        if similarity >= cls.EXACT_MATCH_THRESHOLD:
            return "exact_match"
        elif similarity >= cls.PARAPHRASE_THRESHOLD:
            return "paraphrase"
        elif similarity >= cls.INFERENCE_THRESHOLD:
            return "inference"
        elif similarity >= cls.WEAK_THRESHOLD:
            return "weak"
        else:
            return "no_match"

    @classmethod
    def calculate_confidence(
        cls,
        similarity: float,
        match_type: str,
        source_score: float = 1.0
    ) -> float:
        """
        计算引用置信度

        Args:
            similarity: 相似度分数
            match_type: 匹配类型
            source_score: 源文档检索分数（来自向量搜索）

        Returns:
            置信度分数 (0.0-1.0)
        """
        # 基础置信度 = 相似度
        base_confidence = similarity

        # 匹配类型加成
        type_bonus = {
            "exact_match": 0.1,
            "paraphrase": 0.05,
            "inference": 0.0,
            "weak": -0.1,
            "no_match": -0.3
        }

        confidence = base_confidence + type_bonus.get(match_type, 0.0)

        # 结合源文档检索分数
        confidence = confidence * 0.8 + source_score * 0.2

        # 限制在 [0, 1]
        return max(0.0, min(1.0, confidence))

    @classmethod
    def find_best_match(
        cls,
        sentence: str,
        fragments: List[DocumentFragment],
        source_scores: Optional[Dict[str, float]] = None
    ) -> Optional[Tuple[DocumentFragment, float, str, float]]:
        """
        为答案句子找到最佳匹配的源文档片段

        Args:
            sentence: 答案句子
            fragments: 候选文档片段列表
            source_scores: 文档检索分数字典 {doc_id: score}

        Returns:
            (最佳片段, 相似度, 匹配类型, 置信度) 或 None
        """
        if not fragments:
            return None

        source_scores = source_scores or {}
        best_match = None
        best_similarity = 0.0

        for fragment in fragments:
            similarity = cls.calculate_similarity(sentence, fragment.content)

            if similarity > best_similarity:
                best_similarity = similarity
                match_type = cls.determine_match_type(similarity)

                # 获取该文档的检索分数
                doc_score = source_scores.get(fragment.doc_id, 0.8)
                confidence = cls.calculate_confidence(similarity, match_type, doc_score)

                best_match = (fragment, similarity, match_type, confidence)

        # 只返回有意义的匹配（置信度 >= 0.3）
        if best_match and best_match[3] >= 0.3:
            return best_match

        return None


class CitationTracker:
    """
    引用溯源追踪器

    核心功能：
    1. 答案分句与来源映射
    2. 文档片段精确定位
    3. 引用置信度评分
    4. 可视化展示支持
    """

    def __init__(self):
        """初始化引用追踪器"""
        self.sentence_splitter = SentenceSplitter()
        self.citation_matcher = CitationMatcher()

    def create_fragments_from_document(
        self,
        doc_id: str,
        content: str,
        chunk_size: int = 200,
        overlap: int = 50
    ) -> List[DocumentFragment]:
        """
        从文档创建片段列表（用于后续匹配）

        Args:
            doc_id: 文档ID
            content: 文档内容
            chunk_size: 片段大小（字符数）
            overlap: 重叠大小

        Returns:
            文档片段列表
        """
        fragments = []

        # 按句子分割
        sentences = self.sentence_splitter.split_sentences(content)

        # 滑动窗口创建片段
        current_chunk = []
        current_length = 0
        start_char = 0

        for i, (sentence, sent_start, sent_end) in enumerate(sentences):
            sentence_len = len(sentence)

            # 如果当前块会超过大小限制
            if current_length + sentence_len > chunk_size and current_chunk:
                # 保存当前块
                chunk_text = " ".join(current_chunk)
                end_char = start_char + len(chunk_text)

                fragment = DocumentFragment(
                    doc_id=doc_id,
                    content=chunk_text,
                    start_char=start_char,
                    end_char=end_char,
                    metadata={"sentence_count": len(current_chunk)}
                )
                fragments.append(fragment)

                # 计算重叠部分
                if overlap > 0:
                    overlap_chars = 0
                    overlap_sentences = []
                    for sent in reversed(current_chunk):
                        if overlap_chars + len(sent) <= overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_chars += len(sent)
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_length = overlap_chars
                    start_char = end_char - overlap_chars
                else:
                    current_chunk = []
                    current_length = 0
                    start_char = sent_end

            current_chunk.append(sentence)
            current_length += sentence_len

        # 保存最后一块
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            end_char = start_char + len(chunk_text)

            fragment = DocumentFragment(
                doc_id=doc_id,
                content=chunk_text,
                start_char=start_char,
                end_char=end_char,
                metadata={"sentence_count": len(current_chunk)}
            )
            fragments.append(fragment)

        logger.info(f"Created {len(fragments)} fragments from document {doc_id}")
        return fragments

    def track_citations(
        self,
        query: str,
        answer: str,
        source_documents: List[Dict[str, Any]]
    ) -> AnswerWithCitations:
        """
        追踪答案中的引用来源

        Args:
            query: 用户查询
            answer: 生成的答案
            source_documents: 源文档列表，格式:
                [
                    {
                        "doc_id": "doc_001",
                        "content": "文档内容...",
                        "score": 0.95  # 检索相关性分数
                    },
                    ...
                ]

        Returns:
            带引用的答案对象
        """
        # 1. 分割答案为句子
        answer_sentences = self.sentence_splitter.split_sentences(answer)

        # 2. 为每个源文档创建片段
        all_fragments = []
        doc_scores = {}

        for doc in source_documents:
            doc_id = doc["doc_id"]
            content = doc["content"]
            score = doc.get("score", 0.8)

            fragments = self.create_fragments_from_document(doc_id, content)
            all_fragments.extend(fragments)
            doc_scores[doc_id] = score

        # 3. 为每个答案句子找到最佳匹配的源片段
        citations = []

        for sentence, sent_start, sent_end in answer_sentences:
            # 跳过太短的句子
            if len(sentence.strip()) < 10:
                continue

            match_result = self.citation_matcher.find_best_match(
                sentence,
                all_fragments,
                doc_scores
            )

            if match_result:
                fragment, similarity, match_type, confidence = match_result

                citation = Citation(
                    answer_sentence=sentence,
                    source_fragment=fragment,
                    confidence_score=confidence,
                    similarity_score=similarity,
                    match_type=match_type,
                    evidence_text=fragment.content[:150] + "..."  # 截取证据文本
                )
                citations.append(citation)

        # 4. 计算整体指标
        overall_confidence = self._calculate_overall_confidence(citations)
        coverage_ratio = self._calculate_coverage_ratio(answer, citations)

        result = AnswerWithCitations(
            query=query,
            answer=answer,
            citations=citations,
            overall_confidence=overall_confidence,
            coverage_ratio=coverage_ratio
        )

        logger.info(
            f"Tracked {len(citations)} citations for query: {query[:50]}... "
            f"(confidence: {overall_confidence:.2f}, coverage: {coverage_ratio:.2f})"
        )

        return result

    def _calculate_overall_confidence(self, citations: List[Citation]) -> float:
        """计算整体置信度"""
        if not citations:
            return 0.0

        # 使用加权平均，高置信度的权重更大
        total_weight = 0.0
        weighted_sum = 0.0

        for citation in citations:
            weight = citation.confidence_score  # 置信度本身作为权重
            weighted_sum += citation.confidence_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _calculate_coverage_ratio(self, answer: str, citations: List[Citation]) -> float:
        """计算答案被引用覆盖的比例"""
        if not citations:
            return 0.0

        # 统计被引用覆盖的字符数
        covered_chars = sum(len(c.answer_sentence) for c in citations)
        total_chars = len(answer)

        if total_chars == 0:
            return 0.0

        return min(1.0, covered_chars / total_chars)

    def format_for_visualization(
        self,
        answer_with_citations: AnswerWithCitations
    ) -> Dict[str, Any]:
        """
        格式化为可视化展示格式

        为前端提供结构化数据，支持:
        - 答案文本高亮显示
        - 引用来源标注
        - 置信度可视化
        - 源文档片段展示

        Returns:
            可视化数据结构
        """
        # 按答案句子顺序构建高亮信息
        sentences_with_highlights = []

        answer_sentences = self.sentence_splitter.split_sentences(
            answer_with_citations.answer
        )

        # 创建句子到引用的映射
        sentence_to_citation = {
            c.answer_sentence: c for c in answer_with_citations.citations
        }

        for sentence, start, end in answer_sentences:
            citation = sentence_to_citation.get(sentence)

            highlight_info = {
                "text": sentence,
                "start": start,
                "end": end,
                "has_citation": citation is not None
            }

            if citation:
                highlight_info.update({
                    "confidence": citation.confidence_score,
                    "match_type": citation.match_type,
                    "source_doc_id": citation.source_fragment.doc_id,
                    "source_start": citation.source_fragment.start_char,
                    "source_end": citation.source_fragment.end_char,
                    "evidence": citation.evidence_text,
                    "color": self._get_confidence_color(citation.confidence_score)
                })

            sentences_with_highlights.append(highlight_info)

        # 按文档聚合引用
        sources_grouped = {}
        for citation in answer_with_citations.citations:
            doc_id = citation.source_fragment.doc_id
            if doc_id not in sources_grouped:
                sources_grouped[doc_id] = []
            sources_grouped[doc_id].append(citation)

        # 构建源文档列表
        sources_list = []
        for doc_id, doc_citations in sources_grouped.items():
            avg_confidence = sum(c.confidence_score for c in doc_citations) / len(doc_citations)

            sources_list.append({
                "doc_id": doc_id,
                "citation_count": len(doc_citations),
                "avg_confidence": avg_confidence,
                "citations": [
                    {
                        "answer_sentence": c.answer_sentence,
                        "source_text": c.source_fragment.content,
                        "start_char": c.source_fragment.start_char,
                        "end_char": c.source_fragment.end_char,
                        "confidence": c.confidence_score,
                        "match_type": c.match_type
                    }
                    for c in doc_citations
                ]
            })

        return {
            "query": answer_with_citations.query,
            "answer": {
                "text": answer_with_citations.answer,
                "sentences": sentences_with_highlights
            },
            "overall_metrics": {
                "confidence": answer_with_citations.overall_confidence,
                "coverage": answer_with_citations.coverage_ratio,
                "total_citations": len(answer_with_citations.citations),
                "high_confidence_citations": sum(
                    1 for c in answer_with_citations.citations
                    if c.confidence_score >= 0.8
                )
            },
            "sources": sources_list,
            "timestamp": answer_with_citations.timestamp.isoformat()
        }

    @staticmethod
    def _get_confidence_color(confidence: float) -> str:
        """根据置信度返回颜色代码（用于前端高亮）"""
        if confidence >= 0.8:
            return "#4CAF50"  # 绿色 - 高置信度
        elif confidence >= 0.6:
            return "#FFC107"  # 黄色 - 中等置信度
        elif confidence >= 0.4:
            return "#FF9800"  # 橙色 - 低置信度
        else:
            return "#F44336"  # 红色 - 非常低置信度
