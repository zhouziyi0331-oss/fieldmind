"""Mem0长记忆服务 - 处理大量长文档和碎片化对话"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    logger.warning("Mem0 not installed. Run: pip install mem0ai")
    MEM0_AVAILABLE = False
    Memory = None


class Mem0Service:
    """Mem0长记忆服务 - 为每个项目提供独立的长记忆空间"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化Mem0服务"""
        if not MEM0_AVAILABLE:
            logger.warning("Mem0 not available - memory service disabled")
            self.memory = None
            return

        # 配置Mem0
        config = {
            "version": "v1.1",
            "llm": {
                "provider": "anthropic",
                "config": {
                    "model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.1,
                    "max_tokens": 4000,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "fieldmind_memories",
                    "path": "./chroma_db"
                }
            }
        }

        try:
            self.memory = Memory.from_config(config)
            logger.info("Mem0 memory service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.memory = None

    def add_document_memory(
        self,
        project_id: int,
        document_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """添加文档记忆"""
        if not self.memory:
            return None

        try:
            # 为项目创建唯一的user_id
            user_id = f"project_{project_id}"

            # 添加记忆
            result = self.memory.add(
                messages=[{
                    "role": "user",
                    "content": content
                }],
                user_id=user_id,
                metadata={
                    "source": "document",
                    "document_id": document_id,
                    "project_id": project_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )

            logger.info(f"Added document memory for project {project_id}, document {document_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to add document memory: {e}")
            return None

    def add_conversation_memory(
        self,
        project_id: int,
        session_id: int,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """添加对话记忆"""
        if not self.memory:
            return None

        try:
            user_id = f"project_{project_id}"

            # 添加对话记忆
            result = self.memory.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ],
                user_id=user_id,
                metadata={
                    "source": "conversation",
                    "session_id": session_id,
                    "project_id": project_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )

            logger.info(f"Added conversation memory for project {project_id}, session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to add conversation memory: {e}")
            return None

    def search_memories(
        self,
        project_id: int,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索项目记忆"""
        if not self.memory:
            return []

        try:
            user_id = f"project_{project_id}"

            # 搜索记忆
            results = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit,
                filters=filters
            )

            logger.info(f"Found {len(results)} memories for project {project_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    def get_all_memories(
        self,
        project_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取项目的所有记忆"""
        if not self.memory:
            return []

        try:
            user_id = f"project_{project_id}"

            # 获取所有记忆
            results = self.memory.get_all(
                user_id=user_id,
                limit=limit
            )

            return results

        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            return []

    def delete_project_memories(self, project_id: int) -> bool:
        """删除项目的所有记忆"""
        if not self.memory:
            return False

        try:
            user_id = f"project_{project_id}"

            # 删除所有记忆
            self.memory.reset(user_id=user_id)

            logger.info(f"Deleted all memories for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete memories: {e}")
            return False

    def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新记忆"""
        if not self.memory:
            return None

        try:
            result = self.memory.update(
                memory_id=memory_id,
                data=content,
                metadata=metadata
            )

            logger.info(f"Updated memory {memory_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return None

    def get_memory_stats(self, project_id: int) -> Dict[str, Any]:
        """获取项目记忆统计"""
        if not self.memory:
            return {
                "total_memories": 0,
                "document_memories": 0,
                "conversation_memories": 0,
                "available": False
            }

        try:
            memories = self.get_all_memories(project_id)

            document_count = sum(1 for m in memories if m.get("metadata", {}).get("source") == "document")
            conversation_count = sum(1 for m in memories if m.get("metadata", {}).get("source") == "conversation")

            return {
                "total_memories": len(memories),
                "document_memories": document_count,
                "conversation_memories": conversation_count,
                "available": True
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {
                "total_memories": 0,
                "document_memories": 0,
                "conversation_memories": 0,
                "available": False,
                "error": str(e)
            }
