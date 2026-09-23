#!/usr/bin/env python3
"""修复路由发现逻辑"""
import sys
sys.path.insert(0, 'src')

from fastapi import FastAPI
from app.api import unified_knowledge_graph

print("="*80)
print("正确的路由发现方法")
print("="*80)

app = FastAPI()
app.include_router(unified_knowledge_graph.router, tags=["测试"])

# 正确的遍历方法
def get_all_routes_correct(app):
    """正确递归获取所有路由"""
    all_routes = []
    
    for route in app.router.routes:
        route_type = type(route).__name__
        
        # 检查是否是_IncludedRouter
        if route_type == '_IncludedRouter':
            # 访问original_router
            if hasattr(route, 'original_router'):
                original = route.original_router
                # 获取context中的prefix
                prefix = ''
                if hasattr(route, 'include_context'):
                    prefix = route.include_context.prefix
                
                # 遍历original_router中的routes
                for subroute in original.routes:
                    if hasattr(subroute, 'path'):
                        full_path = prefix + original.prefix + subroute.path
                        all_routes.append((subroute, full_path))
        
        # 普通路由
        elif hasattr(route, 'path'):
            all_routes.append((route, route.path))
    
    return all_routes

routes = get_all_routes_correct(app)
print(f"\n发现的路由总数: {len(routes)}")

api_routes = [(r, p) for r, p in routes if '/api/' in p]
print(f"API路由数: {len(api_routes)}")

if api_routes:
    print(f"\n前10个API路由:")
    for i, (route, path) in enumerate(api_routes[:10]):
        methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
        print(f"  {i+1:2d}. {methods:10s} {path}")

print("\n" + "="*80)
if len(api_routes) >= 20:
    print("✅ 成功！路由都在那里，只是需要正确的方法来发现它们")
else:
    print("❌ 还是有问题")

