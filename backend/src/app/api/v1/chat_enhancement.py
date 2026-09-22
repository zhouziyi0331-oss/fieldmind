"""
对话增强API端点

提供智能对话增强功能，整合学习和技能推荐
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db
from app.services.chat_enhancement_service import ChatEnhancementService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class EnhancedChatRequest(BaseModel):
    """增强对话请求"""
    query: str = Field(..., description="用户查询")
    session_id: str = Field(..., description="会话ID")
    project_id: int = Field(..., description="项目ID")
    skill_config: Optional[Dict[str, Any]] = Field(None, description="技能配置")
    memory_config: Optional[Dict[str, Any]] = Field(None, description="记忆配置")
    use_deep_thinking: bool = Field(False, description="是否使用深度思考")
    learn_from_interaction: bool = Field(True, description="是否从交互中学习")


class EnhancedChatResponse(BaseModel):
    """增强对话响应"""
    response: str
    thinking: Optional[str] = None
    contexts_used: Dict[str, bool]
    metadata: Dict[str, Any]
    timestamp: str
    skill_suggestions: list
    learning_applied: bool
    error: Optional[bool] = None


class ConversationInsightsResponse(BaseModel):
    """对话洞察响应"""
    total_interactions: int
    success_rate: Optional[float] = None
    avg_execution_time: Optional[float] = None
    patterns: list
    recommendations: list
    error: Optional[str] = None


# ==================== 依赖项 ====================

def get_chat_enhancement_service(db: Session = Depends(get_db)) -> ChatEnhancementService:
    """获取对话增强服务"""
    return ChatEnhancementService(db)


# ==================== 对话增强 ====================

@router.post("/chat", summary="增强对话")
async def enhanced_chat(
    request: EnhancedChatRequest,
    service: ChatEnhancementService = Depends(get_chat_enhancement_service)
):
    """
    增强的智能对话

    功能：
    - 整合技能推荐
    - 应用历史学习经验
    - 自动记录交互以供学习
    - 提供相关技能建议

    返回增强的对话响应，包含技能建议和学习应用状态
    """
    response = service.chat_with_learning(
        query=request.query,
        session_id=request.session_id,
        project_id=request.project_id,
        skill_config=request.skill_config,
        memory_config=request.memory_config,
        use_deep_thinking=request.use_deep_thinking,
        learn_from_interaction=request.learn_from_interaction
    )

    return response


@router.get("/insights/{session_id}", response_model=ConversationInsightsResponse, summary="获取对话洞察")
async def get_conversation_insights(
    session_id: str,
    project_id: int,
    service: ChatEnhancementService = Depends(get_chat_enhancement_service)
):
    """
    获取对话洞察分析

    基于历史交互数据分析：
    - 交互统计
    - 对话模式识别
    - 改进建议

    帮助理解对话质量和优化方向
    """
    insights = service.get_conversation_insights(
        session_id=session_id,
        project_id=project_id
    )

    return ConversationInsightsResponse(**insights)


@router.get("/health", summary="健康检查")
async def health_check():
    """对话增强服务健康检查"""
    return {
        "status": "healthy",
        "service": "chat_enhancement"
    }
