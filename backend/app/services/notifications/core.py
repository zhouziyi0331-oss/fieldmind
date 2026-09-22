"""
通知系统

提供多渠道通知服务（邮件、WebSocket、推送）
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    WEBSOCKET = "websocket"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """通知"""
    notification_id: str
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.IN_APP])
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value,
            "priority": self.priority.value,
            "channels": [c.value for c in self.channels],
            "metadata": self.metadata,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None
        }


class NotificationStore:
    """
    通知存储

    管理通知的存储和检索
    """

    def __init__(self):
        """初始化存储"""
        # user_id -> List[Notification]
        self.notifications: Dict[int, List[Notification]] = defaultdict(list)

        # notification_id -> Notification
        self.notification_map: Dict[str, Notification] = {}

    def add_notification(self, notification: Notification):
        """添加通知"""
        self.notifications[notification.user_id].append(notification)
        self.notification_map[notification.notification_id] = notification
        logger.info(f"Added notification {notification.notification_id} for user {notification.user_id}")

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """获取通知"""
        return self.notification_map.get(notification_id)

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        获取用户通知

        Args:
            user_id: 用户 ID
            unread_only: 仅未读
            limit: 数量限制

        Returns:
            通知列表
        """
        user_notifs = self.notifications.get(user_id, [])

        if unread_only:
            user_notifs = [n for n in user_notifs if not n.is_read]

        # 按创建时间倒序
        user_notifs.sort(key=lambda n: n.created_at, reverse=True)

        return user_notifs[:limit]

    def mark_as_read(self, notification_id: str) -> bool:
        """标记为已读"""
        notification = self.notification_map.get(notification_id)
        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.now()
        logger.info(f"Marked notification {notification_id} as read")
        return True

    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有为已读"""
        count = 0
        for notification in self.notifications.get(user_id, []):
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now()
                count += 1

        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        notification = self.notification_map.get(notification_id)
        if not notification:
            return False

        # 从用户列表中移除
        user_notifs = self.notifications.get(notification.user_id, [])
        self.notifications[notification.user_id] = [
            n for n in user_notifs if n.notification_id != notification_id
        ]

        # 从映射中删除
        del self.notification_map[notification_id]

        logger.info(f"Deleted notification {notification_id}")
        return True

    def get_unread_count(self, user_id: int) -> int:
        """获取未读数量"""
        return sum(1 for n in self.notifications.get(user_id, []) if not n.is_read)


class EmailNotificationService:
    """邮件通知服务"""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人
            subject: 主题
            body: 内容
            html: 是否 HTML

        Returns:
            是否成功
        """
        # 模拟邮件发送
        # 实际应该使用 SMTP 或邮件服务 API
        logger.info(f"Sending email to {to_email}: {subject}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return True


class WebSocketNotificationService:
    """WebSocket 通知服务"""

    def __init__(self):
        """初始化服务"""
        # user_id -> List[WebSocket]
        self.connections: Dict[int, List[Any]] = defaultdict(list)

    def add_connection(self, user_id: int, websocket: Any):
        """添加连接"""
        self.connections[user_id].append(websocket)
        logger.info(f"Added WebSocket connection for user {user_id}")

    def remove_connection(self, user_id: int, websocket: Any):
        """移除连接"""
        if user_id in self.connections:
            self.connections[user_id] = [
                ws for ws in self.connections[user_id] if ws != websocket
            ]
            logger.info(f"Removed WebSocket connection for user {user_id}")

    async def send_notification(self, user_id: int, notification: Notification):
        """
        发送通知到 WebSocket

        Args:
            user_id: 用户 ID
            notification: 通知
        """
        connections = self.connections.get(user_id, [])
        if not connections:
            logger.debug(f"No WebSocket connections for user {user_id}")
            return

        message = notification.to_dict()
        disconnected = []

        for ws in connections:
            try:
                # 模拟发送
                # 实际应该调用 ws.send_json(message)
                logger.debug(f"Sent notification to WebSocket for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send notification via WebSocket: {e}")
                disconnected.append(ws)

        # 清理断开的连接
        for ws in disconnected:
            self.remove_connection(user_id, ws)


class PushNotificationService:
    """推送通知服务"""

    async def send_push(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送推送通知

        Args:
            user_id: 用户 ID
            title: 标题
            body: 内容
            data: 附加数据

        Returns:
            是否成功
        """
        # 模拟推送通知
        # 实际应该使用 FCM/APNs
        logger.info(f"Sending push notification to user {user_id}: {title}")
        await asyncio.sleep(0.1)
        return True


class NotificationService:
    """
    通知服务

    统一的通知发送和管理服务
    """

    def __init__(
        self,
        store: NotificationStore,
        email_service: EmailNotificationService,
        websocket_service: WebSocketNotificationService,
        push_service: PushNotificationService
    ):
        """
        初始化服务

        Args:
            store: 通知存储
            email_service: 邮件服务
            websocket_service: WebSocket 服务
            push_service: 推送服务
        """
        self.store = store
        self.email_service = email_service
        self.websocket_service = websocket_service
        self.push_service = push_service

    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        发送通知

        Args:
            user_id: 用户 ID
            title: 标题
            message: 消息
            notification_type: 类型
            priority: 优先级
            channels: 渠道列表
            metadata: 元数据

        Returns:
            通知对象
        """
        import uuid

        # 创建通知
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channels=channels or [NotificationChannel.IN_APP],
            metadata=metadata or {}
        )

        # 存储通知
        self.store.add_notification(notification)

        # 发送到各个渠道
        tasks = []

        if NotificationChannel.EMAIL in notification.channels:
            tasks.append(self._send_email(notification))

        if NotificationChannel.WEBSOCKET in notification.channels:
            tasks.append(self._send_websocket(notification))

        if NotificationChannel.PUSH in notification.channels:
            tasks.append(self._send_push(notification))

        # 并发发送
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Sent notification {notification.notification_id} to user {user_id}")
        return notification

    async def _send_email(self, notification: Notification):
        """发送邮件通知"""
        # 实际应该从数据库获取用户邮箱
        user_email = f"user{notification.user_id}@example.com"

        await self.email_service.send_email(
            to_email=user_email,
            subject=notification.title,
            body=notification.message
        )

    async def _send_websocket(self, notification: Notification):
        """发送 WebSocket 通知"""
        await self.websocket_service.send_notification(
            notification.user_id,
            notification
        )

    async def _send_push(self, notification: Notification):
        """发送推送通知"""
        await self.push_service.send_push(
            user_id=notification.user_id,
            title=notification.title,
            body=notification.message,
            data=notification.metadata
        )

    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """获取用户通知"""
        return self.store.get_user_notifications(user_id, unread_only, limit)

    def mark_as_read(self, notification_id: str) -> bool:
        """标记为已读"""
        return self.store.mark_as_read(notification_id)

    def mark_all_as_read(self, user_id: int) -> int:
        """标记所有为已读"""
        return self.store.mark_all_as_read(user_id)

    def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        return self.store.delete_notification(notification_id)

    def get_unread_count(self, user_id: int) -> int:
        """获取未读数量"""
        return self.store.get_unread_count(user_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_notifications = len(self.store.notification_map)
        total_users = len(self.store.notifications)

        unread_count = sum(
            1 for n in self.store.notification_map.values() if not n.is_read
        )

        return {
            "total_notifications": total_notifications,
            "total_users": total_users,
            "unread_notifications": unread_count,
            "read_notifications": total_notifications - unread_count
        }
