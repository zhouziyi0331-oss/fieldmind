#!/usr/bin/env python3
"""
API功能验证脚本 - 测试所有16个API端点
"""
import sys
sys.path.insert(0, 'src')

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_all_apis():
    """测试所有API端点"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         API功能验证测试                                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 收集所有API端点
    api_endpoints = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method in ['GET', 'POST']:
                    api_endpoints.append((method, route.path, getattr(route, 'name', 'unknown')))

    print(f"找到 {len(api_endpoints)} 个API端点\n")
    print("="*80)

    success_count = 0
    failed_count = 0
    results = []

    for method, path, name in sorted(api_endpoints):
        # 跳过需要参数的路径
        if '{' in path:
            continue

        try:
            if method == 'GET':
                response = client.get(path)
            elif method == 'POST':
                response = client.post(path, json={})

            status = response.status_code

            if status == 200:
                result = "✅ 成功"
                success_count += 1
            elif status == 404:
                result = "⚠️  404 (路由未实现)"
                failed_count += 1
            elif status == 422:
                result = "⚠️  422 (参数错误)"
                failed_count += 1
            elif status == 500:
                result = "❌ 500 (服务器错误)"
                failed_count += 1
            else:
                result = f"⚠️  {status}"
                failed_count += 1

            results.append({
                'method': method,
                'path': path,
                'status': status,
                'result': result
            })

            print(f"{result} | {method:4} {path}")

        except Exception as e:
            result = f"❌ 异常: {str(e)[:50]}"
            failed_count += 1
            results.append({
                'method': method,
                'path': path,
                'status': 'ERROR',
                'result': result
            })
            print(f"{result} | {method:4} {path}")

    print("\n" + "="*80)
    print(f"\n总结:")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {failed_count}")
    print(f"  成功率: {success_count/(success_count+failed_count)*100:.1f}%")

    # 详细结果
    print("\n详细结果:")
    print("="*80)

    for r in results:
        if r['status'] == 200:
            print(f"✅ {r['method']:4} {r['path']}")

    print("\n需要修复的:")
    print("="*80)
    for r in results:
        if r['status'] != 200:
            print(f"{r['result']} | {r['method']:4} {r['path']}")

if __name__ == "__main__":
    test_all_apis()
