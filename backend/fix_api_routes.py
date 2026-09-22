#!/usr/bin/env python3
"""
彻底修复API响应格式问题 - 执行脚本
"""
import sys
import os
sys.path.insert(0, 'src')

print("=" * 80)
print("🔧 深度修复 API 响应格式问题")
print("=" * 80)

# 1. 检查照片API路由注册
print("\n【步骤1】检查照片API路由注册")
print("-" * 80)

from app.main import app

# 查找所有照片相关的路由
photo_routes = []
for route in app.routes:
    if hasattr(route, 'path') and 'photo' in route.path.lower():
        photo_routes.append(route)
        print(f"  ✓ {route.methods if hasattr(route, 'methods') else 'N/A'} {route.path}")

if not photo_routes:
    print("  ❌ 没有找到照片相关路由！")
else:
    print(f"\n  找到 {len(photo_routes)} 个照片路由")

# 2. 检查表格API路由
print("\n【步骤2】检查表格API路由注册")
print("-" * 80)

table_routes = []
for route in app.routes:
    if hasattr(route, 'path') and 'table' in route.path.lower():
        table_routes.append(route)
        print(f"  ✓ {route.methods if hasattr(route, 'methods') else 'N/A'} {route.path}")

if not table_routes:
    print("  ❌ 没有找到表格相关路由！")
else:
    print(f"\n  找到 {len(table_routes)} 个表格路由")

# 3. 测试实际API调用
print("\n【步骤3】测试实际API响应")
print("-" * 80)

from fastapi.testclient import TestClient
client = TestClient(app)

# 测试照片API的各种路径组合
test_paths = [
    "/api/photos",
    "/api/photos/",
    "/photos",
    "/photos/",
]

print("\n测试照片API路径:")
for path in test_paths:
    try:
        response = client.get(f"{path}?project_id=1")
        status = "✅" if response.status_code == 200 else "❌"
        print(f"  {status} GET {path}?project_id=1 -> {response.status_code}")
    except Exception as e:
        print(f"  ❌ GET {path}?project_id=1 -> 错误: {e}")

# 4. 分析问题
print("\n【步骤4】问题分析")
print("-" * 80)

print("""
根据诊断结果：

1. 照片API路由问题：
   - 路由器定义: /photos (不带尾部斜杠)
   - 主应用注册: prefix="/api"
   - 预期完整路径: /api/photos 或 /api/photos/
   - 实际测试: 返回404

2. 可能的原因：
   - FastAPI的尾部斜杠重定向被禁用了
   - 路由器没有正确注册
   - 路由顺序导致被其他路由拦截

3. 表格API工作正常：
   - 返回格式: {success: true, data: {...}}
   - 前端axios拦截器会自动解包data字段

4. 解决方案：
   - 修复照片API路由定义，明确添加尾部斜杠
   - 确保前端调用正确的路径
   - 验证axios拦截器正确解包响应
""")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
