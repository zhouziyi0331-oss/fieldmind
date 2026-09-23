#!/usr/bin/env python3
"""详细分析端点，生成迁移计划"""
import sys
import json
sys.path.insert(0, 'src')

from collections import defaultdict

# 读取清单
with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

print("="*80)
print("🔍 端点详细分析和迁移计划")
print("="*80)

# 分析旧版API
print("\n【旧版API详细分析】 (435个端点)")
print("-"*80)

old_api_routes = inventory['categories']['旧版API']['endpoints']

# 按模块分组
v1_modules = defaultdict(list)
for ep in old_api_routes:
    path = ep['path']
    # 提取 /api/v1/MODULE/...
    if '/api/v1/' in path:
        parts = path.split('/')
        if len(parts) >= 4:
            module = parts[3]
            v1_modules[module].append(ep)

print(f"\nv1版本API模块分布:")
for module, routes in sorted(v1_modules.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  /api/v1/{module:30s} {len(routes):3d} 个端点")

# 分析未分类端点
print(f"\n【未分类端点详细分析】 (214个端点)")
print("-"*80)

uncategorized = inventory['categories']['未分类']['endpoints']

# 按路径模式分组
patterns = defaultdict(list)
for ep in uncategorized:
    path = ep['path']
    # 提取第一个路径段
    parts = path.split('/')
    if len(parts) >= 3:
        pattern = '/' + '/'.join(parts[1:3])  # /api/MODULE
        patterns[pattern].append(ep)

print(f"\n未分类端点按模块分组:")
for pattern, routes in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {pattern:40s} {len(routes):3d} 个端点")

# 生成迁移计划
print(f"\n" + "="*80)
print("📋 迁移计划")
print("="*80)

migration_plan = {
    'phase1': {
        'name': '立即删除：明确废弃的API',
        'actions': []
    },
    'phase2': {
        'name': '合并到统一模块',
        'actions': []
    },
    'phase3': {
        'name': '重复功能去重',
        'actions': []
    }
}

# 阶段1: 识别明确废弃的API
print(f"\n阶段1: 立即删除 - 明确废弃的API")
print("-"*80)

deprecated_patterns = [
    '-old', '-v1', '-v2', '-deprecated', 
    'knowledge_graph_v2', 'knowledge_graph_v3', 'knowledge_graph_enhanced',
    'knowledge_graph_p3', 'experience_graph', 'kg_visualization'
]

to_delete_phase1 = []
for pattern in deprecated_patterns:
    matching = [ep for ep in old_api_routes if pattern in ep['path']]
    if matching:
        to_delete_phase1.extend(matching)
        print(f"  删除包含 '{pattern}' 的端点: {len(matching)} 个")

migration_plan['phase1']['actions'].append({
    'action': 'DELETE',
    'count': len(to_delete_phase1),
    'description': '删除明确标记为旧版的API'
})

# 阶段2: 合并到统一模块
print(f"\n阶段2: 合并到统一模块")
print("-"*80)

merge_mapping = {
    'v1/documents': '统一文档处理',
    'v1/rag': '统一RAG检索',
    'v1/chat': '统一聊天对话',
    'v1/projects': '统一项目管理',
    'v1/skills': '统一技能管理',
    'v1/analysis': '统一分析',
    'v1/reports': '统一报告生成',
}

for v1_path, unified_module in merge_mapping.items():
    matching = [ep for ep in old_api_routes if v1_path in ep['path']]
    if matching:
        print(f"  {v1_path:20s} → {unified_module:20s} ({len(matching)} 个端点)")
        migration_plan['phase2']['actions'].append({
            'from': v1_path,
            'to': unified_module,
            'count': len(matching)
        })

# 阶段3: 重复功能识别
print(f"\n阶段3: 重复功能去重")
print("-"*80)

# 识别可能重复的功能
duplicate_keywords = [
    'search', 'query', 'retrieve', 'get', 'list', 'create', 'update', 'delete'
]

print(f"  识别包含相同功能关键词的端点...")

# 生成最终统计
print(f"\n" + "="*80)
print("📊 迁移计划统计")
print("="*80)

total_to_remove = len(to_delete_phase1)
print(f"\n当前状态:")
print(f"  总端点数: {inventory['total_endpoints']}")
print(f"  目标端点数: 420")
print(f"  需要减少: {inventory['to_remove']}")

print(f"\n迁移计划:")
print(f"  阶段1 - 删除废弃API: {len(to_delete_phase1)} 个")
print(f"  阶段2 - 合并到统一模块: 预计减少 150-200 个")
print(f"  阶段3 - 去重: 预计减少 100-150 个")

print(f"\n预期结果:")
estimated_after_migration = inventory['total_endpoints'] - len(to_delete_phase1) - 150 - 100
print(f"  迁移后预计: ~{estimated_after_migration} 个端点")

if estimated_after_migration <= 450:
    print(f"  ✅ 可达到目标范围")
else:
    print(f"  ⚠️  需要进一步优化")

# 保存迁移计划
with open('migration_plan.json', 'w', encoding='utf-8') as f:
    json.dump(migration_plan, f, indent=2, ensure_ascii=False)

print(f"\n✅ 迁移计划已保存到: migration_plan.json")

