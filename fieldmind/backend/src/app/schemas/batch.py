"""批量操作Schema定义"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    batch_id: str
    total_files: int
    successful_uploads: int
    failed_uploads: int
    document_ids: List[int]
    failures: List[Dict[str, str]] = []
    message: str


class BatchStatusResponse(BaseModel):
    """批次状态响应"""
    batch_id: str
    project_id: int
    operation_type: str
    total_items: int
    completed_items: int
    failed_items: int
    status: str
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    document_ids: List[int] = Field(..., min_length=1, max_length=100)
    project_id: Optional[int] = None


class BatchDeleteRequest(BatchOperationRequest):
    """批量删除请求"""
    pass


class BatchReprocessRequest(BatchOperationRequest):
    """批量重新处理请求"""
    force: bool = False  # 是否强制重新处理已完成的文档


class BatchQualityCheckRequest(BatchOperationRequest):
    """批量质量检查请求"""
    pass


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    batch_id: str
    operation_type: str
    total_items: int
    message: str
    status: str = "pending"


class BatchListResponse(BaseModel):
    """批次列表响应"""
    total: int
    batches: List[BatchStatusResponse]
