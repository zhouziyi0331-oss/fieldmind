#!/usr/bin/env python3
"""
深度诊断API响应格式问题
测试照片、表格、文档API的实际响应
"""
import sys
import os
sys.path.insert(0, 'src')

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

print("=" * 80)
print("深度诊断 API 响应格式")
print("=" * 80)

# 测试1：照片API
print("\n【测试1】照片API - GET /api/photos/")
print("-" * 80)
try:
    response = client.get("/api/photos/?project_id=1")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应体:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"错误: {e}")

# 测试2：表格API
print("\n【测试2】表格API - GET /api/v1/projects/1/tables/")
print("-" * 80)
try:
    response = client.get("/api/v1/projects/1/tables/")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应体:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"错误: {e}")

# 测试3：文档列表API
print("\n【测试3】文档API - GET /api/v1/projects/1/documents/")
print("-" * 80)
try:
    response = client.get("/api/v1/projects/1/documents/")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应体:")
    result = response.json()
    print(f"响应类型: {type(result)}")
    if isinstance(result, dict):
        print(f"响应keys: {result.keys()}")
        if 'data' in result:
            print(f"data类型: {type(result['data'])}")
            if isinstance(result['data'], dict):
                print(f"data keys: {result['data'].keys()}")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
except Exception as e:
    print(f"错误: {e}")

# 测试4：检查success_response格式
print("\n【测试4】检查 success_response 函数输出")
print("-" * 80)
from app.schemas.response import success_response, error_response

test_data = {
    "photos": [{"id": 1, "filename": "test.jpg"}],
    "total": 1
}
result = success_response(data=test_data, message="测试消息")
print("success_response 输出:")
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
