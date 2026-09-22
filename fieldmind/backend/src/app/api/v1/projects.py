"""项目相关的API端点"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.cache import cache
from app.schemas.response import success_response, error_response
from app.models.user import User
from app.models.project import (
    Project, ProjectDocument, ProjectContext,
    ProjectChatSession, ProjectMemory
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectDocumentResponse, ProjectContextCreate, ProjectContextResponse,
    ProjectChatSessionCreate, ProjectChatSessionResponse,
    ProjectDashboardResponse, ProjectMemoryResponse
)
from app.middleware.auth import get_current_user

router = APIRouter()


# ===== 项目CRUD =====

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新项目"""
    db_project = Project(
        name=project.name,
        description=project.description,
        settings=project.settings or {},
        owner_id=current_user.id,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow()
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/")
@router.get("")  # 同时注册不带斜杠的路径
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: Session = Depends(get_db)
):
    """获取项目列表（如果没有项目则自动创建默认项目）"""
    query = db.query(Project)
    if not include_archived:
        query = query.filter(Project.is_archived == False)

    projects = query.order_by(desc(Project.last_activity_at)).offset(skip).limit(limit).all()

    # 🔥 永久修复：如果没有任何项目，自动创建默认项目
    if not projects and skip == 0:
        default_project = Project(
            name="我的第一个项目",
            description="欢迎使用 FieldMind！这是系统自动创建的默认项目，您可以在此管理文档、构建知识图谱。",
            settings={},
            owner_id=1,  # 默认用户ID
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow()
        )
        db.add(default_project)
        db.commit()
        db.refresh(default_project)
        projects = [default_project]
        print(f"✅ 自动创建默认项目: ID={default_project.id}, Name={default_project.name}")

    total = query.count()
    return success_response(
        data={
            "data": [
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "documents": project.document_count or 0,
                    "contexts": project.context_count or 0,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                }
                for project in projects
            ],
            "total": total,
            "page": (skip // limit) + 1 if limit else 1,
            "page_size": limit,
            "has_next": (skip + len(projects)) < total,
            "has_prev": skip > 0,
        }
    )


@router.get("/{project_id}/", response_model=ProjectResponse)
@cache(ttl=180, key_prefix="project")
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目详情（缓存3分钟）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.settings is not None:
        project.settings = project_update.settings

    project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """删除项目（软删除）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.is_archived = True
    project.updated_at = datetime.utcnow()
    db.commit()
    return None


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """归档项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.is_archived = True
    project.status = "archived"
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """恢复归档项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.is_archived = False
    project.status = "active"
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project


# ===== 项目文档 =====

@router.get("/{project_id}/documents", response_model=List[ProjectDocumentResponse])
async def list_project_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目文档列表"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    if status_filter:
        query = query.filter(ProjectDocument.status == status_filter)

    documents = query.order_by(desc(ProjectDocument.created_at)).offset(skip).limit(limit).all()
    return documents


@router.get("/{project_id}/documents/{document_id}", response_model=ProjectDocumentResponse)
async def get_project_document(
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取项目文档详情"""
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    return document


# ===== 项目知识脉络 =====

