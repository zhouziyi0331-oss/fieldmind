"""
WebSocket事件集成服务

整合EventEmitter和ConnectionManager，提供完整的实时事件系统
"""
from typing import Dict, Any, Optional, List
import asyncio
import logging

from app.services.event_emitter import get_event_emitter, EventEmitter
from app.services.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)


class WebSocketEventService:
    """WebSocket事件服务 - 连接事件系统和WebSocket"""

    def __init__(self):
        self.event_emitter = get_event_emitter()
        self.connection_manager = ConnectionManager()
        self._setup_event_listeners()
        logger.info("✅ WebSocket事件服务初始化成功")

    def _setup_event_listeners(self):
        """设置事件监听器，将事件转发到WebSocket"""

        # 文档上传事件
        self.event_emitter.on("document.upload.start", self._handle_document_upload_start)
        self.event_emitter.on("document.upload.progress", self._handle_document_upload_progress)
        self.event_emitter.on("document.upload.complete", self._handle_document_upload_complete)
        self.event_emitter.on("document.upload.error", self._handle_document_upload_error)

        # 文档处理事件
        self.event_emitter.on("document.process.start", self._handle_document_process_start)
        self.event_emitter.on("document.process.progress", self._handle_document_process_progress)
        self.event_emitter.on("document.process.complete", self._handle_document_process_complete)
        self.event_emitter.on("document.process.error", self._handle_document_process_error)

        # 知识蒸馏事件
        self.event_emitter.on("distillation.job.start", self._handle_distillation_start)
        self.event_emitter.on("distillation.job.progress", self._handle_distillation_progress)
        self.event_emitter.on("distillation.job.complete", self._handle_distillation_complete)
        self.event_emitter.on("distillation.job.error", self._handle_distillation_error)

        # Deep RAG查询事件
        self.event_emitter.on("deep_rag.query.start", self._handle_rag_query_start)
        self.event_emitter.on("deep_rag.query.complete", self._handle_rag_query_complete)
        self.event_emitter.on("deep_rag.error", self._handle_rag_error)

        # 批处理事件
        self.event_emitter.on("batch.start", self._handle_batch_start)
        self.event_emitter.on("batch.item.complete", self._handle_batch_item_complete)
        self.event_emitter.on("batch.complete", self._handle_batch_complete)
        self.event_emitter.on("batch.error", self._handle_batch_error)

        # 系统事件
        self.event_emitter.on("system.status", self._handle_system_status)
        self.event_emitter.on("system.error", self._handle_system_error)
        self.event_emitter.on("system.warning", self._handle_system_warning)

        logger.info("✅ 已注册所有WebSocket事件监听器")

    # ==================== 文档上传事件处理 ====================

    async def _handle_document_upload_start(self, event: Dict[str, Any]):
        """处理文档上传开始事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.upload.start",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_upload_progress(self, event: Dict[str, Any]):
        """处理文档上传进度事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.upload.progress",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_upload_complete(self, event: Dict[str, Any]):
        """处理文档上传完成事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.upload.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_upload_error(self, event: Dict[str, Any]):
        """处理文档上传错误事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.upload.error",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    # ==================== 文档处理事件处理 ====================

    async def _handle_document_process_start(self, event: Dict[str, Any]):
        """处理文档处理开始事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.process.start",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_process_progress(self, event: Dict[str, Any]):
        """处理文档处理进度事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.process.progress",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_process_complete(self, event: Dict[str, Any]):
        """处理文档处理完成事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.process.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_document_process_error(self, event: Dict[str, Any]):
        """处理文档处理错误事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "document.process.error",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    # ==================== 知识蒸馏事件处理 ====================

    async def _handle_distillation_start(self, event: Dict[str, Any]):
        """处理知识蒸馏开始事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "distillation.job.start",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_distillation_progress(self, event: Dict[str, Any]):
        """处理知识蒸馏进度事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "distillation.job.progress",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_distillation_complete(self, event: Dict[str, Any]):
        """处理知识蒸馏完成事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "distillation.job.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    async def _handle_distillation_error(self, event: Dict[str, Any]):
        """处理知识蒸馏错误事件"""
        data = event.get("data", {})
        project_id = data.get("project_id")

        message = {
            "event": "distillation.job.error",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if project_id:
            await self.connection_manager.broadcast_to_room(f"project_{project_id}", message)

    # ==================== Deep RAG事件处理 ====================

    async def _handle_rag_query_start(self, event: Dict[str, Any]):
        """处理RAG查询开始事件"""
        data = event.get("data", {})
        session_id = data.get("session_id")

        message = {
            "event": "deep_rag.query.start",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if session_id:
            await self.connection_manager.broadcast_to_room(f"session_{session_id}", message)

    async def _handle_rag_query_complete(self, event: Dict[str, Any]):
        """处理RAG查询完成事件"""
        data = event.get("data", {})
        session_id = data.get("session_id")

        message = {
            "event": "deep_rag.query.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if session_id:
            await self.connection_manager.broadcast_to_room(f"session_{session_id}", message)

    async def _handle_rag_error(self, event: Dict[str, Any]):
        """处理RAG错误事件"""
        data = event.get("data", {})
        session_id = data.get("session_id")

        message = {
            "event": "deep_rag.error",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if session_id:
            await self.connection_manager.broadcast_to_room(f"session_{session_id}", message)

    # ==================== 批处理事件处理 ====================

    async def _handle_batch_start(self, event: Dict[str, Any]):
        """处理批处理开始事件"""
        data = event.get("data", {})
        batch_id = data.get("batch_id")

        message = {
            "event": "batch.start",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if batch_id:
            await self.connection_manager.broadcast_to_room(f"batch_{batch_id}", message)

    async def _handle_batch_item_complete(self, event: Dict[str, Any]):
        """处理批处理项完成事件"""
        data = event.get("data", {})
        batch_id = data.get("batch_id")

        message = {
            "event": "batch.item.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if batch_id:
            await self.connection_manager.broadcast_to_room(f"batch_{batch_id}", message)

    async def _handle_batch_complete(self, event: Dict[str, Any]):
        """处理批处理完成事件"""
        data = event.get("data", {})
        batch_id = data.get("batch_id")

        message = {
            "event": "batch.complete",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if batch_id:
            await self.connection_manager.broadcast_to_room(f"batch_{batch_id}", message)

    async def _handle_batch_error(self, event: Dict[str, Any]):
        """处理批处理错误事件"""
        data = event.get("data", {})
        batch_id = data.get("batch_id")

        message = {
            "event": "batch.error",
            "data": data,
            "timestamp": event.get("timestamp")
        }

        if batch_id:
            await self.connection_manager.broadcast_to_room(f"batch_{batch_id}", message)

    # ==================== 系统事件处理 ====================

    async def _handle_system_status(self, event: Dict[str, Any]):
        """处理系统状态事件"""
        message = {
            "event": "system.status",
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp")
        }

        await self.connection_manager.broadcast(message)

    async def _handle_system_error(self, event: Dict[str, Any]):
        """处理系统错误事件"""
        message = {
            "event": "system.error",
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp")
        }

        await self.connection_manager.broadcast(message)

    async def _handle_system_warning(self, event: Dict[str, Any]):
        """处理系统警告事件"""
        message = {
            "event": "system.warning",
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp")
        }

        await self.connection_manager.broadcast(message)

    # ==================== 公共方法 ====================

    def get_connection_manager(self) -> ConnectionManager:
        """获取连接管理器"""
        return self.connection_manager

    def get_event_emitter(self) -> EventEmitter:
        """获取事件发射器"""
        return self.event_emitter

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connections": {
                "active": len(self.connection_manager.active_connections),
                "total": self.connection_manager.stats["total_connections"],
                "rooms": len(self.connection_manager.rooms)
            },
            "events": self.event_emitter.get_stats()
        }


# 全局单例
_websocket_event_service: Optional[WebSocketEventService] = None


def get_websocket_event_service() -> WebSocketEventService:
    """获取WebSocket事件服务单例"""
    global _websocket_event_service
    if _websocket_event_service is None:
        _websocket_event_service = WebSocketEventService()
    return _websocket_event_service
