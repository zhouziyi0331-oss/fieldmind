"""
统一错误处理框架测试
Test Suite for Unified Error Handling Framework
"""

import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import time
from app.core.exceptions import (
    FieldMindException,
    ErrorCode,
    ValidationException,
    ResourceNotFoundException,
    PermissionDeniedException,
    DatabaseException,
    AIServiceException,
    TimeoutException,
    RateLimitException,
)
from app.core.error_handlers import (
    handle_errors,
    retry_on_failure,
    timeout,
    handle_database_errors,
    handle_ai_errors,
    handle_vector_errors,
    handle_graph_errors,
    combine_decorators,
)


def log(message: str):
    """辅助日志函数"""
    print(f"[TEST] {message}", flush=True)


def test_exception_hierarchy():
    """测试异常类层次结构"""
    log("=" * 60)
    log("测试1: 异常类层次结构")
    log("=" * 60)

    # 测试基础异常
    exc = FieldMindException(
        error_code=ErrorCode.UNKNOWN_ERROR,
        message="测试错误",
        details={"key": "value"}
    )
    assert exc.error_code == ErrorCode.UNKNOWN_ERROR
    assert exc.message == "测试错误"
    assert exc.details == {"key": "value"}
    log("✓ 基础异常创建成功")

    # 测试异常字典转换
    exc_dict = exc.to_dict()
    assert exc_dict["error_code"] == ErrorCode.UNKNOWN_ERROR.code
    assert exc_dict["message"] == "测试错误"
    assert exc_dict["details"] == {"key": "value"}
    log("✓ 异常字典转换正确")

    # 测试ValidationException
    val_exc = ValidationException(message="字段验证失败", field="email")
    assert val_exc.error_code == ErrorCode.VALIDATION_ERROR
    assert val_exc.details["field"] == "email"
    log("✓ ValidationException创建成功")

    # 测试ResourceNotFoundException
    res_exc = ResourceNotFoundException(
        resource_type="User",
        resource_id="123"
    )
    assert res_exc.error_code == ErrorCode.RESOURCE_NOT_FOUND
    assert res_exc.details["resource_type"] == "User"
    assert res_exc.details["resource_id"] == "123"
    log("✓ ResourceNotFoundException创建成功")

    # 测试PermissionDeniedException
    perm_exc = PermissionDeniedException(action="delete", resource="document")
    assert perm_exc.error_code == ErrorCode.PERMISSION_DENIED
    assert perm_exc.details["action"] == "delete"
    log("✓ PermissionDeniedException创建成功")

    # 测试DatabaseException
    db_exc = DatabaseException(message="查询失败", operation="SELECT")
    assert db_exc.error_code == ErrorCode.DATABASE_ERROR
    assert db_exc.details["operation"] == "SELECT"
    log("✓ DatabaseException创建成功")

    # 测试AIServiceException
    ai_exc = AIServiceException(message="模型请求失败", model="gpt-4")
    assert ai_exc.error_code == ErrorCode.AI_SERVICE_ERROR
    assert ai_exc.details["model"] == "gpt-4"
    log("✓ AIServiceException创建成功")

    # 测试TimeoutException
    timeout_exc = TimeoutException(operation="process_document", timeout_seconds=30.0)
    assert timeout_exc.error_code == ErrorCode.TIMEOUT_ERROR
    assert timeout_exc.details["timeout_seconds"] == 30.0
    log("✓ TimeoutException创建成功")

    # 测试RateLimitException
    rate_exc = RateLimitException(limit=100, window=60)
    assert rate_exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
    assert rate_exc.details["limit"] == 100
    log("✓ RateLimitException创建成功")

    log("✅ 测试1通过: 所有异常类正常工作\n")


def test_handle_errors_decorator():
    """测试错误处理装饰器"""
    log("=" * 60)
    log("测试2: 错误处理装饰器")
    log("=" * 60)

    # 测试同步函数
    @handle_errors(error_code=ErrorCode.DATABASE_ERROR, message="数据库操作失败")
    def sync_function_with_error():
        raise ValueError("测试错误")

    try:
        sync_function_with_error()
        assert False, "应该抛出异常"
    except FieldMindException as e:
        assert e.error_code == ErrorCode.DATABASE_ERROR
        assert "数据库操作失败" in e.message
        log("✓ 同步函数错误处理正常")

    # 测试返回默认值
    @handle_errors(
        error_code=ErrorCode.DATABASE_ERROR,
        raise_on_error=False,
        return_on_error={"default": "value"}
    )
    def sync_function_with_default():
        raise ValueError("测试错误")

    result = sync_function_with_default()
    assert result == {"default": "value"}
    log("✓ 错误时返回默认值正常")

    log("✅ 测试2通过: 错误处理装饰器正常工作\n")


