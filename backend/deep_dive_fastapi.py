#!/usr/bin/env python3
"""深入研究FastAPI路由机制"""
import sys
sys.path.insert(0, 'src')

from fastapi import FastAPI
from app.api import unified_knowledge_graph

print("="*80)
print("深入研究FastAPI路由机制")
print("="*80)

app = FastAPI()

print(f"\n1. 注册前app的router结构:")
print(f"   app.router: {app.router}")
print(f"   app.router.routes: {len(app.router.routes)}")

# 注册
app.include_router(unified_knowledge_graph.router, tags=["测试"])

print(f"\n2. 注册后app的router结构:")
print(f"   app.router.routes: {len(app.router.routes)}")

# 检查新增的route
new_route = app.router.routes[-1]
print(f"\n3. 新增的route:")
print(f"   类型: {type(new_route)}")
print(f"   对象: {new_route}")

# 如果是Mount或Router类型
if hasattr(new_route, 'routes'):
    print(f"   这个route本身包含routes: {len(new_route.routes)}")
    print(f"   前3个子路由:")
    for i, subroute in enumerate(list(new_route.routes)[:3]):
        if hasattr(subroute, 'path'):
            methods = ','.join(subroute.methods) if hasattr(subroute, 'methods') else ''
            print(f"     {i+1}. {methods:10s} {subroute.path}")

# 尝试获取所有实际的端点
def get_all_routes(router, prefix=''):
    routes = []
    for route in router.routes:
        if hasattr(route, 'routes'):  # 嵌套router
            routes.extend(get_all_routes(route, prefix + getattr(route, 'path', '')))
        elif hasattr(route, 'path'):
            full_path = prefix + route.path
            routes.append((route, full_path))
    return routes

all_routes = get_all_routes(app.router)
print(f"\n4. 递归获取所有实际路由:")
print(f"   总计: {len(all_routes)} 个路由")

api_routes = [r for r in all_routes if '/api/' in r[1]]
print(f"   API路由: {len(api_routes)} 个")

if api_routes:
    print(f"\n   前5个API路由:")
    for i, (route, path) in enumerate(api_routes[:5]):
        methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
        print(f"     {i+1}. {methods:10s} {path}")

print("\n" + "="*80)
print("关键发现:")
print("="*80)
print("FastAPI的include_router会创建一个嵌套的router结构")
print("需要递归遍历才能获取所有实际端点")

