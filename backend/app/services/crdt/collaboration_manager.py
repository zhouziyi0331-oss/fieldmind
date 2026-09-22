"""
协作管理器

管理多用户协作会话、光标位置和用户状态
"""
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserCursor:
    """用户光标位置"""
    user_id: int
    username: str
    position: int
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    color: str = "#3b82f6"  # 默认蓝色
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "position": self.position,
            "selection_start": self.selection_start,
            "selection_end": self.selection_end,
            "color": self.color,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    document_id: str
    user_id: int
    username: str
    joined_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def update_activity(self) -> None:
        """更新活动时间"""
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "username": self.username,
            "joined_at": self.joined_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active
        }


class CollaborationManager:
    """
    协作管理器

    管理协作会话、用户光标和实时状态
    """

    # 用户颜色调色板
    USER_COLORS = [
        "#3b82f6",  # 蓝色
        "#10b981",  # 绿色
        "#f59e0b",  # 橙色
        "#ef4444",  # 红色
        "#8b5cf6",  # 紫色
        "#ec4899",  # 粉色
        "#06b6d4",  # 青色
        "#f97316",  # 深橙色
    ]

    def __init__(self):
        """初始化管理器"""
        # 文档 -> 会话列表
        self.sessions: Dict[str, List[CollaborationSession]] = {}

        # 文档 -> 用户 -> 光标
        self.cursors: Dict[str, Dict[int, UserCursor]] = {}

        # 会话 ID -> 会话
        self.session_map: Dict[str, CollaborationSession] = {}

        # 用户 -> 分配的颜色索引
        self.user_colors: Dict[int, int] = {}

        # 会话超时时间（秒）
        self.session_timeout = 300  # 5 分钟

    def create_session(
        self,
        session_id: str,
        document_id: str,
        user_id: int,
        username: str
    ) -> CollaborationSession:
        """
        创建协作会话

        Args:
            session_id: 会话 ID
            document_id: 文档 ID
            user_id: 用户 ID
            username: 用户名

        Returns:
            协作会话
        """
        session = CollaborationSession(
            session_id=session_id,
            document_id=document_id,
            user_id=user_id,
            username=username
        )

        # 添加到文档会话列表
        if document_id not in self.sessions:
            self.sessions[document_id] = []
        self.sessions[document_id].append(session)

        # 添加到会话映射
        self.session_map[session_id] = session

        # 分配用户颜色
        if user_id not in self.user_colors:
            color_index = len(self.user_colors) % len(self.USER_COLORS)
            self.user_colors[user_id] = color_index

        # 初始化光标
        if document_id not in self.cursors:
            self.cursors[document_id] = {}

        color = self.USER_COLORS[self.user_colors[user_id]]
        self.cursors[document_id][user_id] = UserCursor(
            user_id=user_id,
            username=username,
            position=0,
            color=color
        )

        logger.info(f"Created collaboration session {session_id} for user {user_id} on document {document_id}")
        return session

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """获取会话"""
        return self.session_map.get(session_id)

    def update_session_activity(self, session_id: str) -> bool:
        """
        更新会话活动时间

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        session = self.session_map.get(session_id)
        if session:
            session.update_activity()
            return True
        return False

    def close_session(self, session_id: str) -> bool:
        """
        关闭会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        session = self.session_map.get(session_id)
        if not session:
            return False

        # 标记为非活跃
        session.is_active = False

        # 从文档会话列表中移除
        doc_sessions = self.sessions.get(session.document_id, [])
        self.sessions[session.document_id] = [s for s in doc_sessions if s.session_id != session_id]

        # 移除光标
        if session.document_id in self.cursors:
            self.cursors[session.document_id].pop(session.user_id, None)

        # 从会话映射中移除
        del self.session_map[session_id]

        logger.info(f"Closed collaboration session {session_id}")
        return True

    def get_document_sessions(self, document_id: str) -> List[CollaborationSession]:
        """获取文档的所有活跃会话"""
        return self.sessions.get(document_id, [])

    def get_active_users(self, document_id: str) -> List[Dict[str, Any]]:
        """
        获取文档的活跃用户列表

        Args:
            document_id: 文档 ID

        Returns:
            用户信息列表
        """
        sessions = self.get_document_sessions(document_id)
        users = []

        for session in sessions:
            if session.is_active:
                cursor = self.cursors.get(document_id, {}).get(session.user_id)
                users.append({
                    "user_id": session.user_id,
                    "username": session.username,
                    "color": cursor.color if cursor else "#3b82f6",
                    "joined_at": session.joined_at.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                })

        return users

    def update_cursor(
        self,
        document_id: str,
        user_id: int,
        position: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None
    ) -> bool:
        """
        更新用户光标位置

        Args:
            document_id: 文档 ID
            user_id: 用户 ID
            position: 光标位置
            selection_start: 选区起始位置
            selection_end: 选区结束位置

        Returns:
            是否成功
        """
        if document_id not in self.cursors:
            return False

        cursor = self.cursors[document_id].get(user_id)
        if not cursor:
            return False

        cursor.position = position
        cursor.selection_start = selection_start
        cursor.selection_end = selection_end
        cursor.last_updated = datetime.now()

        return True

    def get_cursors(self, document_id: str) -> List[Dict[str, Any]]:
        """
        获取文档的所有光标

        Args:
            document_id: 文档 ID

        Returns:
            光标信息列表
        """
        doc_cursors = self.cursors.get(document_id, {})
        return [cursor.to_dict() for cursor in doc_cursors.values()]

    def cleanup_inactive_sessions(self) -> int:
        """
        清理不活跃的会话

        Returns:
            清理的会话数量
        """
        now = datetime.now()
        cleaned = 0

        # 收集要关闭的会话
        sessions_to_close = []

        for session_id, session in self.session_map.items():
            if session.is_active:
                inactive_time = (now - session.last_activity).total_seconds()
                if inactive_time > self.session_timeout:
                    sessions_to_close.append(session_id)

        # 关闭会话
        for session_id in sessions_to_close:
            if self.close_session(session_id):
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} inactive sessions")

        return cleaned

    def get_session_count(self, document_id: Optional[str] = None) -> int:
        """
        获取会话数量

        Args:
            document_id: 文档 ID（可选，不提供则返回所有会话数）

        Returns:
            会话数量
        """
        if document_id:
            return len(self.sessions.get(document_id, []))
        else:
            return len(self.session_map)

    def broadcast_cursor_update(
        self,
        document_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        准备光标更新广播消息

        Args:
            document_id: 文档 ID
            user_id: 用户 ID

        Returns:
            广播消息
        """
        cursor = self.cursors.get(document_id, {}).get(user_id)
        if not cursor:
            return {}

        return {
            "type": "cursor_update",
            "document_id": document_id,
            "cursor": cursor.to_dict()
        }

    def broadcast_user_joined(
        self,
        document_id: str,
        user_id: int,
        username: str
    ) -> Dict[str, Any]:
        """
        准备用户加入广播消息

        Args:
            document_id: 文档 ID
            user_id: 用户 ID
            username: 用户名

        Returns:
            广播消息
        """
        return {
            "type": "user_joined",
            "document_id": document_id,
            "user": {
                "user_id": user_id,
                "username": username,
                "color": self.USER_COLORS[self.user_colors.get(user_id, 0)]
            }
        }

    def broadcast_user_left(
        self,
        document_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        准备用户离开广播消息

        Args:
            document_id: 文档 ID
            user_id: 用户 ID

        Returns:
            广播消息
        """
        return {
            "type": "user_left",
            "document_id": document_id,
            "user_id": user_id
        }
