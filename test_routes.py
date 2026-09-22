#!/usr/bin/env python3
"""测试路由注册"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

# 导入所有必要模块
from fastapi import FastAPI
from app.api.v1 import auth, project_workflow

# 创建测试应用
test_app = FastAPI(title="Test")

# 注册路由（模拟main.py中的代码）
test_app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
test_app.include_router(project_workflow.router, prefix="/api/v1", tags=["项目工作流"])

# 检查路由
print("测试应用路由注册:")
for route in test_app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path}")

print(f"\n总计: {len([r for r in test_app.routes if hasattr(r, 'path')])} 条路由")

# 现在导入真实的main.app
print("\n=== 真实main.app路由 ===")
from app.main import app

print(f"app对象ID: {id(app)}")
print(f"app.routes数量: {len(list(app.routes))}")

v1_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/v1' in r.path]
print(f"/api/v1路由数: {len(v1_routes)}")

if v1_routes:
    for r in v1_routes[:5]:
        print(f"  {r.path}")
else:
    print("  (无)")
    print("\n所有路由:")
    for r in app.routes:
        if hasattr(r, 'path'):
            print(f"  {r.path}")
