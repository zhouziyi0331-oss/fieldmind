"""
响应格式测试
测试统一响应格式的正确性
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.schemas.response import (
    success_response,
    error_response,
    paginated_response,
    ApiResponse,
    PaginatedResponse
)
from app.core.errors import ErrorCode, get_error_status_code, get_error_message
from app.core.exceptions import (
    FieldMindException,
    ValidationException,
    NotFoundException,
    DocumentNotFoundException
)


def test_success_response():
    """测试1: 成功响应"""
    print("\n" + "="*60)
    print("测试1: 成功响应")
    print("="*60)

    data = {"id": "doc_001", "name": "test.pdf"}
    response = success_response(data, request_id="req_123")

    assert response["success"] is True
    assert response["data"] == data
    assert response["error"] is None
    assert response["metadata"]["request_id"] == "req_123"
    assert "timestamp" in response["metadata"]

    print("✅ 成功响应格式正确")
    print(f"   data: {response['data']}")
    print(f"   request_id: {response['metadata']['request_id']}")
    return True


def test_error_response():
    """测试2: 错误响应"""
    print("\n" + "="*60)
    print("测试2: 错误响应")
    print("="*60)

    response = error_response(
        code="NOT_FOUND",
        message="Document not found",
        details={"document_id": "doc_001"},
        request_id="req_456"
    )

    assert response["success"] is False
    assert response["data"] is None
    assert response["error"]["code"] == "NOT_FOUND"
    assert response["error"]["message"] == "Document not found"
    assert response["metadata"]["request_id"] == "req_456"

    print("✅ 错误响应格式正确")
    print(f"   code: {response['error']['code']}")
    print(f"   message: {response['error']['message']}")
    return True


def test_paginated_response():
    """测试3: 分页响应"""
    print("\n" + "="*60)
    print("测试3: 分页响应")
    print("="*60)

    data = [{"id": f"doc_{i:03d}"} for i in range(20)]
    response = paginated_response(
        data=data,
        page=1,
        page_size=20,
        total=100,
        request_id="req_789"
    )

    assert response["success"] is True
    assert len(response["data"]) == 20
    assert response["pagination"]["page"] == 1
    assert response["pagination"]["total"] == 100
    assert response["pagination"]["total_pages"] == 5
    assert response["pagination"]["has_next"] is True
    assert response["pagination"]["has_prev"] is False

    print("✅ 分页响应格式正确")
    print(f"   数据量: {len(response['data'])}")
    print(f"   页码: {response['pagination']['page']}/{response['pagination']['total_pages']}")
    print(f"   总记录: {response['pagination']['total']}")
    return True


def test_error_codes():
    """测试4: 错误码映射"""
    print("\n" + "="*60)
    print("测试4: 错误码映射")
    print("="*60)

    test_cases = [
        (ErrorCode.NOT_FOUND, 404),
        (ErrorCode.VALIDATION_ERROR, 422),
        (ErrorCode.INTERNAL_ERROR, 500),
        (ErrorCode.PERMISSION_DENIED, 403),
        (ErrorCode.RATE_LIMIT_EXCEEDED, 429),
    ]

    for error_code, expected_status in test_cases:
        status = get_error_status_code(error_code)
        assert status == expected_status, f"{error_code} should map to {expected_status}"
        print(f"   {error_code.value} → HTTP {status}")

    print("✅ 错误码映射正确")
    return True


def test_error_messages():
    """测试5: 错误消息（中英文）"""
    print("\n" + "="*60)
    print("测试5: 错误消息（中英文）")
    print("="*60)

    test_codes = [
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.DOCUMENT_NOT_FOUND
    ]

    for code in test_codes:
        en_msg = get_error_message(code, "en")
        zh_msg = get_error_message(code, "zh")
        print(f"   {code.value}:")
        print(f"     EN: {en_msg}")
        print(f"     ZH: {zh_msg}")

    print("✅ 错误消息正确")
    return True


def test_fieldmind_exception():
    """测试6: FieldMind异常"""
    print("\n" + "="*60)
    print("测试6: FieldMind异常")
    print("="*60)

    exc = FieldMindException(
        error_code=ErrorCode.NOT_FOUND,
        message="Test resource not found",
        details={"id": "test_123"}
    )

    assert exc.error_code == ErrorCode.NOT_FOUND
    assert exc.message == "Test resource not found"
    assert exc.status_code == 404
    assert exc.details["id"] == "test_123"

    exc_dict = exc.to_dict()
    assert exc_dict["code"] == "NOT_FOUND"
    assert exc_dict["message"] == "Test resource not found"

    print("✅ FieldMind异常正确")
    print(f"   code: {exc.error_code.value}")
    print(f"   status: {exc.status_code}")
    print(f"   message: {exc.message}")
    return True


def test_validation_exception():
    """测试7: 验证异常"""
    print("\n" + "="*60)
    print("测试7: 验证异常")
    print("="*60)

    exc = ValidationException(
        message="Invalid email format",
        field="email",
        details={"pattern": "^[a-z]+@[a-z]+\\.[a-z]+$"}
    )

    assert exc.error_code == ErrorCode.VALIDATION_ERROR
    assert exc.field == "email"
    assert exc.status_code == 422

    print("✅ 验证异常正确")
    print(f"   field: {exc.field}")
    print(f"   message: {exc.message}")
    return True


def test_not_found_exception():
    """测试8: 资源不存在异常"""
    print("\n" + "="*60)
    print("测试8: 资源不存在异常")
    print("="*60)

    exc = NotFoundException(
        resource_type="Document",
        resource_id="doc_123"
    )

    assert exc.error_code == ErrorCode.NOT_FOUND
    assert exc.status_code == 404
    assert exc.details["resource_type"] == "Document"
    assert exc.details["resource_id"] == "doc_123"

    print("✅ 资源不存在异常正确")
    print(f"   type: {exc.details['resource_type']}")
    print(f"   id: {exc.details['resource_id']}")
    return True


def test_document_not_found_exception():
    """测试9: 文档不存在异常"""
    print("\n" + "="*60)
    print("测试9: 文档不存在异常")
    print("="*60)

    exc = DocumentNotFoundException(document_id="doc_456")

    assert exc.error_code == ErrorCode.DOCUMENT_NOT_FOUND
    assert exc.status_code == 404
    assert "doc_456" in exc.message
    assert exc.details["document_id"] == "doc_456"

    print("✅ 文档不存在异常正确")
    print(f"   document_id: {exc.details['document_id']}")
    print(f"   message: {exc.message}")
    return True


def test_pagination_edge_cases():
    """测试10: 分页边界情况"""
    print("\n" + "="*60)
    print("测试10: 分页边界情况")
    print("="*60)

    # 空数据
    response1 = paginated_response(
        data=[],
        page=1,
        page_size=20,
        total=0
    )
    assert response1["pagination"]["total_pages"] == 0
    assert response1["pagination"]["has_next"] is False
    print("   ✓ 空数据分页正确")

    # 最后一页
    response2 = paginated_response(
        data=[{"id": "doc_001"}],
        page=5,
        page_size=20,
        total=81
    )
    assert response2["pagination"]["total_pages"] == 5
    assert response2["pagination"]["has_next"] is False
    assert response2["pagination"]["has_prev"] is True
    print("   ✓ 最后一页分页正确")

    # 单页数据
    response3 = paginated_response(
        data=[{"id": "doc_001"}],
        page=1,
        page_size=20,
        total=1
    )
    assert response3["pagination"]["total_pages"] == 1
    assert response3["pagination"]["has_next"] is False
    assert response3["pagination"]["has_prev"] is False
    print("   ✓ 单页数据分页正确")

    print("✅ 分页边界情况正确")
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FieldMind 响应格式测试套件")
    print("="*60)

    tests = [
        ("成功响应", test_success_response),
        ("错误响应", test_error_response),
        ("分页响应", test_paginated_response),
        ("错误码映射", test_error_codes),
        ("错误消息", test_error_messages),
        ("FieldMind异常", test_fieldmind_exception),
        ("验证异常", test_validation_exception),
        ("资源不存在异常", test_not_found_exception),
        ("文档不存在异常", test_document_not_found_exception),
        ("分页边界情况", test_pagination_edge_cases),
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
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
