"""
Agent记忆绑定服务 - 链路十三核心模块
将项目记忆注入到LLM的system prompt中，使AI能够记住用户偏好和上下文
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.project import ProjectMemory, Project, ProjectChatSession, ProjectChatMessage
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class MemoryInjector:
    """记忆注入器 - 将记忆转换为系统提示词"""

    def __init__(self, db: Session, project_id: int):
        self.db = db
        self.project_id = project_id
        self.memory_service = MemoryService(db, project_id)

    def build_system_prompt(
        self,
        base_prompt: str,
        user_query: Optional[str] = None,
        include_short_term: bool = True,
        include_mid_term: bool = True,
        include_long_term: bool = True,
        max_memories: int = 10
    ) -> str:
        """
        构建包含记忆的系统提示词

        Args:
            base_prompt: 基础系统提示词
            user_query: 用户查询（用于检索相关记忆）
            include_short_term: 是否包含短期记忆
            include_mid_term: 是否包含中期记忆
            include_long_term: 是否包含长期记忆
            max_memories: 最多包含的记忆数量

        Returns:
            完整的系统提示词
        """
        logger.info(f"🧠 为项目 {self.project_id} 构建记忆增强提示词")

        # 1. 获取项目基本信息
        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        if not project:
            logger.warning(f"项目 {self.project_id} 不存在")
            return base_prompt

        # 2. 收集记忆
        memories = self._collect_memories(
            user_query,
            include_short_term,
            include_mid_term,
            include_long_term,
            max_memories
        )

        if not memories:
            logger.info("没有可用的记忆，使用基础提示词")
            return base_prompt

        # 3. 构建记忆部分
        memory_section = self._format_memories(memories)

        # 4. 拼接完整提示词
        enhanced_prompt = f"""{base_prompt}

# 项目记忆与上下文

你正在为项目「{project.name}」提供服务。以下是该项目的重要记忆和上下文信息：

{memory_section}