@router.post("/{project_id}/contexts", response_model=ProjectContextResponse, status_code=status.HTTP_201_CREATED)
async def create_project_context(
    project_id: int,
    context: ProjectContextCreate,
    db: Session = Depends(get_db)
):
    """创建知识脉络"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 如果有父节点，验证父节点存在且属于同一项目
    if context.parent_id:
        parent = db.query(ProjectContext).filter(
            ProjectContext.id == context.parent_id,
            ProjectContext.project_id == project_id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父节点不存在")

    db_context = ProjectContext(
        project_id=project_id,
        name=context.name,
        description=context.description,
        level=context.level,
        parent_id=context.parent_id,
        keywords=context.keywords or [],
        document_ids=context.document_ids or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(db_context)
    project.context_count = db.query(func.count(ProjectContext.id)).filter(
        ProjectContext.project_id == project_id
    ).scalar() + 1
    project.updated_at = datetime.utcnow()
    project.last_activity_at = datetime.utcnow()

    db.commit()
    db.refresh(db_context)
    return db_context


@router.get("/{project_id}/contexts", response_model=List[ProjectContextResponse])
async def list_project_contexts(
    project_id: int,
    level: Optional[int] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取项目知识脉络列表"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ProjectContext).filter(ProjectContext.project_id == project_id)

    if level is not None:
        query = query.filter(ProjectContext.level == level)

    if parent_id is not None:
        query = query.filter(ProjectContext.parent_id == parent_id)

    contexts = query.options(joinedload(ProjectContext.children)).all()
    return contexts


@router.get("/{project_id}/contexts/{context_id}", response_model=ProjectContextResponse)
async def get_project_context(
    project_id: int,
    context_id: int,
    db: Session = Depends(get_db)
):
    """获取知识脉络详情"""
    context = db.query(ProjectContext).filter(
        ProjectContext.id == context_id,
        ProjectContext.project_id == project_id
    ).options(joinedload(ProjectContext.children)).first()

    if not context:
        raise HTTPException(status_code=404, detail="知识脉络不存在")

    return context


# ===== 项目对话会话 =====

@router.post("/{project_id}/chat-sessions", response_model=ProjectChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    project_id: int,
    session: ProjectChatSessionCreate,
    db: Session = Depends(get_db)
):
    """创建对话会话"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db_session = ProjectChatSession(
        project_id=project_id,
        name=session.name,
        document_ids=session.document_ids or [],
        config=session.config or {
            "use_long_memory": True,
            "use_deep_thinking": False,
            "memory_search_depth": 10,
            "skill_name": None
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(db_session)
    project.chat_session_count = db.query(func.count(ProjectChatSession.id)).filter(
        ProjectChatSession.project_id == project_id
    ).scalar() + 1
    project.updated_at = datetime.utcnow()
    project.last_activity_at = datetime.utcnow()

    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/{project_id}/chat-sessions", response_model=List[ProjectChatSessionResponse])
async def list_chat_sessions(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取项目对话会话列表"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    sessions = db.query(ProjectChatSession).filter(
        ProjectChatSession.project_id == project_id
    ).order_by(desc(ProjectChatSession.updated_at)).offset(skip).limit(limit).all()

    return sessions


@router.get("/{project_id}/chat-sessions/{session_id}", response_model=ProjectChatSessionResponse)
async def get_chat_session(
    project_id: int,
    session_id: int,
    include_messages: bool = True,
    db: Session = Depends(get_db)
):
    """获取对话会话详情"""
    query = db.query(ProjectChatSession).filter(
        ProjectChatSession.id == session_id,
        ProjectChatSession.project_id == project_id
    )

    if include_messages:
        query = query.options(joinedload(ProjectChatSession.messages))

    session = query.first()

    if not session:
        raise HTTPException(status_code=404, detail="对话会话不存在")

    return session


# ===== 项目数据看板 =====

@router.get("/{project_id}/dashboard", response_model=ProjectDashboardResponse)
@cache(ttl=300, key_prefix="project_dashboard")
async def get_project_dashboard(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目数据看板（缓存5分钟）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取最近的文档
    recent_documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(desc(ProjectDocument.created_at)).limit(5).all()

    # 获取最近的对话
    recent_chats = db.query(ProjectChatSession).filter(
        ProjectChatSession.project_id == project_id
    ).order_by(desc(ProjectChatSession.updated_at)).limit(5).all()

    # 统计关键词（从文档中提取）
    keyword_count = 0
    top_keywords = []

    # 统计实体（从文档中提取）
    entity_count = 0
    top_entities = []

    # 统计记忆数量
    memory_count = db.query(func.count(ProjectMemory.id)).filter(
        ProjectMemory.project_id == project_id
    ).scalar()

    dashboard = ProjectDashboardResponse(
        project_id=project.id,
        project_name=project.name,
        document_count=project.document_count,
        context_count=project.context_count,
        chat_count=project.chat_session_count,
        keyword_count=keyword_count,
        entity_count=entity_count,
        memory_count=memory_count,
        recent_documents=recent_documents,
        recent_chats=recent_chats,
        top_keywords=top_keywords,
        top_entities=top_entities,
        created_at=project.created_at,
        last_activity_at=project.last_activity_at
    )

    return dashboard


# ===== 项目记忆 =====

@router.get("/{project_id}/memories", response_model=List[ProjectMemoryResponse])
async def list_project_memories(
    project_id: int,
    memory_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取项目记忆列表"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ProjectMemory).filter(ProjectMemory.project_id == project_id)

    if memory_type:
        query = query.filter(ProjectMemory.memory_type == memory_type)

    memories = query.order_by(
        desc(ProjectMemory.relevance_score),
        desc(ProjectMemory.created_at)
    ).offset(skip).limit(limit).all()

    return memories


# ===== 项目会话列表 =====

@router.get("/{project_id}/sessions/")
async def list_project_sessions(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取项目的聊天会话列表"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 查询会话
    sessions = db.query(ProjectChatSession).filter(
        ProjectChatSession.project_id == project_id
    ).order_by(
        desc(ProjectChatSession.updated_at)
    ).offset(skip).limit(limit).all()

    return success_response(
        data={
            "sessions": [
                {
                    "id": session.id,
                    "session_id": str(session.id),
                    "name": session.name or f"会话 {session.id}",
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                    "message_count": session.message_count or 0
                }
                for session in sessions
            ],
            "total": db.query(func.count(ProjectChatSession.id)).filter(
                ProjectChatSession.project_id == project_id
            ).scalar() or 0,
            "skip": skip,
            "limit": limit
        }
    )
