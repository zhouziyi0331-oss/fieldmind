"""
全局异常处理器
Global Exception Handlers

统一处理所有FieldMind自定义异常和通用异常
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback
from typing import Union

from app.core.exceptions import FieldMindException, ErrorCode

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(FieldMindException)
    async def fieldmind_exception_handler(request: Request, exc: FieldMindException):
        """
        处理FieldMind自定义异常

        特点：
        1. 返回标准化的错误响应格式
        2. 根据异常严重程度记录日志
        3. 保留原始错误上下文
        """
        # 记录日志
        log_message = f"[{exc.error_code.code}] {exc.message}"
        if exc.error_code.http_status >= 500:
            logger.error(log_message, exc_info=exc.cause if exc.cause else None)
        else:
            logger.warning(log_message)

        # 构建响应
        response_data = {
            "success": False,
            "error_code": exc.error_code.code,
            "message": exc.message,
            "http_status": exc.error_code.http_status
        }

        # 添加详细信息（如果存在）
        if exc.details:
            response_data["details"] = exc.details

        # 开发环境下添加cause信息
        if exc.cause and logger.level <= logging.DEBUG:
            response_data["cause"] = str(exc.cause)

        return JSONResponse(
            status_code=exc.error_code.http_status,
            content=response_data
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        处理FastAPI请求验证错误

        将Pydantic验证错误转换为统一格式
        """
        logger.warning(f"请求验证失败: {exc.errors()}")

        # 提取验证错误详情
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error_code": ErrorCode.VALIDATION_ERROR.code,
                "message": "请求参数验证失败",
                "http_status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": {
                    "validation_errors": errors
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        处理所有未捕获的通用异常

        这是最后的防线，确保所有错误都返回统一格式
        """
        # 记录完整堆栈跟踪
        logger.error(
            f"未捕获的异常: {type(exc).__name__}: {str(exc)}",
            exc_info=True
        )
        logger.error(f"请求路径: {request.method} {request.url.path}")
        logger.error(traceback.format_exc())

        # 返回通用错误响应
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": ErrorCode.UNKNOWN_ERROR.code,
                "message": f"服务器内部错误: {str(exc)}",
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "details": {
                    "exception_type": type(exc).__name__,
                    "path": request.url.path,
                    "method": request.method
                }
            }
        )

    logger.info("✅ 全局异常处理器已注册")
