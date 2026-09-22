"""
全局异常处理器
捕获和处理所有API异常
"""

import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import FieldMindException
from app.core.errors import ErrorCode
from app.schemas.response import error_response


async def fieldmind_exception_handler(
    request: Request,
    exc: FieldMindException
) -> JSONResponse:
    """
    处理 FieldMind 自定义异常

    Args:
        request: FastAPI 请求对象
        exc: FieldMind 异常

    Returns:
        JSONResponse: 标准错误响应
    """
    request_id = request.headers.get("X-Request-ID")

    response_data = error_response(
        code=exc.error_code.value,
        message=exc.message,
        field=exc.field,
        details=exc.details,
        request_id=request_id,
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    处理请求验证异常

    Args:
        request: FastAPI 请求对象
        exc: 验证异常

    Returns:
        JSONResponse: 标准错误响应
    """
    request_id = request.headers.get("X-Request-ID")

    # 提取第一个验证错误
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")

    response_data = error_response(
        code=ErrorCode.VALIDATION_ERROR.value,
        message=message,
        field=field if field else None,
        details={"errors": errors},
        request_id=request_id,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    处理 HTTP 异常

    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常

    Returns:
        JSONResponse: 标准错误响应
    """
    request_id = request.headers.get("X-Request-ID")

    # 映射 HTTP 状态码到错误码
    error_code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.RESOURCE_CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    response_data = error_response(
        code=error_code.value,
        message=exc.detail,
        request_id=request_id,
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    处理未捕获的通用异常

    Args:
        request: FastAPI 请求对象
        exc: 异常

    Returns:
        JSONResponse: 标准错误响应
    """
    request_id = request.headers.get("X-Request-ID")

    # 记录异常堆栈（生产环境应使用日志系统）
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())

    response_data = error_response(
        code=ErrorCode.INTERNAL_ERROR.value,
        message="Internal server error",
        details={"exception": str(exc)} if request.app.debug else None,
        request_id=request_id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(FieldMindException, fieldmind_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
