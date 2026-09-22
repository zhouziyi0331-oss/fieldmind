#!/usr/bin/env python3
"""检查实际注册的路由"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.main import app

print("="*80)
print("检查所有已注册的路由")
print("="*80)

# 获取所有路由
all_routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        all_routes.append({
            'path': route.path,
            'methods': list(route.methods) if route.methods else [],
            'name': route.name if hasattr(route, 'name') else 'unknown'
        })

# 按路径排序
all_routes.sort(key=lambda x: x['path'])

# 查找我们关心的路由
targets = [
    '/api/memory',
    '/api/timeline',
    '/api/tables',
    '/api/proposal',
    '/api/photos',
    '/api/v1/super-agents',
    '/api/agent-pipeline',
    '/api/v1/tasks',
    '/api/v1/topic-analysis',
    '/api/v1/sop',
    '/api/v1/chunks-quantification',
    '/api/v1/dashboard-optimized',
    '/api/export',
    '/api/file-summaries',
    '/api/quantification',
    '/api/websocket',
    '/api/monitoring',
]

print(f"\n总路由数: {len(all_routes)}")

print("\n查找目标路由:")
found = 0
for target in targets:
    matching = [r for r in all_routes if r['path'].startswith(target)]
    if matching:
        print(f"  ✅ {target}: 找到 {len(matching)} 个端点")
        found += 1
    else:
        print(f"  ❌ {target}: 未找到")

print(f"\n结果: {found}/{len(targets)} 已注册")

# 显示所有以/api开头的路由（前50个）
print("\n所有API路由（前50个）:")
api_routes = [r for r in all_routes if r['path'].startswith('/api')]
for i, route in enumerate(api_routes[:50], 1):
    methods = ','.join(route['methods']) if route['methods'] else 'ANY'
    print(f"  {i}. {methods:20} {route['path']}")

if len(api_routes) > 50:
    print(f"  ... 还有 {len(api_routes)-50} 个API路由")
