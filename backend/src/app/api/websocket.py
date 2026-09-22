"""
WebSocket API路由
Phase 3.7 - WebSocket实时通知系统

功能：
- /ws/{client_id} - 主WebSocket连接端点
- /broadcast - HTTP广播端点（测试用）
- /rooms/{room_id}/broadcast - 房间广播
- /rooms/{room_id}/join - 加入房间
- /rooms/{room_id}/leave - 离开房间
- /stats - 获取统计信息
- /events/emit - 发射事件
- /events/history - 获取事件历史

作者：FieldMind Team
创建时间：2026-08-09
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.response import success_response, error_response
import logging

from app.services.websocket_manager import get_connection_manager
from app.services.event_emitter import get_event_emitter

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ Pydantic模型 ============

class BroadcastRequest(BaseModel):
    """广播消息请求"""
    event: str = Field(..., description="事件类型")
    data: Dict[str, Any] = Field(..., description="事件数据")
    exclude_clients: Optional[list] = Field(None, description="排除的客户端ID列表")


class RoomBroadcastRequest(BaseModel):
    """房间广播消息请求"""
    event: str = Field(..., description="事件类型")
    data: Dict[str, Any] = Field(..., description="事件数据")


class JoinRoomRequest(BaseModel):
    """加入房间请求"""
    client_id: str = Field(..., description="客户端ID")


class EmitEventRequest(BaseModel):
    """发射事件请求"""
    event_type: str = Field(..., description="事件类型")
    data: Dict[str, Any] = Field(..., description="事件数据")


# ============ WebSocket端点 ============

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None)
):
    """
    WebSocket主连接端点

    Args:
        websocket: WebSocket连接对象
        client_id: 客户端唯一ID
        user_id: 用户ID（可选）
        session_id: 会话ID（可选）
        project_id: 项目ID（可选）

    消息格式：
        客户端 -> 服务器：
        {
            "type": "ping" | "join_room" | "leave_room" | "message",
            "room_id": "room_123",  // join_room/leave_room时必需
            "data": {...}           // message时的数据
        }

        服务器 -> 客户端：
        {
            "event": "connected" | "ping" | "pong" | "message" | ...,
            "data": {...},
            "timestamp": "2026-08-09T12:00:00"
        }
    """
    manager = get_connection_manager()

    # 准备元数据
    metadata = {
        'user_id': user_id,
        'session_id': session_id,
        'project_id': project_id
    }

    # 建立连接
    await manager.connect(websocket, client_id, metadata)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            message_type = data.get('type', 'unknown')

            if message_type == 'ping':
                # 处理心跳ping
                manager.update_heartbeat(client_id)
                await manager.send_personal_message(
                    message={'event': 'pong', 'timestamp': data.get('timestamp')},
                    client_id=client_id
                )

            elif message_type == 'join_room':
                # 加入房间
                room_id = data.get('room_id')
                if room_id:
                    success = manager.join_room(client_id, room_id)
                    await manager.send_personal_message(
                        message={
                            'event': 'room_joined',
                            'room_id': room_id,
                            'success': success
                        },
                        client_id=client_id
                    )

            elif message_type == 'leave_room':
                # 离开房间
                room_id = data.get('room_id')
                if room_id:
                    manager.leave_room(client_id, room_id)
                    await manager.send_personal_message(
                        message={
                            'event': 'room_left',
                            'room_id': room_id
                        },
                        client_id=client_id
                    )

            elif message_type == 'message':
                # 回显消息（测试用）
                await manager.send_personal_message(
                    message={
                        'event': 'message_received',
                        'data': data.get('data', {})
                    },
                    client_id=client_id
                )

            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")

    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


# ============ HTTP管理端点 ============

@router.post("/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """
    HTTP端点：广播消息给所有连接的客户端

    适用场景：
    - 系统级通知
    - 测试WebSocket功能
    """
    manager = get_connection_manager()

    exclude_set = set(request.exclude_clients) if request.exclude_clients else None

    message = {
        'event': request.event,
        'data': request.data
    }

    await manager.broadcast(message, exclude=exclude_set)

    return success_response(
        data={
            'recipients': len(manager.active_connections) - (len(exclude_set) if exclude_set else 0)
        },
        message='Broadcast sent'
    )


@router.post("/rooms/{room_id}/broadcast/")
async def broadcast_to_room(room_id: str, request: RoomBroadcastRequest):
    """
    HTTP端点：广播消息给特定房间的客户端

    适用场景：
    - 项目级通知（room_id = f"project_{project_id}"）
    - 会话级通知（room_id = f"session_{session_id}"）
    """
    manager = get_connection_manager()

    message = {
        'event': request.event,
        'data': request.data
    }

    await manager.broadcast_to_room(room_id, message)

    room_info = manager.get_room_info(room_id)

    return success_response(
        data={'room_info': room_info},
        message=f'Broadcast sent to room {room_id}'
    )


@router.post("/rooms/{room_id}/join/")
async def join_room_http(room_id: str, request: JoinRoomRequest):
    """
    HTTP端点：客户端加入房间

    通常应通过WebSocket消息完成，此端点用于测试或特殊场景
    """
    manager = get_connection_manager()

    success = manager.join_room(request.client_id, room_id)

    if not success:
        return error_response(
            code="CLIENT_NOT_CONNECTED",
            message=f"Client {request.client_id} not connected"
        )

    return success_response(
        data={
            'client_id': request.client_id,
            'room_id': room_id
        }
    )


@router.post("/rooms/{room_id}/leave/")
async def leave_room_http(room_id: str, request: JoinRoomRequest):
    """
    HTTP端点：客户端离开房间
    """
    manager = get_connection_manager()
    manager.leave_room(request.client_id, room_id)

    return success_response(
        data={
            'client_id': request.client_id,
            'room_id': room_id
        }
    )


@router.get("/stats")
async def get_stats():
    """
    获取WebSocket统计信息

    返回：
    - 活跃连接数
    - 房间数量
    - 消息统计
    - 客户端列表
    """
    manager = get_connection_manager()
    stats = manager.get_stats()

    return success_response(data=stats)


@router.get("/clients/{client_id}/")
async def get_client_info(client_id: str):
    """
    获取特定客户端信息
    """
    manager = get_connection_manager()
    info = manager.get_client_info(client_id)

    if not info:
        return error_response(
            code="CLIENT_NOT_FOUND",
            message=f"Client {client_id} not found"
        )

    return success_response(data=info)


@router.get("/rooms/{room_id}/")
async def get_room_info_endpoint(room_id: str):
    """
    获取房间信息
    """
    manager = get_connection_manager()
    info = manager.get_room_info(room_id)

    return success_response(data=info)


# ============ 事件系统端点 ============

@router.post("/events/emit")
async def emit_event(request: EmitEventRequest):
    """
    HTTP端点：发射事件到事件系统

    事件会被EventEmitter处理，并通过已注册的监听器
    自动广播到相应的WebSocket客户端

    适用场景：
    - 后台任务触发事件
    - 外部系统集成
    - 测试事件流
    """
    emitter = get_event_emitter()

    await emitter.emit(request.event_type, request.data)

    return success_response(
        data={'event_type': request.event_type},
        message=f'Event {request.event_type} emitted'
    )


@router.get("/events/history")
async def get_event_history(
    event_type: Optional[str] = Query(None, description="过滤事件类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量")
):
    """
    获取事件历史

    Args:
        event_type: 过滤特定事件类型（可选）
        limit: 返回数量（1-100）
    """
    emitter = get_event_emitter()
    history = emitter.get_history(event_type=event_type, limit=limit)

    return success_response(
        data={
            'count': len(history),
            'history': history
        }
    )


@router.get("/events/stats")
async def get_event_stats():
    """
    获取事件系统统计信息
    """
    emitter = get_event_emitter()
    stats = emitter.get_stats()

    return success_response(data=stats)


# ============ 健康检查 ============

@router.get("/health")
async def health_check():
    """
    WebSocket系统健康检查
    """
    manager = get_connection_manager()
    emitter = get_event_emitter()

    return success_response(
        data={
            'status': 'healthy',
            'websocket': {
                'active_connections': len(manager.active_connections),
                'total_rooms': len(manager.rooms)
            },
            'events': {
                'total_events': emitter.stats['total_events'],
                'total_listeners': emitter.stats['total_listeners']
            }
        }
    )