async def test_async_decorators():
    """测试异步装饰器"""
    log("=" * 60)
    log("测试3: 异步装饰器")
    log("=" * 60)

    # 测试异步错误处理
    @handle_errors(error_code=ErrorCode.AI_SERVICE_ERROR)
    async def async_function_with_error():
        await asyncio.sleep(0.01)
        raise ValueError("异步错误")

    try:
        await async_function_with_error()
        assert False, "应该抛出异常"
    except FieldMindException as e:
        assert e.error_code == ErrorCode.AI_SERVICE_ERROR
        log("✓ 异步错误处理正常")

    # 测试超时装饰器
    @timeout(0.1, "操作超时")
    async def slow_function():
        await asyncio.sleep(0.5)
        return "完成"

    try:
        await slow_function()
        assert False, "应该超时"
    except TimeoutException as e:
        assert e.error_code == ErrorCode.TIMEOUT_ERROR
        assert e.details["timeout_seconds"] == 0.1
        log("✓ 超时装饰器正常")

    # 测试快速函数不超时
    @timeout(1.0)
    async def fast_function():
        await asyncio.sleep(0.01)
        return "完成"

    result = await fast_function()
    assert result == "完成"
    log("✓ 快速函数不超时")

    log("✅ 测试3通过: 异步装饰器正常工作\n")


async def test_retry_decorator():
    """测试重试装饰器"""
    log("=" * 60)
    log("测试4: 重试装饰器")
    log("=" * 60)

    # 测试重试成功
    attempt_count = [0]

    @retry_on_failure(max_retries=3, delay=0.01, backoff=1.5)
    async def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ValueError("临时错误")
        return "成功"

    result = await flaky_function()
    assert result == "成功"
    assert attempt_count[0] == 3
    log(f"✓ 重试装饰器成功 (尝试{attempt_count[0]}次)")

    # 测试重试失败
    @retry_on_failure(max_retries=2, delay=0.01)
    async def always_fail():
        raise ValueError("永久错误")

    try:
        await always_fail()
        assert False, "应该抛出异常"
    except ValueError as e:
        assert str(e) == "永久错误"
        log("✓ 重试耗尽后正确抛出异常")

    # 测试同步重试
    sync_count = [0]

    @retry_on_failure(max_retries=2, delay=0.01)
    def sync_flaky():
        sync_count[0] += 1
        if sync_count[0] < 2:
            raise ValueError("同步错误")
        return "同步成功"

    result = sync_flaky()
    assert result == "同步成功"
    log("✓ 同步函数重试正常")

    log("✅ 测试4通过: 重试装饰器正常工作\n")


def test_context_managers():
    """测试上下文管理器"""
    log("=" * 60)
    log("测试5: 上下文管理器")
    log("=" * 60)

    # 测试数据库错误处理
    try:
        with handle_database_errors("查询用户"):
            raise ValueError("数据库连接失败")
    except DatabaseException as e:
        assert e.error_code == ErrorCode.DATABASE_ERROR
        assert "查询用户" in e.message
        log("✓ 数据库错误上下文管理器正常")

    # 测试AI错误处理
    try:
        with handle_ai_errors(model="gpt-4", operation="文本生成"):
            raise ValueError("API调用失败")
    except AIServiceException as e:
        assert e.error_code == ErrorCode.AI_SERVICE_ERROR
        assert e.details["model"] == "gpt-4"
        log("✓ AI错误上下文管理器正常")

    # 测试向量存储错误处理
    try:
        with handle_vector_errors(collection="documents", operation="搜索"):
            raise ValueError("向量搜索失败")
    except Exception as e:
        assert "向量存储错误" in str(e)
        log("✓ 向量存储错误上下文管理器正常")

    # 测试知识图谱错误处理
    try:
        with handle_graph_errors(operation="查询节点", query="MATCH (n) RETURN n"):
            raise ValueError("图谱查询失败")
    except Exception as e:
        assert "知识图谱错误" in str(e)
        log("✓ 知识图谱错误上下文管理器正常")

    log("✅ 测试5通过: 上下文管理器正常工作\n")


