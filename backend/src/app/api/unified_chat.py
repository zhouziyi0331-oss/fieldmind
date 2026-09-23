"""
统一聊天对话API - 整合所有聊天对话相关功能
合并自: chat, enhanced_chat, project_chat, conversation_memory, conversation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter(prefix="/api/chat", tags=["统一聊天对话"])

# ============================================================================
# 请求/响应模型
# ============================================================================

class SessionCreateRequest(BaseModel):
    """会话创建请求"""
    project_id: int = Field(..., description="项目ID")
    title: Optional[str] = Field(None, description="会话标题")


class MessageSendRequest(BaseModel):
    """消息发送请求"""
    content: str = Field(..., description="消息内容")
    role: str = Field(default="user", description="角色: user/assistant")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    stream: bool = Field(default=False, description="是否流式输出")
    use_rag: bool = Field(default=True, description="是否使用RAG")


class ConversationSearchRequest(BaseModel):
    """对话搜索请求"""
    query: str = Field(..., description="搜索关键词")
    project_id: Optional[int] = Field(None, description="项目ID")
    limit: int = Field(default=20, ge=1, le=100)


# ============================================================================
# 1. 会话管理
# ============================================================================

@router.post("/sessions", response_model=ApiResponse, summary="创建会话")
async def create_session(
    request: Request,
    session_request: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建新的聊天会话

    每个项目可以有多个会话
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession
        import uuid

        session = ChatSession(
            id=str(uuid.uuid4()),
            project_id=session_request.project_id,
            title=session_request.title or "新对话",
            created_at=datetime.now()
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return success_response(
            data={
                "session_id": session.id,
                "project_id": session.project_id,
                "title": session.title
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=ApiResponse, summary="查询会话列表")
async def list_sessions(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取项目的会话列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession

        query = db.query(ChatSession).filter(
            ChatSession.project_id == project_id
        ).order_by(ChatSession.created_at.desc())

        total = query.count()
        sessions = query.offset(offset).limit(limit).all()

        result = {
            "sessions": [
                {
                    "session_id": s.id,
                    "title": s.title,
                    "project_id": s.project_id,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in sessions
            ],
            "total": total
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ApiResponse, summary="获取会话详情")
async def get_session(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        result = {
            "session_id": session.id,
            "title": session.title,
            "project_id": session.project_id,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", response_model=ApiResponse, summary="删除会话")
async def delete_session(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除会话及其所有消息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession, ChatMessage

        # 删除消息
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()

        # 删除会话
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        db.delete(session)
        db.commit()

        return success_response(
            data={"deleted_session_id": session_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. 消息管理
# ============================================================================

@router.post("/sessions/{session_id}/messages", response_model=ApiResponse, summary="发送消息")
async def send_message(
    request: Request,
    session_id: str,
    message_request: MessageSendRequest,
    db: Session = Depends(get_db)
):
    """
    向会话发送消息

    支持用户消息和助手消息
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatMessage, ChatSession

        # 验证会话存在
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 创建消息
        message = ChatMessage(
            session_id=session_id,
            role=message_request.role,
            content=message_request.content,
            created_at=datetime.now()
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return success_response(
            data={
                "message_id": message.id,
                "session_id": session_id,
                "role": message.role,
                "content": message.content
            },
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse, summary="获取消息列表")
async def get_messages(
    request: Request,
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取会话的消息历史"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatMessage

        query = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())

        total = query.count()
        messages = query.offset(offset).limit(limit).all()

        result = {
            "messages": [
                {
                    "message_id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ],
            "total": total,
            "session_id": session_id
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. 增强对话
# ============================================================================

@router.post("/enhanced", response_model=ApiResponse, summary="增强对话")
async def enhanced_chat(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    增强对话接口

    特性:
    - 支持RAG检索
    - 上下文管理
    - 记忆增强
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 集成RAG和LLM
        # 1. 如果use_rag=True，先检索相关文档
        # 2. 构建上下文
        # 3. 调用LLM生成回答
        # 4. 保存对话历史

        response_text = f"收到您的消息：{chat_request.message}"

        return success_response(
            data={
                "response": response_text,
                "session_id": chat_request.session_id or "new_session"
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced/stream", summary="流式增强对话")
async def enhanced_chat_stream(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    流式增强对话

    使用SSE推送响应
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def generate():
        try:
            # 模拟流式输出
            response_text = f"正在处理您的问题：{chat_request.message}..."

            for char in response_text:
                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                await asyncio.sleep(0.01)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# 4. 项目对话
# ============================================================================

@router.post("/projects/{project_id}/ask", response_model=ApiResponse, summary="项目问答")
async def project_ask(
    request: Request,
    project_id: int,
    question: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    针对项目进行问答

    自动检索项目相关文档进行回答
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 实现项目问答逻辑
        # 1. 检索项目文档
        # 2. 生成回答
        # 3. 记录对话

        answer = f"针对项目{project_id}的问题：{question}"

        return success_response(
            data={"answer": answer, "project_id": project_id},
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/context", response_model=ApiResponse, summary="获取项目上下文")
async def get_project_context(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的对话上下文"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession

        # 获取项目的会话数
        session_count = db.query(ChatSession).filter(
            ChatSession.project_id == project_id
        ).count()

        result = {
            "project_id": project_id,
            "session_count": session_count,
            "has_context": session_count > 0
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. 对话搜索
# ============================================================================

@router.post("/conversations/search", response_model=ApiResponse, summary="搜索对话")
async def search_conversations(
    request: Request,
    search_request: ConversationSearchRequest,
    db: Session = Depends(get_db)
):
    """在对话历史中搜索"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatMessage

        query = db.query(ChatMessage).filter(
            ChatMessage.content.contains(search_request.query)
        )

        if search_request.project_id:
            # TODO: 通过session关联过滤项目
            pass

        messages = query.limit(search_request.limit).all()

        result = {
            "query": search_request.query,
            "messages": [
                {
                    "message_id": m.id,
                    "session_id": m.session_id,
                    "content": m.content,
                    "role": m.role
                }
                for m in messages
            ],
            "total": len(messages)
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/recent", response_model=ApiResponse, summary="获取最近对话")
async def get_recent_conversations(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取最近的对话"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession

        query = db.query(ChatSession).order_by(
            ChatSession.created_at.desc()
        )

        if project_id:
            query = query.filter(ChatSession.project_id == project_id)

        sessions = query.limit(limit).all()

        result = {
            "sessions": [
                {
                    "session_id": s.id,
                    "title": s.title,
                    "project_id": s.project_id,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in sessions
            ]
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. 统计与总结
# ============================================================================

@router.get("/statistics", response_model=ApiResponse, summary="对话统计")
async def get_statistics(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db)
):
    """获取对话统计信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession, ChatMessage
        from sqlalchemy import func

        # 会话数
        session_query = db.query(func.count(ChatSession.id))
        if project_id:
            session_query = session_query.filter(ChatSession.project_id == project_id)
        session_count = session_query.scalar() or 0

        # 消息数
        message_count = db.query(func.count(ChatMessage.id)).scalar() or 0

        result = {
            "session_count": session_count,
            "message_count": message_count,
            "project_id": project_id
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/summary", response_model=ApiResponse, summary="项目对话总结")
async def get_project_summary(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的对话总结"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chat import ChatSession, ChatMessage
        from sqlalchemy import func

        # 项目会话数
        session_count = db.query(func.count(ChatSession.id)).filter(
            ChatSession.project_id == project_id
        ).scalar() or 0

        # TODO: 生成总结

        result = {
            "project_id": project_id,
            "session_count": session_count,
            "summary": "项目对话总结"
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
