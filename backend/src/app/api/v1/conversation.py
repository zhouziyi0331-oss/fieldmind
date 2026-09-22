"""
对话记忆API端点

提供对话历史管理、上下文检索和智能摘要接口
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.conversation_service import ConversationMemoryService


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ConversationMemoryCreate(BaseModel):
    """创建对话记忆请求"""
    project_id: int = Field(..., description="项目ID")
    conversation_turn: int = Field(..., description="对话轮次")
    user_message: str = Field(..., description="用户消息")
    ai_response: str = Field(..., description="AI响应")
    context_keywords: Optional[List[str]] = Field(None, description="上下文关键词")
    referenced_entities: Optional[List[str]] = Field(None, description="引用的实体")
    topic_tags: Optional[List[str]] = Field(None, description="主题标签")
    importance_score: float = Field(0.5, description="重要性分数（0-1）", ge=0, le=1)


class ConversationMemoryResponse(BaseModel):
    """对话记忆响应"""
    id: int
    user_id: int
    project_id: int
    conversation_turn: int
    user_message: str
    ai_response: str
    context_keywords: List[str]
    referenced_entities: List[str]
    topic_tags: List[str]
    importance_score: float
    created_at: str

    class Config:
        from_attributes = True


class ConversationSearchRequest(BaseModel):
    """对话搜索请求"""
    keywords: List[str] = Field(..., description="搜索关键词")
    project_id: Optional[int] = Field(None, description="项目ID")
    limit: int = Field(10, description="返回数量", ge=1, le=50)


class ConversationSummaryResponse(BaseModel):
    """对话摘要响应"""
    period_days: int
    total_turns: int
    avg_importance: float
    top_topics: List[tuple]
    top_entities: List[tuple]
    start_date: str
    end_date: str


class ImportanceUpdateRequest(BaseModel):
    """重要性更新请求"""
    importance_score: float = Field(..., description="新的重要性分数", ge=0, le=1)


# ==================== 依赖项 ====================

def get_conversation_service(db: Session = Depends(get_db)) -> ConversationMemoryService:
    """获取对话记忆服务"""
    return ConversationMemoryService(db)


# ==================== 对话记忆管理 ====================

@router.post("/conversations", response_model=ConversationMemoryResponse, summary="创建对话记忆")
async def create_conversation_memory(
    memory: ConversationMemoryCreate,
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    创建对话记忆记录

    - **project_id**: 项目ID
    - **conversation_turn**: 对话轮次
    - **user_message**: 用户消息内容
    - **ai_response**: AI响应内容
    - **context_keywords**: 上下文关键词列表
    - **referenced_entities**: 引用的实体列表
    - **topic_tags**: 主题标签列表
    - **importance_score**: 重要性分数（0-1）
    """
    result = service.create_memory(
        user_id=current_user.id,
        project_id=memory.project_id,
        conversation_turn=memory.conversation_turn,
        user_message=memory.user_message,
        ai_response=memory.ai_response,
        context_keywords=memory.context_keywords,
        referenced_entities=memory.referenced_entities,
        topic_tags=memory.topic_tags,
        importance_score=memory.importance_score
    )

    return ConversationMemoryResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        conversation_turn=result.conversation_turn,
        user_message=result.user_message,
        ai_response=result.ai_response,
        context_keywords=result.context_keywords,
        referenced_entities=result.referenced_entities,
        topic_tags=result.topic_tags,
        importance_score=result.importance_score,
        created_at=result.created_at.isoformat()
    )


