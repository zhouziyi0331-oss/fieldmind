"""
WebSocket 工作流进度推送管理器

提供实时进度更新和状态推送功能
"""
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class WorkflowProgressManager:
    """工作流进度WebSocket管理器"""

    def __init__(self):
        # execution_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, execution_id: int):
        """
        连接WebSocket客户端

        Args:
            websocket: WebSocket连接
            execution_id: 工作流执行ID
        """
        await websocket.accept()

        async with self.lock:
            if execution_id not in self.active_connections:
                self.active_connections[execution_id] = set()
            self.active_connections[execution_id].add(websocket)

        logger.info(f"WebSocket连接: execution_id={execution_id}, 总连接数={len(self.active_connections[execution_id])}")

    async def disconnect(self, websocket: WebSocket, execution_id: int):
        """
        断开WebSocket客户端

        Args:
            websocket: WebSocket连接
            execution_id: 工作流执行ID
        """
        async with self.lock:
            if execution_id in self.active_connections:
                self.active_connections[execution_id].discard(websocket)

                # 如果没有连接了，清理该执行的记录
                if not self.active_connections[execution_id]:
                    del self.active_connections[execution_id]

        logger.info(f"WebSocket断开: execution_id={execution_id}")

    async def send_progress(
        self,
        execution_id: int,
        step_name: str,
        status: str,
        progress: float,
        message: Optional[str] = None,
        error: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        发送进度更新到所有订阅该执行的客户端

        Args:
            execution_id: 工作流执行ID
            step_name: 步骤名称
            status: 状态（pending, running, completed, failed）
            progress: 进度百分比（0-100）
            message: 可选，进度消息
            error: 可选，错误信息
            extra_data: 可选，额外数据
        """
        if execution_id not in self.active_connections:
            return

        # 构造进度消息
        progress_data = {
            "type": "progress",
            "execution_id": execution_id,
            "step_name": step_name,
            "status": status,
            "progress": progress,
            "message": message,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }

        if extra_data:
            progress_data.update(extra_data)

        message_json = json.dumps(progress_data, ensure_ascii=False)

        # 向所有连接发送
        disconnected = []
        for websocket in self.active_connections[execution_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"发送进度失败: {e}")
                disconnected.append(websocket)

        # 清理失败的连接
        for ws in disconnected:
            await self.disconnect(ws, execution_id)

    async def send_execution_status(
        self,
        execution_id: int,
        status: str,
        total_steps: int,
        completed_steps: int,
        failed_steps: int,
        current_step: Optional[str] = None,
        message: Optional[str] = None
    ):
        """
        发送整体执行状态更新

        Args:
            execution_id: 工作流执行ID
            status: 整体状态
            total_steps: 总步骤数
            completed_steps: 已完成步骤数
            failed_steps: 失败步骤数
            current_step: 当前步骤名称
            message: 可选消息
        """
        if execution_id not in self.active_connections:
            return

        status_data = {
            "type": "execution_status",
            "execution_id": execution_id,
            "status": status,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "current_step": current_step,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }

        message_json = json.dumps(status_data, ensure_ascii=False)

        # 向所有连接发送
        disconnected = []
        for websocket in self.active_connections[execution_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"发送状态失败: {e}")
                disconnected.append(websocket)

        # 清理失败的连接
        for ws in disconnected:
            await self.disconnect(ws, execution_id)

    async def send_step_output(
        self,
        execution_id: int,
        step_name: str,
        output_data: Dict[str, Any]
    ):
        """
        发送步骤输出数据

        Args:
            execution_id: 工作流执行ID
            step_name: 步骤名称
            output_data: 输出数据
        """
        if execution_id not in self.active_connections:
            return

        output_message = {
            "type": "step_output",
            "execution_id": execution_id,
            "step_name": step_name,
            "output_data": output_data,
            "timestamp": asyncio.get_event_loop().time()
        }

        message_json = json.dumps(output_message, ensure_ascii=False)

        disconnected = []
        for websocket in self.active_connections[execution_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"发送输出失败: {e}")
                disconnected.append(websocket)

        for ws in disconnected:
            await self.disconnect(ws, execution_id)

    async def send_completion(
        self,
        execution_id: int,
        status: str,
        result: Dict[str, Any],
        duration_seconds: float
    ):
        """
        发送工作流完成消息

        Args:
            execution_id: 工作流执行ID
            status: 最终状态（completed, failed, cancelled）
            result: 结果数据
            duration_seconds: 执行耗时（秒）
        """
        if execution_id not in self.active_connections:
            return

        completion_message = {
            "type": "completion",
            "execution_id": execution_id,
            "status": status,
            "result": result,
            "duration_seconds": duration_seconds,
            "timestamp": asyncio.get_event_loop().time()
        }

        message_json = json.dumps(completion_message, ensure_ascii=False)

        disconnected = []
        for websocket in self.active_connections[execution_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"发送完成消息失败: {e}")
                disconnected.append(websocket)

        for ws in disconnected:
            await self.disconnect(ws, execution_id)

    def get_connection_count(self, execution_id: Optional[int] = None) -> int:
        """
        获取连接数

        Args:
            execution_id: 可选，指定执行ID

        Returns:
            连接数
        """
        if execution_id:
            return len(self.active_connections.get(execution_id, set()))
        else:
            return sum(len(conns) for conns in self.active_connections.values())

    async def broadcast_message(
        self,
        execution_id: int,
        message_type: str,
        data: Dict[str, Any]
    ):
        """
        广播自定义消息

        Args:
            execution_id: 工作流执行ID
            message_type: 消息类型
            data: 消息数据
        """
        if execution_id not in self.active_connections:
            return

        message = {
            "type": message_type,
            "execution_id": execution_id,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }

        message_json = json.dumps(message, ensure_ascii=False)

        disconnected = []
        for websocket in self.active_connections[execution_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"广播消息失败: {e}")
                disconnected.append(websocket)

        for ws in disconnected:
            await self.disconnect(ws, execution_id)


# 全局单例实例
workflow_progress_manager = WorkflowProgressManager()


def create_progress_callback(execution_id: int):
    """
    创建进度回调函数工厂

    用法示例：
        progress_callback = create_progress_callback(execution_id)
        await workflow_service.execute_workflow(execution_id, progress_callback)

    Args:
        execution_id: 工作流执行ID

    Returns:
        进度回调函数
    """
    async def progress_callback(
        step_name: str,
        status: str,
        progress: float,
        message: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        await workflow_progress_manager.send_progress(
            execution_id=execution_id,
            step_name=step_name,
            status=status,
            progress=progress,
            message=message,
            error=error,
            extra_data=kwargs
        )

    return progress_callback
