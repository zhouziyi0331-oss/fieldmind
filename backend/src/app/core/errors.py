"""
错误码规范
定义所有API错误代码和对应的HTTP状态码
"""

from enum import Enum
from typing import Dict, Tuple


class ErrorCode(str, Enum):
    """
    错误代码枚举

    格式: CATEGORY_SPECIFIC_ERROR
    """

    # ============================================
    # 通用错误 (1xxx)
    # ============================================
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # ============================================
    # 资源错误 (2xxx)
    # ============================================
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    RESOURCE_DELETED = "RESOURCE_DELETED"

    # ============================================
    # 文档错误 (3xxx)
    # ============================================
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_UPLOAD_FAILED = "DOCUMENT_UPLOAD_FAILED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    DOCUMENT_TYPE_UNSUPPORTED = "DOCUMENT_TYPE_UNSUPPORTED"
    DOCUMENT_SIZE_EXCEEDED = "DOCUMENT_SIZE_EXCEEDED"
    DOCUMENT_CORRUPTED = "DOCUMENT_CORRUPTED"

    # ============================================
    # 项目错误 (4xxx)
    # ============================================
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_ALREADY_EXISTS = "PROJECT_ALREADY_EXISTS"
    PROJECT_ACCESS_DENIED = "PROJECT_ACCESS_DENIED"

    # ============================================
    # 存储错误 (5xxx)
    # ============================================
    STORAGE_ERROR = "STORAGE_ERROR"
    STORAGE_QUOTA_EXCEEDED = "STORAGE_QUOTA_EXCEEDED"
    STORAGE_UPLOAD_FAILED = "STORAGE_UPLOAD_FAILED"
    STORAGE_DOWNLOAD_FAILED = "STORAGE_DOWNLOAD_FAILED"
    STORAGE_DELETE_FAILED = "STORAGE_DELETE_FAILED"

    # ============================================
    # 数据库错误 (6xxx)
    # ============================================
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    DATABASE_QUERY_FAILED = "DATABASE_QUERY_FAILED"
    DATABASE_CONSTRAINT_VIOLATION = "DATABASE_CONSTRAINT_VIOLATION"

    # ============================================
    # 向量错误 (7xxx)
    # ============================================
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"
    VECTOR_EMBEDDING_FAILED = "VECTOR_EMBEDDING_FAILED"
    VECTOR_SEARCH_FAILED = "VECTOR_SEARCH_FAILED"
    VECTOR_NOT_FOUND = "VECTOR_NOT_FOUND"

    # ============================================
    # 处理错误 (8xxx)
    # ============================================
    PROCESSING_ERROR = "PROCESSING_ERROR"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    PROCESSING_QUEUE_FULL = "PROCESSING_QUEUE_FULL"
    CHUNKING_FAILED = "CHUNKING_FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"

    # ============================================
    # AI服务错误 (9xxx)
    # ============================================
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"

    @property
    def code(self) -> str:
        """兼容旧代码读取错误码字符串。"""
        return self.value


# 错误码到HTTP状态码的映射
ERROR_CODE_TO_STATUS: Dict[ErrorCode, int] = {
    # 通用错误
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.SERVICE_UNAVAILABLE: 503,

    # 资源错误
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.ALREADY_EXISTS: 409,
    ErrorCode.RESOURCE_CONFLICT: 409,
    ErrorCode.RESOURCE_LOCKED: 423,
    ErrorCode.RESOURCE_DELETED: 410,

    # 文档错误
    ErrorCode.DOCUMENT_NOT_FOUND: 404,
    ErrorCode.DOCUMENT_UPLOAD_FAILED: 500,
    ErrorCode.DOCUMENT_PROCESSING_FAILED: 500,
    ErrorCode.DOCUMENT_TYPE_UNSUPPORTED: 415,
    ErrorCode.DOCUMENT_SIZE_EXCEEDED: 413,
    ErrorCode.DOCUMENT_CORRUPTED: 422,

    # 项目错误
    ErrorCode.PROJECT_NOT_FOUND: 404,
    ErrorCode.PROJECT_ALREADY_EXISTS: 409,
    ErrorCode.PROJECT_ACCESS_DENIED: 403,

    # 存储错误
    ErrorCode.STORAGE_ERROR: 500,
    ErrorCode.STORAGE_QUOTA_EXCEEDED: 507,
    ErrorCode.STORAGE_UPLOAD_FAILED: 500,
    ErrorCode.STORAGE_DOWNLOAD_FAILED: 500,
    ErrorCode.STORAGE_DELETE_FAILED: 500,

    # 数据库错误
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.DATABASE_CONNECTION_FAILED: 503,
    ErrorCode.DATABASE_QUERY_FAILED: 500,
    ErrorCode.DATABASE_CONSTRAINT_VIOLATION: 409,

    # 向量错误
    ErrorCode.VECTOR_STORE_ERROR: 500,
    ErrorCode.VECTOR_EMBEDDING_FAILED: 500,
    ErrorCode.VECTOR_SEARCH_FAILED: 500,
    ErrorCode.VECTOR_NOT_FOUND: 404,

    # 处理错误
    ErrorCode.PROCESSING_ERROR: 500,
    ErrorCode.PROCESSING_TIMEOUT: 504,
    ErrorCode.PROCESSING_QUEUE_FULL: 503,
    ErrorCode.CHUNKING_FAILED: 500,
    ErrorCode.EXTRACTION_FAILED: 500,

    # AI服务错误
    ErrorCode.AI_SERVICE_ERROR: 500,
    ErrorCode.AI_SERVICE_UNAVAILABLE: 503,
    ErrorCode.AI_RATE_LIMIT: 429,
    ErrorCode.AI_INVALID_RESPONSE: 502,
    ErrorCode.AI_QUOTA_EXCEEDED: 429,
}