@router.get("/conversations/recent", response_model=List[ConversationMemoryResponse], summary="获取最近对话")
async def get_recent_conversations(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    获取用户最近的对话记录

    按时间倒序返回对话历史
    """
    conversations = service.get_recent_conversations(
        user_id=current_user.id,
        project_id=project_id,
        limit=limit
    )

    return [
        ConversationMemoryResponse(
            id=conv.id,
            user_id=conv.user_id,
            project_id=conv.project_id,
            conversation_turn=conv.conversation_turn,
            user_message=conv.user_message,
            ai_response=conv.ai_response,
            context_keywords=conv.context_keywords,
            referenced_entities=conv.referenced_entities,
            topic_tags=conv.topic_tags,
            importance_score=conv.importance_score,
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@router.post("/conversations/search", response_model=List[ConversationMemoryResponse], summary="搜索对话")
async def search_conversations(
    search: ConversationSearchRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    通过关键词搜索对话

    - **keywords**: 搜索关键词列表
    - **project_id**: 可选，筛选特定项目
    - **limit**: 返回数量限制

    返回匹配度最高的对话记录
    """
    conversations = service.search_by_keywords(
        user_id=current_user.id,
        keywords=search.keywords,
        project_id=search.project_id,
        limit=search.limit
    )

    return [
        ConversationMemoryResponse(
            id=conv.id,
            user_id=conv.user_id,
            project_id=conv.project_id,
            conversation_turn=conv.conversation_turn,
            user_message=conv.user_message,
            ai_response=conv.ai_response,
            context_keywords=conv.context_keywords,
            referenced_entities=conv.referenced_entities,
            topic_tags=conv.topic_tags,
            importance_score=conv.importance_score,
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@router.get("/conversations/entity/{entity_name}", response_model=List[ConversationMemoryResponse], summary="获取实体相关对话")
async def get_entity_conversations(
    entity_name: str = Path(..., description="实体名称"),
    limit: int = Query(5, description="返回数量", ge=1, le=20),
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    获取与特定实体相关的对话上下文

    返回所有提到该实体的对话，按重要性排序
    """
    conversations = service.get_context_for_entity(
        user_id=current_user.id,
        entity_name=entity_name,
        limit=limit
    )

    return [
        ConversationMemoryResponse(
            id=conv.id,
            user_id=conv.user_id,
            project_id=conv.project_id,
            conversation_turn=conv.conversation_turn,
            user_message=conv.user_message,
            ai_response=conv.ai_response,
            context_keywords=conv.context_keywords,
            referenced_entities=conv.referenced_entities,
            topic_tags=conv.topic_tags,
            importance_score=conv.importance_score,
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@router.get("/conversations/summary/{project_id}", response_model=ConversationSummaryResponse, summary="获取对话摘要")
async def get_conversation_summary(
    project_id: int = Path(..., description="项目ID"),
    days: int = Query(7, description="统计天数", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    获取对话摘要统计

    包含：
    - 对话轮次统计
    - 平均重要性
    - 高频主题
    - 高频实体
    """
    summary = service.get_conversation_summary(
        user_id=current_user.id,
        project_id=project_id,
        days=days
    )

    return ConversationSummaryResponse(**summary)


@router.put("/conversations/{memory_id}/importance", response_model=ConversationMemoryResponse, summary="更新对话重要性")
async def update_conversation_importance(
    memory_id: int = Path(..., description="对话记忆ID"),
    update: ImportanceUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    更新对话的重要性分数

    - **importance_score**: 新的重要性分数（0-1）
    """
    result = service.update_importance_score(
        memory_id=memory_id,
        importance_score=update.importance_score
    )

    return ConversationMemoryResponse(
        id=result.id,
        user_id=result.user_id,
        project_id=result.project_id,
        conversation_turn=result.conversation_turn,
        user_message=result.user_message,
        ai_response=result.ai_response,
        context_keywords=result.context_keywords,
        referenced_entities=result.referenced_entities,
        topic_tags=result.topic_tags,
        importance_score=result.importance_score,
        created_at=result.created_at.isoformat()
    )


@router.delete("/conversations/cleanup", summary="清理旧对话")
async def cleanup_old_conversations(
    days: int = Query(90, description="保留天数", ge=30, le=365),
    keep_important: bool = Query(True, description="是否保留重要对话"),
    importance_threshold: float = Query(0.7, description="重要性阈值", ge=0, le=1),
    current_user: User = Depends(get_current_user),
    service: ConversationMemoryService = Depends(get_conversation_service)
):
    """
    清理旧的对话记录

    - **days**: 保留天数（删除更早的记录）
    - **keep_important**: 是否保留重要对话
    - **importance_threshold**: 重要性阈值（高于此值的对话被保留）

    返回删除的记录数
    """
    deleted_count = service.delete_old_conversations(
        user_id=current_user.id,
        days=days,
        keep_important=keep_important,
        importance_threshold=importance_threshold
    )

    return {
        "deleted_count": deleted_count,
        "retention_days": days,
        "kept_important": keep_important,
        "threshold": importance_threshold
    }
