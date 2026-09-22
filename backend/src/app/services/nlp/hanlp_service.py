"""
HanLP 中文 NLP 服务

提供完整的中文自然语言处理能力：
- 中文分词
- 词性标注
- 命名实体识别
- 依存句法分析
- 关键词提取
- 文本摘要
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HanLPService:
    """
    HanLP 中文 NLP 服务

    封装 HanLP 提供统一接口
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self._hanlp = None
        self._initialized = False

        # 尝试导入 HanLP
        try:
            import hanlp
            self._hanlp = hanlp
            self._initialize_models()
            self._initialized = True
            logger.info("✅ HanLP 服务初始化成功")
        except ImportError:
            logger.warning("⚠️ HanLP 未安装，请运行: pip install hanlp")
        except Exception as e:
            logger.error(f"❌ HanLP 初始化失败: {e}")

    def _initialize_models(self):
        """初始化 HanLP 模型"""
        try:
            # 加载多任务模型（中文）
            self.model = self._hanlp.load(self._hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH)
            logger.info("✅ HanLP 中文模型加载成功")
        except Exception as e:
            logger.warning(f"⚠️ HanLP 模型加载失败，使用基础功能: {e}")
            self.model = None

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized and self._hanlp is not None

    # ==================== 分词 ====================

    def segment(self, text: str) -> List[str]:
        """
        中文分词

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        if not self.is_available():
            # 降级：使用简单的字符分割
            logger.warning("HanLP 不可用，使用简单分词")
            return list(text.replace(" ", ""))

        try:
            if self.model:
                # 使用完整模型
                result = self.model(text, tasks='tok')
                return result['tok/fine']
            else:
                # 使用基础分词器
                tokenizer = self._hanlp.utils.rules.tokenize_english(text)
                return list(tokenizer)
        except Exception as e:
            logger.error(f"分词失败: {e}")
            return text.split()

    # ==================== 词性标注 ====================

    def pos_tag(self, text: str) -> List[Dict[str, str]]:
        """
        词性标注

        Args:
            text: 输入文本

        Returns:
            [{"word": "词", "pos": "词性"}, ...]
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，无法进行词性标注")
            return []

        try:
            if self.model:
                result = self.model(text, tasks=['tok', 'pos'])
                words = result['tok/fine']
                pos_tags = result['pos/ctb']

                return [
                    {"word": word, "pos": pos}
                    for word, pos in zip(words, pos_tags)
                ]
            else:
                logger.warning("模型未加载，无法进行词性标注")
                return []
        except Exception as e:
            logger.error(f"词性标注失败: {e}")
            return []

    # ==================== 命名实体识别 ====================

    def recognize_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        命名实体识别 (NER)

        Args:
            text: 输入文本

        Returns:
            [
                {
                    "text": "实体文本",
                    "type": "实体类型",
                    "start": 起始位置,
                    "end": 结束位置
                },
                ...
            ]
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，无法进行命名实体识别")
            return []

        try:
            if self.model:
                result = self.model(text, tasks=['tok', 'ner'])
                ner_results = result.get('ner/msra', [])

                entities = []
                for entity_group in ner_results:
                    if isinstance(entity_group, list) and len(entity_group) == 2:
                        entity_type, entity_spans = entity_group
                        for span in entity_spans:
                            if isinstance(span, (list, tuple)) and len(span) == 2:
                                start, end = span
                                entity_text = text[start:end]
                                entities.append({
                                    "text": entity_text,
                                    "type": entity_type,
                                    "start": start,
                                    "end": end
                                })

                return entities
            else:
                logger.warning("模型未加载，无法进行命名实体识别")
                return []
        except Exception as e:
            logger.error(f"命名实体识别失败: {e}")
            return []

    # ==================== 依存句法分析 ====================

    def dependency_parse(self, text: str) -> Dict[str, Any]:
        """
        依存句法分析

        Args:
            text: 输入文本

        Returns:
            {
                "words": [...],
                "deps": [(head, relation, dependent), ...]
            }
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，无法进行依存句法分析")
            return {"words": [], "deps": []}

        try:
            if self.model:
                result = self.model(text, tasks=['tok', 'dep'])
                words = result['tok/fine']
                deps = result.get('dep', [])

                return {
                    "words": words,
                    "deps": deps
                }
            else:
                logger.warning("模型未加载，无法进行依存句法分析")
                return {"words": [], "deps": []}
        except Exception as e:
            logger.error(f"依存句法分析失败: {e}")
            return {"words": [], "deps": []}

    # ==================== 关键词提取 ====================

    def extract_keywords(
        self,
        text: str,
        top_k: int = 10,
        method: str = "textrank"
    ) -> List[Dict[str, Any]]:
        """
        关键词提取

        Args:
            text: 输入文本
            top_k: 返回前k个关键词
            method: 提取方法 (textrank/tfidf)

        Returns:
            [{"word": "关键词", "score": 0.95}, ...]
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，使用简单关键词提取")
            # 降级：返回最长的词
            words = self.segment(text)
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 过滤单字
                    word_freq[word] = word_freq.get(word, 0) + 1

            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [
                {"word": word, "score": freq / len(words)}
                for word, freq in sorted_words[:top_k]
            ]

        try:
            # 使用 HanLP 的关键词提取
            from hanlp.components.extractive_summarization import TextRankKeyword

            extractor = TextRankKeyword()
            keywords = extractor(text, topk=top_k)

            return [
                {"word": word, "score": score}
                for word, score in keywords
            ]
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            # 降级到简单方法
            words = self.segment(text)
            unique_words = list(set(words))[:top_k]
            return [
                {"word": word, "score": 1.0 / (i + 1)}
                for i, word in enumerate(unique_words)
            ]

    # ==================== 文本摘要 ====================

    def summarize(
        self,
        text: str,
        max_length: int = 200,
        num_sentences: int = 3
    ) -> str:
        """
        文本摘要

        Args:
            text: 输入文本
            max_length: 最大长度
            num_sentences: 句子数量

        Returns:
            摘要文本
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，使用简单摘要")
            # 降级：返回前 max_length 个字符
            return text[:max_length] + ("..." if len(text) > max_length else "")

        try:
            # 使用 HanLP 的摘要提取
            from hanlp.components.extractive_summarization import TextRankSentence

            extractor = TextRankSentence()
            sentences = extractor(text, topk=num_sentences)

            summary = "".join(sentences)

            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

            return summary
        except Exception as e:
            logger.error(f"文本摘要失败: {e}")
            # 降级：分句后返回前几句
            import re
            sentences = re.split(r'[。！？\n]', text)
            summary = "。".join(sentences[:num_sentences]) + "。"

            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

            return summary

    # ==================== 情感分析 ====================

    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        情感分析

        Args:
            text: 输入文本

        Returns:
            {
                "sentiment": "positive/negative/neutral",
                "score": 0.0-1.0,
                "confidence": 0.0-1.0
            }
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，无法进行情感分析")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "confidence": 0.0
            }

        try:
            # HanLP 可能需要额外的情感分析模型
            # 这里提供一个简单的基于关键词的方法

            positive_words = ["好", "棒", "优秀", "喜欢", "高兴", "满意", "赞"]
            negative_words = ["差", "糟", "失望", "讨厌", "难过", "不满", "烂"]

            words = self.segment(text)

            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)

            total = positive_count + negative_count

            if total == 0:
                return {
                    "sentiment": "neutral",
                    "score": 0.5,
                    "confidence": 0.5
                }

            if positive_count > negative_count:
                score = (positive_count / total)
                return {
                    "sentiment": "positive",
                    "score": 0.5 + score * 0.5,
                    "confidence": score
                }
            elif negative_count > positive_count:
                score = (negative_count / total)
                return {
                    "sentiment": "negative",
                    "score": 0.5 - score * 0.5,
                    "confidence": score
                }
            else:
                return {
                    "sentiment": "neutral",
                    "score": 0.5,
                    "confidence": 0.5
                }

        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "confidence": 0.0
            }

    # ==================== 文本相似度 ====================

    def text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0-1.0)
        """
        if not self.is_available():
            logger.warning("HanLP 不可用，使用简单相似度计算")
            # 降级：字符重叠率
            set1 = set(text1)
            set2 = set(text2)
            intersection = set1 & set2
            union = set1 | set2
            return len(intersection) / len(union) if union else 0.0

        try:
            # 基于词袋的相似度
            words1 = set(self.segment(text1))
            words2 = set(self.segment(text2))

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union) if union else 0.0

        except Exception as e:
            logger.error(f"文本相似度计算失败: {e}")
            return 0.0


# ==================== 全局单例 ====================

_hanlp_service: Optional[HanLPService] = None


def get_hanlp_service() -> HanLPService:
    """获取 HanLP 服务单例"""
    global _hanlp_service

    if _hanlp_service is None:
        _hanlp_service = HanLPService()

    return _hanlp_service
