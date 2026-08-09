"""
记忆管理API - 链路十三：Agent记忆绑定
提供记忆的创建、查询、升级、注入等功能
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.project import ProjectMemory
from app.services.memory_injector import get_memory_injector

router = APIRouter(tags=["memory"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class MemoryCreateRequest(BaseModel):
    """创建记忆请求"""
    project_id: int
    memory_type: str  # short_term, mid_term, long_term
    content: str
    summary: Optional[str] = None
    source_type: Optional[str] = None  # chat, document, manual
    source_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    importance_score: Optional[float] = 0.5


class MemoryResponse(BaseModel):
    """记忆响应"""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    memory_type: str
    content: str
    summary: Optional[str]
    source_type: Optional[str]
    relevance_score: int
    access_count: int
    created_at: str


class SystemPromptRequest(BaseModel):
    """系统提示词构建请求"""
    project_id: int
    base_prompt: str
    user_query: Optional[str] = None
    include_short_term: bool = True
    include_mid_term: bool = True
    include_long_term: bool = True
    max_memories: int = 10


class MemoryPromoteRequest(BaseModel):
    """记忆升级请求"""
    memory_id: int
    target_type: str  # mid_term, long_term


# ==================== API接口 ====================

@router.post("/create", response_model=MemoryResponse)
async def create_memory(
    request: MemoryCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建新记忆

    支持三种记忆类型：
    - short_term: 短期记忆（最近对话、临时上下文）
    - mid_term: 中期记忆（重要概念、关键信息）
    - long_term: 长期记忆（核心知识、持久化信息）
    """
    try:
        extra_data = {}
        if request.keywords:
            extra_data["keywords"] = request.keywords
        if request.importance_score:
            extra_data["importance_score"] = request.importance_score

        memory = ProjectMemory(
            project_id=request.project_id,
            memory_type=request.memory_type,
            content=request.content,
            summary=request.summary or request.content[:200],
            source_type=request.source_type,
            source_id=request.source_id,
            relevance_score=int(request.importance_score * 100),
            extra_data=extra_data
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        logger.info(f"✅ 创建记忆: {memory.id} ({memory.memory_type})")

        return MemoryResponse(
            id=memory.id,
            project_id=memory.project_id,
            memory_type=memory.memory_type,
            content=memory.content,
            summary=memory.summary,
            source_type=memory.source_type,
            relevance_score=memory.relevance_score,
            access_count=memory.access_count,
            created_at=memory.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"创建记忆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/project/{project_id}", response_model=List[MemoryResponse])
async def get_project_memories(
    project_id: int,
    memory_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取项目的记忆列表

    - memory_type: 过滤记忆类型
    - limit: 返回数量
    """
    query = db.query(ProjectMemory).filter(
        ProjectMemory.project_id == project_id
    )

    if memory_type:
        query = query.filter(ProjectMemory.memory_type == memory_type)

    memories = query.order_by(
        ProjectMemory.relevance_score.desc(),
        ProjectMemory.created_at.desc()
    ).limit(limit).all()

    return [
        MemoryResponse(
            id=mem.id,
            project_id=mem.project_id,
            memory_type=mem.memory_type,
            content=mem.content,
            summary=mem.summary,
            source_type=mem.source_type,
            relevance_score=mem.relevance_score,
            access_count=mem.access_count,
            created_at=mem.created_at.isoformat()
        )
        for mem in memories
    ]


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory_detail(
    memory_id: int,
    db: Session = Depends(get_db)
):
    """获取记忆详情"""
    memory = db.query(ProjectMemory).filter(ProjectMemory.id == memory_id).first()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    # 更新访问记录
    memory.access_count += 1
    from datetime import datetime
    memory.last_accessed_at = datetime.utcnow()
    db.commit()

    return MemoryResponse(
        id=memory.id,
        project_id=memory.project_id,
        memory_type=memory.memory_type,
        content=memory.content,
        summary=memory.summary,
        source_type=memory.source_type,
        relevance_score=memory.relevance_score,
        access_count=memory.access_count,
        created_at=memory.created_at.isoformat()
    )


@router.post("/build-prompt")
async def build_system_prompt(
    request: SystemPromptRequest,
    db: Session = Depends(get_db)
):
    """
    构建包含记忆的系统提示词（链路十三核心功能）

    将项目的长期记忆、中期概念、短期上下文注入到系统提示词中，
    使LLM能够记住用户偏好和历史对话。

    返回：
    - enhanced_prompt: 增强后的系统提示词
    - memories_used: 使用的记忆数量
    - memory_types: 包含的记忆类型
    """
    try:
        injector = get_memory_injector(db, request.project_id)

        enhanced_prompt = injector.build_system_prompt(
            base_prompt=request.base_prompt,
            user_query=request.user_query,
            include_short_term=request.include_short_term,
            include_mid_term=request.include_mid_term,
            include_long_term=request.include_long_term,
            max_memories=request.max_memories
        )

        # 统计使用的记忆
        memory_types = []
        if request.include_short_term:
            memory_types.append("short_term")
        if request.include_mid_term:
            memory_types.append("mid_term")
        if request.include_long_term:
            memory_types.append("long_term")

        memories_count = db.query(ProjectMemory).filter(
            ProjectMemory.project_id == request.project_id,
            ProjectMemory.memory_type.in_(memory_types)
        ).count()

        return {
            "enhanced_prompt": enhanced_prompt,
            "memories_used": min(memories_count, request.max_memories),
            "memory_types": memory_types,
            "original_length": len(request.base_prompt),
            "enhanced_length": len(enhanced_prompt)
        }

    except Exception as e:
        logger.error(f"构建系统提示词失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.post("/promote")
async def promote_memory(
    request: MemoryPromoteRequest,
    db: Session = Depends(get_db)
):
    """
    升级记忆层级

    short_term → mid_term → long_term

    使用场景：
    - 用户标记重要信息
    - 高频访问的记忆自动升级
    """
    try:
        injector = get_memory_injector(db, project_id=None)  # project_id从memory获取

        memory = db.query(ProjectMemory).filter(
            ProjectMemory.id == request.memory_id
        ).first()

        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")

        injector.project_id = memory.project_id
        updated_memory = injector.promote_memory(request.memory_id, request.target_type)

        return {
            "message": f"记忆升级成功: {updated_memory.memory_type}",
            "memory_id": updated_memory.id,
            "old_type": memory.memory_type,
            "new_type": updated_memory.memory_type,
            "relevance_score": updated_memory.relevance_score
        }

    except Exception as e:
        logger.error(f"升级记忆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


@router.post("/auto-promote/{project_id}")
async def auto_promote_memories(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    自动升级高价值记忆

    规则：
    - 访问次数 > 10 且是 short_term → mid_term
    - 访问次数 > 30 且是 mid_term → long_term
    - 相关性评分 > 80 → 升级一级
    """
    try:
        injector = get_memory_injector(db, project_id)
        injector.auto_promote_memories()

        return {
            "message": "自动升级完成",
            "project_id": project_id
        }

    except Exception as e:
        logger.error(f"自动升级失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"自动升级失败: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):
    """删除记忆"""
    memory = db.query(ProjectMemory).filter(ProjectMemory.id == memory_id).first()

    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")

    db.delete(memory)
    db.commit()

    return {"message": f"记忆 {memory_id} 已删除"}


@router.post("/cleanup/{project_id}")
async def cleanup_old_memories(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    清理过期的短期记忆

    - days: 保留天数（默认30天）
    """
    try:
        injector = get_memory_injector(db, project_id)
        deleted_count = injector.cleanup_old_memories(days)

        return {
            "message": f"清理完成，删除了 {deleted_count} 条过期记忆",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"清理记忆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/stats/{project_id}")
async def get_memory_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目记忆统计信息

    返回各类型记忆的数量、总访问次数等
    """
    from sqlalchemy import func

    # 按类型统计
    type_stats = db.query(
        ProjectMemory.memory_type,
        func.count(ProjectMemory.id).label("count"),
        func.sum(ProjectMemory.access_count).label("total_access")
    ).filter(
        ProjectMemory.project_id == project_id
    ).group_by(ProjectMemory.memory_type).all()

    stats = {
        "project_id": project_id,
        "total_memories": 0,
        "by_type": {},
        "total_access_count": 0
    }

    for type_name, count, total_access in type_stats:
        stats["by_type"][type_name] = {
            "count": count,
            "total_access": total_access or 0
        }
        stats["total_memories"] += count
        stats["total_access_count"] += (total_access or 0)

    # 最常访问的记忆
    top_memories = db.query(ProjectMemory).filter(
        ProjectMemory.project_id == project_id
    ).order_by(ProjectMemory.access_count.desc()).limit(5).all()

    stats["top_memories"] = [
        {
            "id": mem.id,
            "summary": mem.summary[:100] if mem.summary else mem.content[:100],
            "access_count": mem.access_count,
            "memory_type": mem.memory_type
        }
        for mem in top_memories
    ]

    return stats


# ==================== 快捷接口 ====================

@router.post("/quick/from-chat")
async def quick_create_from_chat(
    project_id: int,
    session_id: int,
    message_id: int,
    memory_type: str = "short_term",
    importance_score: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    快捷接口：从对话创建记忆

    自动从对话消息提取内容创建记忆
    """
    try:
        injector = get_memory_injector(db, project_id)
        memory = injector.create_memory_from_chat(
            session_id,
            message_id,
            memory_type,
            importance_score
        )

        return {
            "message": "从对话创建记忆成功",
            "memory_id": memory.id,
            "memory_type": memory.memory_type
        }

    except Exception as e:
        logger.error(f"从对话创建记忆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick/from-document")
async def quick_create_from_document(
    project_id: int,
    document_id: int,
    content: str,
    summary: Optional[str] = None,
    memory_type: str = "mid_term",
    db: Session = Depends(get_db)
):
    """
    快捷接口：从文档创建记忆

    自动从文档内容创建记忆
    """
    try:
        injector = get_memory_injector(db, project_id)
        memory = injector.create_memory_from_document(
            document_id,
            content,
            summary,
            memory_type
        )

        return {
            "message": "从文档创建记忆成功",
            "memory_id": memory.id,
            "memory_type": memory.memory_type
        }

    except Exception as e:
        logger.error(f"从文档创建记忆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
