"""
统一异常处理框架
Unified Exception Handling Framework

提供完整的异常类层次结构、错误装饰器和标准化的错误响应格式
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import status


class ErrorCode(Enum):
    """错误代码枚举 - 与配置系统集成"""
    # 通用错误 (1000-1999)
    SUCCESS = (1000, "操作成功", status.HTTP_200_OK)
    UNKNOWN_ERROR = (1001, "未知错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VALIDATION_ERROR = (1002, "数据验证失败", 422)
    PARAMETER_ERROR = (1003, "参数错误", status.HTTP_400_BAD_REQUEST)
    RESOURCE_NOT_FOUND = (1004, "资源不存在", status.HTTP_404_NOT_FOUND)
    PERMISSION_DENIED = (1005, "权限不足", status.HTTP_403_FORBIDDEN)
    AUTHENTICATION_FAILED = (1006, "认证失败", status.HTTP_401_UNAUTHORIZED)
    RATE_LIMIT_EXCEEDED = (1007, "请求频率超限", status.HTTP_429_TOO_MANY_REQUESTS)
    SERVICE_UNAVAILABLE = (1008, "服务暂时不可用", status.HTTP_503_SERVICE_UNAVAILABLE)
    TIMEOUT_ERROR = (1009, "操作超时", status.HTTP_408_REQUEST_TIMEOUT)

    # 数据库错误 (2000-2999)
    DATABASE_ERROR = (2001, "数据库错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    DATABASE_CONNECTION_ERROR = (2002, "数据库连接失败", status.HTTP_503_SERVICE_UNAVAILABLE)
    DATABASE_QUERY_ERROR = (2003, "数据库查询失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    DATABASE_COMMIT_ERROR = (2004, "数据库提交失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    DUPLICATE_RECORD = (2005, "记录已存在", status.HTTP_409_CONFLICT)
    RECORD_NOT_FOUND = (2006, "记录不存在", status.HTTP_404_NOT_FOUND)

    # 文件处理错误 (3000-3999)
    FILE_ERROR = (3001, "文件处理错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    FILE_NOT_FOUND = (3002, "文件不存在", status.HTTP_404_NOT_FOUND)
    FILE_TOO_LARGE = (3003, "文件过大", 413)
    FILE_TYPE_NOT_SUPPORTED = (3004, "不支持的文件类型", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    FILE_UPLOAD_ERROR = (3005, "文件上传失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    FILE_DOWNLOAD_ERROR = (3006, "文件下载失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    FILE_PARSING_ERROR = (3007, "文件解析失败", 422)

    # AI服务错误 (4000-4999)
    AI_SERVICE_ERROR = (4001, "AI服务错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    AI_MODEL_NOT_AVAILABLE = (4002, "AI模型不可用", status.HTTP_503_SERVICE_UNAVAILABLE)
    AI_REQUEST_FAILED = (4003, "AI请求失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    AI_QUOTA_EXCEEDED = (4004, "AI配额已用尽", status.HTTP_429_TOO_MANY_REQUESTS)
    AI_RESPONSE_INVALID = (4005, "AI响应无效", status.HTTP_502_BAD_GATEWAY)

    # 向量存储错误 (5000-5999)
    VECTOR_STORE_ERROR = (5001, "向量存储错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VECTOR_STORE_CONNECTION_ERROR = (5002, "向量存储连接失败", status.HTTP_503_SERVICE_UNAVAILABLE)
    VECTOR_SEARCH_ERROR = (5003, "向量搜索失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VECTOR_EMBEDDING_ERROR = (5004, "向量嵌入生成失败", status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 知识图谱错误 (6000-6999)
    GRAPH_ERROR = (6001, "知识图谱错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    GRAPH_CONNECTION_ERROR = (6002, "知识图谱连接失败", status.HTTP_503_SERVICE_UNAVAILABLE)
    GRAPH_QUERY_ERROR = (6003, "图谱查询失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    GRAPH_NODE_NOT_FOUND = (6004, "节点不存在", status.HTTP_404_NOT_FOUND)

    # 工作流错误 (7000-7999)
    WORKFLOW_ERROR = (7001, "工作流错误", status.HTTP_500_INTERNAL_SERVER_ERROR)
    WORKFLOW_EXECUTION_ERROR = (7002, "工作流执行失败", status.HTTP_500_INTERNAL_SERVER_ERROR)
    WORKFLOW_VALIDATION_ERROR = (7003, "工作流验证失败", 422)
    WORKFLOW_NOT_FOUND = (7004, "工作流不存在", status.HTTP_404_NOT_FOUND)

    # 业务逻辑错误 (8000-8999)
    BUSINESS_LOGIC_ERROR = (8001, "业务逻辑错误", status.HTTP_400_BAD_REQUEST)
    INVALID_OPERATION = (8002, "无效操作", status.HTTP_400_BAD_REQUEST)
    OPERATION_NOT_ALLOWED = (8003, "操作不允许", status.HTTP_403_FORBIDDEN)
    RESOURCE_LOCKED = (8004, "资源已锁定", status.HTTP_423_LOCKED)
    RESOURCE_CONFLICT = (8005, "资源冲突", status.HTTP_409_CONFLICT)

    def __init__(self, code: int, message: str, http_status: int):
        self.code = code
        self.message = message
        self.http_status = http_status


class FieldMindException(Exception):
    """FieldMind异常基类"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "error_code": self.error_code.code,
            "message": self.message,
            "http_status": self.error_code.http_status
        }
        if self.details:
            result["details"] = self.details
        if self.cause:
            result["cause"] = str(self.cause)
        return result

    def __str__(self) -> str:
        return f"[{self.error_code.code}] {self.message}"


