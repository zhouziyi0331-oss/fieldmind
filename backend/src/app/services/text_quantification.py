"""
文本量化服务 (Text Quantification Service)
负责计算文本的各种量化指标并更新 chunks 表
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class TextQuantificationService:
    """
    文本量化服务

    计算 15+ 指标：
    - 基础指标：字数、句数、段落数
    - 情感指标：情感极性、主观性
    - 复杂度：平均句长、词汇丰富度
    - 情绪词密度
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 情感词典（简化版）
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.positive_words = set([
            "好", "棒", "优秀", "美好", "幸福", "快乐", "喜欢", "爱",
            "成功", "发展", "进步", "繁荣", "和谐", "满意"
        ])

        self.negative_words = set([
            "坏", "差", "糟糕", "痛苦", "悲伤", "失望", "讨厌", "恨",
            "失败", "衰退", "落后", "贫困", "冲突", "不满"
        ])

        self.emotion_words = set([
            "高兴", "激动", "兴奋", "愤怒", "恐惧", "担心", "焦虑",
            "悲伤", "失落", "惊讶", "感动", "温暖", "冷漠"
        ])

    def quantify_text(self, text: str) -> Dict[str, Any]:
        """
        量化文本

        Args:
            text: 输入文本

        Returns:
            {
                "char_count": int,
                "word_count": int,
                "sentence_count": int,
                "paragraph_count": int,
                "avg_sentence_length": float,
                "sentiment_score": float,  # -1 到 1
                "sentiment_polarity": str,  # positive/neutral/negative
                "subjectivity": float,  # 0 到 1
                "emotion_density": float,  # 情绪词密度
                "lexical_diversity": float,  # 词汇丰富度
                "positive_word_count": int,
                "negative_word_count": int,
                "emotion_word_count": int,
                "question_count": int,
                "exclamation_count": int
            }
        """
        if not text or len(text.strip()) == 0:
            return self._empty_metrics()

        metrics = {}

        # 基础指标
        metrics["char_count"] = len(text)
        metrics["word_count"] = self._count_words(text)
        metrics["sentence_count"] = self._count_sentences(text)
        metrics["paragraph_count"] = self._count_paragraphs(text)

        # 平均句长
        if metrics["sentence_count"] > 0:
            metrics["avg_sentence_length"] = metrics["word_count"] / metrics["sentence_count"]
        else:
            metrics["avg_sentence_length"] = 0.0

        # 情感分析
        sentiment = self.calculate_sentiment(text)
        metrics.update(sentiment)

        # 词汇丰富度
        metrics["lexical_diversity"] = self._calculate_lexical_diversity(text)

        # 标点统计
        metrics["question_count"] = text.count("？") + text.count("?")
        metrics["exclamation_count"] = text.count("！") + text.count("!")

        return metrics

    def calculate_sentiment(self, text: str) -> Dict[str, Any]:
        """
        情感分析

        Returns:
            {
                "sentiment_score": float,
                "sentiment_polarity": str,
                "subjectivity": float,
                "emotion_density": float,
                "positive_word_count": int,
                "negative_word_count": int,
                "emotion_word_count": int
            }
        """
        # 分词（简化版：按字符）
        words = list(text)

        # 统计情感词
        positive_count = sum(1 for w in words if w in self.positive_words)
        negative_count = sum(1 for w in words if w in self.negative_words)
        emotion_count = sum(1 for w in words if w in self.emotion_words)

        total_words = len(words)

        # 情感分数 (-1 到 1)
        if positive_count + negative_count > 0:
            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            sentiment_score = 0.0

        # 情感极性
        if sentiment_score > 0.2:
            polarity = "positive"
        elif sentiment_score < -0.2:
            polarity = "negative"
        else:
            polarity = "neutral"

        # 主观性 (0 到 1)
        if total_words > 0:
            subjectivity = (positive_count + negative_count + emotion_count) / total_words
        else:
            subjectivity = 0.0

        # 情绪词密度
        if total_words > 0:
            emotion_density = emotion_count / total_words
        else:
            emotion_density = 0.0

        return {
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_polarity": polarity,
            "subjectivity": round(subjectivity, 3),
            "emotion_density": round(emotion_density, 3),
            "positive_word_count": positive_count,
            "negative_word_count": negative_count,
            "emotion_word_count": emotion_count,
        }

    def _count_words(self, text: str) -> int:
        """统计词数（中文按字符，英文按单词）"""
        # 移除空白字符
        text_clean = text.replace(" ", "").replace("\n", "").replace("\t", "")
        return len(text_clean)

    def _count_sentences(self, text: str) -> int:
        """统计句子数"""
        sentences = re.split(r'[。！？\.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)

    def _count_paragraphs(self, text: str) -> int:
        """统计段落数"""
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return len(paragraphs)

    def _calculate_lexical_diversity(self, text: str) -> float:
        """计算词汇丰富度（Type-Token Ratio）"""
        words = list(text.replace(" ", "").replace("\n", ""))

        if len(words) == 0:
            return 0.0

        unique_words = set(words)
        return round(len(unique_words) / len(words), 3)

    def _empty_metrics(self) -> Dict[str, Any]:
        """空文本的默认指标"""
        return {
            "char_count": 0,
            "word_count": 0,
            "sentence_count": 0,
            "paragraph_count": 0,
            "avg_sentence_length": 0.0,
            "sentiment_score": 0.0,
            "sentiment_polarity": "neutral",
            "subjectivity": 0.0,
            "emotion_density": 0.0,
            "lexical_diversity": 0.0,
            "positive_word_count": 0,
            "negative_word_count": 0,
            "emotion_word_count": 0,
            "question_count": 0,
            "exclamation_count": 0,
        }

    def quantify_and_update_chunks(
        self,
        db: Session,
        document_id: int
    ) -> int:
        """
        量化文档的所有 chunks 并更新数据库

        Args:
            db: 数据库会话
            document_id: 文档 ID

        Returns:
            更新的 chunk 数量
        """
        from app.models.chunk import Chunk

        # 获取该文档的所有 chunks
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()

        if not chunks:
            logger.warning(f"文档 {document_id} 没有 chunks")
            return 0

        updated_count = 0

        for chunk in chunks:
            # 量化
            metrics = self.quantify_text(chunk.content)

            # 更新字段
            chunk.sentence_count = metrics["sentence_count"]
            chunk.avg_sentence_length = metrics["avg_sentence_length"]
            chunk.sentiment_score = metrics["sentiment_score"]
            chunk.sentiment_polarity = metrics["sentiment_polarity"]
            chunk.subjectivity = metrics["subjectivity"]
            chunk.emotion_density = metrics["emotion_density"]
            chunk.lexical_diversity = metrics["lexical_diversity"]
            chunk.positive_word_count = metrics["positive_word_count"]
            chunk.negative_word_count = metrics["negative_word_count"]
            chunk.emotion_word_count = metrics["emotion_word_count"]

            updated_count += 1

        db.commit()

        logger.info(f"文档 {document_id} 的 {updated_count} 个 chunks 已量化")

        return updated_count


# 全局实例
text_quantification_service = TextQuantificationService()
