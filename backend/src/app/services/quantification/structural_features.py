"""
结构性特征提取器

提取文本的结构性特征：
- 字数
- 句数
- 段落数
- 平均词长
- 平均句长
"""

import re
import jieba
import logging

logger = logging.getLogger(__name__)


def extract_structural_features(text: str) -> dict:
    """
    提取结构性特征

    Args:
        text: 输入文本

    Returns:
        包含结构性特征的字典
    """
    if not text or not text.strip():
        return {
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'avg_word_length': 0.0,
            'avg_sentence_length': 0.0,
        }

    try:
        # 分词
        words = list(jieba.cut(text))
        words = [w for w in words if w.strip()]  # 过滤空白词

        # 分句
        sentences = re.split(r'[。！？\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 分段
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        # 计算平均词长
        total_word_len = sum(len(w) for w in words)
        avg_word_length = total_word_len / len(words) if words else 0

        # 计算平均句长（词数）
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
        }

    except Exception as e:
        logger.error(f"结构性特征提取失败: {e}")
        return {
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'avg_word_length': 0.0,
            'avg_sentence_length': 0.0,
        }



# ==================== WorkflowEngine 包装类 ====================

class StructuralFeaturesWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_extract_structural(self, text: str, _context: dict) -> dict:
        """任务: 提取结构性特征"""
        features = extract_structural_features(text)
        return {"structural_features": features}

    def _task_batch_extract_structural(self, texts: list, _context: dict) -> dict:
        """任务: 批量提取结构性特征"""
        results = [extract_structural_features(text) for text in texts]
        return {"results": results, "count": len(results)}

    def extract_structural_workflow(self, text: str) -> dict:
        """工作流: 使用 WorkflowEngine 提取结构性特征"""
        if not self.use_workflow_engine:
            return extract_structural_features(text)

        tasks = {
            "extract": {
                "function": self._task_extract_structural,
                "args": {"text": text}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["extract"]["structural_features"]

    def batch_extract_structural_workflow(self, texts: list) -> list:
        """工作流: 使用 WorkflowEngine 批量提取结构性特征"""
        if not self.use_workflow_engine:
            return [extract_structural_features(text) for text in texts]

        tasks = {
            "batch_extract": {
                "function": self._task_batch_extract_structural,
                "args": {"texts": texts}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_extract"]["results"]
