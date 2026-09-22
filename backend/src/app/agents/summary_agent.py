"""
摘要 Agent
负责文本摘要和内容提炼
"""
from typing import List, Dict, Any
import logging
from datetime import datetime

from .base_agent import BaseAgent
from .agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent(
    name="summary_agent",
    description="文本摘要和内容提炼",
    version="1.0.0",
    capabilities=["summarization", "text_processing"],
    dependencies=[]
)
class SummaryAgent(BaseAgent):
    """
    摘要 Agent

    功能：
    - 文本摘要
    - 关键信息提取
    - 多段落压缩
    """

    def __init__(self):
        super().__init__()
        self.name = "SummaryAgent"
        logger.info("摘要 Agent 已初始化")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文本摘要

        Args:
            input_data: {
                "text": str,  # 原始文本
                "max_length": int,  # 最大摘要长度（默认200）
                "summary_type": str  # 摘要类型：extractive/abstractive
            }

        Returns:
            {
                "summary": str,  # 摘要文本
                "key_points": List[str],  # 关键点
                "compression_ratio": float  # 压缩比
            }
        """
        text = input_data.get("text", "")
        max_length = input_data.get("max_length", 200)
        summary_type = input_data.get("summary_type", "extractive")

        if not text:
            return {"summary": "", "key_points": [], "compression_ratio": 0.0}

        # 生成摘要
        if summary_type == "abstractive":
            summary = self._abstractive_summary(text, max_length)
        else:
            summary = self._extractive_summary(text, max_length)

        # 提取关键点
        key_points = self._extract_key_points(text)

        # 计算压缩比
        compression_ratio = len(summary) / len(text) if text else 0.0

        return {
            "summary": summary,
            "key_points": key_points,
            "compression_ratio": compression_ratio,
            "original_length": len(text),
            "summary_length": len(summary),
            "summarized_at": datetime.now().isoformat()
        }

    def _extractive_summary(self, text: str, max_length: int) -> str:
        """抽取式摘要"""
        sentences = text.split('。')
        sentences = [s.strip() + '。' for s in sentences if s.strip()]

        # 简单选择前几句
        summary = ""
        for sent in sentences:
            if len(summary) + len(sent) <= max_length:
                summary += sent
            else:
                break

        return summary if summary else sentences[0] if sentences else ""

    def _abstractive_summary(self, text: str, max_length: int) -> str:
        """生成式摘要（简化版）"""
        # 这里简化处理，实际应该使用NLP模型
        return self._extractive_summary(text, max_length)

    def _extract_key_points(self, text: str) -> List[str]:
        """提取关键点"""
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]

        # 简单返回前3句
        return sentences[:3]

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "text" in input_data and input_data["text"]

    def get_capabilities(self) -> List[str]:
        """返回能力"""
        return ["summarization", "text_processing"]
