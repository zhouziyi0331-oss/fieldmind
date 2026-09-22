"""
文档相关的 Schema 定义
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.models.document import DocumentType, DocumentStatus


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    project_id: int = Field(..., description="项目ID", ge=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "metadata": {
                    "source": "web_upload",
                    "category": "research"
                }
            }
        }


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    id: str = Field(..., description="文档ID")
    name: str = Field(..., description="文件名")
    type: DocumentType = Field(..., description="文档类型")
    size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="MIME类型")
    hash: str = Field(..., description="文件哈希")
    status: DocumentStatus = Field(..., description="处理状态")
    storage_path: str = Field(..., description="存储路径")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "doc_abc123xyz",
                "name": "example.pdf",
                "type": "document",
                "size": 1024000,
                "mime_type": "application/pdf",
                "hash": "a1b2c3d4...",
                "status": "uploaded",
                "storage_path": "documents/projects/1/document/2024/01/20/a1b2c3d4/example.pdf",
                "created_at": "2024-01-20T10:00:00Z"
            }
        }


class DocumentDetailResponse(BaseModel):
    """文档详情响应"""
    id: str
    project_id: int
    name: str
    type: DocumentType
    size: int
    mime_type: str
    hash: str
    status: DocumentStatus
    storage_path: str
    uploaded_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # 统计信息
    chunk_count: Optional[int] = Field(None, description="分块数量")
    entity_count: Optional[int] = Field(None, description="实体数量")
    tag_count: Optional[int] = Field(None, description="标签数量")

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """兼容旧文档接口，但字段统一映射到 project_documents。"""
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
    text_content: Optional[str] = None
    entities: Optional[Any] = None  # 允许任意类型（列表或字典）
    keywords: Optional[Any] = None
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DocumentListQuery(BaseModel):
    """文档列表查询"""
    project_id: Optional[int] = Field(None, description="项目ID")
    type: Optional[DocumentType] = Field(None, description="文档类型")
    status: Optional[DocumentStatus] = Field(None, description="处理状态")
    search: Optional[str] = Field(None, description="搜索关键词", max_length=100)
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "type": "document",
                "status": "processed",
                "search": "report",
                "page": 1,
                "page_size": 20
            }
        }


class DocumentUpdateRequest(BaseModel):
    """文档更新请求"""
    name: Optional[str] = Field(None, description="文件名", max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "renamed_document.pdf",
                "metadata": {
                    "category": "updated_category"
                }
            }
        }


class FileClassificationResult(BaseModel):
    """文件分类结果"""
    type: DocumentType = Field(..., description="文档类型")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    method: str = Field(..., description="分类方法")
    details: Dict[str, Any] = Field(..., description="详细信息")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "document",
                "confidence": 0.95,
                "method": "mime_type+extension",
                "details": {
                    "mime_type": "application/pdf",
                    "extension": ".pdf"
                }
            }
        }


class DocumentDownloadResponse(BaseModel):
    """文档下载响应"""
    url: str = Field(..., description="下载URL（预签名）")
    expires_in: int = Field(..., description="过期时间（秒）")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://storage.example.com/...",
                "expires_in": 3600,
                "filename": "example.pdf",
                "size": 1024000
            }
        }
