"""项目相关的Pydantic模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ===== 项目模型 =====

class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectCreate(ProjectBase):
    """创建项目请求"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    """项目响应"""
    model_config = {"from_attributes": True}

    id: int
    document_count: int = 0
    context_count: int = 0
    chat_session_count: int = 0
    entity_count: int = 0
    keyword_count: int = 0
    is_archived: bool = False
    status: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime


# ===== 项目文档模型 =====

class ProjectDocumentResponse(BaseModel):
    """项目文档响应"""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    filename: str
    original_filename: str
    file_type: str
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    processing_progress: int = 0
    chunk_count: int = 0
    word_count: int = 0
    summary: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    keywords: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    assets: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime


# ===== 项目知识脉络模型 =====

class ProjectContextCreate(BaseModel):
    """创建知识脉络请求"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    level: int = Field(1, ge=1, le=3)
    parent_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    document_ids: Optional[List[int]] = None


class ProjectContextResponse(BaseModel):
    """知识脉络响应"""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    level: int
    parent_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    document_ids: Optional[List[int]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    children: Optional[List["ProjectContextResponse"]] = None
    created_at: datetime
    updated_at: datetime


# ===== 项目对话模型 =====

class ProjectChatSessionCreate(BaseModel):
    """创建对话会话请求"""
    name: str = Field(..., min_length=1, max_length=200)
    document_ids: Optional[List[int]] = None
    config: Optional[Dict[str, Any]] = None


class ProjectChatMessageCreate(BaseModel):
    """发送消息请求"""
    message: str = Field(..., min_length=1)
    use_long_memory: bool = True
    use_deep_thinking: bool = False
    skill_name: Optional[str] = None
    framework: Optional[str] = None


class ProjectChatMessageResponse(BaseModel):
    """聊天消息响应"""
    model_config = {"from_attributes": True}

    id: int
    session_id: int
    role: str
    content: str
    thinking_process: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ProjectChatSessionResponse(BaseModel):
    """对话会话响应"""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    name: str
    document_ids: Optional[List[int]] = None
    config: Optional[Dict[str, Any]] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    messages: Optional[List[ProjectChatMessageResponse]] = None


# ===== 数据看板模型 =====

class ProjectDashboardResponse(BaseModel):
    """项目数据看板响应"""
    project_id: int
    project_name: str

    # 统计数据
    document_count: int
    context_count: int
    chat_count: int
    keyword_count: int
    entity_count: int
    memory_count: int

    # 详细数据
    recent_documents: Optional[List[ProjectDocumentResponse]] = None
    recent_chats: Optional[List[ProjectChatSessionResponse]] = None
    top_keywords: Optional[List[Dict[str, Any]]] = None
    top_entities: Optional[List[Dict[str, Any]]] = None

    # 时间数据
    created_at: datetime
    last_activity_at: datetime


# ===== 项目记忆模型 =====

class ProjectMemoryCreate(BaseModel):
    """创建记忆请求"""
    content: str
    memory_type: str = Field(..., pattern="^(short_term|mid_term|long_term)$")
    summary: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectMemoryResponse(BaseModel):
    """记忆响应"""
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    memory_type: str
    content: str
    summary: Optional[str] = None
    source_type: Optional[str] = None
    access_count: int = 0
    relevance_score: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_accessed_at: Optional[datetime] = None


class ProjectMemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., min_length=1)
    memory_types: Optional[List[str]] = None
    top_k: int = Field(10, ge=1, le=50)
    relevance_threshold: float = Field(0.7, ge=0.0, le=1.0)


class ProjectMemorySearchResponse(BaseModel):
    """记忆搜索响应"""
    memories: List[ProjectMemoryResponse]
    total_count: int
    query: str


# 更新前向引用
ProjectContextResponse.model_rebuild()
