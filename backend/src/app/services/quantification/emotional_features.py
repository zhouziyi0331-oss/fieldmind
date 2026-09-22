"""
情绪与情感特征提取器

提取文本的情绪特征：
- 情感极性值 (-1到1)
- 情绪强度 (0到1)
- 情绪分类标签 (正面/中性/负面)
"""

import logging

logger = logging.getLogger(__name__)


def extract_emotional_features(text: str) -> dict:
    """
    提取情绪与情感特征

    Args:
        text: 输入文本

    Returns:
        包含情绪特征的字典
    """
    if not text or not text.strip():
        return {
            'emotion_polarity': 0.0,
            'emotion_intensity': 0.0,
            'emotion_label': '中性',
        }

    try:
        # 使用SnowNLP进行情感分析
        from snownlp import SnowNLP

        s = SnowNLP(text)
        polarity = s.sentiments  # 0~1, 越接近0越负面，越接近1越正面

        # 转换到 -1~1
        polarity_scaled = (polarity - 0.5) * 2

        # 强度：离0.5越远越强烈
        intensity = abs(polarity - 0.5) * 2

        # 分类标签
        if polarity > 0.6:
            label = '正面'
        elif polarity < 0.4:
            label = '负面'
        else:
            label = '中性'

        return {
            'emotion_polarity': round(polarity_scaled, 4),
            'emotion_intensity': round(intensity, 4),
            'emotion_label': label,
        }

    except ImportError:
        logger.warning("SnowNLP未安装，使用简单规则替代")
        # 简单规则：基于情绪词数量
        positive_words = ['好', '棒', '喜欢', '开心', '满意', '幸福', '快乐', '爱']
        negative_words = ['差', '糟', '讨厌', '愤怒', '失望', '痛苦', '悲伤', '恨']

        pos_count = sum(text.count(w) for w in positive_words)
        neg_count = sum(text.count(w) for w in negative_words)
        total = pos_count + neg_count

        if total == 0:
            return {
                'emotion_polarity': 0.0,
                'emotion_intensity': 0.0,
                'emotion_label': '中性',
            }

        polarity = (pos_count - neg_count) / total
        intensity = total / len(text) if len(text) > 0 else 0

        if polarity > 0.2:
            label = '正面'
        elif polarity < -0.2:
            label = '负面'
        else:
            label = '中性'

        return {
            'emotion_polarity': round(polarity, 4),
            'emotion_intensity': round(min(intensity * 10, 1.0), 4),
            'emotion_label': label,
        }

    except Exception as e:
        logger.error(f"情绪特征提取失败: {e}")
        return {
            'emotion_polarity': 0.0,
            'emotion_intensity': 0.0,
            'emotion_label': '中性',
        }



# ==================== WorkflowEngine 包装类 ====================

class EmotionalFeaturesWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_extract_emotional(self, text: str, _context: dict) -> dict:
        """任务: 提取情绪特征"""
        features = extract_emotional_features(text)
        return {"emotional_features": features}

    def _task_batch_extract_emotional(self, texts: list, _context: dict) -> dict:
        """任务: 批量提取情绪特征"""
        results = [extract_emotional_features(text) for text in texts]
        return {"results": results, "count": len(results)}

    def extract_emotional_workflow(self, text: str) -> dict:
        """工作流: 使用 WorkflowEngine 提取情绪特征"""
        if not self.use_workflow_engine:
            return extract_emotional_features(text)

        tasks = {
            "extract": {
                "function": self._task_extract_emotional,
                "args": {"text": text}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["extract"]["emotional_features"]

    def batch_extract_emotional_workflow(self, texts: list) -> list:
        """工作流: 使用 WorkflowEngine 批量提取情绪特征"""
        if not self.use_workflow_engine:
            return [extract_emotional_features(text) for text in texts]

        tasks = {
            "batch_extract": {
                "function": self._task_batch_extract_emotional,
                "args": {"texts": texts}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_extract"]["results"]
