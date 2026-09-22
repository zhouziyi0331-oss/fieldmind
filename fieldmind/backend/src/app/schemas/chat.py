"""对话Schema定义"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatSessionCreate(BaseModel):
    project_id: int
    name: str
    document_ids: Optional[List[int]] = None
    config: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    name: str
    document_ids: Optional[List[int]]
    config: Optional[Dict[str, Any]]
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]


class ChatSessionListResponse(BaseModel):
    total: int
    sessions: List[ChatSessionResponse]


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    session_id: int
    role: str
    content: str
    thinking_process: Optional[str]
    sources: Optional[List[Dict[str, Any]]]
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
