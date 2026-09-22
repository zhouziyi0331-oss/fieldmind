"""
关键词提取服务 (Keyword Extraction Service)
使用 TF-IDF 算法提取文本关键词
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from collections import Counter
import math
import logging
import jieba
import jieba.analyse

logger = logging.getLogger(__name__)


class KeywordExtractionService:
    """
    关键词提取服务

    方法：
    1. TF-IDF 算法
    2. TextRank 算法
    3. 词频统计
    """

    def __init__(self):
        # 停用词列表
        self.stop_words = self._load_stop_words()

    def _load_stop_words(self) -> set:
        """加载停用词"""
        # 简化版停用词
        return set([
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那"
        ])

    def extract_keywords(
        self,
        text: str,
        top_k: int = 20,
        method: str = "tfidf"
    ) -> List[Dict[str, Any]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前 K 个关键词
            method: 提取方法 (tfidf/textrank/frequency)

        Returns:
            [
                {
                    "word": str,
                    "score": float,
                    "method": str
                }
            ]
        """
        if not text or len(text.strip()) == 0:
            return []

        if method == "tfidf":
            return self._extract_tfidf(text, top_k)
        elif method == "textrank":
            return self._extract_textrank(text, top_k)
        elif method == "frequency":
            return self._extract_frequency(text, top_k)
        else:
            return self._extract_tfidf(text, top_k)

    def _extract_tfidf(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """TF-IDF 提取"""
        try:
            # 使用 jieba 的 TF-IDF
            keywords = jieba.analyse.extract_tags(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a')
            )

            return [
                {
                    "word": word,
                    "score": float(score),
                    "method": "tfidf"
                }
                for word, score in keywords
            ]

        except Exception as e:
            logger.error(f"TF-IDF 提取失败: {e}")
            return []

    def _extract_textrank(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """TextRank 提取"""
        try:
            # 使用 jieba 的 TextRank
            keywords = jieba.analyse.textrank(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a')
            )

            return [
                {
                    "word": word,
                    "score": float(score),
                    "method": "textrank"
                }
                for word, score in keywords
            ]

        except Exception as e:
            logger.error(f"TextRank 提取失败: {e}")
            return []

    def _extract_frequency(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """词频统计提取"""
        try:
            # 分词
            words = jieba.lcut(text)

            # 过滤停用词和单字
            words = [
                w for w in words
                if len(w) > 1 and w not in self.stop_words
            ]

            # 统计词频
            word_counts = Counter(words)

            # 归一化
            total = sum(word_counts.values())

            keywords = [
                {
                    "word": word,
                    "score": count / total,
                    "method": "frequency"
                }
                for word, count in word_counts.most_common(top_k)
            ]

            return keywords

        except Exception as e:
            logger.error(f"词频统计失败: {e}")
            return []

    def extract_and_save_keywords(
        self,
        db: Session,
        document_id: int,
        text: str,
        top_k: int = 20
    ) -> int:
        """
        提取关键词并保存到数据库

        Args:
            db: 数据库会话
            document_id: 文档 ID
            text: 文本内容
            top_k: 提取数量

        Returns:
            保存的关键词数量
        """
        from app.models.keyword import Keyword

        # 提取关键词
        keywords = self.extract_keywords(text, top_k=top_k, method="tfidf")

        if not keywords:
            logger.warning(f"文档 {document_id} 未提取到关键词")
            return 0

        # 保存到数据库
        saved_count = 0

        for kw in keywords:
            keyword = Keyword(
                document_id=document_id,
                word=kw["word"],
                score=kw["score"],
                extraction_method=kw["method"],
            )

            db.add(keyword)
            saved_count += 1

        db.commit()

        logger.info(f"文档 {document_id} 提取了 {saved_count} 个关键词")

        return saved_count

    def extract_from_chunks(
        self,
        db: Session,
        project_id: int,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        从项目的所有 chunks 中提取关键词

        Args:
            db: 数据库会话
            project_id: 项目 ID
            top_k: 返回前 K 个

        Returns:
            项目级别的关键词列表
        """
        from app.models.chunk import Chunk

        # 获取所有 chunks
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

        if not chunks:
            return []

        # 合并所有文本
        all_text = "\n".join([chunk.content for chunk in chunks if chunk.content])

        # 提取关键词
        keywords = self.extract_keywords(all_text, top_k=top_k, method="tfidf")

        return keywords


# 全局实例
keyword_extraction_service = KeywordExtractionService()
