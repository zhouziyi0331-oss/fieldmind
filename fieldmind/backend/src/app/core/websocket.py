"""
WebSocket 管理器
用于实时通知前端数据更新
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 存储所有活跃连接：{project_id: set of websockets}
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int):
        """接受新的 WebSocket 连接"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()

        self.active_connections[project_id].add(websocket)
        logger.info(f"WebSocket 连接: project={project_id}, 当前连接数={len(self.active_connections[project_id])}")

    def disconnect(self, websocket: WebSocket, project_id: int):
        """断开 WebSocket 连接"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)

            # 如果没有连接了，删除这个项目的记录
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

        logger.info(f"WebSocket 断开: project={project_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送消息给特定连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def broadcast_to_project(self, message: dict, project_id: int):
        """广播消息给项目的所有连接"""
        if project_id not in self.active_connections:
            logger.debug(f"项目 {project_id} 没有活跃连接")
            return

        # 复制集合，避免在迭代时修改
        connections = self.active_connections[project_id].copy()

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                # 移除失败的连接
                self.disconnect(connection, project_id)

    async def notify_document_status(self, project_id: int, document_id: int, status: str, details: dict = None):
        """通知文档状态变化"""
        message = {
            "type": "document_status",
            "document_id": document_id,
            "status": status,
            "details": details or {},
            "timestamp": import_datetime().isoformat()
        }
        await self.broadcast_to_project(message, project_id)

    async def notify_project_stats(self, project_id: int, stats: dict):
        """通知项目统计更新"""
        message = {
            "type": "project_stats",
            "stats": stats,
            "timestamp": import_datetime().isoformat()
        }
        await self.broadcast_to_project(message, project_id)


def import_datetime():
    """延迟导入 datetime"""
    from datetime import datetime
    return datetime.utcnow()


# 全局实例
manager = ConnectionManager()
