"""
WebSocket API 端点
提供实时通知功能
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.websocket import manager
from app.models.project import Project

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket 连接端点

    客户端连接后会收到实时通知：
    - document_status: 文档处理状态变化
    - project_stats: 项目统计更新
    """

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        await websocket.close(code=1008, reason="Project not found")
        return

    # 接受连接
    await manager.connect(websocket, project_id)

    try:
        # 发送欢迎消息
        await manager.send_personal_message({
            "type": "connected",
            "project_id": project_id,
            "project_name": project.name,
            "message": "WebSocket 连接成功"
        }, websocket)

        # 保持连接，接收客户端消息（如果需要）
        while True:
            data = await websocket.receive_text()
            # 这里可以处理客户端发来的消息
            logger.debug(f"收到客户端消息: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        logger.info(f"客户端断开连接: project_id={project_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect(websocket, project_id)
