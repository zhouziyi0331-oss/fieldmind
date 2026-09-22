"""
内容类特征提取器

提取文本的内容类特征：
- 情绪词密度
- 关键词密度
"""

import jieba
import logging

logger = logging.getLogger(__name__)

# 情绪词表（来自需求文档中的示例）
EMOTION_WORDS = {
    '喜欢', '讨厌', '满意', '愤怒', '开心', '失望', '激动', '惊讶',
    '好', '差', '棒', '糟', '爱', '恨', '希望', '害怕', '担心', '相信',
    '感谢', '抱歉', '幸福', '痛苦', '快乐', '悲伤', '兴奋', '焦虑',
    '高兴', '难过', '生气', '紧张', '放心', '安心', '舒服', '难受',
    '喜悦', '哀伤', '恐惧', '惊喜', '遗憾', '满足', '不满', '欣慰'
}


def extract_content_features(text: str, keyword_list: list = None) -> dict:
    """
    提取内容类特征

    Args:
        text: 输入文本
        keyword_list: 自定义关键词列表（可选）

    Returns:
        包含内容类特征的字典
    """
    if not text or not text.strip():
        return {
            'emotion_word_density': 0.0,
            'keyword_density': 0.0,
        }

    try:
        # 分词
        words = list(jieba.cut(text))
        words = [w for w in words if w.strip()]
        word_count = len(words)

        if word_count == 0:
            return {
                'emotion_word_density': 0.0,
                'keyword_density': 0.0,
            }

        # 情绪词密度
        emotion_count = sum(1 for w in words if w in EMOTION_WORDS)
        emotion_density = emotion_count / word_count

        # 关键词密度（如果传入关键词列表）
        keyword_density = 0.0
        if keyword_list:
            keyword_count = sum(1 for w in words if w in keyword_list)
            keyword_density = keyword_count / word_count

        return {
            'emotion_word_density': round(emotion_density, 4),
            'keyword_density': round(keyword_density, 4),
        }

    except Exception as e:
        logger.error(f"内容类特征提取失败: {e}")
        return {
            'emotion_word_density': 0.0,
            'keyword_density': 0.0,
        }



# ==================== WorkflowEngine 包装类 ====================

class ContentFeaturesWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_extract_content(self, text: str, _context: dict) -> dict:
        """任务: 提取内容特征"""
        keyword_list = _context.get('keyword_list')
        features = extract_content_features(text, keyword_list)
        return {"content_features": features}

    def _task_batch_extract_content(self, texts: list, _context: dict) -> dict:
        """任务: 批量提取内容特征"""
        keyword_list = _context.get('keyword_list')
        results = [extract_content_features(text, keyword_list) for text in texts]
        return {"results": results, "count": len(results)}

    def extract_content_workflow(self, text: str, keyword_list: list = None) -> dict:
        """工作流: 使用 WorkflowEngine 提取内容特征"""
        if not self.use_workflow_engine:
            return extract_content_features(text, keyword_list)

        tasks = {
            "extract": {
                "function": self._task_extract_content,
                "args": {"text": text},
                "context": {"keyword_list": keyword_list}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["extract"]["content_features"]

    def batch_extract_content_workflow(self, texts: list, keyword_list: list = None) -> list:
        """工作流: 使用 WorkflowEngine 批量提取内容特征"""
        if not self.use_workflow_engine:
            return [extract_content_features(text, keyword_list) for text in texts]

        tasks = {
            "batch_extract": {
                "function": self._task_batch_extract_content,
                "args": {"texts": texts},
                "context": {"keyword_list": keyword_list}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_extract"]["results"]
