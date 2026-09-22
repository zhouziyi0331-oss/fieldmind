"""
对话历史管理器 - 管理对话上下文和历史
"""

from typing import List, Dict, Any
from collections import deque
from datetime import datetime


class ConversationHistoryManager:
    """对话历史管理器"""
    def __init__(self, max_history: int = 10, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化对话历史管理器

        Args:
            max_history: 最多保留的对话轮数
        """
        self.max_history = max_history
        self.conversations = {}  # project_id -> deque

    def add_conversation(
        self,
        project_id: int,
        query: str,
        response: Dict[str, Any]
    ):
        """添加对话记录（增强版）"""
        if project_id not in self.conversations:
            self.conversations[project_id] = deque(maxlen=self.max_history)

        # 自动分类对话
        category = self._classify_query(query)

        # 生成对话摘要
        summary = self._generate_summary(query, response)

        self.conversations[project_id].append({
            'query': query,
            'answer': response.get('answer'),
            'confidence': response.get('confidence'),
            'citations': response.get('citations', []),
            'category': category,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })

    def _classify_query(self, query: str) -> str:
        """对话分类"""
        query_lower = query.lower()

        # 关键词匹配
        if any(word in query_lower for word in ['什么', '哪些', '介绍']):
            return '信息查询'
        elif any(word in query_lower for word in ['为什么', '原因', '如何']):
            return '深度分析'
        elif any(word in query_lower for word in ['建议', '方案', '怎么办']):
            return '方案咨询'
        elif any(word in query_lower for word in ['对比', '比较', '区别']):
            return '对比分析'
        else:
            return '一般咨询'

    def _generate_summary(self, query: str, response: Dict[str, Any]) -> str:
        """生成对话摘要"""
        answer = response.get('answer', '')

        # 简单摘要：取前50字
        summary = query[:30]
        if len(query) > 30:
            summary += '...'

        return summary

    def get_conversations_by_category(
        self,
        project_id: int,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """按分类获取对话"""
        if project_id not in self.conversations:
            return []

        conversations = list(self.conversations[project_id])

        if category:
            conversations = [
                c for c in conversations
                if c.get('category') == category
            ]

        return conversations

    def get_conversation_statistics(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """获取对话统计"""
        if project_id not in self.conversations:
            return {
                'total': 0,
                'by_category': {},
                'avg_confidence': 0
            }

        conversations = list(self.conversations[project_id])

        # 按分类统计
        category_counts = {}
        total_confidence = 0

        for conv in conversations:
            category = conv.get('category', '一般咨询')
            category_counts[category] = category_counts.get(category, 0) + 1
            total_confidence += conv.get('confidence', 0)

        return {
            'total': len(conversations),
            'by_category': category_counts,
            'avg_confidence': total_confidence / len(conversations) if conversations else 0
        }

    def get_history(
        self,
        project_id: int,
        last_n: int = 5
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        if project_id not in self.conversations:
            return []

        history = list(self.conversations[project_id])
        return history[-last_n:] if last_n else history

    def clear_history(self, project_id: int):
        """清除对话历史"""
        if project_id in self.conversations:
            self.conversations[project_id].clear()

    def get_context_for_prompt(
        self,
        project_id: int,
        last_n: int = 3
    ) -> str:
        """获取用于提示词的上下文"""
        history = self.get_history(project_id, last_n)

        if not history:
            return ""

        context_parts = ["最近的对话历史：\n"]

        for conv in history:
            context_parts.append(f"Q: {conv['query']}\n")
            context_parts.append(f"A: {conv['answer'][:200]}...\n\n")

        return "".join(context_parts)
