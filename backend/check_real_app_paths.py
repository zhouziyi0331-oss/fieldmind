#!/usr/bin/env python3
"""检查实际应用中的真实路径"""
import sys
sys.path.insert(0, 'src')

from app.main import app

print("="*80)
print("检查实际应用中的路由路径")
print("="*80)

def get_all_routes_from_app(app):
    """从实际app中获取所有路由"""
    all_routes = []
    
    for route in app.router.routes:
        route_type = type(route).__name__
        
        if route_type == '_IncludedRouter':
            if hasattr(route, 'original_router'):
                original = route.original_router
                prefix_from_context = ''
                if hasattr(route, 'include_context'):
                    prefix_from_context = route.include_context.prefix
                
                for subroute in original.routes:
                    if hasattr(subroute, 'path'):
                        # 正确的路径应该是：context_prefix + subroute.path
                        # subroute.path已经包含了router.prefix
                        full_path = prefix_from_context + subroute.path
                        all_routes.append((subroute, full_path))
        
        elif hasattr(route, 'path'):
            all_routes.append((route, route.path))
    
    return all_routes

routes = get_all_routes_from_app(app)
api_routes = [(r, p) for r, p in routes if '/api/' in p]

print(f"\n总API路由数: {len(api_routes)}")

# 按模块分组
from collections import defaultdict
grouped = defaultdict(list)

for route, path in api_routes:
    # 提取模块名
    if '/api/kg' in path:
        grouped['知识图谱'].append((route, path))
    elif '/api/documents' in path:
        grouped['文档处理'].append((route, path))
    elif '/api/rag' in path:
        grouped['RAG检索'].append((route, path))
    elif '/api/chat' in path:
        grouped['聊天对话'].append((route, path))
    elif '/api/analysis' in path:
        grouped['分析'].append((route, path))
    elif '/api/projects' in path:
        grouped['项目管理'].append((route, path))
    elif '/api/skills' in path:
        grouped['技能管理'].append((route, path))
    elif '/api/reports' in path:
        grouped['报告生成'].append((route, path))
    elif '/api/tools' in path:
        grouped['工具'].append((route, path))
    else:
        grouped['其他'].append((route, path))

print(f"\n统一模块路由分布:")
total_unified = 0
for module, routes_list in sorted(grouped.items()):
    if module != '其他':
        print(f"  {module:12s} {len(routes_list):3d} 个路由")
        total_unified += len(routes_list)
        # 显示前2个路径
        for i, (route, path) in enumerate(routes_list[:2]):
            methods = ','.join(route.methods) if hasattr(route, 'methods') else ''
            print(f"      {methods:10s} {path}")

print(f"\n统一模块总计: {total_unified} 个路由")
print(f"其他路由: {len(grouped.get('其他', []))} 个")

print(f"\n" + "="*80)
print("🎯 最终结论")
print("="*80)

if total_unified >= 100:
    print(f"✅ 成功！统一模块的{total_unified}个端点都已正确注册")
    print(f"   之前的统计方法有问题，实际端点都在")
elif total_unified > 0:
    print(f"⚠️  部分成功：发现{total_unified}个统一模块端点")
    print(f"   但预期应该有131个")
else:
    print(f"❌ 失败：统一模块端点仍然没有被识别")

