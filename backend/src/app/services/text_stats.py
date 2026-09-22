"""统一文本统计工具。"""

from __future__ import annotations

import regex as re
import jieba


def count_words(text: str) -> int:
    """对中英混合文本做更稳的词/字计数。"""
    if not text:
        return 0
    cleaned = text.strip()
    if not cleaned:
        return 0

    has_chinese = bool(re.search(r"\p{IsHan}", cleaned))
    has_latin = bool(re.search(r"[A-Za-z]", cleaned))

    if has_chinese and not has_latin:
        tokens = [token.strip() for token in jieba.cut(cleaned) if token.strip()]
        return len(tokens) if tokens else len(cleaned)

    tokens = re.findall(r"\p{IsHan}+|[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", cleaned)
    return len(tokens) if tokens else len(cleaned.split())




# ==================== WorkflowEngine 包装类 ====================

class TextStatsWrapper:
    """WorkflowEngine 包装类 - 将函数式模块集成到 WorkflowEngine"""

    def __init__(self, use_workflow_engine: bool = True):
        """初始化包装器"""
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _task_count_words(self, text: str, _context: dict) -> dict:
        """任务: 统计文本词数"""
        word_count = count_words(text)
        return {"word_count": word_count}

    def _task_batch_count_words(self, texts: list, _context: dict) -> dict:
        """任务: 批量统计词数"""
        results = [{"text": text, "word_count": count_words(text)} for text in texts]
        return {"results": results, "total": len(results)}

    def count_words_workflow(self, text: str) -> int:
        """工作流: 使用 WorkflowEngine 统计词数"""
        if not self.use_workflow_engine:
            return count_words(text)

        tasks = {
            "count": {
                "function": self._task_count_words,
                "args": {"text": text}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["count"]["word_count"]

    def batch_count_words_workflow(self, texts: list) -> list:
        """工作流: 使用 WorkflowEngine 批量统计词数"""
        if not self.use_workflow_engine:
            return [count_words(text) for text in texts]

        tasks = {
            "batch_count": {
                "function": self._task_batch_count_words,
                "args": {"texts": texts}
            }
        }

        results = self.workflow_engine.execute(tasks)
        return results["batch_count"]["results"]
