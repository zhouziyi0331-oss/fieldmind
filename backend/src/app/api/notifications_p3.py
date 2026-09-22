"""
通知系统 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.notifications import (
    NotificationService,
    NotificationStore,
    EmailNotificationService,
    WebSocketNotificationService,
    PushNotificationService,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# 全局通知服务实例
_notification_store = NotificationStore()
_email_service = EmailNotificationService()
_websocket_service = WebSocketNotificationService()
_push_service = PushNotificationService()
_notification_service = NotificationService(
    _notification_store,
    _email_service,
    _websocket_service,
    _push_service
)


# Request/Response Models
class SendNotificationRequest(BaseModel):
    user_id: int = Field(..., description="用户 ID")
    title: str = Field(..., description="标题")
    message: str = Field(..., description="消息内容")
    notification_type: str = Field("info", description="通知类型")
    priority: str = Field("normal", description="优先级")
    channels: List[str] = Field(default_factory=lambda: ["in_app"], description="通知渠道")
    metadata: dict = Field(default_factory=dict, description="元数据")


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发送通知

    支持多渠道发送：
    - in_app: 应用内通知
    - email: 邮件通知
    - websocket: WebSocket 实时通知
    - push: 推送通知
    - sms: 短信通知
    """
    try:
        notification = await _notification_service.send_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=NotificationType(request.notification_type),
            priority=NotificationPriority(request.priority),
            channels=[NotificationChannel(ch) for ch in request.channels],
            metadata=request.metadata
        )

        return {
            "status": "success",
            "notification": notification.to_dict()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的通知

    可选择仅显示未读通知
    """
    notifications = _notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )

    return {
        "notifications": [n.to_dict() for n in notifications],
        "count": len(notifications),
        "unread_count": _notification_service.get_unread_count(current_user.id)
    }


@router.get("/unread/count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """获取未读通知数量"""
    count = _notification_service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    success = _notification_service.mark_as_read(notification_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )

    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_as_read(current_user: User = Depends(get_current_user)):
    """标记所有通知为已读"""
    count = _notification_service.mark_all_as_read(current_user.id)

    return {
        "message": f"Marked {count} notifications as read",
        "count": count
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    success = _notification_service.delete_notification(notification_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )

    return {"message": "Notification deleted"}


@router.get("/statistics")
async def get_statistics(current_user: User = Depends(get_current_user)):
    """获取通知统计信息"""
    return _notification_service.get_statistics()
