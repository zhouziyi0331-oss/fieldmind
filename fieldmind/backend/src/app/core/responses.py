"""
API响应优化和错误处理增强
统一响应格式，提升用户体验
"""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime


class APIResponse(BaseModel):
    """统一API响应格式"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: str = datetime.now().isoformat()


class PaginatedResponse(BaseModel):
    """分页响应格式"""
    success: bool = True
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    message: str = ""


def success_response(data: Any = None, message: str = "操作成功") -> Dict:
    """成功响应"""
    return APIResponse(
        success=True,
        data=data,
        message=message
    ).dict()


def error_response(
    message: str,
    error_code: str = None,
    error_details: str = None
) -> Dict:
    """错误响应"""
    return APIResponse(
        success=False,
        message=message,
        error=error_details,
        error_code=error_code
    ).dict()


def paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = ""
) -> Dict:
    """分页响应"""
    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        message=message
    ).dict()


class ValidationError(BaseModel):
    """验证错误详情"""
    field: str
    message: str
    value: Any = None


def validation_error_response(errors: List[ValidationError]) -> Dict:
    """验证错误响应"""
    return APIResponse(
        success=False,
        message="数据验证失败",
        error_code="VALIDATION_ERROR",
        data={"errors": [e.dict() for e in errors]}
    ).dict()
