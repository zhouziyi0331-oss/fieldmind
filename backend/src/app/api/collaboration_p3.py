"""
协作编辑 API 端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
import uuid

from app.middleware.auth import get_current_user
# WebSocket 认证暂时禁用，直接允许连接
# from app.middleware.auth import get_current_user_ws
try:
    from app.models.user import User
except ImportError:
    from app.schemas.user import User
# 暂时禁用 WebSocket 处理器，使用内联实现
# from app.websocket.collaboration_handler import collaboration_handler

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


class CreateDocumentRequest(BaseModel):
    """创建文档请求"""
    document_id: Optional[str] = Field(None, description="文档 ID，不提供则自动生成")
    initial_content: str = Field("", description="初始内容")


class DocumentResponse(BaseModel):
    """文档响应"""
    document_id: str
    content: str
    version: int
    active_users: int
    created_at: str
    updated_at: str


@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    request: CreateDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建新文档

    创建一个可协作编辑的文档
    """
    document_id = request.document_id or str(uuid.uuid4())

    # 检查文档是否已存在
    existing_doc = collaboration_handler.document_sync.get_document(document_id)
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document {document_id} already exists"
        )

    # 创建文档
    doc = collaboration_handler.document_sync.create_document(
        document_id=document_id,
        initial_content=request.initial_content
    )

    return DocumentResponse(
        document_id=doc.document_id,
        content=doc.content,
        version=doc.version,
        active_users=len(doc.active_users),
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat()
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文档信息

    获取文档当前状态和元数据
    """
    doc = collaboration_handler.document_sync.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return DocumentResponse(
        document_id=doc.document_id,
        content=doc.content,
        version=doc.version,
        active_users=len(doc.active_users),
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat()
    )


@router.get("/documents/{document_id}/users")
async def get_active_users(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文档的活跃用户

    返回正在编辑该文档的所有用户
    """
    doc = collaboration_handler.document_sync.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    active_users = collaboration_handler.collaboration_manager.get_active_users(document_id)

    return {
        "document_id": document_id,
        "active_users": active_users,
        "count": len(active_users)
    }


@router.get("/documents/{document_id}/cursors")
async def get_cursors(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文档的所有光标位置

    返回所有用户的光标位置和选区
    """
    doc = collaboration_handler.document_sync.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    cursors = collaboration_handler.collaboration_manager.get_cursors(document_id)

    return {
        "document_id": document_id,
        "cursors": cursors
    }


@router.get("/stats")
async def get_collaboration_stats(current_user: User = Depends(get_current_user)):
    """
    获取协作统计信息

    返回当前所有协作会话的统计数据
    """
    stats = collaboration_handler.get_stats()
    return stats


@router.websocket("/ws/{document_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    document_id: str,
    token: str
):
    """
    WebSocket 协作编辑连接

    建立实时协作编辑的 WebSocket 连接

    Args:
        websocket: WebSocket 连接
        document_id: 文档 ID
        token: 认证 token (通过查询参数传递)
    """
    try:
        # 认证用户
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 生成会话 ID
        session_id = str(uuid.uuid4())

        # 启动清理任务（如果还没启动）
        await collaboration_handler.start_cleanup_task()

        # 连接
        await collaboration_handler.connect(websocket, document_id, user, session_id)

        try:
            # 消息循环
            while True:
                message = await websocket.receive_text()
                await collaboration_handler.handle_message(websocket, message)

        except WebSocketDisconnect:
            await collaboration_handler.disconnect(websocket)

    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