class ValidationException(FieldMindException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )


class ResourceNotFoundException(FieldMindException):
    """资源不存在异常"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        message: Optional[str] = None
    ):
        message = message or f"{resource_type} 不存在: {resource_id}"
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details={"resource_type": resource_type, "resource_id": str(resource_id)}
        )


class PermissionDeniedException(FieldMindException):
    """权限不足异常"""

    def __init__(
        self,
        action: str,
        resource: Optional[str] = None,
        message: Optional[str] = None
    ):
        message = message or f"无权限执行操作: {action}"
        details = {"action": action}
        if resource:
            details["resource"] = resource
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message,
            details=details
        )


class AuthenticationException(FieldMindException):
    """认证失败异常"""

    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            message=message,
            details=details
        )


class DatabaseException(FieldMindException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库错误",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            details=details,
            cause=cause
        )


class FileException(FieldMindException):
    """文件处理异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.FILE_ERROR,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if filename:
            details["filename"] = filename
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details,
            cause=cause
        )


class AIServiceException(FieldMindException):
    """AI服务异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.AI_SERVICE_ERROR,
        message: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if model:
            details["model"] = model
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details,
            cause=cause
        )


class VectorStoreException(FieldMindException):
    """向量存储异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.VECTOR_STORE_ERROR,
        message: Optional[str] = None,
        collection: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if collection:
            details["collection"] = collection
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details,
            cause=cause
        )


class GraphException(FieldMindException):
    """知识图谱异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.GRAPH_ERROR,
        message: Optional[str] = None,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if query:
            details["query"] = query
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details,
            cause=cause
        )


class WorkflowException(FieldMindException):
    """工作流异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.WORKFLOW_ERROR,
        message: Optional[str] = None,
        workflow_id: Optional[str] = None,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        details = details or {}
        if workflow_id:
            details["workflow_id"] = workflow_id
        if stage:
            details["stage"] = stage
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details,
            cause=cause
        )


class BusinessLogicException(FieldMindException):
    """业务逻辑异常"""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.BUSINESS_LOGIC_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message or error_code.message,
            details=details
        )


class RateLimitException(FieldMindException):
    """速率限制异常"""

    def __init__(
        self,
        message: str = "请求频率超限",
        limit: Optional[int] = None,
        window: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if limit:
            details["limit"] = limit
        if window:
            details["window_seconds"] = window
        super().__init__(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details
        )


class TimeoutException(FieldMindException):
    """超时异常"""

    def __init__(
        self,
        operation: str,
        timeout_seconds: float,
        message: Optional[str] = None
    ):
        message = message or f"操作超时: {operation} (>{timeout_seconds}s)"
        super().__init__(
            error_code=ErrorCode.TIMEOUT_ERROR,
            message=message,
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )
