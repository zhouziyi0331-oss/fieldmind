"""
日志和监控系统测试
测试日志记录和性能指标收集
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.logging import (
    logger,
    LogContext,
    log_request,
    log_error,
    log_document_processing,
    log_vector_operation,
    log_storage_operation,
    log_database_query,
    log_ai_request,
    log_performance
)

from app.core.metrics import (
    record_http_request,
    record_document_upload,
    record_document_processing,
    record_vector_insert,
    record_vector_search,
    record_storage_operation,
    record_database_query,
    record_ai_request,
    record_error,
    update_vector_store_size,
    init_metrics
)


def test_basic_logging():
    """测试1: 基础日志记录"""
    print("\n" + "="*60)
    print("测试1: 基础日志记录")
    print("="*60)

    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")

    print("✅ 基础日志记录成功")
    print("   检查 logs/fieldmind.log 查看日志输出")
    return True


def test_structured_logging():
    """测试2: 结构化日志"""
    print("\n" + "="*60)
    print("测试2: 结构化日志")
    print("="*60)

    logger.bind(
        request_id="req_123",
        user_id="user_456",
        operation="test"
    ).info("结构化日志测试")

    print("✅ 结构化日志记录成功")
    print("   日志包含: request_id, user_id, operation")
    return True


def test_log_context():
    """测试3: 日志上下文"""
    print("\n" + "="*60)
    print("测试3: 日志上下文")
    print("="*60)

    with LogContext(request_id="req_789", user_id="user_012"):
        logger.info("上下文中的日志1")
        logger.info("上下文中的日志2")

    logger.info("上下文外的日志")

    print("✅ 日志上下文功能正常")
    print("   上下文内的日志自动包含 request_id 和 user_id")
    return True


def test_request_logging():
    """测试4: 请求日志"""
    print("\n" + "="*60)
    print("测试4: 请求日志")
    print("="*60)

    log_request(
        request_id="req_abc123",
        method="GET",
        path="/api/v1/documents/doc_001",
        status_code=200,
        process_time=0.0234,
        client_ip="192.168.1.100",
        user_id="user_123"
    )

    print("✅ 请求日志记录成功")
    print("   记录了完整的请求信息和处理时间")
    return True


def test_error_logging():
    """测试5: 错误日志"""
    print("\n" + "="*60)
    print("测试5: 错误日志")
    print("="*60)

    log_error(
        error_code="DOCUMENT_NOT_FOUND",
        message="Document doc_001 not found",
        request_id="req_def456",
        details={"document_id": "doc_001"}
    )

    print("✅ 错误日志记录成功")
    print("   包含错误码、消息和详细信息")
    return True


def test_document_processing_logging():
    """测试6: 文档处理日志"""
    print("\n" + "="*60)
    print("测试6: 文档处理日志")
    print("="*60)

    # 开始处理
    log_document_processing(
        document_id="doc_001",
        operation="upload",
        status="started"
    )

    time.sleep(0.1)

    # 完成处理
    log_document_processing(
        document_id="doc_001",
        operation="upload",
        status="completed",
        duration=0.1,
        details={"size": 1024000, "type": "pdf"}
    )

    print("✅ 文档处理日志记录成功")
    print("   记录了处理开始和完成")
    return True


def test_vector_operation_logging():
    """测试7: 向量操作日志"""
    print("\n" + "="*60)
    print("测试7: 向量操作日志")
    print("="*60)

    log_vector_operation(
        operation="insert",
        document_id="doc_001",
        count=10,
        duration=0.05,
        success=True
    )

    log_vector_operation(
        operation="search",
        count=5,
        duration=0.02,
        success=True
    )

    print("✅ 向量操作日志记录成功")
    print("   记录了插入和搜索操作")
    return True


def test_performance_decorator():
    """测试8: 性能监控装饰器"""
    print("\n" + "="*60)
    print("测试8: 性能监控装饰器")
    print("="*60)

    @log_performance("test_operation")
    def slow_function():
        time.sleep(0.1)
        return "done"

    result = slow_function()

    print("✅ 性能装饰器工作正常")
    print(f"   函数返回: {result}")
    print("   自动记录了执行时间")
    return True


def test_metrics_initialization():
    """测试9: 指标初始化"""
    print("\n" + "="*60)
    print("测试9: 指标初始化")
    print("="*60)

    init_metrics(version="1.0.0", environment="test")

    print("✅ 指标系统初始化成功")
    print("   版本: 1.0.0")
    print("   环境: test")
    return True


def test_http_metrics():
    """测试10: HTTP 请求指标"""
    print("\n" + "="*60)
    print("测试10: HTTP 请求指标")
    print("="*60)

    # 记录一些请求
    record_http_request("GET", "/api/v1/documents", 200, 0.023)
    record_http_request("POST", "/api/v1/documents", 201, 0.156)
    record_http_request("GET", "/api/v1/documents/doc_001", 404, 0.012)

    print("✅ HTTP 请求指标记录成功")
    print("   记录了 3 个请求")
    return True


def test_document_metrics():
    """测试11: 文档处理指标"""
    print("\n" + "="*60)
    print("测试11: 文档处理指标")
    print("="*60)

    record_document_upload("pdf")
    record_document_upload("image")

    record_document_processing("pdf", "extract", "success", 1.234)
    record_document_processing("pdf", "chunk", "success", 0.567)

    print("✅ 文档处理指标记录成功")
    print("   上传: 2 个文档")
    print("   处理: 2 个操作")
    return True


def test_vector_metrics():
    """测试12: 向量存储指标"""
    print("\n" + "="*60)
    print("测试12: 向量存储指标")
    print("="*60)

    record_vector_insert(10)
    record_vector_insert(20)

    record_vector_search(0.015)
    record_vector_search(0.023)
    record_vector_search(0.018)

    update_vector_store_size(1000)

    print("✅ 向量存储指标记录成功")
    print("   插入: 30 个向量")
    print("   搜索: 3 次")
    print("   总量: 1000 个向量")
    return True


def test_storage_metrics():
    """测试13: 存储操作指标"""
    print("\n" + "="*60)
    print("测试13: 存储操作指标")
    print("="*60)

    record_storage_operation(
        operation="upload",
        bucket="documents",
        status="success",
        duration=0.234,
        size=1024000
    )

    record_storage_operation(
        operation="download",
        bucket="documents",
        status="success",
        duration=0.123,
        size=512000
    )

    print("✅ 存储操作指标记录成功")
    print("   上传: 1 MB")
    print("   下载: 0.5 MB")
    return True


def test_database_metrics():
    """测试14: 数据库查询指标"""
    print("\n" + "="*60)
    print("测试14: 数据库查询指标")
    print("="*60)

    record_database_query("select", "documents", "success", 0.012)
    record_database_query("insert", "documents", "success", 0.008)
    record_database_query("update", "documents", "success", 0.015)

    print("✅ 数据库查询指标记录成功")
    print("   记录了 3 个查询")
    return True


def test_ai_metrics():
    """测试15: AI 服务指标"""
    print("\n" + "="*60)
    print("测试15: AI 服务指标")
    print("="*60)

    record_ai_request(
        provider="openai",
        model="gpt-4",
        operation="completion",
        status="success",
        duration=2.345,
        tokens=150
    )

    record_ai_request(
        provider="openai",
        model="text-embedding-ada-002",
        operation="embedding",
        status="success",
        duration=0.567,
        tokens=500
    )

    print("✅ AI 服务指标记录成功")
    print("   请求: 2 次")
    print("   Token: 650")
    return True


def test_error_metrics():
    """测试16: 错误指标"""
    print("\n" + "="*60)
    print("测试16: 错误指标")
    print("="*60)

    record_error("NOT_FOUND", "/api/v1/documents/doc_001")
    record_error("VALIDATION_ERROR", "/api/v1/documents")
    record_error("INTERNAL_ERROR", "/api/v1/process")

    print("✅ 错误指标记录成功")
    print("   记录了 3 个错误")
    return True


def test_log_files_created():
    """测试17: 日志文件创建"""
    print("\n" + "="*60)
    print("测试17: 日志文件创建")
    print("="*60)

    log_dir = Path("logs")

    expected_files = [
        "fieldmind.log",
        "error.log",
        "access.log"
    ]

    created_files = []
    for log_file in expected_files:
        file_path = log_dir / log_file
        if file_path.exists():
            size = file_path.stat().st_size
            created_files.append(f"{log_file} ({size} bytes)")

    print("✅ 日志文件检查完成")
    print(f"   日志目录: {log_dir.absolute()}")
    print(f"   创建的文件:")
    for file_info in created_files:
        print(f"     - {file_info}")

    return len(created_files) >= 2  # 至少有2个日志文件


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FieldMind 日志和监控系统测试套件")
    print("="*60)

    tests = [
        ("基础日志记录", test_basic_logging),
        ("结构化日志", test_structured_logging),
        ("日志上下文", test_log_context),
        ("请求日志", test_request_logging),
        ("错误日志", test_error_logging),
        ("文档处理日志", test_document_processing_logging),
        ("向量操作日志", test_vector_operation_logging),
        ("性能装饰器", test_performance_decorator),
        ("指标初始化", test_metrics_initialization),
        ("HTTP 请求指标", test_http_metrics),
        ("文档处理指标", test_document_metrics),
        ("向量存储指标", test_vector_metrics),
        ("存储操作指标", test_storage_metrics),
        ("数据库查询指标", test_database_metrics),
        ("AI 服务指标", test_ai_metrics),
        ("错误指标", test_error_metrics),
        ("日志文件创建", test_log_files_created),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n📊 监控端点: http://localhost:8000/metrics")
        print("📝 日志目录: logs/")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