async def test_combined_decorators():
    """测试装饰器组合"""
    log("=" * 60)
    log("测试6: 装饰器组合")
    log("=" * 60)

    attempt_count = [0]

    @combine_decorators(
        timeout(1.0),
        retry_on_failure(max_retries=2, delay=0.01),
        handle_errors(error_code=ErrorCode.AI_SERVICE_ERROR)
    )
    async def complex_function():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise ValueError("临时失败")
        await asyncio.sleep(0.01)
        return "组合成功"

    result = await complex_function()
    assert result == "组合成功"
    log(f"✓ 装饰器组合正常工作 (尝试{attempt_count[0]}次)")

    log("✅ 测试6通过: 装饰器可以正常组合\n")


def test_error_code_enum():
    """测试ErrorCode枚举"""
    log("=" * 60)
    log("测试7: ErrorCode枚举")
    log("=" * 60)

    # 测试通用错误码
    assert ErrorCode.SUCCESS.code == 1000
    assert ErrorCode.UNKNOWN_ERROR.code == 1001
    assert ErrorCode.VALIDATION_ERROR.code == 1002
    log("✓ 通用错误码正确")

    # 测试数据库错误码
    assert ErrorCode.DATABASE_ERROR.code == 2001
    assert ErrorCode.DATABASE_CONNECTION_ERROR.code == 2002
    log("✓ 数据库错误码正确")

    # 测试文件错误码
    assert ErrorCode.FILE_ERROR.code == 3001
    assert ErrorCode.FILE_NOT_FOUND.code == 3002
    log("✓ 文件错误码正确")

    # 测试AI服务错误码
    assert ErrorCode.AI_SERVICE_ERROR.code == 4001
    assert ErrorCode.AI_MODEL_NOT_AVAILABLE.code == 4002
    log("✓ AI服务错误码正确")

    # 测试向量存储错误码
    assert ErrorCode.VECTOR_STORE_ERROR.code == 5001
    assert ErrorCode.VECTOR_SEARCH_ERROR.code == 5003
    log("✓ 向量存储错误码正确")

    # 测试知识图谱错误码
    assert ErrorCode.GRAPH_ERROR.code == 6001
    assert ErrorCode.GRAPH_QUERY_ERROR.code == 6003
    log("✓ 知识图谱错误码正确")

    # 测试工作流错误码
    assert ErrorCode.WORKFLOW_ERROR.code == 7001
    assert ErrorCode.WORKFLOW_EXECUTION_ERROR.code == 7002
    log("✓ 工作流错误码正确")

    # 测试HTTP状态码映射
    assert ErrorCode.SUCCESS.http_status == 200
    assert ErrorCode.VALIDATION_ERROR.http_status == 422
    assert ErrorCode.RESOURCE_NOT_FOUND.http_status == 404
    assert ErrorCode.PERMISSION_DENIED.http_status == 403
    assert ErrorCode.RATE_LIMIT_EXCEEDED.http_status == 429
    log("✓ HTTP状态码映射正确")

    log("✅ 测试7通过: ErrorCode枚举定义正确\n")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("统一错误处理框架测试套件")
    print("=" * 60 + "\n")

    start_time = time.time()

    try:
        # 运行所有测试
        test_exception_hierarchy()
        test_handle_errors_decorator()
        await test_async_decorators()
        await test_retry_decorator()
        test_context_managers()
        await test_combined_decorators()
        test_error_code_enum()

        elapsed = time.time() - start_time

        print("=" * 60)
        print(f"✅ 所有测试通过! (耗时: {elapsed:.2f}秒)")
        print("=" * 60)
        print("\n测试覆盖:")
        print("  • 异常类层次结构 (8个异常类)")
        print("  • 错误处理装饰器 (@handle_errors)")
        print("  • 重试装饰器 (@retry_on_failure)")
        print("  • 超时装饰器 (@timeout)")
        print("  • 上下文管理器 (4种)")
        print("  • 装饰器组合 (@combine_decorators)")
        print("  • ErrorCode枚举 (80+错误码)")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
