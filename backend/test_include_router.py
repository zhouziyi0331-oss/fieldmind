#!/usr/bin/env python3
"""测试include_router的实际效果"""
import sys
sys.path.insert(0, 'src')

from fastapi import FastAPI
from app.api import unified_knowledge_graph

print("="*80)
print("测试include_router的实际行为")
print("="*80)

# 创建测试app
app = FastAPI()

print(f"\n注册前:")
print(f"  app.routes数: {len(app.routes)}")
print(f"  router.routes数: {len(unified_knowledge_graph.router.routes)}")
print(f"  router.prefix: {unified_knowledge_graph.router.prefix}")

# 注册
app.include_router(unified_knowledge_graph.router, tags=["测试"])

print(f"\n注册后:")
print(f"  app.routes数: {len(app.routes)}")

# 检查路由详情
api_routes = []
for route in app.routes:
    if hasattr(route, 'path') and '/api/' in route.path:
        api_routes.append(route)
        
print(f"  API routes数: {len(api_routes)}")

if api_routes:
    print(f"\n前5个API路由:")
    for i, route in enumerate(api_routes[:5]):
        methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
        print(f"    {i+1}. {methods:10s} {route.path}")
else:
    print(f"\n❌ 没有找到任何API路由!")
    print(f"\n所有routes:")
    for i, route in enumerate(app.routes):
        if hasattr(route, 'path'):
            print(f"    {i+1}. {route.path}")

# 尝试直接访问router.routes
print(f"\n直接检查router.routes的前3个:")
for i, route in enumerate(unified_knowledge_graph.router.routes[:3]):
    if hasattr(route, 'path'):
        methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
        print(f"    {i+1}. {methods:10s} {route.path}")

print("\n" + "="*80)
print("结论:")
if len(api_routes) >= 20:
    print("✅ include_router工作正常")
else:
    print("❌ include_router没有正确添加路由")
    print("   可能原因:")
    print("   1. router.prefix导致路径不匹配")
    print("   2. FastAPI版本兼容性问题")
    print("   3. 路由对象有问题")

