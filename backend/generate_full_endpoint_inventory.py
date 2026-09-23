#!/usr/bin/env python3
"""生成完整的端点清单"""
import sys
import json
sys.path.insert(0, 'src')

from app.main import app
from collections import defaultdict

print("="*80)
print("📋 生成完整端点清单")
print("="*80)

def get_all_routes_from_app(app):
    """从app中获取所有路由"""
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
                        full_path = prefix_from_context + subroute.path
                        all_routes.append({
                            'route': subroute,
                            'path': full_path,
                            'methods': list(subroute.methods) if hasattr(subroute, 'methods') else [],
                            'name': subroute.name if hasattr(subroute, 'name') else '',
                        })
        
        elif hasattr(route, 'path'):
            all_routes.append({
                'route': route,
                'path': route.path,
                'methods': list(route.methods) if hasattr(route, 'methods') else [],
                'name': route.name if hasattr(route, 'name') else '',
            })
    
    return all_routes

# 获取所有路由
all_routes = get_all_routes_from_app(app)
api_routes = [r for r in all_routes if '/api/' in r['path']]

print(f"\n总API端点数: {len(api_routes)}")

# 分类
categories = {
    '统一模块': {
        'prefixes': ['/api/kg', '/api/documents', '/api/rag', '/api/chat', 
                    '/api/analysis', '/api/projects', '/api/skills', 
                    '/api/reports', '/api/tools'],
        'routes': []
    },
    '旧版API': {
        'prefixes': ['/api/v1/', '/api/v2/', '/api/v3/', '-old', '-v1', '-v2', '-v3'],
        'routes': []
    },
    '核心功能': {
        'prefixes': ['/api/auth', '/api/users', '/api/runtime'],
        'routes': []
    },
    '未分类': {
        'prefixes': [],
        'routes': []
    }
}

# 分类路由
for route_info in api_routes:
    path = route_info['path']
    categorized = False
    
    for cat_name, cat_info in categories.items():
        if cat_name == '未分类':
            continue
        for prefix in cat_info['prefixes']:
            if prefix in path:
                cat_info['routes'].append(route_info)
                categorized = True
                break
        if categorized:
            break
    
    if not categorized:
        categories['未分类']['routes'].append(route_info)

# 打印分类统计
print(f"\n📊 端点分类统计:")
for cat_name, cat_info in categories.items():
    print(f"  {cat_name:12s} {len(cat_info['routes']):4d} 个端点")

# 生成详细清单
inventory = {
    'total_endpoints': len(api_routes),
    'target': 420,
    'to_remove': len(api_routes) - 420,
    'categories': {}
}

for cat_name, cat_info in categories.items():
    inventory['categories'][cat_name] = {
        'count': len(cat_info['routes']),
        'endpoints': []
    }
    
    for route_info in cat_info['routes']:
        methods_str = ','.join(route_info['methods'])
        inventory['categories'][cat_name]['endpoints'].append({
            'methods': methods_str,
            'path': route_info['path'],
            'name': route_info['name'],
            'action': 'KEEP' if cat_name in ['统一模块', '核心功能'] else 'REVIEW'
        })

# 保存到文件
with open('endpoint_inventory.json', 'w', encoding='utf-8') as f:
    json.dump(inventory, f, indent=2, ensure_ascii=False)

print(f"\n✅ 详细清单已保存到: endpoint_inventory.json")

# 生成人类可读的报告
print(f"\n" + "="*80)
print("📋 详细端点清单")
print("="*80)

for cat_name, cat_info in categories.items():
    print(f"\n【{cat_name}】 ({len(cat_info['routes'])} 个端点)")
    
    # 按路径排序
    sorted_routes = sorted(cat_info['routes'], key=lambda x: x['path'])
    
    # 显示前10个
    for i, route_info in enumerate(sorted_routes[:10]):
        methods_str = ','.join(route_info['methods'])
        action = 'KEEP' if cat_name in ['统一模块', '核心功能'] else 'REVIEW'
        print(f"  [{action:6s}] {methods_str:15s} {route_info['path']}")
    
    if len(sorted_routes) > 10:
        print(f"  ... 还有 {len(sorted_routes) - 10} 个端点")

print(f"\n" + "="*80)
print("🎯 清理建议")
print("="*80)

print(f"\n保留 (KEEP):")
print(f"  - 统一模块: {len(categories['统一模块']['routes'])} 个端点")
print(f"  - 核心功能: {len(categories['核心功能']['routes'])} 个端点")
print(f"  小计: {len(categories['统一模块']['routes']) + len(categories['核心功能']['routes'])} 个")

print(f"\n需要审查 (REVIEW):")
print(f"  - 旧版API: {len(categories['旧版API']['routes'])} 个端点")
print(f"  - 未分类: {len(categories['未分类']['routes'])} 个端点")
print(f"  小计: {len(categories['旧版API']['routes']) + len(categories['未分类']['routes'])} 个")

print(f"\n需要删除数量: {len(api_routes) - 420} 个端点")