# 错误码到默认消息的映射（中英文）
ERROR_MESSAGES: Dict[ErrorCode, Tuple[str, str]] = {
    # 通用错误
    ErrorCode.INTERNAL_ERROR: ("Internal server error", "服务器内部错误"),
    ErrorCode.UNKNOWN_ERROR: ("Unknown error", "未知错误"),
    ErrorCode.INVALID_REQUEST: ("Invalid request", "无效的请求"),
    ErrorCode.VALIDATION_ERROR: ("Validation error", "验证错误"),
    ErrorCode.AUTHENTICATION_REQUIRED: ("Authentication required", "需要身份验证"),
    ErrorCode.PERMISSION_DENIED: ("Permission denied", "权限不足"),
    ErrorCode.RATE_LIMIT_EXCEEDED: ("Rate limit exceeded", "请求频率超限"),
    ErrorCode.SERVICE_UNAVAILABLE: ("Service unavailable", "服务暂时不可用"),

    # 资源错误
    ErrorCode.NOT_FOUND: ("Resource not found", "资源不存在"),
    ErrorCode.ALREADY_EXISTS: ("Resource already exists", "资源已存在"),
    ErrorCode.RESOURCE_CONFLICT: ("Resource conflict", "资源冲突"),
    ErrorCode.RESOURCE_LOCKED: ("Resource is locked", "资源已锁定"),
    ErrorCode.RESOURCE_DELETED: ("Resource has been deleted", "资源已删除"),

    # 文档错误
    ErrorCode.DOCUMENT_NOT_FOUND: ("Document not found", "文档不存在"),
    ErrorCode.DOCUMENT_UPLOAD_FAILED: ("Document upload failed", "文档上传失败"),
    ErrorCode.DOCUMENT_PROCESSING_FAILED: ("Document processing failed", "文档处理失败"),
    ErrorCode.DOCUMENT_TYPE_UNSUPPORTED: ("Document type not supported", "不支持的文档类型"),
    ErrorCode.DOCUMENT_SIZE_EXCEEDED: ("Document size exceeded limit", "文档大小超出限制"),
    ErrorCode.DOCUMENT_CORRUPTED: ("Document is corrupted", "文档已损坏"),

    # 项目错误
    ErrorCode.PROJECT_NOT_FOUND: ("Project not found", "项目不存在"),
    ErrorCode.PROJECT_ALREADY_EXISTS: ("Project already exists", "项目已存在"),
    ErrorCode.PROJECT_ACCESS_DENIED: ("Project access denied", "无权访问该项目"),

    # 存储错误
    ErrorCode.STORAGE_ERROR: ("Storage error", "存储错误"),
    ErrorCode.STORAGE_QUOTA_EXCEEDED: ("Storage quota exceeded", "存储空间不足"),
    ErrorCode.STORAGE_UPLOAD_FAILED: ("Storage upload failed", "上传到存储失败"),
    ErrorCode.STORAGE_DOWNLOAD_FAILED: ("Storage download failed", "从存储下载失败"),
    ErrorCode.STORAGE_DELETE_FAILED: ("Storage delete failed", "从存储删除失败"),

    # 数据库错误
    ErrorCode.DATABASE_ERROR: ("Database error", "数据库错误"),
    ErrorCode.DATABASE_CONNECTION_FAILED: ("Database connection failed", "数据库连接失败"),
    ErrorCode.DATABASE_QUERY_FAILED: ("Database query failed", "数据库查询失败"),
    ErrorCode.DATABASE_CONSTRAINT_VIOLATION: ("Database constraint violation", "数据库约束冲突"),

    # 向量错误
    ErrorCode.VECTOR_STORE_ERROR: ("Vector store error", "向量存储错误"),
    ErrorCode.VECTOR_EMBEDDING_FAILED: ("Vector embedding failed", "向量生成失败"),
    ErrorCode.VECTOR_SEARCH_FAILED: ("Vector search failed", "向量检索失败"),
    ErrorCode.VECTOR_NOT_FOUND: ("Vector not found", "向量不存在"),

    # 处理错误
    ErrorCode.PROCESSING_ERROR: ("Processing error", "处理错误"),
    ErrorCode.PROCESSING_TIMEOUT: ("Processing timeout", "处理超时"),
    ErrorCode.PROCESSING_QUEUE_FULL: ("Processing queue is full", "处理队列已满"),
    ErrorCode.CHUNKING_FAILED: ("Document chunking failed", "文档分块失败"),
    ErrorCode.EXTRACTION_FAILED: ("Content extraction failed", "内容提取失败"),

    # AI服务错误
    ErrorCode.AI_SERVICE_ERROR: ("AI service error", "AI服务错误"),
    ErrorCode.AI_SERVICE_UNAVAILABLE: ("AI service unavailable", "AI服务不可用"),
    ErrorCode.AI_RATE_LIMIT: ("AI service rate limit", "AI服务请求限制"),
    ErrorCode.AI_INVALID_RESPONSE: ("Invalid AI service response", "AI服务响应无效"),
    ErrorCode.AI_QUOTA_EXCEEDED: ("AI service quota exceeded", "AI服务配额不足"),
}


def get_error_status_code(error_code: ErrorCode) -> int:
    """获取错误码对应的HTTP状态码"""
    return ERROR_CODE_TO_STATUS.get(error_code, 500)


def get_error_message(error_code: ErrorCode, lang: str = "en") -> str:
    """
    获取错误码对应的默认消息

    Args:
        error_code: 错误码
        lang: 语言 ("en" 或 "zh")

    Returns:
        str: 错误消息
    """
    messages = ERROR_MESSAGES.get(error_code, ("Unknown error", "未知错误"))
    return messages[1] if lang == "zh" else messages[0]
