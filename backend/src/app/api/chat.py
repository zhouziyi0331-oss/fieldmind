"""智能对话API - 基于项目资料的深度学习对话"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.project import Project, ProjectChatSession, ProjectChatMessage, ProjectDocument
from app.schemas.chat import (
    ChatSessionCreate, ChatMessageCreate, ChatMessageResponse,
    ChatSessionResponse
)
from app.services.mem0_service import Mem0Service
from app.services.intelligent_agent import IntelligentAgent

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

# 初始化服务
mem0_service = Mem0Service()
intelligent_agent = IntelligentAgent()


@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建对话会话"""
    try:
        # 验证项目存在
        project = db.query(Project).filter(Project.id == session_data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 创建会话
        session = ProjectChatSession(
            project_id=session_data.project_id,
            name=session_data.name,
            document_ids=session_data.document_ids,
            config=session_data.config or {}
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Created chat session {session.id} for project {session_data.project_id}")

        return ChatSessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """获取对话会话"""
    try:
        session = db.query(ProjectChatSession).filter(ProjectChatSession.id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return ChatSessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/sessions")
def list_project_sessions(
    project_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取项目的所有对话会话"""
    try:
        query = db.query(ProjectChatSession).filter(ProjectChatSession.project_id == project_id)

        total = query.count()
        sessions = query.order_by(ProjectChatSession.last_message_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "sessions": [ChatSessionResponse.model_validate(s) for s in sessions]
        }

    except Exception as e:
        logger.error(f"Failed to list sessions for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def send_message(
    session_id: int,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI响应

    这是核心对话功能：
    1. 检索项目的长记忆
    2. 加载项目专属的skill框架
    3. 结合文档内容和对话历史
    4. 使用深度思考生成响应
    5. 自动学习并更新记忆
    """
    try:
        # 获取会话
        session = db.query(ProjectChatSession).filter(ProjectChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        project_id = session.project_id

        # 获取项目
        project = db.query(Project).filter(Project.id == project_id).first()

        # 保存用户消息
        user_msg = ProjectChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.content
        )
        db.add(user_msg)

        # 1. 检索相关记忆
        relevant_memories = mem0_service.search_memories(
            project_id=project_id,
            query=message_data.content,
            limit=10
        )

        # 2. 获取技能框架
        skill_framework = None
        if project.settings and "skill_framework" in project.settings:
            skill_framework = project.settings["skill_framework"]

        # 3. 获取项目分析结果
        project_summary = None
        key_themes = []
        if project.settings and "analysis" in project.settings:
            analysis = project.settings["analysis"]
            project_summary = analysis.get("project_summary")
            key_themes = analysis.get("key_themes", [])

        # 4. 获取相关文档
        relevant_documents = []
        if session.document_ids:
            docs = db.query(ProjectDocument).filter(
                ProjectDocument.id.in_(session.document_ids)
            ).all()

            relevant_documents = [{
                "filename": doc.filename,
                "content": doc.text_content[:2000] if doc.text_content else ""
            } for doc in docs]

        # 5. 获取最近对话历史
        recent_messages = db.query(ProjectChatMessage).filter(
            ProjectChatMessage.session_id == session_id
        ).order_by(ProjectChatMessage.created_at.desc()).limit(10).all()

        recent_conversations = [{
            "role": msg.role,
            "content": msg.content
        } for msg in reversed(recent_messages)]

        # 6. 构建上下文
        context = {
            "project_summary": project_summary,
            "key_themes": key_themes,
            "relevant_memories": relevant_memories,
            "relevant_documents": relevant_documents,
            "recent_conversations": recent_conversations
        }

        # 7. 获取会话配置
        config = session.config or {}
        enable_deep_thinking = config.get("use_deep_thinking", True)
        enable_web_search = config.get("enable_web_search", False)

        # 8. 生成AI响应
        ai_response = intelligent_agent.generate_response(
            project_id=project_id,
            user_message=message_data.content,
            context=context,
            skill_framework=skill_framework,
            enable_deep_thinking=enable_deep_thinking,
            enable_web_search=enable_web_search
        )

        if "error" in ai_response:
            raise HTTPException(status_code=500, detail=ai_response["error"])

        # 9. 保存AI响应
        assistant_msg = ProjectChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_response["message"],
            thinking_process=ai_response.get("thinking_process"),
            sources=ai_response.get("sources"),
            extra_data={
                "model": ai_response.get("model"),
                "tokens_used": ai_response.get("tokens_used"),
                "memory_retrieved": len(relevant_memories)
            }
        )
        db.add(assistant_msg)

        # 10. 添加到长记忆
        mem0_service.add_conversation_memory(
            project_id=project_id,
            session_id=session_id,
            user_message=message_data.content,
            assistant_message=ai_response["message"],
            metadata={
                "session_name": session.name,
                "has_thinking": bool(ai_response.get("thinking_process"))
            }
        )

        # 11. 更新会话统计
        session.message_count += 2
        session.last_message_at = datetime.utcnow()

        # 12. 更新项目活动时间
        project.last_activity_at = datetime.utcnow()

        db.commit()
        db.refresh(assistant_msg)

        logger.info(f"Generated AI response for session {session_id}")

        return ChatMessageResponse.model_validate(assistant_msg)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取会话的所有消息"""
    try:
        session = db.query(ProjectChatSession).filter(ProjectChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        query = db.query(ProjectChatMessage).filter(ProjectChatMessage.session_id == session_id)

        total = query.count()
        messages = query.order_by(ProjectChatMessage.created_at.asc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "messages": [ChatMessageResponse.model_validate(msg) for msg in messages]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """删除对话会话"""
    try:
        session = db.query(ProjectChatSession).filter(ProjectChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        db.delete(session)
        db.commit()

        logger.info(f"Deleted session {session_id}")

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/evolve-skill")
def evolve_session_skill(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    进化会话的技能框架

    基于最新的对话历史，自动优化项目的skill框架
    这实现了自我学习和进化功能
    """
    try:
        session = db.query(ProjectChatSession).filter(ProjectChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        project = db.query(Project).filter(Project.id == session.project_id).first()

        # 获取当前技能框架
        current_framework = project.settings.get("skill_framework") if project.settings else {}

        if not current_framework:
            raise HTTPException(status_code=400, detail="No skill framework found. Run project analysis first.")

        # 获取最近的交互
        recent_messages = db.query(ProjectChatMessage).filter(
            ProjectChatMessage.session_id == session_id
        ).order_by(ProjectChatMessage.created_at.desc()).limit(50).all()

        new_interactions = [{
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        } for msg in reversed(recent_messages)]

        # 进化技能框架
        evolved_framework = intelligent_agent.evolve_skill_framework(
            project_id=session.project_id,
            current_framework=current_framework,
            new_interactions=new_interactions,
            feedback=None  # TODO: 添加用户反馈机制
        )

        # 保存进化后的框架
        project.settings = project.settings or {}
        project.settings["skill_framework"] = evolved_framework
        project.settings["last_evolution"] = datetime.utcnow().isoformat()

        db.commit()

        logger.info(f"Evolved skill framework for project {session.project_id}")

        return {
            "message": "Skill framework evolved successfully",
            "framework": evolved_framework
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to evolve skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))
