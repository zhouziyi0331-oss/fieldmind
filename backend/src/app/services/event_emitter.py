"""
事件发射器 - 事件发布/订阅系统
Phase 3.7 - WebSocket实时通知系统

功能：
- 事件发布/订阅模式
- 与WebSocket管理器集成
- 处理流程进度钩子
- 异步事件处理

作者：FieldMind Team
创建时间：2026-08-09
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventEmitter:
    """事件发射器 - 发布/订阅模式"""
    def __init__(self, use_workflow_engine: bool = True):

        # 事件监听器：{event_type: [callback1, callback2, ...]}
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.listeners: Dict[str, List[Callable]] = {}

        # 事件历史（最近100条）
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 100

        # 统计信息
        self.stats = {
            'total_events': 0,
            'total_listeners': 0,
            'events_by_type': {}
        }

        logger.info("EventEmitter initialized")

    def on(self, event_type: str, callback: Callable):
        """
        注册事件监听器

        Args:
            event_type: 事件类型
            callback: 回调函数（可以是同步或异步）
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []

        self.listeners[event_type].append(callback)
        self.stats['total_listeners'] += 1

        logger.info(f"Registered listener for event '{event_type}'. Total listeners: {len(self.listeners[event_type])}")

    def off(self, event_type: str, callback: Callable):
        """
        移除事件监听器

        Args:
            event_type: 事件类型
            callback: 要移除的回调函数
        """
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
            self.stats['total_listeners'] -= 1
            logger.info(f"Removed listener for event '{event_type}'")

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        发射事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        # 添加元数据
        event = {
            'event': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        # 记录到历史
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # 更新统计
        self.stats['total_events'] += 1
        if event_type not in self.stats['events_by_type']:
            self.stats['events_by_type'][event_type] = 0
        self.stats['events_by_type'][event_type] += 1

        logger.debug(f"Emitting event '{event_type}' with data: {data}")

        # 调用所有监听器
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    # 支持同步和异步回调
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event listener for '{event_type}': {e}")

    def get_history(self, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取事件历史

        Args:
            event_type: 过滤特定事件类型（None表示全部）
            limit: 返回数量限制

        Returns:
            事件历史列表
        """
        if event_type:
            filtered = [e for e in self.event_history if e['event'] == event_type]
            return filtered[-limit:]
        else:
            return self.event_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_events': self.stats['total_events'],
            'total_listeners': self.stats['total_listeners'],
            'events_by_type': self.stats['events_by_type'],
            'registered_event_types': list(self.listeners.keys())
        }


# 全局单例
_emitter: Optional[EventEmitter] = None


def get_event_emitter() -> EventEmitter:
    """获取全局EventEmitter实例"""
    global _emitter
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter


# ============ 预定义事件类型 ============

class EventTypes:
    """标准事件类型定义"""

    # 文档处理事件
    DOCUMENT_UPLOAD_START = "document.upload.start"
    DOCUMENT_UPLOAD_PROGRESS = "document.upload.progress"
    DOCUMENT_UPLOAD_COMPLETE = "document.upload.complete"
    DOCUMENT_UPLOAD_ERROR = "document.upload.error"

    DOCUMENT_PROCESS_START = "document.process.start"
    DOCUMENT_PROCESS_PROGRESS = "document.process.progress"
    DOCUMENT_PROCESS_COMPLETE = "document.process.complete"
    DOCUMENT_PROCESS_ERROR = "document.process.error"

    # 检索事件
    RETRIEVAL_START = "retrieval.start"
    RETRIEVAL_SOURCE_COMPLETE = "retrieval.source.complete"
    RETRIEVAL_COMPLETE = "retrieval.complete"
    RETRIEVAL_ERROR = "retrieval.error"

    # Deep RAG事件
    DEEP_RAG_QUERY_START = "deep_rag.query.start"
    DEEP_RAG_RETRIEVE_START = "deep_rag.retrieve.start"
    DEEP_RAG_RETRIEVE_COMPLETE = "deep_rag.retrieve.complete"
    DEEP_RAG_FUSION_START = "deep_rag.fusion.start"
    DEEP_RAG_FUSION_COMPLETE = "deep_rag.fusion.complete"
    DEEP_RAG_LLM_START = "deep_rag.llm.start"
    DEEP_RAG_LLM_COMPLETE = "deep_rag.llm.complete"
    DEEP_RAG_QUERY_COMPLETE = "deep_rag.query.complete"
    DEEP_RAG_ERROR = "deep_rag.error"

    # 批处理事件
    BATCH_START = "batch.start"
    BATCH_ITEM_START = "batch.item.start"
    BATCH_ITEM_COMPLETE = "batch.item.complete"
    BATCH_ITEM_ERROR = "batch.item.error"
    BATCH_COMPLETE = "batch.complete"
    BATCH_ERROR = "batch.error"

    # 系统事件
    SYSTEM_STATUS = "system.status"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


# ============ WebSocket集成助手 ============

async def setup_websocket_listeners():
    """
    设置WebSocket事件监听器
    将事件通过WebSocket推送给客户端
    """
    from app.services.websocket_manager import get_connection_manager

    emitter = get_event_emitter()
    manager = get_connection_manager()

    # 定义通用广播处理器
    async def broadcast_handler(event: Dict[str, Any]):
        """将事件广播给所有WebSocket客户端"""
        await manager.broadcast(event)

    # 定义房间广播处理器
    def room_broadcast_handler(room_key: str):
        """返回一个向特定房间广播的处理器"""
        async def handler(event: Dict[str, Any]):
            # 从事件数据中提取房间ID
            room_id = event.get('data', {}).get(room_key)
            if room_id:
                await manager.broadcast_to_room(str(room_id), event)
            else:
                # 如果没有房间ID，全局广播
                await manager.broadcast(event)
        return handler

    # 注册文档处理事件（按project_id分组）
    emitter.on(EventTypes.DOCUMENT_UPLOAD_START, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_UPLOAD_PROGRESS, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_UPLOAD_COMPLETE, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_UPLOAD_ERROR, room_broadcast_handler('project_id'))

    emitter.on(EventTypes.DOCUMENT_PROCESS_START, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_PROCESS_PROGRESS, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_PROCESS_COMPLETE, room_broadcast_handler('project_id'))
    emitter.on(EventTypes.DOCUMENT_PROCESS_ERROR, room_broadcast_handler('project_id'))

    # 注册Deep RAG事件（按session_id分组）
    emitter.on(EventTypes.DEEP_RAG_QUERY_START, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_RETRIEVE_START, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_RETRIEVE_COMPLETE, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_FUSION_START, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_FUSION_COMPLETE, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_LLM_START, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_LLM_COMPLETE, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_QUERY_COMPLETE, room_broadcast_handler('session_id'))
    emitter.on(EventTypes.DEEP_RAG_ERROR, room_broadcast_handler('session_id'))

    # 注册批处理事件（按batch_id分组）
    emitter.on(EventTypes.BATCH_START, room_broadcast_handler('batch_id'))
    emitter.on(EventTypes.BATCH_ITEM_START, room_broadcast_handler('batch_id'))
    emitter.on(EventTypes.BATCH_ITEM_COMPLETE, room_broadcast_handler('batch_id'))
    emitter.on(EventTypes.BATCH_ITEM_ERROR, room_broadcast_handler('batch_id'))
    emitter.on(EventTypes.BATCH_COMPLETE, room_broadcast_handler('batch_id'))
    emitter.on(EventTypes.BATCH_ERROR, room_broadcast_handler('batch_id'))

    # 注册系统事件（全局广播）
    emitter.on(EventTypes.SYSTEM_STATUS, broadcast_handler)
    emitter.on(EventTypes.SYSTEM_ERROR, broadcast_handler)
    emitter.on(EventTypes.SYSTEM_WARNING, broadcast_handler)

    logger.info("WebSocket event listeners configured")
