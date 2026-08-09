"""文档Schema定义"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    message: str


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    project_id: int
    filename: str
    original_filename: str
    file_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    text_content: Optional[str] = None
    summary: Optional[str] = None
    vector_collection: Optional[str] = None
    chunk_count: int = 0
    entities: Optional[List[Dict[str, Any]]] = []
    keywords: Optional[List[str]] = []
    extra_data: Optional[Dict[str, Any]] = {}
    status: str
    processing_progress: int = 0
    error_message: Optional[str] = None
    word_count: int = 0
    created_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]
