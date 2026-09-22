"""
WebSocket API端点

提供WebSocket连接和实时事件推送
"""
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import logging
import asyncio

from app.services.websocket_event_service import get_websocket_event_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="客户端唯一ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    session_id: Optional[str] = Query(None, description="会话ID")
):
    """
    WebSocket连接端点

    连接后自动加入相关房间：
    - project_{project_id}: 接收项目相关事件
    - session_{session_id}: 接收会话相关事件
    - user_{user_id}: 接收用户相关事件

    支持的事件类型：
    - document.upload.*: 文档上传事件
    - document.process.*: 文档处理事件
    - distillation.job.*: 知识蒸馏事件
    - deep_rag.*: Deep RAG查询事件
    - batch.*: 批处理事件
    - system.*: 系统事件

    客户端消息格式：
    {
        "type": "ping|join_room|leave_room",
        "data": {...}
    }
    """
    ws_service = get_websocket_event_service()
    connection_manager = ws_service.get_connection_manager()

    # 构建客户端元数据
    metadata = {
        "user_id": user_id,
        "project_id": project_id,
        "session_id": session_id
    }

    try:
        # 接受连接
        await connection_manager.connect(websocket, client_id, metadata)

        # 自动加入房间
        if project_id:
            connection_manager.join_room(client_id, f"project_{project_id}")
        if session_id:
            connection_manager.join_room(client_id, f"session_{session_id}")
        if user_id:
            connection_manager.join_room(client_id, f"user_{user_id}")

        # 启动心跳任务
        heartbeat_task = asyncio.create_task(_heartbeat_loop(connection_manager, client_id))

        # 消息处理循环
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "ping":
                # 更新心跳
                connection_manager.update_heartbeat(client_id)
                await connection_manager.send_personal_message(
                    {"event": "pong", "timestamp": data.get("timestamp")},
                    client_id
                )

            elif message_type == "join_room":
                # 加入房间
                room_id = data.get("room_id")
                if room_id:
                    success = connection_manager.join_room(client_id, room_id)
                    await connection_manager.send_personal_message(
                        {
                            "event": "room_joined" if success else "room_join_failed",
                            "room_id": room_id
                        },
                        client_id
                    )

            elif message_type == "leave_room":
                # 离开房间
                room_id = data.get("room_id")
                if room_id:
                    connection_manager.leave_room(client_id, room_id)
                    await connection_manager.send_personal_message(
                        {"event": "room_left", "room_id": room_id},
                        client_id
                    )

            elif message_type == "get_info":
                # 获取客户端信息
                info = connection_manager.get_client_info(client_id)
                await connection_manager.send_personal_message(
                    {"event": "client_info", "data": info},
                    client_id
                )

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # 清理
        heartbeat_task.cancel()
        connection_manager.disconnect(client_id)


async def _heartbeat_loop(connection_manager, client_id: str):
    """心跳循环"""
    try:
        while True:
            await asyncio.sleep(30)  # 每30秒发送心跳
            if client_id in connection_manager.active_connections:
                await connection_manager.send_heartbeat(client_id)
            else:
                break
    except asyncio.CancelledError:
        pass


@router.get("/ws/stats", summary="获取WebSocket统计")
async def get_websocket_stats():
    """获取WebSocket连接和事件统计"""
    ws_service = get_websocket_event_service()
    return ws_service.get_stats()


@router.get("/ws/connections", summary="获取活跃连接")
async def get_active_connections():
    """获取所有活跃的WebSocket连接"""
    ws_service = get_websocket_event_service()
    connection_manager = ws_service.get_connection_manager()

    connections = []
    for client_id in connection_manager.active_connections.keys():
        info = connection_manager.get_client_info(client_id)
        if info:
            connections.append(info)

    return {
        "total": len(connections),
        "connections": connections
    }


@router.get("/ws/rooms", summary="获取活跃房间")
async def get_active_rooms():
    """获取所有活跃的房间"""
    ws_service = get_websocket_event_service()
    connection_manager = ws_service.get_connection_manager()

    rooms = []
    for room_id, clients in connection_manager.rooms.items():
        rooms.append({
            "room_id": room_id,
            "client_count": len(clients),
            "clients": list(clients)
        })

    return {
        "total": len(rooms),
        "rooms": rooms
    }


@router.post("/ws/broadcast", summary="广播消息（测试用）")
async def broadcast_message(
    event: str,
    data: dict
):
    """
    广播消息到所有连接的客户端（仅用于测试）

    生产环境应通过EventEmitter发射事件
    """
    ws_service = get_websocket_event_service()
    event_emitter = ws_service.get_event_emitter()

    # 通过事件发射器发射事件
    await event_emitter.emit(event, data)

    return {
        "message": "Event emitted successfully",
        "event": event
    }


@router.get("/health", summary="健康检查")
async def health_check():
    """WebSocket服务健康检查"""
    ws_service = get_websocket_event_service()
    stats = ws_service.get_stats()

    return {
        "status": "healthy",
        "service": "websocket",
        "active_connections": stats["connections"]["active"],
        "total_events": stats["events"]["total_events"]
    }
