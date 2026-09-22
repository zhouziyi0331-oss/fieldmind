"""
BM25 稀疏检索实现

基于 BM25 算法的关键词检索
"""

import math
from typing import List, Dict, Set
from collections import Counter
import numpy as np


class BM25Retriever:
    """BM25 检索器

    实现 BM25 算法进行关键词匹配
    用于混合检索的稀疏检索部分

    特性：
    - 经典 BM25 算法
    - 支持中英文分词
    - TF-IDF 变体
    - 文档长度归一化

    参数：
        k1: 词频饱和参数 (默认 1.5)
        b: 文档长度归一化参数 (默认 0.75)
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        language: str = "zh"  # zh 或 en
    ):
        """初始化 BM25 检索器

        Args:
            k1: 词频饱和参数，控制词频的影响
            b: 长度归一化参数，0=不归一化，1=完全归一化
            language: 语言类型（zh/en）
        """
        self.k1 = k1
        self.b = b
        self.language = language

        # 文档数据
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0

        # IDF 数据
        self.idf: Dict[str, float] = {}
        self.vocab: Set[str] = set()

    def _tokenize(self, text: str) -> List[str]:
        """分词

        Args:
            text: 输入文本

        Returns:
            词列表
        """
        if self.language == "zh":
            # 简单的中文分词（按字符）
            # 生产环境应该使用 jieba 等分词工具
            # 这里为了避免外部依赖，使用简单实现
            tokens = []
            for char in text:
                if char.strip() and not char.isspace():
                    tokens.append(char)
            return tokens
        else:
            # 英文分词（按空格和标点）
            import re
            text = text.lower()
            tokens = re.findall(r'\b\w+\b', text)
            return tokens

    def add_documents(self, documents: List[str], doc_ids: List[str]) -> None:
        """添加文档到索引

        Args:
            documents: 文档内容列表
            doc_ids: 文档ID列表
        """
        if len(documents) != len(doc_ids):
            raise ValueError("documents and doc_ids must have the same length")

        # 保存文档
        self.documents.extend(documents)
        self.doc_ids.extend(doc_ids)

        # 分词
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            self.vocab.update(tokens)

        # 计算平均文档长度
        if self.doc_lengths:
            self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths)

        # 计算 IDF
        self._compute_idf()

    def _compute_idf(self) -> None:
        """计算 IDF (Inverse Document Frequency)

        IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
        """
        N = len(self.documents)
        if N == 0:
            return

        # 计算每个词的文档频率
        df: Dict[str, int] = {}
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        # 计算 IDF
        for token, freq in df.items():
            # BM25 IDF 公式
            idf = math.log((N - freq + 0.5) / (freq + 0.5) + 1)
            self.idf[token] = idf

    def search(self, query: str, top_k: int = 10) -> List[tuple]:
        """搜索相关文档

        Args:
            query: 查询字符串
            top_k: 返回前K个结果

        Returns:
            (doc_id, score) 列表，按分数降序
        """
        if not self.documents:
            return []

        # 查询分词
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 计算每个文档的 BM25 分数
        scores = []
        for i, tokens in enumerate(self.doc_tokens):
            score = self._bm25_score(query_tokens, tokens, self.doc_lengths[i])
            scores.append((self.doc_ids[i], score))

        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def _bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_length: int
    ) -> float:
        """计算 BM25 分数

        BM25(q, d) = Σ IDF(qi) * (f(qi, d) * (k1 + 1)) / (f(qi, d) + k1 * (1 - b + b * |d| / avgdl))

        Args:
            query_tokens: 查询词列表
            doc_tokens: 文档词列表
            doc_length: 文档长度

        Returns:
            BM25 分数
        """
        score = 0.0

        # 计算文档中每个词的频率
        doc_freqs = Counter(doc_tokens)

        # 长度归一化因子
        norm_factor = 1 - self.b + self.b * (doc_length / self.avgdl) if self.avgdl > 0 else 1

        # 累加每个查询词的贡献
        for token in query_tokens:
            if token not in self.idf:
                continue

            # 词频
            tf = doc_freqs.get(token, 0)

            # BM25 公式
            idf = self.idf[token]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * norm_factor

            score += idf * (numerator / denominator)

        return score

    def clear(self) -> None:
        """清空所有数据"""
        self.documents.clear()
        self.doc_ids.clear()
        self.doc_tokens.clear()
        self.doc_lengths.clear()
        self.idf.clear()
        self.vocab.clear()
        self.avgdl = 0.0

    def __len__(self) -> int:
        """返回文档数量"""
        return len(self.documents)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"BM25Retriever(docs={len(self.documents)}, vocab={len(self.vocab)})"
