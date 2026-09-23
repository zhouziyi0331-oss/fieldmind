#!/usr/bin/env python3
"""测试FastAPI路由注册"""
import sys
sys.path.insert(0, 'src')

from fastapi import FastAPI
from app.api import unified_knowledge_graph

print("="*80)
print("测试FastAPI路由注册机制")
print("="*80)

# 创建一个测试app
test_app = FastAPI()

print("\n1. 统一知识图谱模块的router信息:")
print(f"   router对象: {unified_knowledge_graph.router}")
print(f"   prefix: {unified_knowledge_graph.router.prefix}")
print(f"   routes数量: {len(unified_knowledge_graph.router.routes)}")

print("\n2. 测试注册到FastAPI:")
test_app.include_router(unified_knowledge_graph.router)

print(f"   注册后test_app的routes数量: {len(test_app.routes)}")

# 统计API路由
api_routes = [r for r in test_app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
print(f"   API路由数量: {len(api_routes)}")

if len(api_routes) > 0:
    print(f"\n3. 前5个API路由:")
    for i, route in enumerate(api_routes[:5]):
        methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
        print(f"   {i+1}. {methods:20s} {route.path}")

print("\n" + "="*80)
print("结论:")
print("="*80)

if len(api_routes) >= 20:
    print("✅ 路由注册机制正常工作")
    print(f"   测试app成功注册了{len(api_routes)}个路由")
    print("\n问题可能在于:")
    print("   1. 实际app.main中的注册时机")
    print("   2. 或者路由统计脚本的问题")
else:
    print("❌ 路由注册有问题")
    print(f"   预期23个路由，实际只有{len(api_routes)}个")

