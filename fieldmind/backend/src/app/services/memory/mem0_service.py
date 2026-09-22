"""
Mem0 长期记忆服务

提供 AI 长期记忆能力：
- 用户对话历史存储
- 用户偏好学习
- 上下文保持
- 语义记忆搜索
- 知识积累
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Mem0Service:
    """
    Mem0 长期记忆服务

    封装 mem0 提供统一记忆接口
    """

    def __init__(self, db=None):
        self.db = db
        self._mem0 = None
        self._initialized = False

        # 尝试导入 mem0
        try:
            from mem0 import Memory
            self._Memory = Memory
            self._initialize_memory()
            self._initialized = True
            logger.info("✅ Mem0 记忆服务初始化成功")
        except ImportError:
            logger.warning("⚠️ Mem0 未安装，请运行: pip install mem0ai")
        except Exception as e:
            logger.error(f"❌ Mem0 初始化失败: {e}")

    def _initialize_memory(self):
        """初始化 Mem0 记忆系统"""
        try:
            # 配置 mem0
            config = {
                "vector_store": {
                    "provider": "chroma",  # 使用 ChromaDB 作为向量存储
                    "config": {
                        "collection_name": "fieldmind_memory",
                        "path": "./data/memory_db"
                    }
                }
            }

            self._mem0 = self._Memory.from_config(config)
            logger.info("✅ Mem0 记忆系统配置成功")
        except Exception as e:
            logger.warning(f"⚠️ Mem0 配置失败，使用默认设置: {e}")
            try:
                self._mem0 = self._Memory()
            except:
                self._mem0 = None

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized and self._mem0 is not None

    # ==================== 记忆存储 ====================

    def store_memory(
        self,
        user_id: int,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储记忆

        Args:
            user_id: 用户ID
            content: 记忆内容
            context: 上下文信息
            metadata: 元数据

        Returns:
            记忆ID
        """
        if not self.is_available():
            logger.warning("Mem0 不可用，使用数据库存储")
            return self._store_to_database(user_id, content, context, metadata)

        try:
            # 使用 mem0 存储
            memory_data = {
                "messages": [{"role": "user", "content": content}],
                "user_id": str(user_id)
            }

            if metadata:
                memory_data["metadata"] = metadata

            result = self._mem0.add(**memory_data)

            # 提取记忆ID
            memory_id = result.get("id") if isinstance(result, dict) else str(result)

            logger.info(f"✅ 记忆已存储: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"记忆存储失败: {e}")
            # 降级到数据库
            return self._store_to_database(user_id, content, context, metadata)

    def _store_to_database(
        self,
        user_id: int,
        content: str,
        context: Optional[Dict],
        metadata: Optional[Dict]
    ) -> str:
        """降级：存储到数据库"""
        if not self.db:
            raise RuntimeError("数据库不可用")

        # TODO: 实现数据库存储
        logger.warning("数据库存储功能待实现")
        return f"db_memory_{user_id}_{datetime.now().timestamp()}"

    # ==================== 记忆检索 ====================

    def search_memory(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            user_id: 用户ID
            query: 查询内容
            limit: 返回数量

        Returns:
            记忆列表
        """
        if not self.is_available():
            logger.warning("Mem0 不可用，无法搜索记忆")
            return []

        try:
            # 使用 mem0 搜索
            results = self._mem0.search(
                query=query,
                user_id=str(user_id),
                limit=limit
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"记忆搜索失败: {e}")
            return []

    def _format_search_results(self, results) -> List[Dict[str, Any]]:
        """格式化搜索结果"""
        formatted = []

        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    formatted.append({
                        "id": item.get("id"),
                        "content": item.get("memory") or item.get("content"),
                        "score": item.get("score", 0.0),
                        "metadata": item.get("metadata", {})
                    })

        return formatted

    # ==================== 获取用户记忆 ====================

    def get_user_memories(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有记忆

        Args:
            user_id: 用户ID
            limit: 返回数量

        Returns:
            记忆列表
        """
        if not self.is_available():
            logger.warning("Mem0 不可用")
            return []

        try:
            # 获取用户记忆
            results = self._mem0.get_all(
                user_id=str(user_id),
                limit=limit
            )

            return self._format_search_results(results)

        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return []

    # ==================== 获取对话上下文 ====================

    def get_conversation_context(
        self,
        user_id: int,
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取对话上下文

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            limit: 上下文条数

        Returns:
            上下文列表
        """
        if not self.is_available():
            return []

        try:
            # 构建查询过滤器
            filters = {"user_id": str(user_id)}
            if conversation_id:
                filters["conversation_id"] = conversation_id

            # 获取最近的对话
            memories = self.get_user_memories(user_id, limit)

            # 过滤相关记忆
            context = []
            for memory in memories[:limit]:
                context.append({
                    "content": memory.get("content", ""),
                    "timestamp": memory.get("metadata", {}).get("timestamp"),
                    "role": memory.get("metadata", {}).get("role", "user")
                })

            return context

        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return []

    # ==================== 删除记忆 ====================

    def delete_memory(
        self,
        memory_id: str,
        user_id: int
    ) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        if not self.is_available():
            logger.warning("Mem0 不可用")
            return False

        try:
            self._mem0.delete(memory_id)
            logger.info(f"✅ 记忆已删除: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    # ==================== 更新记忆 ====================

    def update_memory(
        self,
        memory_id: str,
        user_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新记忆

        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            content: 新内容
            metadata: 新元数据

        Returns:
            是否成功
        """
        if not self.is_available():
            logger.warning("Mem0 不可用")
            return False

        try:
            # mem0 可能不直接支持更新，需要删除后重新添加
            self.delete_memory(memory_id, user_id)
            self.store_memory(user_id, content, metadata=metadata)

            logger.info(f"✅ 记忆已更新: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return False

    # ==================== 清除用户记忆 ====================

    def clear_user_memories(
        self,
        user_id: int
    ) -> bool:
        """
        清除用户的所有记忆

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        if not self.is_available():
            logger.warning("Mem0 不可用")
            return False

        try:
            # 获取所有记忆
            memories = self.get_user_memories(user_id, limit=1000)

            # 删除所有记忆
            for memory in memories:
                memory_id = memory.get("id")
                if memory_id:
                    self.delete_memory(memory_id, user_id)

            logger.info(f"✅ 用户 {user_id} 的记忆已清除")
            return True

        except Exception as e:
            logger.error(f"清除记忆失败: {e}")
            return False

    # ==================== 用户偏好学习 ====================

    def learn_user_preference(
        self,
        user_id: int,
        preference_type: str,
        preference_value: Any
    ) -> str:
        """
        学习用户偏好

        Args:
            user_id: 用户ID
            preference_type: 偏好类型（如：language, topic, style）
            preference_value: 偏好值

        Returns:
            记忆ID
        """
        content = f"用户偏好: {preference_type} = {preference_value}"

        return self.store_memory(
            user_id=user_id,
            content=content,
            metadata={
                "type": "preference",
                "preference_type": preference_type,
                "preference_value": preference_value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def get_user_preferences(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户ID

        Returns:
            偏好字典
        """
        memories = self.get_user_memories(user_id, limit=100)

        preferences = {}
        for memory in memories:
            metadata = memory.get("metadata", {})
            if metadata.get("type") == "preference":
                pref_type = metadata.get("preference_type")
                pref_value = metadata.get("preference_value")
                if pref_type:
                    preferences[pref_type] = pref_value

        return preferences

    # ==================== 记忆统计 ====================

    def get_memory_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        try:
            memories = self.get_user_memories(user_id, limit=1000)

            return {
                "total_memories": len(memories),
                "preferences_count": sum(
                    1 for m in memories
                    if m.get("metadata", {}).get("type") == "preference"
                ),
                "conversations_count": sum(
                    1 for m in memories
                    if m.get("metadata", {}).get("type") == "conversation"
                ),
                "oldest_memory": memories[-1].get("metadata", {}).get("timestamp") if memories else None,
                "newest_memory": memories[0].get("metadata", {}).get("timestamp") if memories else None
            }

        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {
                "total_memories": 0,
                "preferences_count": 0,
                "conversations_count": 0
            }


# ==================== 全局单例 ====================

_mem0_service: Optional[Mem0Service] = None


def get_mem0_service(db=None) -> Mem0Service:
    """获取 Mem0 服务单例"""
    global _mem0_service

    if _mem0_service is None:
        _mem0_service = Mem0Service(db)

    return _mem0_service
