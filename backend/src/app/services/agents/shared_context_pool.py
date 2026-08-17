"""
共享上下文池 - Agent协同网络的记忆中枢

设计理念：
1. 统一数据访问：所有Agent共享同一个上下文
2. 访问追踪：记录谁读了什么、谁写了什么
3. 版本控制：支持回滚到历史状态
4. 项目隔离：确保不同项目的数据不混淆

核心价值：
- Agent之间无缝数据传递
- 数据血缘可追溯
- 防止数据污染
"""

import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import copy

logger = logging.getLogger(__name__)


class ContextScope(Enum):
    """上下文作用域"""
    GLOBAL = "global"           # 全局作用域
    PROJECT = "project"         # 项目级作用域
    DOCUMENT = "document"       # 文档级作用域
    SESSION = "session"         # 会话级作用域


class AccessType(Enum):
    """访问类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


@dataclass
class ContextAccessLog:
    """上下文访问日志"""
    timestamp: datetime
    agent_id: str
    access_type: AccessType
    key: str
    scope: ContextScope
    value_snapshot: Optional[Any] = None  # 写操作时保存快照

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "access_type": self.access_type.value,
            "key": self.key,
            "scope": self.scope.value,
            "value_snapshot": str(self.value_snapshot)[:200] if self.value_snapshot else None
        }


@dataclass
class ContextEntry:
    """上下文条目"""
    key: str
    value: Any
    scope: ContextScope
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "metadata": self.metadata
        }


class SharedContextPool:
    """
    共享上下文池

    功能：
    1. 统一数据存储：所有Agent的中间结果
    2. 访问控制：记录谁访问了什么
    3. 数据隔离：项目级/文档级隔离
    4. 版本管理：支持历史回溯

    数据结构：
    ```
    {
        "global": {
            "system_config": {...},
            "agent_registry": {...}
        },
        "project:123": {
            "document_ids": [1, 2, 3],
            "entities": {...},
            "graph": {...}
        },
        "document:456": {
            "text": "...",
            "chunks": [...],
            "embeddings": [...]
        },
        "session:abc": {
            "current_query": "...",
            "search_results": [...]
        }
    }
    ```

    使用示例：
    ```python
    # 初始化
    pool = SharedContextPool()

    # 设置项目上下文
    pool.set_project(project_id=123)

    # KnowledgeAgent写入实体
    pool.set("entities", entities_data, agent_id="knowledge_agent_001")

    # SearchAgent读取实体
    entities = pool.get("entities", agent_id="search_agent_002")

    # 查看访问历史
    logs = pool.get_access_logs(key="entities")
    ```
    """

    def __init__(self, enable_logging: bool = True):
        """
        初始化共享上下文池

        Args:
            enable_logging: 是否启用访问日志
        """
        # 主存储：{scope:id -> {key -> ContextEntry}}
        self._storage: Dict[str, Dict[str, ContextEntry]] = {
            "global": {}
        }

        # 访问日志
        self._access_logs: List[ContextAccessLog] = []

        # 当前作用域
        self._current_project_id: Optional[int] = None
        self._current_document_id: Optional[int] = None
        self._current_session_id: Optional[str] = None

        # 配置
        self.enable_logging = enable_logging
        self.max_log_size = 10000  # 最多保存10000条日志

        # 统计
        self.stats = {
            "reads": 0,
            "writes": 0,
            "deletes": 0,
            "agents_active": set()
        }

        logger.info("🧠 SharedContextPool 初始化完成")

    def set_project(self, project_id: int):
        """设置当前项目"""
        self._current_project_id = project_id
        scope_key = f"project:{project_id}"

        if scope_key not in self._storage:
            self._storage[scope_key] = {}
            logger.info(f"📁 创建项目上下文: {project_id}")
        else:
            logger.info(f"📂 切换到项目上下文: {project_id}")

    def set_document(self, document_id: int):
        """设置当前文档"""
        self._current_document_id = document_id
        scope_key = f"document:{document_id}"

        if scope_key not in self._storage:
            self._storage[scope_key] = {}
            logger.info(f"📄 创建文档上下文: {document_id}")

    def set_session(self, session_id: str):
        """设置当前会话"""
        self._current_session_id = session_id
        scope_key = f"session:{session_id}"

        if scope_key not in self._storage:
            self._storage[scope_key] = {}
            logger.info(f"💬 创建会话上下文: {session_id}")

    def set(
        self,
        key: str,
        value: Any,
        agent_id: str,
        scope: Optional[ContextScope] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        设置上下文值

        Args:
            key: 键名
            value: 值
            agent_id: 操作的Agent ID
            scope: 作用域（默认根据当前上下文自动判断）
            metadata: 元数据

        Returns:
            是否成功
        """
        # 自动判断作用域
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        # 确保作用域存在
        if scope_key not in self._storage:
            self._storage[scope_key] = {}

        storage = self._storage[scope_key]

        # 检查是否已存在
        if key in storage:
            # 更新已有条目
            entry = storage[key]
            entry.value = copy.deepcopy(value)  # 深拷贝防止外部修改
            entry.updated_by = agent_id
            entry.updated_at = datetime.now()
            entry.version += 1
            if metadata:
                entry.metadata.update(metadata)

            logger.debug(f"✏️ 更新上下文: {key} @ {scope_key} (版本 {entry.version}, Agent: {agent_id})")
        else:
            # 创建新条目
            entry = ContextEntry(
                key=key,
                value=copy.deepcopy(value),
                scope=scope,
                created_by=agent_id,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            storage[key] = entry

            logger.debug(f"➕ 创建上下文: {key} @ {scope_key} (Agent: {agent_id})")

        # 记录访问日志
        self._log_access(
            agent_id=agent_id,
            access_type=AccessType.WRITE,
            key=key,
            scope=scope,
            value_snapshot=value
        )

        # 统计
        self.stats["writes"] += 1
        self.stats["agents_active"].add(agent_id)

        return True

    def get(
        self,
        key: str,
        agent_id: str,
        scope: Optional[ContextScope] = None,
        default: Any = None
    ) -> Any:
        """
        获取上下文值

        Args:
            key: 键名
            agent_id: 操作的Agent ID
            scope: 作用域（默认根据当前上下文自动判断）
            default: 默认值

        Returns:
            值（如果不存在返回default）
        """
        # 自动判断作用域
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        # 检查作用域是否存在
        if scope_key not in self._storage:
            logger.debug(f"⚠️ 作用域不存在: {scope_key}")
            return default

        storage = self._storage[scope_key]

        # 获取值
        if key not in storage:
            logger.debug(f"⚠️ 键不存在: {key} @ {scope_key}")
            return default

        entry = storage[key]
        value = copy.deepcopy(entry.value)  # 深拷贝防止外部修改

        logger.debug(f"📖 读取上下文: {key} @ {scope_key} (Agent: {agent_id})")

        # 记录访问日志
        self._log_access(
            agent_id=agent_id,
            access_type=AccessType.READ,
            key=key,
            scope=scope
        )

        # 统计
        self.stats["reads"] += 1
        self.stats["agents_active"].add(agent_id)

        return value

    def get_all(
        self,
        agent_id: str,
        scope: Optional[ContextScope] = None
    ) -> Dict[str, Any]:
        """
        获取当前作用域的所有上下文

        Args:
            agent_id: 操作的Agent ID
            scope: 作用域

        Returns:
            所有键值对
        """
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        if scope_key not in self._storage:
            return {}

        storage = self._storage[scope_key]

        # 返回所有键值对（深拷贝）
        result = {
            key: copy.deepcopy(entry.value)
            for key, entry in storage.items()
        }

        logger.debug(f"📚 读取所有上下文: {scope_key} ({len(result)} 项, Agent: {agent_id})")

        return result

    def delete(
        self,
        key: str,
        agent_id: str,
        scope: Optional[ContextScope] = None
    ) -> bool:
        """
        删除上下文值

        Args:
            key: 键名
            agent_id: 操作的Agent ID
            scope: 作用域

        Returns:
            是否成功
        """
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        if scope_key not in self._storage:
            return False

        storage = self._storage[scope_key]

        if key not in storage:
            return False

        del storage[key]

        logger.debug(f"🗑️ 删除上下文: {key} @ {scope_key} (Agent: {agent_id})")

        # 记录访问日志
        self._log_access(
            agent_id=agent_id,
            access_type=AccessType.DELETE,
            key=key,
            scope=scope
        )

        # 统计
        self.stats["deletes"] += 1

        return True

    def exists(
        self,
        key: str,
        scope: Optional[ContextScope] = None
    ) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名
            scope: 作用域

        Returns:
            是否存在
        """
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        if scope_key not in self._storage:
            return False

        return key in self._storage[scope_key]

    def get_entry(
        self,
        key: str,
        scope: Optional[ContextScope] = None
    ) -> Optional[ContextEntry]:
        """
        获取完整的上下文条目（包含元数据）

        Args:
            key: 键名
            scope: 作用域

        Returns:
            ContextEntry或None
        """
        if scope is None:
            scope = self._infer_scope()

        scope_key = self._get_scope_key(scope)

        if scope_key not in self._storage:
            return None

        storage = self._storage[scope_key]

        return storage.get(key)

    def _infer_scope(self) -> ContextScope:
        """自动推断作用域"""
        if self._current_document_id is not None:
            return ContextScope.DOCUMENT
        elif self._current_project_id is not None:
            return ContextScope.PROJECT
        elif self._current_session_id is not None:
            return ContextScope.SESSION
        else:
            return ContextScope.GLOBAL

    def _get_scope_key(self, scope: ContextScope) -> str:
        """获取作用域键"""
        if scope == ContextScope.GLOBAL:
            return "global"
        elif scope == ContextScope.PROJECT:
            if self._current_project_id is None:
                raise ValueError("当前未设置项目ID")
            return f"project:{self._current_project_id}"
        elif scope == ContextScope.DOCUMENT:
            if self._current_document_id is None:
                raise ValueError("当前未设置文档ID")
            return f"document:{self._current_document_id}"
        elif scope == ContextScope.SESSION:
            if self._current_session_id is None:
                raise ValueError("当前未设置会话ID")
            return f"session:{self._current_session_id}"
        else:
            raise ValueError(f"未知作用域: {scope}")

    def _log_access(
        self,
        agent_id: str,
        access_type: AccessType,
        key: str,
        scope: ContextScope,
        value_snapshot: Optional[Any] = None
    ):
        """记录访问日志"""
        if not self.enable_logging:
            return

        log = ContextAccessLog(
            timestamp=datetime.now(),
            agent_id=agent_id,
            access_type=access_type,
            key=key,
            scope=scope,
            value_snapshot=value_snapshot
        )

        self._access_logs.append(log)

        # 限制日志大小
        if len(self._access_logs) > self.max_log_size:
            self._access_logs = self._access_logs[-self.max_log_size:]

    def get_access_logs(
        self,
        key: Optional[str] = None,
        agent_id: Optional[str] = None,
        access_type: Optional[AccessType] = None,
        limit: int = 100
    ) -> List[ContextAccessLog]:
        """
        获取访问日志

        Args:
            key: 过滤键名
            agent_id: 过滤Agent ID
            access_type: 过滤访问类型
            limit: 返回数量限制

        Returns:
            日志列表
        """
        logs = self._access_logs

        # 过滤
        if key:
            logs = [log for log in logs if log.key == key]
        if agent_id:
            logs = [log for log in logs if log.agent_id == agent_id]
        if access_type:
            logs = [log for log in logs if log.access_type == access_type]

        # 限制数量
        return logs[-limit:]

    def get_data_lineage(self, key: str) -> List[Dict[str, Any]]:
        """
        获取数据血缘（追踪数据的创建和修改历史）

        Args:
            key: 键名

        Returns:
            血缘链：[{agent, action, timestamp, version}, ...]
        """
        logs = self.get_access_logs(key=key)

        lineage = []
        for log in logs:
            if log.access_type in [AccessType.WRITE]:
                lineage.append({
                    "agent_id": log.agent_id,
                    "action": log.access_type.value,
                    "timestamp": log.timestamp.isoformat(),
                    "scope": log.scope.value
                })

        return lineage

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "reads": self.stats["reads"],
            "writes": self.stats["writes"],
            "deletes": self.stats["deletes"],
            "agents_active": len(self.stats["agents_active"]),
            "scopes_count": len(self._storage),
            "total_entries": sum(len(storage) for storage in self._storage.values()),
            "log_size": len(self._access_logs)
        }

    def clear_scope(self, scope: ContextScope):
        """清空指定作用域"""
        scope_key = self._get_scope_key(scope)

        if scope_key in self._storage:
            self._storage[scope_key].clear()
            logger.info(f"🗑️ 清空作用域: {scope_key}")

    def export_context(self, scope: Optional[ContextScope] = None) -> Dict[str, Any]:
        """
        导出上下文（用于调试或持久化）

        Args:
            scope: 作用域（None表示导出所有）

        Returns:
            上下文数据
        """
        if scope is None:
            # 导出所有作用域
            return {
                scope_key: {
                    key: entry.to_dict()
                    for key, entry in storage.items()
                }
                for scope_key, storage in self._storage.items()
            }
        else:
            # 导出指定作用域
            scope_key = self._get_scope_key(scope)
            if scope_key not in self._storage:
                return {}

            return {
                key: entry.to_dict()
                for key, entry in self._storage[scope_key].items()
            }


# 全局共享上下文池实例
shared_context_pool = SharedContextPool()
