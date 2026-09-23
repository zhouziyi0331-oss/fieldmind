#!/usr/bin/env python3
"""第2步：分析v1/projects端点"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第2步：分析v1/projects端点")
print("="*80)

# 读取端点清单
with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

# 找到所有v1/projects端点
v1_routes = inventory['categories']['旧版API']['endpoints']
v1_projects_routes = [r for r in v1_routes if '/api/v1/projects' in r['path']]

print(f"\n找到 {len(v1_projects_routes)} 个v1/projects端点")
print("-"*80)

# 按功能分组
from collections import defaultdict
grouped = defaultdict(list)

for route in v1_projects_routes:
    path = route['path']
    # 提取功能
    if '/contexts' in path:
        grouped['上下文管理'].append(route)
    elif '/documents' in path:
        grouped['文档管理'].append(route)
    elif '/members' in path:
        grouped['成员管理'].append(route)
    elif '/settings' in path:
        grouped['设置管理'].append(route)
    elif '/stats' in path or '/statistics' in path:
        grouped['统计信息'].append(route)
    elif '/export' in path:
        grouped['导出功能'].append(route)
    elif path.endswith('/projects') or path.endswith('/projects/'):
        grouped['项目CRUD'].append(route)
    else:
        grouped['其他功能'].append(route)

print("\nv1/projects功能分布:")
for func, routes in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n【{func}】 ({len(routes)} 个端点)")
    for route in routes[:3]:
        print(f"  {route['methods']:15s} {route['path']}")
    if len(routes) > 3:
        print(f"  ... 还有 {len(routes) - 3} 个")

# 对比统一项目管理模块
print(f"\n" + "="*80)
print("📊 对比统一项目管理模块")
print("="*80)

unified_routes = inventory['categories']['统一模块']['endpoints']
unified_projects_routes = [r for r in unified_routes if '/api/projects' in r['path']]

print(f"\n统一项目管理模块: {len(unified_projects_routes)} 个端点")
print(f"v1项目模块: {len(v1_projects_routes)} 个端点")
print(f"差异: {len(v1_projects_routes) - len(unified_projects_routes)} 个端点")

# 识别缺失的功能
print(f"\n可能缺失的功能:")
unified_paths = set([r['path'] for r in unified_projects_routes])

for func, routes in grouped.items():
    # 检查统一模块中是否有类似功能
    has_similar = False
    for route in routes:
        v1_path = route['path']
        # 转换为统一模块路径
        unified_equivalent = v1_path.replace('/api/v1/projects', '/api/projects')
        if unified_equivalent in unified_paths:
            has_similar = True
            break
    
    if not has_similar:
        print(f"  ⚠️  {func}: 可能需要补充")

# 生成迁移计划
migration_plan = {
    'step': '第2步',
    'module': 'v1/projects',
    'total_endpoints': len(v1_projects_routes),
    'unified_endpoints': len(unified_projects_routes),
    'actions': []
}

for func, routes in grouped.items():
    migration_plan['actions'].append({
        'function': func,
        'count': len(routes),
        'routes': [{'methods': r['methods'], 'path': r['path']} for r in routes]
    })

with open('step2_v1_projects_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(migration_plan, f, indent=2, ensure_ascii=False)

print(f"\n✅ 分析结果已保存到: step2_v1_projects_analysis.json")

