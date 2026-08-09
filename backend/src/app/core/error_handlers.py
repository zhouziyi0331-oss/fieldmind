"""
错误装饰器和处理器
Error Decorators and Handlers

提供自动异常处理、重试机制和错误记录功能
"""

import functools
import asyncio
import time
from typing import Callable, Optional, Type, Tuple, Any, Union, List
from contextlib import contextmanager
import logging

from app.core.exceptions import (
    FieldMindException,
    ErrorCode,
    TimeoutException,
    DatabaseException,
    AIServiceException,
    VectorStoreException,
    GraphException,
    FileException,
)

logger = logging.getLogger(__name__)


def handle_errors(
    error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    message: Optional[str] = None,
    log_error: bool = True,
    raise_on_error: bool = True,
    return_on_error: Any = None,
):
    """
    错误处理装饰器

    Args:
        error_code: 默认错误代码
        message: 错误消息模板
        log_error: 是否记录错误日志
        raise_on_error: 是否抛出异常（False时返回return_on_error）
        return_on_error: 发生错误时的返回值

    Example:
        @handle_errors(error_code=ErrorCode.DATABASE_ERROR, message="数据库查询失败")
        def query_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FieldMindException:
                # 已经是FieldMind异常，直接向上抛出
                raise
            except Exception as e:
                error_msg = message or f"{func.__name__} 执行失败"

                if log_error:
                    logger.error(
                        f"{error_msg}: {str(e)}",
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "error_code": error_code.code,
                            "func_args": str(args),
                            "func_kwargs": str(kwargs),
                        }
                    )

                # 记录到监控系统
                try:
                    from app.core.monitoring import record_error
                    record_error(
                        error_code=error_code,
                        error_type=type(e).__name__,
                        component=func.__module__,
                        details={"function": func.__name__}
                    )
                except ImportError:
                    pass

                if raise_on_error:
                    raise FieldMindException(
                        error_code=error_code,
                        message=error_msg,
                        details={"function": func.__name__},
                        cause=e
                    )
                else:
                    return return_on_error

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FieldMindException:
                raise
            except Exception as e:
                error_msg = message or f"{func.__name__} 执行失败"

                if log_error:
                    logger.error(
                        f"{error_msg}: {str(e)}",
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "error_code": error_code.code,
                            "func_args": str(args),
                            "func_kwargs": str(kwargs),
                        }
                    )

                try:
                    from app.core.monitoring import record_error
                    record_error(
                        error_code=error_code,
                        error_type=type(e).__name__,
                        component=func.__module__,
                        details={"function": func.__name__}
                    )
                except ImportError:
                    pass

                if raise_on_error:
                    raise FieldMindException(
                        error_code=error_code,
                        message=error_msg,
                        details={"function": func.__name__},
                        cause=e
                    )
                else:
                    return return_on_error

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    失败重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间倍数
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数

    Example:
        @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
        async def call_external_api():
            return await api_client.get("/data")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)

                        logger.warning(
                            f"{func.__name__} 执行失败，{current_delay}秒后重试 "
                            f"(尝试 {attempt + 1}/{max_retries}): {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": current_delay,
                            }
                        )

                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} 重试{max_retries}次后仍然失败: {str(e)}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "max_retries": max_retries,
                            }
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)

                        logger.warning(
                            f"{func.__name__} 执行失败，{current_delay}秒后重试 "
                            f"(尝试 {attempt + 1}/{max_retries}): {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": current_delay,
                            }
                        )

                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} 重试{max_retries}次后仍然失败: {str(e)}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "max_retries": max_retries,
                            }
                        )

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def timeout(seconds: float, error_message: Optional[str] = None):
    """
    超时装饰器（仅支持异步函数）

    Args:
        seconds: 超时时间(秒)
        error_message: 超时错误消息

    Example:
        @timeout(30.0, "处理文档超时")
        async def process_document(doc_id: str):
            return await heavy_processing(doc_id)
    """
    def decorator(func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"timeout decorator只支持异步函数: {func.__name__}")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                msg = error_message or f"{func.__name__} 执行超时"
                logger.error(
                    f"{msg} (>{seconds}s)",
                    extra={
                        "function": func.__name__,
                        "timeout_seconds": seconds,
                    }
                )
                raise TimeoutException(
                    operation=func.__name__,
                    timeout_seconds=seconds,
                    message=msg
                )

        return wrapper

    return decorator


@contextmanager
def handle_database_errors(operation: str):
    """
    数据库错误上下文管理器

    Example:
        with handle_database_errors("查询用户"):
            user = db.query(User).filter(User.id == user_id).first()
    """
    try:
        yield
    except FieldMindException:
        raise
    except Exception as e:
        logger.error(f"数据库操作失败: {operation}", exc_info=True)
        try:
            from app.core.monitoring import record_error
            record_error(
                error_code=ErrorCode.DATABASE_ERROR,
                error_type=type(e).__name__,
                component="database",
                details={"operation": operation}
            )
        except ImportError:
            pass
        raise DatabaseException(
            message=f"数据库操作失败: {operation}",
            operation=operation,
            cause=e
        )


@contextmanager
def handle_ai_errors(model: str, operation: str = "AI请求"):
    """
    AI服务错误上下文管理器

    Example:
        with handle_ai_errors(model="gpt-4", operation="文本生成"):
            response = await ai_service.generate(prompt)
    """
    try:
        yield
    except FieldMindException:
        raise
    except Exception as e:
        logger.error(f"AI服务错误: {operation} (模型: {model})", exc_info=True)
        try:
            from app.core.monitoring import record_error
            record_error(
                error_code=ErrorCode.AI_SERVICE_ERROR,
                error_type=type(e).__name__,
                component="ai_service",
                details={"model": model, "operation": operation}
            )
        except ImportError:
            pass
        raise AIServiceException(
            message=f"AI服务错误: {operation}",
            model=model,
            cause=e
        )


@contextmanager
def handle_vector_errors(collection: str, operation: str = "向量操作"):
    """
    向量存储错误上下文管理器

    Example:
        with handle_vector_errors(collection="documents", operation="向量搜索"):
            results = vector_store.search(query_vector, top_k=10)
    """
    try:
        yield
    except FieldMindException:
        raise
    except Exception as e:
        logger.error(f"向量存储错误: {operation} (集合: {collection})", exc_info=True)
        try:
            from app.core.monitoring import record_error
            record_error(
                error_code=ErrorCode.VECTOR_STORE_ERROR,
                error_type=type(e).__name__,
                component="vector_store",
                details={"collection": collection, "operation": operation}
            )
        except ImportError:
            pass
        raise VectorStoreException(
            message=f"向量存储错误: {operation}",
            collection=collection,
            cause=e
        )


@contextmanager
def handle_graph_errors(operation: str, query: Optional[str] = None):
    """
    知识图谱错误上下文管理器

    Example:
        with handle_graph_errors(operation="查询节点关系", query=cypher_query):
            results = graph.run(cypher_query)
    """
    try:
        yield
    except FieldMindException:
        raise
    except Exception as e:
        logger.error(f"知识图谱错误: {operation}", exc_info=True)
        try:
            from app.core.monitoring import record_error
            record_error(
                error_code=ErrorCode.GRAPH_ERROR,
                error_type=type(e).__name__,
                component="knowledge_graph",
                details={"operation": operation}
            )
        except ImportError:
            pass
        raise GraphException(
            message=f"知识图谱错误: {operation}",
            query=query,
            cause=e
        )


@contextmanager
def handle_file_errors(filename: str, operation: str = "文件操作"):
    """
    文件处理错误上下文管理器

    Example:
        with handle_file_errors(filename="document.pdf", operation="文件解析"):
            content = parse_pdf(filename)
    """
    try:
        yield
    except FieldMindException:
        raise
    except Exception as e:
        logger.error(f"文件处理错误: {operation} (文件: {filename})", exc_info=True)
        try:
            from app.core.monitoring import record_error
            record_error(
                error_code=ErrorCode.FILE_ERROR,
                error_type=type(e).__name__,
                component="file_processing",
                details={"filename": filename, "operation": operation}
            )
        except ImportError:
            pass
        raise FileException(
            message=f"文件处理错误: {operation}",
            filename=filename,
            cause=e
        )


def combine_decorators(*decorators):
    """
    组合多个装饰器

    Example:
        @combine_decorators(
            retry_on_failure(max_retries=3),
            timeout(30.0),
            handle_errors(error_code=ErrorCode.AI_SERVICE_ERROR)
        )
        async def call_ai_service():
            return await ai_client.generate()
    """
    def decorator(func: Callable) -> Callable:
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator
