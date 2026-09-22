"""
通知系统测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.services.notifications import (
    Notification,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationStore,
    EmailNotificationService,
    WebSocketNotificationService,
    PushNotificationService,
    NotificationService
)


class TestNotificationStore:
    """测试通知存储"""

    def test_add_notification(self):
        """测试添加通知"""
        store = NotificationStore()

        notification = Notification(
            notification_id="notif1",
            user_id=1,
            title="Test",
            message="Test message",
            notification_type=NotificationType.INFO
        )

        store.add_notification(notification)
        assert len(store.notification_map) == 1
        assert "notif1" in store.notification_map

    def test_get_user_notifications(self):
        """测试获取用户通知"""
        store = NotificationStore()

        for i in range(5):
            notif = Notification(
                notification_id=f"notif{i}",
                user_id=1,
                title=f"Title {i}",
                message=f"Message {i}",
                notification_type=NotificationType.INFO
            )
            store.add_notification(notif)

        notifications = store.get_user_notifications(1)
        assert len(notifications) == 5

    def test_unread_only(self):
        """测试仅未读通知"""
        store = NotificationStore()

        # 添加通知
        for i in range(3):
            notif = Notification(
                notification_id=f"notif{i}",
                user_id=1,
                title=f"Title {i}",
                message=f"Message {i}",
                notification_type=NotificationType.INFO
            )
            store.add_notification(notif)

        # 标记一个为已读
        store.mark_as_read("notif0")

        # 获取未读
        unread = store.get_user_notifications(1, unread_only=True)
        assert len(unread) == 2

    def test_mark_as_read(self):
        """测试标记已读"""
        store = NotificationStore()

        notif = Notification(
            notification_id="notif1",
            user_id=1,
            title="Test",
            message="Test",
            notification_type=NotificationType.INFO
        )
        store.add_notification(notif)

        success = store.mark_as_read("notif1")
        assert success == True
        assert notif.is_read == True
        assert notif.read_at is not None

    def test_mark_all_as_read(self):
        """测试标记所有已读"""
        store = NotificationStore()

        for i in range(3):
            notif = Notification(
                notification_id=f"notif{i}",
                user_id=1,
                title=f"Title {i}",
                message=f"Message {i}",
                notification_type=NotificationType.INFO
            )
            store.add_notification(notif)

        count = store.mark_all_as_read(1)
        assert count == 3
        assert store.get_unread_count(1) == 0

    def test_delete_notification(self):
        """测试删除通知"""
        store = NotificationStore()

        notif = Notification(
            notification_id="notif1",
            user_id=1,
            title="Test",
            message="Test",
            notification_type=NotificationType.INFO
        )
        store.add_notification(notif)

        success = store.delete_notification("notif1")
        assert success == True
        assert len(store.notification_map) == 0

    def test_unread_count(self):
        """测试未读数量"""
        store = NotificationStore()

        for i in range(5):
            notif = Notification(
                notification_id=f"notif{i}",
                user_id=1,
                title=f"Title {i}",
                message=f"Message {i}",
                notification_type=NotificationType.INFO
            )
            store.add_notification(notif)

        # 标记 2 个已读
        store.mark_as_read("notif0")
        store.mark_as_read("notif1")

        count = store.get_unread_count(1)
        assert count == 3


class TestEmailNotificationService:
    """测试邮件通知服务"""

    async def test_send_email(self):
        """测试发送邮件"""
        service = EmailNotificationService()

        success = await service.send_email(
            to_email="test@example.com",
            subject="Test Email",
            body="This is a test email"
        )

        assert success == True


class TestWebSocketNotificationService:
    """测试 WebSocket 通知服务"""

    def test_add_connection(self):
        """测试添加连接"""
        service = WebSocketNotificationService()
        mock_ws = "mock_websocket"

        service.add_connection(1, mock_ws)
        assert len(service.connections[1]) == 1

    def test_remove_connection(self):
        """测试移除连接"""
        service = WebSocketNotificationService()
        mock_ws = "mock_websocket"

        service.add_connection(1, mock_ws)
        service.remove_connection(1, mock_ws)
        assert len(service.connections[1]) == 0

    async def test_send_notification(self):
        """测试发送通知"""
        service = WebSocketNotificationService()
        mock_ws = "mock_websocket"
        service.add_connection(1, mock_ws)

        notif = Notification(
            notification_id="notif1",
            user_id=1,
            title="Test",
            message="Test",
            notification_type=NotificationType.INFO
        )

        await service.send_notification(1, notif)
        # 应该不抛出异常


class TestPushNotificationService:
    """测试推送通知服务"""

    async def test_send_push(self):
        """测试发送推送"""
        service = PushNotificationService()

        success = await service.send_push(
            user_id=1,
            title="Test Push",
            body="Test message"
        )

        assert success == True


class TestNotificationService:
    """测试通知服务"""

    async def test_send_notification(self):
        """测试发送通知"""
        store = NotificationStore()
        email_service = EmailNotificationService()
        ws_service = WebSocketNotificationService()
        push_service = PushNotificationService()

        service = NotificationService(
            store, email_service, ws_service, push_service
        )

        notification = await service.send_notification(
            user_id=1,
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.INFO,
            channels=[NotificationChannel.IN_APP]
        )

        assert notification.user_id == 1
        assert notification.title == "Test Notification"
        assert len(store.notification_map) == 1

    async def test_send_multi_channel(self):
        """测试多渠道发送"""
        store = NotificationStore()
        email_service = EmailNotificationService()
        ws_service = WebSocketNotificationService()
        push_service = PushNotificationService()

        service = NotificationService(
            store, email_service, ws_service, push_service
        )

        notification = await service.send_notification(
            user_id=1,
            title="Multi-channel",
            message="Test",
            channels=[
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL,
                NotificationChannel.PUSH
            ]
        )

        assert len(notification.channels) == 3

    async def test_get_user_notifications(self):
        """测试获取用户通知"""
        store = NotificationStore()
        email_service = EmailNotificationService()
        ws_service = WebSocketNotificationService()
        push_service = PushNotificationService()

        service = NotificationService(
            store, email_service, ws_service, push_service
        )

        # 发送多个通知
        for i in range(3):
            await service.send_notification(
                user_id=1,
                title=f"Notification {i}",
                message=f"Message {i}"
            )

        notifications = service.get_user_notifications(1)
        assert len(notifications) == 3

    async def test_mark_as_read(self):
        """测试标记已读"""
        store = NotificationStore()
        email_service = EmailNotificationService()
        ws_service = WebSocketNotificationService()
        push_service = PushNotificationService()

        service = NotificationService(
            store, email_service, ws_service, push_service
        )

        notification = await service.send_notification(
            user_id=1,
            title="Test",
            message="Test"
        )

        success = service.mark_as_read(notification.notification_id)
        assert success == True
        assert notification.is_read == True

    async def test_statistics(self):
        """测试统计信息"""
        store = NotificationStore()
        email_service = EmailNotificationService()
        ws_service = WebSocketNotificationService()
        push_service = PushNotificationService()

        service = NotificationService(
            store, email_service, ws_service, push_service
        )

        # 发送通知
        for i in range(5):
            await service.send_notification(
                user_id=1,
                title=f"Notification {i}",
                message=f"Message {i}"
            )

        stats = service.get_statistics()
        assert stats["total_notifications"] == 5
        assert stats["unread_notifications"] == 5


async def test_integration_notification_system():
    """集成测试：完整通知流程"""
    # 创建服务
    store = NotificationStore()
    email_service = EmailNotificationService()
    ws_service = WebSocketNotificationService()
    push_service = PushNotificationService()

    service = NotificationService(
        store, email_service, ws_service, push_service
    )

    # 发送不同类型的通知
    await service.send_notification(
        user_id=1,
        title="Info Notification",
        message="This is an info message",
        notification_type=NotificationType.INFO,
        priority=NotificationPriority.NORMAL
    )

    await service.send_notification(
        user_id=1,
        title="Warning",
        message="This is a warning",
        notification_type=NotificationType.WARNING,
        priority=NotificationPriority.HIGH
    )

    await service.send_notification(
        user_id=1,
        title="Error",
        message="An error occurred",
        notification_type=NotificationType.ERROR,
        priority=NotificationPriority.URGENT
    )

    # 验证通知
    notifications = service.get_user_notifications(1)
    assert len(notifications) == 3

    # 验证未读数量
    unread_count = service.get_unread_count(1)
    assert unread_count == 3

    # 标记一个已读
    service.mark_as_read(notifications[0].notification_id)
    assert service.get_unread_count(1) == 2

    # 标记所有已读
    service.mark_all_as_read(1)
    assert service.get_unread_count(1) == 0

    # 删除通知
    service.delete_notification(notifications[0].notification_id)
    assert len(service.get_user_notifications(1)) == 2


def run_async_test(coro):
    """运行异步测试"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running Notification system tests...")

    print("\n=== Testing NotificationStore ===")
    test_store = TestNotificationStore()
    test_store.test_add_notification()
    test_store.test_get_user_notifications()
    test_store.test_unread_only()
    test_store.test_mark_as_read()
    test_store.test_mark_all_as_read()
    test_store.test_delete_notification()
    test_store.test_unread_count()
    print("✓ NotificationStore tests passed")

    print("\n=== Testing EmailNotificationService ===")
    test_email = TestEmailNotificationService()
    run_async_test(test_email.test_send_email())
    print("✓ EmailNotificationService tests passed")

    print("\n=== Testing WebSocketNotificationService ===")
    test_ws = TestWebSocketNotificationService()
    test_ws.test_add_connection()
    test_ws.test_remove_connection()
    run_async_test(test_ws.test_send_notification())
    print("✓ WebSocketNotificationService tests passed")

    print("\n=== Testing PushNotificationService ===")
    test_push = TestPushNotificationService()
    run_async_test(test_push.test_send_push())
    print("✓ PushNotificationService tests passed")

    print("\n=== Testing NotificationService ===")
    test_service = TestNotificationService()
    run_async_test(test_service.test_send_notification())
    run_async_test(test_service.test_send_multi_channel())
    run_async_test(test_service.test_get_user_notifications())
    run_async_test(test_service.test_mark_as_read())
    run_async_test(test_service.test_statistics())
    print("✓ NotificationService tests passed")

    print("\n=== Running Integration Tests ===")
    run_async_test(test_integration_notification_system())
    print("✓ Integration tests passed")

    print("\n✅ All notification system tests passed successfully!")
