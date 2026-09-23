"""项目对话API端点 - 集成长记忆和深度思考"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.project import ProjectChatSession, ProjectChatMessage
from app.schemas.project import (
    ProjectChatSessionCreate, ProjectChatSessionResponse,
    ProjectChatMessageCreate, ProjectChatMessageResponse
)
from app.services.enhanced_chat_service import enhanced_chat_service
from app.services.memory_service import MemoryService

router = APIRouter()


@router.post("/{project_id}/chat-sessions/{session_id}/messages", response_model=ProjectChatMessageResponse)
async def send_chat_message(
    project_id: int,
    session_id: int,
    message_data: ProjectChatMessageCreate,
    db: Session = Depends(get_db)
):
    """发送对话消息（增强版）"""

    # 验证会话存在
    session = db.query(ProjectChatSession).filter(
        ProjectChatSession.id == session_id,
        ProjectChatSession.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取配置
    config = session.config or {}
    use_long_memory = message_data.use_long_memory if message_data.use_long_memory is not None else config.get("use_long_memory", True)
    use_deep_thinking = message_data.use_deep_thinking if message_data.use_deep_thinking is not None else config.get("use_deep_thinking", False)
    skill_name = message_data.skill_name or config.get("skill_name")
    framework = message_data.framework or config.get("framework")

    # 构建技能配置
    skill_config = None
    if skill_name or framework:
        skill_config = {
            "skill_name": skill_name or framework,
            "workflow_prompt": _get_framework_prompt(framework) if framework else None
        }

    # 调用增强对话服务
    try:
        result = enhanced_chat_service.chat_with_skill(
            query=message_data.message,
            session_id=str(session_id),
            skill_config=skill_config,
            memory_config={
                "search_depth": config.get("memory_search_depth", 10),
                "relevance_threshold": 0.7
            },
            project_id=project_id,
            use_deep_thinking=use_deep_thinking,
            use_long_context=use_long_memory,
            max_tokens=8192
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("answer", "对话失败"))

        # 保存用户消息
        user_msg = ProjectChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.message,
            metadata={
                "use_long_memory": use_long_memory,
                "use_deep_thinking": use_deep_thinking,
                "skill_name": skill_name,
                "framework": framework
            }
        )
        db.add(user_msg)

        # 保存助手消息
        assistant_msg = ProjectChatMessage(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            thinking_process=result.get("thinking_process"),
            sources=result.get("sources", []),
            metadata={
                "model": result["model"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "processing_time": result["processing_time"],
                "memory_used": result["memory_used"],
                "deep_thinking_used": result["deep_thinking_used"],
                "skill_applied": result.get("skill_applied")
            }
        )
        db.add(assistant_msg)

        # 更新会话
        session.message_count += 2
        session.last_message_at = assistant_msg.created_at
        session.updated_at = assistant_msg.created_at

        # 更新项目活动时间
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.last_activity_at = assistant_msg.created_at

        db.commit()
        db.refresh(assistant_msg)

        # 异步提取记忆
        memory_service = MemoryService(db, project_id)
        await memory_service.extract_from_chat(session_id, assistant_msg.id)

        return assistant_msg

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.get("/{project_id}/chat-sessions/{session_id}/messages", response_model=List[ProjectChatMessageResponse])
async def get_chat_messages(
    project_id: int,
    session_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取对话消息列表"""

    # 验证会话存在
    session = db.query(ProjectChatSession).filter(
        ProjectChatSession.id == session_id,
        ProjectChatSession.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.query(ProjectChatMessage).filter(
        ProjectChatMessage.session_id == session_id
    ).order_by(ProjectChatMessage.created_at).offset(skip).limit(limit).all()

    return messages


def _get_framework_prompt(framework: str) -> str:
    """获取分析框架提示词"""
    frameworks = {
        "fxt-differential": """## 差序格局分析框架

分析社会关系的层次结构：
1. 核心圈层：家庭、亲属关系
2. 次级圈层：朋友、熟人
3. 外围圈层：陌生人、外来者

关注：权力分配、资源流动、信任机制""",

        "fxt-ritual": """## 仪式过程分析框架

分析仪式的结构和意义：
1. 分离阶段：脱离日常状态
2. 过渡阶段：边缘状态（liminality）
3. 整合阶段：重新融入社会

关注：象征符号、权力关系、身份转换""",

        "fxt-acquaintance": """## 熟人社会分析框架

分析熟人关系网络：
1. 信任基础：血缘、地缘、业缘
2. 互惠机制：人情往来、面子工程
3. 社会资本：关系网络的价值

关注：关系维护、资源交换、社会规范"""
    }

    return frameworks.get(framework, "")
