"""
检索质量保证模块 (Retrieval Quality Assurance)

实现多路召回、重排序、结果多样性控制等高级检索策略
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import numpy as np
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    retrieval_method: str  # vector, keyword, bm25, hybrid
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "retrieval_method": self.retrieval_method,
            "rank": self.rank,
            "metadata": self.metadata
        }


@dataclass
class RetrievalMetrics:
    """检索质量指标"""
    total_retrieved: int
    unique_docs: int
    avg_score: float
    min_score: float
    max_score: float
    diversity_score: float  # 结果多样性 0-1
    coverage_score: float   # 覆盖率 0-1
    method_distribution: Dict[str, int]  # 各召回方法的文档数

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_retrieved": self.total_retrieved,
            "unique_docs": self.unique_docs,
            "avg_score": self.avg_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "diversity_score": self.diversity_score,
            "coverage_score": self.coverage_score,
            "method_distribution": self.method_distribution
        }


class KeywordRetriever:
    """
    关键词检索器

    基于关键词匹配的召回策略
    """

    def __init__(self):
        """初始化关键词检索器"""
        self.documents: Dict[str, str] = {}  # doc_id -> content
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)  # word -> doc_ids

    def index_document(self, doc_id: str, content: str):
        """索引文档"""
        self.documents[doc_id] = content

        # 构建倒排索引
        words = self._tokenize(content)
        for word in words:
            self.inverted_index[word].add(doc_id)

    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """
        关键词搜索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        query_words = self._tokenize(query)

        # 计算文档得分
        doc_scores: Dict[str, float] = defaultdict(float)

        for word in query_words:
            if word in self.inverted_index:
                matching_docs = self.inverted_index[word]
                for doc_id in matching_docs:
                    # TF计分
                    doc_content = self.documents[doc_id]
                    doc_words = self._tokenize(doc_content)
                    tf = doc_words.count(word) / len(doc_words) if doc_words else 0

                    # IDF计分
                    idf = np.log(len(self.documents) / len(matching_docs)) if matching_docs else 0

                    doc_scores[doc_id] += tf * idf

        # 排序并返回Top-K
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            results.append(RetrievalResult(
                doc_id=doc_id,
                content=self.documents[doc_id],
                score=score,
                retrieval_method="keyword",
                rank=rank
            ))

        return results

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """分词（简单实现）"""
        # 中文按字分，英文按词分
        words = []

        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        words.extend(english_words)

        # 提取中文字符
        chinese_chars = re.findall(r'[一-鿿]+', text)
        for chars in chinese_chars:
            words.extend(list(chars))

        return words


