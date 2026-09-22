"""
WebSocket 连接管理器
Phase 3.7 - WebSocket实时通知系统

功能：
- 连接池管理（多客户端）
- 消息广播（全局、房间、单播）
- 心跳保活（30秒间隔）
- 断线重连支持
- 事件类型路由

作者：FieldMind Team
创建时间：2026-08-09
"""

import asyncio
import json
import time
from typing import Dict, Set, Optional, Any, List
from collections import defaultdict
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self, use_workflow_engine: bool = True):

        # 活跃连接：{client_id: WebSocket}
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.active_connections: Dict[str, WebSocket] = {}

        # 房间管理：{room_id: Set[client_id]}
        self.rooms: Dict[str, Set[str]] = defaultdict(set)

        # 客户端元数据：{client_id: metadata}
        self.client_metadata: Dict[str, Dict[str, Any]] = {}

        # 心跳记录：{client_id: last_heartbeat_time}
        self.heartbeats: Dict[str, float] = {}

        # 心跳配置
        self.heartbeat_interval = 30  # 30秒
        self.heartbeat_timeout = 90   # 90秒超时

        # 统计信息
        self.stats = {
            'total_connections': 0,
            'total_messages': 0,
            'total_broadcasts': 0,
            'connection_errors': 0
        }

        logger.info("WebSocket ConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        接受WebSocket连接

        Args:
            websocket: WebSocket对象
            client_id: 客户端唯一ID
            metadata: 客户端元数据（user_id, session_id等）
        """
        await websocket.accept()

        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = metadata or {}
        self.heartbeats[client_id] = time.time()

        self.stats['total_connections'] += 1

        logger.info(f"Client {client_id} connected. Total active: {len(self.active_connections)}")

        # 发送欢迎消息
        await self.send_personal_message(
            message={
                'event': 'connected',
                'client_id': client_id,
                'timestamp': datetime.now().isoformat(),
                'message': 'WebSocket connection established'
            },
            client_id=client_id
        )

    def disconnect(self, client_id: str):
        """
        断开连接并清理资源

        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.client_metadata:
            del self.client_metadata[client_id]

        if client_id in self.heartbeats:
            del self.heartbeats[client_id]

        # 从所有房间移除
        for room_id in list(self.rooms.keys()):
            if client_id in self.rooms[room_id]:
                self.rooms[room_id].remove(client_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]

        logger.info(f"Client {client_id} disconnected. Total active: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """
        发送消息给特定客户端（单播）

        Args:
            message: 消息内容
            client_id: 目标客户端ID
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                self.stats['total_messages'] += 1
                logger.debug(f"Sent message to {client_id}: {message.get('event', 'unknown')}")
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.stats['connection_errors'] += 1
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """
        广播消息给所有连接的客户端

        Args:
            message: 消息内容
            exclude: 要排除的客户端ID集合
        """
        exclude = exclude or set()
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            if client_id in exclude:
                continue

            try:
                await websocket.send_json(message)
                self.stats['total_messages'] += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                self.stats['connection_errors'] += 1
                disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

        self.stats['total_broadcasts'] += 1
        logger.debug(f"Broadcast to {len(self.active_connections) - len(exclude)} clients: {message.get('event', 'unknown')}")

    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any]):
        """
        广播消息给特定房间的所有客户端

        Args:
            room_id: 房间ID
            message: 消息内容
        """
        if room_id not in self.rooms or not self.rooms[room_id]:
            logger.warning(f"Room {room_id} has no clients")
            return

        disconnected_clients = []

        for client_id in self.rooms[room_id]:
            if client_id not in self.active_connections:
                disconnected_clients.append(client_id)
                continue

            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                self.stats['total_messages'] += 1
            except Exception as e:
                logger.error(f"Error sending to room {room_id}, client {client_id}: {e}")
                self.stats['connection_errors'] += 1
                disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

        logger.debug(f"Broadcast to room {room_id}: {len(self.rooms[room_id])} clients")

    def join_room(self, client_id: str, room_id: str):
        """
        客户端加入房间

        Args:
            client_id: 客户端ID
            room_id: 房间ID
        """
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not connected, cannot join room {room_id}")
            return False

        self.rooms[room_id].add(client_id)
        logger.info(f"Client {client_id} joined room {room_id}. Room size: {len(self.rooms[room_id])}")
        return True

    def leave_room(self, client_id: str, room_id: str):
        """
        客户端离开房间

        Args:
            client_id: 客户端ID
            room_id: 房间ID
        """
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            logger.info(f"Client {client_id} left room {room_id}")

            # 清理空房间
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} is empty and removed")

    def update_heartbeat(self, client_id: str):
        """
        更新客户端心跳时间

        Args:
            client_id: 客户端ID
        """
        self.heartbeats[client_id] = time.time()
        logger.debug(f"Heartbeat updated for {client_id}")

    async def check_heartbeats(self):
        """
        检查所有连接的心跳状态，移除超时连接
        """
        current_time = time.time()
        disconnected_clients = []

        for client_id, last_heartbeat in self.heartbeats.items():
            if current_time - last_heartbeat > self.heartbeat_timeout:
                logger.warning(f"Client {client_id} heartbeat timeout")
                disconnected_clients.append(client_id)

        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def send_heartbeat(self, client_id: str):
        """
        发送心跳ping消息

        Args:
            client_id: 客户端ID
        """
        await self.send_personal_message(
            message={
                'event': 'ping',
                'timestamp': datetime.now().isoformat()
            },
            client_id=client_id
        )

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        获取客户端信息

        Args:
            client_id: 客户端ID

        Returns:
            客户端信息字典
        """
        if client_id not in self.active_connections:
            return None

        return {
            'client_id': client_id,
            'connected': True,
            'metadata': self.client_metadata.get(client_id, {}),
            'last_heartbeat': self.heartbeats.get(client_id, 0),
            'rooms': [room_id for room_id, clients in self.rooms.items() if client_id in clients]
        }

    def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """
        获取房间信息

        Args:
            room_id: 房间ID

        Returns:
            房间信息字典
        """
        clients = list(self.rooms.get(room_id, set()))
        return {
            'room_id': room_id,
            'client_count': len(clients),
            'clients': clients
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'active_connections': len(self.active_connections),
            'total_rooms': len(self.rooms),
            'stats': self.stats,
            'clients': list(self.active_connections.keys())
        }


# 全局单例
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """获取全局ConnectionManager实例"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


async def heartbeat_task():
    """
    后台心跳检查任务
    每30秒运行一次
    """
    manager = get_connection_manager()

    while True:
        await asyncio.sleep(manager.heartbeat_interval)

        # 检查超时连接
        await manager.check_heartbeats()

        # 向所有客户端发送心跳
        for client_id in list(manager.active_connections.keys()):
            try:
                await manager.send_heartbeat(client_id)
            except Exception as e:
                logger.error(f"Error sending heartbeat to {client_id}: {e}")
