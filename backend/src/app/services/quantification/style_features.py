"""
语言风格特征提取器

提取文本的语言风格特征：
- 主观性 (0到1)
- 客观性 (0到1)
- 语气强度 (0到1)
- 感叹号数量
- 情态动词数量
"""

import re
import logging

logger = logging.getLogger(__name__)


def extract_style_features(text: str) -> dict:
    """
    提取语言风格特征

    Args:
        text: 输入文本

    Returns:
        包含语言风格特征的字典
    """
    if not text or not text.strip():
        return {
            'subjectivity': 0.5,
            'objectivity': 0.5,
            'tone_strength': 0.0,
            'exclamation_count': 0,
            'modal_verb_count': 0,
        }

    try:
        # 感叹号计数
        exclamation_count = text.count('！') + text.count('!')

        # 情态动词计数
        modal_verbs = ['必须', '一定', '应该', '可能', '可以', '需要', '能够', '会', '要', '得', '想']
        modal_count = sum(text.count(mv) for mv in modal_verbs)

        # 主观性（尝试使用SnowNLP，否则用简单规则）
        try:
            from snownlp import SnowNLP
            s = SnowNLP(text)
            subjectivity = abs(s.sentiments - 0.5) * 2  # 离0.5越远越主观
        except:
            # 简单规则：基于第一人称代词和情态动词
            subjective_markers = ['我', '我们', '觉得', '认为', '感觉', '希望', '想', '喜欢']
            subjective_count = sum(text.count(marker) for marker in subjective_markers)
            subjectivity = min(subjective_count / max(len(text), 1) * 20, 1.0)

        objectivity = 1 - subjectivity

        # 语气强度（综合感叹号和情态动词密度）
        word_count = len(text)
        tone_strength = min(
            (exclamation_count * 0.3 + modal_count * 0.2) / max(word_count, 1) * 100,
            1.0
        )

        return {
            'subjectivity': round(subjectivity, 4),
            'objectivity': round(objectivity, 4),
            'tone_strength': round(tone_strength, 4),
            'exclamation_count': exclamation_count,
            'modal_verb_count': modal_count,
        }

    except Exception as e:
        logger.error(f"语言风格特征提取失败: {e}")
        return {
            'subjectivity': 0.5,
            'objectivity': 0.5,
            'tone_strength': 0.0,
            'exclamation_count': 0,
            'modal_verb_count': 0,
        }



# ==================== WorkflowEngine 包装类 ====================

class StyleFeaturesWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_extract_style(self, text: str, _context: dict) -> dict:
        """任务: 提取语言风格特征"""
        features = extract_style_features(text)
        return {"style_features": features}

    def _task_batch_extract_style(self, texts: list, _context: dict) -> dict:
        """任务: 批量提取语言风格特征"""
        results = [extract_style_features(text) for text in texts]
        return {"results": results, "count": len(results)}

    def extract_style_workflow(self, text: str) -> dict:
        """工作流: 使用 WorkflowEngine 提取语言风格特征"""
        if not self.use_workflow_engine:
            return extract_style_features(text)

        tasks = {
            "extract": {
                "function": self._task_extract_style,
                "args": {"text": text}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["extract"]["style_features"]

    def batch_extract_style_workflow(self, texts: list) -> list:
        """工作流: 使用 WorkflowEngine 批量提取语言风格特征"""
        if not self.use_workflow_engine:
            return [extract_style_features(text) for text in texts]

        tasks = {
            "batch_extract": {
                "function": self._task_batch_extract_style,
                "args": {"texts": texts}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_extract"]["results"]