class BM25Retriever:
    """
    BM25检索器

    基于BM25算法的召回策略
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25检索器

        Args:
            k1: 词频饱和参数
            b: 长度归一化参数
        """
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.term_freq: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def index_document(self, doc_id: str, content: str):
        """索引文档"""
        self.documents[doc_id] = content

        # 分词
        words = self._tokenize(content)
        self.doc_lengths[doc_id] = len(words)

        # 更新平均文档长度
        self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

        # 构建倒排索引和词频统计
        for word in words:
            self.inverted_index[word].add(doc_id)
            self.term_freq[doc_id][word] += 1

    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """
        BM25搜索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        query_words = self._tokenize(query)

        # 计算BM25分数
        doc_scores: Dict[str, float] = defaultdict(float)

        for word in query_words:
            if word not in self.inverted_index:
                continue

            # IDF计算
            df = len(self.inverted_index[word])  # 文档频率
            idf = np.log((len(self.documents) - df + 0.5) / (df + 0.5) + 1.0)

            # 遍历包含该词的文档
            for doc_id in self.inverted_index[word]:
                tf = self.term_freq[doc_id][word]  # 词频
                doc_len = self.doc_lengths[doc_id]

                # BM25公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)

                doc_scores[doc_id] += idf * (numerator / denominator)

        # 排序并返回Top-K
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            results.append(RetrievalResult(
                doc_id=doc_id,
                content=self.documents[doc_id],
                score=score,
                retrieval_method="bm25",
                rank=rank
            ))

        return results

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """分词"""
        words = []
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        words.extend(english_words)
        chinese_chars = re.findall(r'[一-鿿]+', text)
        for chars in chinese_chars:
            words.extend(list(chars))
        return words


class HybridRetriever:
    """
    混合检索器

    融合向量、关键词、BM25多路召回结果
    """

    def __init__(
        self,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.25,
        bm25_weight: float = 0.25
    ):
        """
        初始化混合检索器

        Args:
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            bm25_weight: BM25检索权重
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.bm25_weight = bm25_weight

        # 归一化权重
        total = vector_weight + keyword_weight + bm25_weight
        self.vector_weight /= total
        self.keyword_weight /= total
        self.bm25_weight /= total

    def fuse_results(
        self,
        vector_results: List[RetrievalResult],
        keyword_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult],
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        融合多路召回结果

        使用加权RRF (Reciprocal Rank Fusion) 算法

        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            bm25_results: BM25检索结果
            top_k: 返回数量

        Returns:
            融合后的结果列表
        """
        # 收集所有文档ID
        all_doc_ids: Set[str] = set()

        # 构建排名字典
        vector_ranks = {r.doc_id: r.rank for r in vector_results}
        keyword_ranks = {r.doc_id: r.rank for r in keyword_results}
        bm25_ranks = {r.doc_id: r.rank for r in bm25_results}

        all_doc_ids.update(vector_ranks.keys())
        all_doc_ids.update(keyword_ranks.keys())
        all_doc_ids.update(bm25_ranks.keys())

        # 计算融合分数 (Reciprocal Rank Fusion with weights)
        k = 60  # RRF参数
        doc_scores: Dict[str, float] = {}

        for doc_id in all_doc_ids:
            score = 0.0

            # 向量检索分数
            if doc_id in vector_ranks:
                score += self.vector_weight / (k + vector_ranks[doc_id])

            # 关键词检索分数
            if doc_id in keyword_ranks:
                score += self.keyword_weight / (k + keyword_ranks[doc_id])

            # BM25检索分数
            if doc_id in bm25_ranks:
                score += self.bm25_weight / (k + bm25_ranks[doc_id])

            doc_scores[doc_id] = score

        # 排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 构建结果
        # 获取文档内容（从任一结果列表）
        doc_contents: Dict[str, str] = {}
        for result in vector_results + keyword_results + bm25_results:
            if result.doc_id not in doc_contents:
                doc_contents[result.doc_id] = result.content

        results = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            results.append(RetrievalResult(
                doc_id=doc_id,
                content=doc_contents.get(doc_id, ""),
                score=score,
                retrieval_method="hybrid",
                rank=rank,
                metadata={
                    "in_vector": doc_id in vector_ranks,
                    "in_keyword": doc_id in keyword_ranks,
                    "in_bm25": doc_id in bm25_ranks
                }
            ))

        return results


class DiversityReranker:
    """
    多样性重排序器

    确保检索结果的多样性，避免冗余
    """

    def __init__(self, lambda_param: float = 0.5):
        """
        初始化多样性重排序器

        Args:
            lambda_param: 多样性权重 (0-1)，越大越重视多样性
        """
        self.lambda_param = lambda_param

    def rerank(
        self,
        results: List[RetrievalResult],
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        MMR (Maximal Marginal Relevance) 重排序

        在相关性和多样性之间取得平衡

        Args:
            results: 原始检索结果
            top_k: 返回数量

        Returns:
            重排序后的结果
        """
        if not results:
            return []

        # 已选择的结果
        selected: List[RetrievalResult] = []
        # 候选池
        candidates = results.copy()

        # 第一个选择相关性最高的
        if candidates:
            first = max(candidates, key=lambda x: x.score)
            selected.append(first)
            candidates.remove(first)

        # 迭代选择剩余文档
        while len(selected) < top_k and candidates:
            best_candidate = None
            best_mmr_score = -float('inf')

            for candidate in candidates:
                # 相关性分数（归一化）
                relevance = candidate.score

                # 计算与已选文档的最大相似度
                max_similarity = 0.0
                for selected_doc in selected:
                    similarity = self._calculate_similarity(
                        candidate.content,
                        selected_doc.content
                    )
                    max_similarity = max(max_similarity, similarity)

                # MMR分数
                mmr_score = (
                    self.lambda_param * relevance -
                    (1 - self.lambda_param) * max_similarity
                )

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_candidate = candidate

            if best_candidate:
                selected.append(best_candidate)
                candidates.remove(best_candidate)

        # 更新排名
        for rank, result in enumerate(selected, 1):
            result.rank = rank

        return selected

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """计算文本相似度（简化版Jaccard相似度）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class RetrievalQualityAnalyzer:
    """检索质量分析器"""

    @staticmethod
    def calculate_metrics(results: List[RetrievalResult]) -> RetrievalMetrics:
        """
        计算检索质量指标

        Args:
            results: 检索结果列表

        Returns:
            质量指标
        """
        if not results:
            return RetrievalMetrics(
                total_retrieved=0,
                unique_docs=0,
                avg_score=0.0,
                min_score=0.0,
                max_score=0.0,
                diversity_score=0.0,
                coverage_score=0.0,
                method_distribution={}
            )

        # 基础统计
        total = len(results)
        unique_docs = len(set(r.doc_id for r in results))
        scores = [r.score for r in results]

        # 分数统计
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        # 多样性分数（基于内容相似度）
        diversity_score = RetrievalQualityAnalyzer._calculate_diversity(results)

        # 覆盖率分数（归一化的唯一文档比例）
        coverage_score = unique_docs / total if total > 0 else 0.0

        # 召回方法分布
        method_distribution: Dict[str, int] = defaultdict(int)
        for result in results:
            method_distribution[result.retrieval_method] += 1

        return RetrievalMetrics(
            total_retrieved=total,
            unique_docs=unique_docs,
            avg_score=avg_score,
            min_score=min_score,
            max_score=max_score,
            diversity_score=diversity_score,
            coverage_score=coverage_score,
            method_distribution=dict(method_distribution)
        )

    @staticmethod
    def _calculate_diversity(results: List[RetrievalResult]) -> float:
        """
        计算结果多样性

        基于两两文档的平均相似度，越不相似越多样
        """
        if len(results) < 2:
            return 1.0

        similarities = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                sim = DiversityReranker._calculate_similarity(
                    results[i].content,
                    results[j].content
                )
                similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        diversity = 1.0 - avg_similarity  # 相似度越低，多样性越高

        return diversity

    @staticmethod
    def identify_low_quality_results(
        results: List[RetrievalResult],
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        识别低质量检索结果

        Args:
            results: 检索结果
            score_threshold: 分数阈值

        Returns:
            低质量结果列表
        """
        low_quality = []

        for result in results:
            issues = []

            # 检查分数
            if result.score < score_threshold:
                issues.append(f"低分数: {result.score:.3f}")

            # 检查内容长度
            if len(result.content) < 50:
                issues.append(f"内容过短: {len(result.content)}字符")

            # 检查是否有重复
            duplicate_count = sum(
                1 for r in results
                if r.doc_id != result.doc_id and
                   DiversityReranker._calculate_similarity(r.content, result.content) > 0.8
            )
            if duplicate_count > 0:
                issues.append(f"与{duplicate_count}个文档高度相似")

            if issues:
                low_quality.append({
                    "doc_id": result.doc_id,
                    "rank": result.rank,
                    "score": result.score,
                    "method": result.retrieval_method,
                    "issues": issues
                })

        return low_quality
