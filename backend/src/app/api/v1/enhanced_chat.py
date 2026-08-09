"""
增强对话API路由 - 支持长记忆、技能模型、深度思考
Enhanced Chat API with Long Memory, Skills, and Deep Thinking
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.enhanced_chat_service import enhanced_chat_service
from app.services.long_memory_service import long_memory_service
from app.models.chat import ChatSession, ChatMessage
import json

router = APIRouter()


# ==================== Schemas ====================

class MemoryConfig(BaseModel):
    """记忆配置"""
    search_depth: int = Field(10, description="检索深度")
    relevance_threshold: float = Field(0.7, description="相关度阈值")
    max_context_tokens: int = Field(8000, description="最大上下文tokens")


class SkillConfig(BaseModel):
    """技能配置"""
    skill_id: Optional[int] = None
    skill_name: str = Field(..., description="技能名称")
    workflow_prompt: Optional[str] = Field(None, description="工作流提示词")
    parameters: Optional[Dict[str, Any]] = None


class EnhancedChatRequest(BaseModel):
    """增强对话请求"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    project_id: Optional[int] = Field(None, description="项目ID")

    # 增强功能配置
    use_long_memory: bool = Field(True, description="启用长记忆")
    use_deep_thinking: bool = Field(False, description="启用深度思考")
    use_long_context: bool = Field(True, description="启用长上下文")

    # 配置对象
    memory_config: Optional[MemoryConfig] = None
    skill_config: Optional[SkillConfig] = None

    # 其他参数
    max_tokens: int = Field(8192, description="最大输出tokens")


class ChatSessionCreate(BaseModel):
    """创建会话请求"""
    project_id: int = Field(..., description="项目ID")
    name: str = Field(..., description="会话名称")
    document_ids: Optional[List[int]] = Field(None, description="关联文档ID列表")


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., description="搜索查询")
    project_id: Optional[int] = None
    top_k: int = Field(10, description="返回结果数量")
    relevance_threshold: float = Field(0.7, description="相关度阈值")


# ==================== API Endpoints ====================

@router.post("/chat/enhanced")
async def enhanced_chat(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """
    增强AI对话

    支持功能：
    - 长记忆系统（向量检索）
    - 技能模型（工作流引导）
    - 深度思考（扩展思考模式）
    - 长上下文（大文档处理）
    """
    try:
        # 验证会话存在
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 保存用户消息
        user_message = ChatMessage(
            session_id=request.session_id,
            role='user',
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # 调用增强对话服务
        result = enhanced_chat_service.chat_with_skill(
            query=request.message,
            session_id=request.session_id,
            skill_config=request.skill_config.dict() if request.skill_config else None,
            memory_config=request.memory_config.dict() if request.memory_config else None,
            project_id=request.project_id,
            use_deep_thinking=request.use_deep_thinking,
            use_long_context=request.use_long_context,
            max_tokens=request.max_tokens
        )

        # 保存AI响应
        assistant_message = ChatMessage(
            session_id=request.session_id,
            role='assistant',
            content=result['answer'],
            sources=result.get('sources', []),
            metadata={
                'model': result.get('model'),
                'processing_time': result.get('processing_time'),
                'input_tokens': result.get('input_tokens'),
                'output_tokens': result.get('output_tokens'),
                'memory_used': result.get('memory_used'),
                'deep_thinking_used': result.get('deep_thinking_used'),
                'skill_applied': result.get('skill_applied')
            }
        )
        db.add(assistant_message)

        # 更新会话
        session.message_count += 2
        session.last_message_at = user_message.created_at

        db.commit()

        return {
            'success': True,
            'session_id': request.session_id,
            'user_message_id': user_message.id,
            'assistant_message_id': assistant_message.id,
            'answer': result['answer'],
            'thinking_process': result.get('thinking_process'),
            'metadata': {
                'model': result.get('model'),
                'processing_time': result.get('processing_time'),
                'tokens': {
                    'input': result.get('input_tokens'),
                    'output': result.get('output_tokens')
                },
                'features': {
                    'long_memory': result.get('memory_used'),
                    'deep_thinking': result.get('deep_thinking_used'),
                    'skill': result.get('skill_applied')
                }
            },
            'sources': result.get('sources', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/chat/enhanced/stream")
async def enhanced_chat_stream(
    request: EnhancedChatRequest,
    db: Session = Depends(get_db)
):
    """
    增强AI对话（流式输出）

    实时返回AI生成的内容
    """
    try:
        # 验证会话
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 保存用户消息
        user_message = ChatMessage(
            session_id=request.session_id,
            role='user',
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # 流式生成器
        async def generate():
            full_response = ""
            try:
                for chunk in enhanced_chat_service.stream_chat_with_skill(
                    query=request.message,
                    session_id=request.session_id,
                    skill_config=request.skill_config.dict() if request.skill_config else None,
                    memory_config=request.memory_config.dict() if request.memory_config else None,
                    project_id=request.project_id,
                    use_deep_thinking=request.use_deep_thinking,
                    use_long_context=request.use_long_context
                ):
                    if 'error' in chunk:
                        yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                        break

                    if chunk.get('type') == 'text':
                        content = chunk['content']
                        full_response += content
                        yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"

                # 保存完整响应
                assistant_message = ChatMessage(
                    session_id=request.session_id,
                    role='assistant',
                    content=full_response
                )
                db.add(assistant_message)
                session.message_count += 2
                db.commit()

                yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/sessions")
async def create_chat_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建AI对话会话"""
    try:
        session = ChatSession(
            project_id=request.project_id,
            name=request.name,
            context={
                'document_ids': request.document_ids or [],
                'scope': 'custom' if request.document_ids else 'all'
            }
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return {
            'success': True,
            'session': {
                'id': session.id,
                'project_id': session.project_id,
                'name': session.name,
                'created_at': session.created_at.isoformat(),
                'message_count': session.message_count
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/chat/sessions/{project_id}")
async def list_chat_sessions(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的所有对话会话"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.project_id == project_id
        ).order_by(ChatSession.updated_at.desc()).all()

        return {
            'success': True,
            'sessions': [
                {
                    'id': s.id,
                    'name': s.name,
                    'message_count': s.message_count,
                    'created_at': s.created_at.isoformat(),
                    'last_message_at': s.last_message_at.isoformat() if s.last_message_at else None
                }
                for s in sessions
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取会话的历史消息"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        messages.reverse()

        return {
            'success': True,
            'session_id': session_id,
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'sources': msg.sources,
                    'metadata': msg.metadata,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """搜索长期记忆"""
    try:
        results = long_memory_service.search_long_term_memory(
            query=request.query,
            project_id=request.project_id,
            top_k=request.top_k,
            relevance_threshold=request.relevance_threshold
        )

        return {
            'success': True,
            'query': request.query,
            'results': results,
            'count': len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记忆搜索失败: {str(e)}")


@router.get("/memory/statistics")
async def get_memory_statistics(project_id: Optional[int] = None):
    """获取记忆系统统计信息"""
    try:
        stats = long_memory_service.get_memory_statistics(project_id=project_id)

        return {
            'success': True,
            'statistics': stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除对话会话"""
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        db.delete(session)
        db.commit()

        return {
            'success': True,
            'message': '会话已删除'
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
