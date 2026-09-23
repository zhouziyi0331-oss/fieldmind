#!/usr/bin/env python3
"""第1步：识别明确重复的v1端点"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第1步：识别明确已迁移的v1端点")
print("="*80)

# 读取端点清单
with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

# 统一模块映射
unified_modules = {
    'documents': '/api/documents',
    'analysis': '/api/analysis',
    'reports': '/api/reports',
    'chat': '/api/chat',
    'rag': '/api/rag',
    'projects': '/api/projects',
    'skills': '/api/skills',
    'kg': '/api/kg',
    'tools': '/api/tools'
}

# 查找v1中已有统一模块的端点
v1_routes = inventory['categories']['旧版API']['endpoints']

duplicates = {
    'documents': [],
    'analysis': [],
    'reports': [],
    'chat': [],
}

for route in v1_routes:
    path = route['path']
    for module_name, unified_prefix in unified_modules.items():
        if f'/api/v1/{module_name}' in path and module_name in duplicates:
            duplicates[module_name].append(route)

print("\n找到的重复端点:")
print("-"*80)

total_duplicates = 0
for module, routes in duplicates.items():
    if routes:
        print(f"\n【{module}】 - {len(routes)} 个v1端点")
        total_duplicates += len(routes)
        for route in routes[:5]:  # 显示前5个
            print(f"  ❌ {route['methods']:10s} {route['path']}")
        if len(routes) > 5:
            print(f"  ... 还有 {len(routes) - 5} 个")

print(f"\n" + "="*80)
print(f"📊 统计")
print("="*80)
print(f"找到明确重复的端点: {total_duplicates} 个")

# 保存删除列表
delete_list = {
    'step': '第1步',
    'description': '删除明确已迁移的v1端点',
    'to_delete': []
}

for module, routes in duplicates.items():
    if routes:
        delete_list['to_delete'].append({
            'module': module,
            'unified_prefix': unified_modules[module],
            'v1_routes': [
                {
                    'methods': r['methods'],
                    'path': r['path'],
                    'name': r['name']
                } for r in routes
            ],
            'count': len(routes)
        })

with open('step1_delete_list.json', 'w', encoding='utf-8') as f:
    json.dump(delete_list, f, indent=2, ensure_ascii=False)

print(f"\n✅ 删除列表已保存到: step1_delete_list.json")