请在回答时参考这些记忆，但不要直接引用"记忆"这个词。自然地运用这些信息来提供更个性化、更有针对性的回答。
"""

        logger.info(f"✅ 记忆注入完成，添加了 {len(memories)} 条记忆")
        return enhanced_prompt

    def _collect_memories(
        self,
        user_query: Optional[str],
        include_short_term: bool,
        include_mid_term: bool,
        include_long_term: bool,
        max_memories: int
    ) -> List[ProjectMemory]:
        """收集相关记忆"""
        # 确定要查询的记忆类型
        memory_types = []
        if include_short_term:
            memory_types.append("short_term")
        if include_mid_term:
            memory_types.append("mid_term")
        if include_long_term:
            memory_types.append("long_term")

        if not memory_types:
            return []

        # 查询记忆
        query = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type.in_(memory_types)
        )

        # 如果有用户查询，尝试相关性过滤
        if user_query:
            # 简单的关键词匹配（后续可升级为向量搜索）
            query = query.filter(
                ProjectMemory.content.contains(user_query) |
                ProjectMemory.summary.contains(user_query)
            )

        # 排序：按相关性、访问次数、创建时间
        memories = query.order_by(
            ProjectMemory.relevance_score.desc(),
            ProjectMemory.access_count.desc(),
            ProjectMemory.created_at.desc()
        ).limit(max_memories).all()

        # 更新访问记录
        for memory in memories:
            memory.access_count += 1
            memory.last_accessed_at = datetime.utcnow()

        self.db.commit()

        return memories

    def _format_memories(self, memories: List[ProjectMemory]) -> str:
        """格式化记忆为文本"""
        sections = {
            "long_term": [],
            "mid_term": [],
            "short_term": []
        }

        for memory in memories:
            sections[memory.memory_type].append(memory)

        output = []

        # 长期记忆（核心知识）
        if sections["long_term"]:
            output.append("## 核心知识与长期记忆\n")
            for i, mem in enumerate(sections["long_term"], 1):
                output.append(f"{i}. {mem.summary or mem.content[:200]}")
                if mem.extra_data and mem.extra_data.get("keywords"):
                    output.append(f"   关键词: {', '.join(mem.extra_data['keywords'][:5])}")
            output.append("")

        # 中期记忆（重要概念）
        if sections["mid_term"]:
            output.append("## 重要概念与中期记忆\n")
            for i, mem in enumerate(sections["mid_term"], 1):
                output.append(f"{i}. {mem.summary or mem.content[:150]}")
            output.append("")

        # 短期记忆（最近上下文）
        if sections["short_term"]:
            output.append("## 最近上下文与短期记忆\n")
            for i, mem in enumerate(sections["short_term"], 1):
                output.append(f"{i}. {mem.summary or mem.content[:100]}")
            output.append("")

        return "\n".join(output)

    def create_memory_from_chat(
        self,
        session_id: int,
        message_id: int,
        memory_type: str = "short_term",
        importance_score: float = 0.5
    ) -> ProjectMemory:
        """
        从对话消息创建记忆

        Args:
            session_id: 会话ID
            message_id: 消息ID
            memory_type: 记忆类型
            importance_score: 重要性评分
        """
        message = self.db.query(ProjectChatMessage).filter(
            ProjectChatMessage.id == message_id
        ).first()

        if not message:
            raise ValueError(f"消息 {message_id} 不存在")

        # 提取关键信息作为摘要
        summary = message.content[:200] if len(message.content) > 200 else message.content

        memory = ProjectMemory(
            project_id=self.project_id,
            memory_type=memory_type,
            content=message.content,
            summary=summary,
            source_type="chat",
            source_id=str(message_id),
            relevance_score=int(importance_score * 100),
            extra_data={
                "session_id": session_id,
                "role": message.role,
                "importance_score": importance_score,
                "created_from": "chat_message"
            }
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        logger.info(f"✅ 从对话创建记忆: {memory.id} ({memory_type})")
        return memory

    def create_memory_from_document(
        self,
        document_id: int,
        content: str,
        summary: Optional[str] = None,
        memory_type: str = "mid_term"
    ) -> ProjectMemory:
        """
        从文档创建记忆

        Args:
            document_id: 文档ID
            content: 记忆内容
            summary: 摘要
            memory_type: 记忆类型
        """
        memory = ProjectMemory(
            project_id=self.project_id,
            memory_type=memory_type,
            content=content,
            summary=summary or content[:200],
            source_type="document",
            source_id=str(document_id),
            relevance_score=50,
            extra_data={
                "document_id": document_id,
                "created_from": "document_analysis"
            }
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        logger.info(f"✅ 从文档创建记忆: {memory.id} ({memory_type})")
        return memory

    def promote_memory(self, memory_id: int, target_type: str) -> ProjectMemory:
        """
        升级记忆层级

        short_term → mid_term → long_term
        """
        memory = self.db.query(ProjectMemory).filter(
            ProjectMemory.id == memory_id,
            ProjectMemory.project_id == self.project_id
        ).first()

        if not memory:
            raise ValueError(f"记忆 {memory_id} 不存在")

        old_type = memory.memory_type
        memory.memory_type = target_type

        # 提升相关性评分
        memory.relevance_score = min(100, memory.relevance_score + 20)

        self.db.commit()
        logger.info(f"📈 记忆升级: {memory_id} ({old_type} → {target_type})")

        return memory

    def auto_promote_memories(self):
        """
        自动升级高价值记忆

        规则：
        - 访问次数 > 10 且是 short_term → 升级为 mid_term
        - 访问次数 > 30 且是 mid_term → 升级为 long_term
        - 相关性评分 > 80 → 升级一级
        """
        # 短期 → 中期
        short_to_mid = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "short_term",
            ProjectMemory.access_count > 10
        ).all()

        for memory in short_to_mid:
            memory.memory_type = "mid_term"
            memory.relevance_score = min(100, memory.relevance_score + 10)
            logger.info(f"📈 自动升级记忆 {memory.id}: short_term → mid_term")

        # 中期 → 长期
        mid_to_long = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "mid_term",
            ProjectMemory.access_count > 30
        ).all()

        for memory in mid_to_long:
            memory.memory_type = "long_term"
            memory.relevance_score = min(100, memory.relevance_score + 10)
            logger.info(f"📈 自动升级记忆 {memory.id}: mid_term → long_term")

        # 高相关性快速升级
        high_relevance = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.relevance_score > 80,
            ProjectMemory.memory_type.in_(["short_term", "mid_term"])
        ).all()

        for memory in high_relevance:
            if memory.memory_type == "short_term":
                memory.memory_type = "mid_term"
            elif memory.memory_type == "mid_term":
                memory.memory_type = "long_term"
            logger.info(f"⚡ 高相关性快速升级记忆 {memory.id}")

        self.db.commit()
        logger.info(f"✅ 自动升级完成: {len(short_to_mid) + len(mid_to_long) + len(high_relevance)} 条记忆")

    def cleanup_old_memories(self, days: int = 30):
        """
        清理过期的短期记忆

        Args:
            days: 保留天数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == self.project_id,
            ProjectMemory.memory_type == "short_term",
            ProjectMemory.created_at < cutoff_date,
            ProjectMemory.access_count < 3  # 访问次数少的才删除
        ).delete(synchronize_session=False)

        self.db.commit()
        logger.info(f"🗑️ 清理了 {deleted} 条过期短期记忆")

        return deleted


def get_memory_injector(db: Session, project_id: int) -> MemoryInjector:
    """获取记忆注入器实例"""
    return MemoryInjector(db, project_id)
