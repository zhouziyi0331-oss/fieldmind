"""
统一响应格式
定义标准的 API 响应结构
"""

from typing import Generic, TypeVar, Optional, Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class ResponseMetadata(BaseModel):
    """响应元数据"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID，用于追踪")
    version: str = Field(default="1.0", description="API版本")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-20T10:30:00Z",
                "request_id": "req_abc123",
                "version": "1.0"
            }
        }


class PaginationInfo(BaseModel):
    """分页信息"""
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, le=100, description="每页数量")
    total: int = Field(ge=0, description="总记录数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total": 100,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False
            }
        }


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(description="错误代码")
    message: str = Field(description="错误消息")
    field: Optional[str] = Field(None, description="错误字段（用于验证错误）")
    details: Optional[Dict[str, Any]] = Field(None, description="额外错误详情")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid email format",
                "field": "email",
                "details": {"pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"}
            }
        }


class ApiResponse(BaseModel, Generic[T]):
    """
    标准API响应格式

    用于所有API端点的统一响应结构
    """
    success: bool = Field(description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional[ErrorDetail] = Field(None, description="错误信息（失败时）")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")

    class Config:
        json_schema_extra = {
            "example_success": {
                "success": True,
                "data": {"id": "doc_001", "name": "example.pdf"},
                "error": None,
                "metadata": {
                    "timestamp": "2024-01-20T10:30:00Z",
                    "request_id": "req_abc123",
                    "version": "1.0"
                }
            },
            "example_error": {
                "success": False,
                "data": None,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Document not found",
                    "field": None,
                    "details": {"document_id": "doc_001"}
                },
                "metadata": {
                    "timestamp": "2024-01-20T10:30:00Z",
                    "request_id": "req_abc123",
                    "version": "1.0"
                }
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应格式

    用于返回列表数据的API端点
    """
    success: bool = Field(description="请求是否成功")
    data: List[T] = Field(default_factory=list, description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")
    error: Optional[ErrorDetail] = Field(None, description="错误信息（失败时）")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"id": "doc_001", "name": "file1.pdf"},
                    {"id": "doc_002", "name": "file2.pdf"}
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                },
                "error": None,
                "metadata": {
                    "timestamp": "2024-01-20T10:30:00Z",
                    "request_id": "req_abc123",
                    "version": "1.0"
                }
            }
        }


# ============================================
# 便捷构造函数
# ============================================

def success_response(
    data: Any = None,
    request_id: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    构造成功响应

    Args:
        data: 响应数据
        request_id: 请求ID
        message: 可选消息

    Returns:
        Dict: 标准响应字典
    """
    response = {
        "success": True,
        "data": data,
        "error": None,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "version": "1.0"
        }
    }

    if message:
        response["message"] = message

    return response


def error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """
    构造错误响应

    Args:
        code: 错误代码
        message: 错误消息
        field: 错误字段
        details: 额外详情
        request_id: 请求ID
        status_code: HTTP状态码

    Returns:
        Dict: 标准响应字典
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "field": field,
            "details": details
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "version": "1.0"
        }
    }


def paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total: int,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    构造分页响应

    Args:
        data: 数据列表
        page: 当前页码
        page_size: 每页数量
        total: 总记录数
        request_id: 请求ID

    Returns:
        Dict: 标准分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "error": None,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "version": "1.0"
        }
    }
