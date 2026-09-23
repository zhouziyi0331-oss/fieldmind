"""
提取原话 Skill - 基于引用挖掘
"""
from typing import Dict, Any, List
import re


class ExtractQuotesSkill:
    """
    原话提取Skill

    方法论：Quote Mining
    - 识别引号内容
    - 提取说话人
    - 分析情感强度
    - 验证上下文完整性
    """

    METADATA = {
        "name": "extract_quotes",
        "version": "1.0.0",
        "type": "text_extraction",
        "output_type": "原话"
    }

    # 引号模式（中英文）
    QUOTE_PATTERNS = [
        r'"([^"]{10,200})"',  # 英文引号
        r'"([^"]{10,200})"',  # 中文引号
        r'「([^」]{10,200})」',  # 日文引号
    ]

    # 情感关键词
    EMOTION_KEYWORDS = {
        "强烈正面": ["非常好", "太棒了", "完美", "卓越", "杰出"],
        "正面": ["好", "不错", "满意", "同意", "支持"],
        "中性": ["认为", "觉得", "表示", "说", "提到"],
        "负面": ["不好", "问题", "困难", "担心", "反对"],
        "强烈负面": ["糟糕", "失败", "灾难", "严重", "危机"]
    }

    def __init__(self, db_session):
        self.db = db_session

    def extract(self, chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]],
                relations: List[Dict[str, Any]],
                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行原话提取

        参数:
            chunks: 文本块列表
            entities: 实体列表
            relations: 关系列表
            events: 事件列表

        返回:
            原话列表，每个包含：
            - content: 引用内容
            - speaker: 说话人（如果能识别）
            - emotion: 情感分类
            - context: 上下文信息
            - credibility: 可信度
            - confidence: 置信度
            - source_chunks: 来源块ID列表
        """
        quotes = []

        # 构建实体名称集合用于说话人识别
        person_entities = {
            e.get("entity_name"): e.get("chunk_id")
            for e in entities
            if e.get("entity_type") in ["人物", "PERSON", "角色"]
        }

        # 遍历每个chunk提取引用
        for chunk in chunks:
            chunk_id = chunk.get("id")
            text = chunk.get("content", "")

            # 应用所有引号模式
            for pattern in self.QUOTE_PATTERNS:
                matches = re.finditer(pattern, text)

                for match in matches:
                    quote_text = match.group(1).strip()

                    # 识别说话人
                    speaker = self._identify_speaker(text, match.start(), person_entities)

                    # 分析情感
                    emotion = self._analyze_emotion(quote_text)

                    # 提取上下文
                    context = self._extract_context(text, match.start(), match.end())

                    quote = {
                        "content": quote_text,
                        "speaker": speaker,
                        "emotion": emotion,
                        "context": context,
                        "credibility": 0.9,  # 直接引用可信度高
                        "confidence": 0.85 if speaker else 0.7,  # 有说话人更可信
                        "source_chunks": [chunk_id]
                    }
                    quotes.append(quote)

        return quotes

    def _identify_speaker(self, text: str, quote_start: int,
                         person_entities: Dict[str, Any]) -> str:
        """识别说话人"""
        # 在引用前50字符内查找人名
        before_text = text[max(0, quote_start - 50):quote_start]

        # 查找"XXX说"、"XXX表示"等模式
        for person_name in person_entities.keys():
            if person_name in before_text:
                # 检查是否紧邻"说"、"表示"等动词
                if any(verb in before_text for verb in ["说", "表示", "认为", "指出", "提到"]):
                    return person_name

        return "未知"

    def _analyze_emotion(self, quote_text: str) -> str:
        """分析情感"""
        # 检查情感关键词
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            if any(kw in quote_text for kw in keywords):
                return emotion

        return "中性"

    def _extract_context(self, text: str, start: int, end: int) -> str:
        """提取上下文（前后各30字符）"""
        before = text[max(0, start - 30):start].strip()
        after = text[end:min(len(text), end + 30)].strip()

        context_parts = []
        if before:
            context_parts.append(f"...{before}")
        if after:
            context_parts.append(f"{after}...")

        return " ".join(context_parts)
