"""
对话记忆服务

提供对话历史管理、上下文提取和智能检索功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import Session

from app.models.user_engagement import ConversationMemory


class ConversationMemoryService:
    """对话记忆服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def create_memory(
        self,
        user_id: int,
        project_id: int,
        conversation_turn: int,
        user_message: str,
        ai_response: str,
        context_keywords: Optional[List[str]] = None,
        referenced_entities: Optional[List[str]] = None,
        topic_tags: Optional[List[str]] = None,
        importance_score: float = 0.5
    ) -> ConversationMemory:
        """
        创建对话记忆

        Args:
            user_id: 用户ID
            project_id: 项目ID
            conversation_turn: 对话轮次
            user_message: 用户消息
            ai_response: AI响应
            context_keywords: 上下文关键词
            referenced_entities: 引用的实体
            topic_tags: 主题标签
            importance_score: 重要性分数（0-1）

        Returns:
            创建的记忆记录
        """
        memory = ConversationMemory(
            user_id=user_id,
            project_id=project_id,
            conversation_turn=conversation_turn,
            user_message=user_message,
            ai_response=ai_response,
            context_keywords=context_keywords or [],
            referenced_entities=referenced_entities or [],
            topic_tags=topic_tags or [],
            importance_score=importance_score,
            created_at=datetime.utcnow()
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return memory

    def get_recent_conversations(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        limit: int = 20
    ) -> List[ConversationMemory]:
        """
        获取最近的对话记录

        Args:
            user_id: 用户ID
            project_id: 可选，项目ID
            limit: 返回数量

        Returns:
            对话记录列表
        """
        query = self.db.query(ConversationMemory).filter(
            ConversationMemory.user_id == user_id
        )

        if project_id:
            query = query.filter(ConversationMemory.project_id == project_id)

        conversations = query.order_by(
            desc(ConversationMemory.created_at)
        ).limit(limit).all()

        return conversations

    def search_by_keywords(
        self,
        user_id: int,
        keywords: List[str],
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> List[ConversationMemory]:
        """
        通过关键词搜索对话

        Args:
            user_id: 用户ID
            keywords: 关键词列表
            project_id: 可选，项目ID
            limit: 返回数量

        Returns:
            匹配的对话列表
        """
        query = self.db.query(ConversationMemory).filter(
            ConversationMemory.user_id == user_id
        )

        if project_id:
            query = query.filter(ConversationMemory.project_id == project_id)

        # 模糊匹配关键词
        results = []
        for memory in query.all():
            match_count = sum(
                1 for keyword in keywords
                if keyword.lower() in memory.user_message.lower() or
                   keyword.lower() in memory.ai_response.lower() or
                   keyword in memory.context_keywords
            )
            if match_count > 0:
                results.append((match_count, memory))

        # 按匹配度排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in results[:limit]]

    def get_context_for_entity(
        self,
        user_id: int,
        entity_name: str,
        limit: int = 5
    ) -> List[ConversationMemory]:
        """
        获取与特定实体相关的对话上下文

        Args:
            user_id: 用户ID
            entity_name: 实体名称
            limit: 返回数量

        Returns:
            相关对话列表
        """
        conversations = self.db.query(ConversationMemory).filter(
            ConversationMemory.user_id == user_id
        ).all()

        # 筛选包含该实体的对话
        relevant = [
            conv for conv in conversations
            if entity_name in conv.referenced_entities
        ]

        # 按重要性和时间排序
        relevant.sort(
            key=lambda x: (x.importance_score, x.created_at),
            reverse=True
        )

        return relevant[:limit]

    def get_conversation_summary(
        self,
        user_id: int,
        project_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取对话摘要统计

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            统计数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        conversations = self.db.query(ConversationMemory).filter(
            and_(
                ConversationMemory.user_id == user_id,
                ConversationMemory.project_id == project_id,
                ConversationMemory.created_at >= start_date
            )
        ).all()

        # 统计
        total_turns = len(conversations)
        avg_importance = (
            sum(c.importance_score for c in conversations) / total_turns
            if total_turns > 0 else 0
        )

        # 提取所有主题标签
        all_topics = []
        for conv in conversations:
            all_topics.extend(conv.topic_tags)

        # 统计主题频率
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # 提取高频实体
        all_entities = []
        for conv in conversations:
            all_entities.extend(conv.referenced_entities)

        entity_counts = {}
        for entity in all_entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1

        return {
            "period_days": days,
            "total_turns": total_turns,
            "avg_importance": round(avg_importance, 2),
            "top_topics": sorted(
                topic_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "top_entities": sorted(
                entity_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def update_importance_score(
        self,
        memory_id: int,
        importance_score: float
    ) -> ConversationMemory:
        """
        更新对话重要性分数

        Args:
            memory_id: 记忆ID
            importance_score: 新的重要性分数

        Returns:
            更新后的记忆
        """
        memory = self.db.query(ConversationMemory).filter(
            ConversationMemory.id == memory_id
        ).first()

        if not memory:
            raise ValueError(f"对话记忆 {memory_id} 不存在")

        memory.importance_score = max(0.0, min(1.0, importance_score))
        self.db.commit()
        self.db.refresh(memory)

        return memory

    def delete_old_conversations(
        self,
        user_id: int,
        days: int = 90,
        keep_important: bool = True,
        importance_threshold: float = 0.7
    ) -> int:
        """
        删除旧的对话记录

        Args:
            user_id: 用户ID
            days: 保留天数
            keep_important: 是否保留重要对话
            importance_threshold: 重要性阈值

        Returns:
            删除的记录数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(ConversationMemory).filter(
            and_(
                ConversationMemory.user_id == user_id,
                ConversationMemory.created_at < cutoff_date
            )
        )

        if keep_important:
            query = query.filter(
                ConversationMemory.importance_score < importance_threshold
            )

        count = query.count()
        query.delete()
        self.db.commit()

        return count
