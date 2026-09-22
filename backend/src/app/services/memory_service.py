"""项目长记忆服务 - 三层记忆架构"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import json

from app.models.project import ProjectMemory, ProjectDocument, ProjectChatMessage
from app.schemas.project import ProjectMemoryCreate, ProjectMemorySearchRequest


class MemoryService:
    """三层记忆管理服务

    short_term: 最近的对话和文档片段（7天内）
    mid_term: 重要的概念和关键信息（1个月内）
    long_term: 核心知识和长期记忆（持久化）
    """
    def __init__(self, db: Session, project_id: int, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.project_id = project_id

    async def create_memory(
        self,
        content: str,
        memory_type: str,
        summary: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectMemory:
        """创建新记忆"""
        memory = ProjectMemory(
            project_id=self.project_id,
            memory_type=memory_type,
            content=content,
            summary=summary or content[:200],
            source_type=source_type,
            source_id=source_id,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return memory

    async def search_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        top_k: int = 10,
        relevance_threshold: float = 0.7
    ) -> List[ProjectMemory]:
        """搜索记忆

        TODO: 实现向量相似度搜索
        目前使用简单的文本匹配
        """
        query_base = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id
        )

        if memory_types:
            query_base = query_base.filter(ProjectMemory.memory_type.in_(memory_types))

        # 简单文本匹配（后续替换为向量搜索）
        memories = query_base.filter(
            ProjectMemory.content.contains(query) |
            ProjectMemory.summary.contains(query)
        ).order_by(
            desc(ProjectMemory.relevance_score),
            desc(ProjectMemory.access_count),
            desc(ProjectMemory.created_at)
        ).limit(top_k).all()

        # 更新访问计数和时间
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed_at = datetime.utcnow()

        self.db.commit()

        return memories

    async def retrieve_context(
        self,
        query: str,
        max_tokens: int = 4000,
        include_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """检索对话上下文

        优先级：long_term > mid_term > short_term
        按相关度和访问频率排序
        """
        if include_types is None:
            include_types = ["short_term", "mid_term", "long_term"]

        # 分层检索
        context = {
            "long_term": [],
            "mid_term": [],
            "short_term": [],
            "total_tokens": 0
        }

        for memory_type in ["long_term", "mid_term", "short_term"]:
            if memory_type not in include_types:
                continue

            memories = await self.search_memories(
                query=query,
                memory_types=[memory_type],
                top_k=5
            )

            for memory in memories:
                # 估算token数（粗略估计：1 token ≈ 4 characters）
                estimated_tokens = len(memory.content) // 4

                if context["total_tokens"] + estimated_tokens > max_tokens:
                    break

                context[memory_type].append({
                    "id": memory.id,
                    "content": memory.content,
                    "summary": memory.summary,
                    "source_type": memory.source_type,
                    "relevance_score": memory.relevance_score,
                    "access_count": memory.access_count
                })

                context["total_tokens"] += estimated_tokens

        return context

    async def consolidate_memories(self, days: int = 7):
        """记忆整合：将短期记忆提升为中期/长期记忆

        规则：
        - 访问次数 >= 5 的短期记忆 -> 中期记忆
        - 访问次数 >= 10 的中期记忆 -> 长期记忆
        - 相关度分数 >= 80 的记忆直接提升
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 提升短期记忆到中期
        short_term_candidates = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "short_term",
            ProjectMemory.created_at <= cutoff_date,
            (ProjectMemory.access_count >= 5) | (ProjectMemory.relevance_score >= 80)
        ).all()

        for memory in short_term_candidates:
            memory.memory_type = "mid_term"
            memory.relevance_score += 10

        # 提升中期记忆到长期
        mid_term_candidates = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "mid_term",
            (ProjectMemory.access_count >= 10) | (ProjectMemory.relevance_score >= 90)
        ).all()

        for memory in mid_term_candidates:
            memory.memory_type = "long_term"
            memory.relevance_score = min(100, memory.relevance_score + 10)

        self.db.commit()

        return {
            "promoted_to_mid_term": len(short_term_candidates),
            "promoted_to_long_term": len(mid_term_candidates)
        }

    async def cleanup_old_memories(self, days: int = 30):
        """清理旧的短期记忆（访问次数少且时间久远）"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_memories = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "short_term",
            ProjectMemory.created_at <= cutoff_date,
            ProjectMemory.access_count < 3,
            ProjectMemory.relevance_score < 50
        ).all()

        count = len(old_memories)

        for memory in old_memories:
            self.db.delete(memory)

        self.db.commit()

        return {"deleted_count": count}

    async def extract_from_document(self, document_id: int):
        """从文档提取记忆"""
        from app.models.project import ProjectDocument

        document = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == self.project_id
        ).first()

        if not document:
            return None

        # 创建文档摘要记忆
        if document.summary:
            await self.create_memory(
                content=document.summary,
                memory_type="mid_term",
                summary=document.summary[:200],
                source_type="document",
                source_id=str(document_id),
                metadata={
                    "filename": document.filename,
                    "file_type": document.file_type,
                    "keywords": document.keywords or []
                }
            )

        # 创建关键词记忆
        if document.keywords:
            keywords_text = "关键词: " + ", ".join(document.keywords)
            await self.create_memory(
                content=keywords_text,
                memory_type="long_term",
                summary=keywords_text,
                source_type="document",
                source_id=str(document_id),
                metadata={
                    "filename": document.filename,
                    "keywords": document.keywords
                }
            )

        # 创建实体记忆
        if document.entities:
            for entity in document.entities[:10]:  # 限制前10个实体
                entity_text = f"{entity.get('type', 'Entity')}: {entity.get('text', '')}"
                await self.create_memory(
                    content=entity_text,
                    memory_type="long_term",
                    summary=entity_text,
                    source_type="document",
                    source_id=str(document_id),
                    metadata={
                        "filename": document.filename,
                        "entity": entity
                    }
                )

        return {"status": "success", "document_id": document_id}

    async def extract_from_chat(self, session_id: int, message_id: int):
        """从对话提取记忆"""
        from app.models.project import ProjectChatMessage

        message = self.db.query(ProjectChatMessage).filter(
            ProjectChatMessage.id == message_id,
            ProjectChatMessage.session_id == session_id
        ).first()

        if not message or message.role != "assistant":
            return None

        # 提取助手回复为短期记忆
        await self.create_memory(
            content=message.content,
            memory_type="short_term",
            summary=message.content[:200],
            source_type="chat",
            source_id=str(message_id),
            metadata={
                "session_id": session_id,
                "has_thinking": bool(message.thinking_process),
                "sources": message.sources or []
            }
        )

        return {"status": "success", "message_id": message_id}

    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {}

        for memory_type in ["short_term", "mid_term", "long_term"]:
            count = self.db.query(func.count(ProjectMemory.id)).filter(
                ProjectMemory.project_id == self.project_id,
                ProjectMemory.memory_type == memory_type
            ).scalar()

            avg_relevance = self.db.query(func.avg(ProjectMemory.relevance_score)).filter(
                ProjectMemory.project_id == self.project_id,
                ProjectMemory.memory_type == memory_type
            ).scalar() or 0

            stats[memory_type] = {
                "count": count,
                "avg_relevance": round(avg_relevance, 2)
            }

        return stats
