"""
自定义异常类
用于业务逻辑中的错误处理
"""

from typing import Optional, Dict, Any
from app.core.errors import ErrorCode, get_error_status_code, get_error_message


class FieldMindException(Exception):
    """
    FieldMind 基础异常类

    所有业务异常都应该继承这个类
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        lang: str = "en",
        cause: Optional[BaseException] = None,
        operation: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code, lang)
        self.field = field
        self.details = details or {}
        self.cause = cause
        self.operation = operation
        if operation:
            self.details.setdefault("operation", operation)
        self.status_code = get_error_status_code(error_code)
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.error_code.value,
            "message": self.message,
            "field": self.field,
            "details": self.details
        }


# ============================================
# 具体异常类
# ============================================

class ValidationException(FieldMindException):
    """验证异常"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            field=field,
            details=details
        )


class NotFoundException(FieldMindException):
    """资源不存在异常"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message or f"{resource_type} not found",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class DocumentNotFoundException(FieldMindException):
    """文档不存在异常"""

    def __init__(self, document_id: str, message: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            message=message or f"Document {document_id} not found",
            details={"document_id": document_id}
        )


class ProjectNotFoundException(FieldMindException):
    """项目不存在异常"""

    def __init__(self, project_id: int, message: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.PROJECT_NOT_FOUND,
            message=message or f"Project {project_id} not found",
            details={"project_id": project_id}
        )


class AlreadyExistsException(FieldMindException):
    """资源已存在异常"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.ALREADY_EXISTS,
            message=message or f"{resource_type} already exists",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class PermissionDeniedException(FieldMindException):
    """权限不足异常"""

    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message or "Permission denied",
            details=details
        )


class AuthenticationRequiredException(FieldMindException):
    """需要身份验证异常"""

    def __init__(self, message: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=message or "Authentication required"
        )


class StorageException(FieldMindException):
    """存储异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.STORAGE_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details
        )


class DocumentProcessingException(FieldMindException):
    """文档处理异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.DOCUMENT_PROCESSING_FAILED,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details
        )


class VectorStoreException(FieldMindException):
    """向量存储异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.VECTOR_STORE_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details
        )


class DatabaseException(FieldMindException):
    """数据库异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details
        )


class AIServiceException(FieldMindException):
    """AI服务异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.AI_SERVICE_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details
        )


class RateLimitException(FieldMindException):
    """频率限制异常"""

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message or "Rate limit exceeded",
            details=details
        )


class ServiceUnavailableException(FieldMindException):
    """服务不可用异常"""

    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message or "Service temporarily unavailable",
            details=details
        )


class TimeoutException(FieldMindException):
    """处理超时异常。"""

    def __init__(
        self,
        operation: str = "operation",
        timeout_seconds: Optional[float] = None,
        message: Optional[str] = None,
    ):
        details = {"operation": operation}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            error_code=ErrorCode.PROCESSING_TIMEOUT,
            message=message or f"{operation} 执行超时",
            details=details,
            operation=operation,
        )


class GraphException(FieldMindException):
    """知识图谱处理异常。"""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(
            error_code=ErrorCode.PROCESSING_ERROR,
            message=message or "知识图谱处理失败",
            details=details,
            cause=cause,
        )


class FileException(FieldMindException):
    """文件处理异常。"""

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(
            error_code=ErrorCode.DOCUMENT_PROCESSING_FAILED,
            message=message or "文件处理失败",
            details=details,
            cause=cause,
        )


class ResourceNotFoundException(NotFoundException):
    """兼容旧接口的资源不存在异常。"""

    def __init__(self, resource_type: str, resource_id: str, message: Optional[str] = None):
        super().__init__(resource_type, resource_id, message=message)
