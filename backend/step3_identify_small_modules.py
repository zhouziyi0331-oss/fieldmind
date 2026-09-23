#!/usr/bin/env python3
"""第3步：识别可批量删除的小型v1模块"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第3步：识别可批量删除的小型v1模块")
print("="*80)

# 读取端点清单
with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

# 获取所有v1端点
v1_routes = inventory['categories']['旧版API']['endpoints']

# 按模块分组
from collections import defaultdict
v1_modules = defaultdict(list)

for route in v1_routes:
    path = route['path']
    if '/api/v1/' in path:
        parts = path.split('/')
        if len(parts) >= 4:
            module = parts[3]
            v1_modules[module].append(route)

# 筛选小型模块（<20个端点）
small_modules = {k: v for k, v in v1_modules.items() if len(v) < 20 and len(v) > 0}

print(f"\n找到 {len(small_modules)} 个小型v1模块 (<20个端点):")
print("-"*80)

# 按端点数排序
sorted_modules = sorted(small_modules.items(), key=lambda x: len(x[1]), reverse=True)

total_endpoints = 0
for module, routes in sorted_modules[:20]:
    count = len(routes)
    total_endpoints += count
    print(f"  v1/{module:30s} {count:2d} 个端点")

print(f"\n  前20个小模块总计: {total_endpoints} 个端点")

# 识别可以删除的模块
print(f"\n" + "="*80)
print("📋 分类小型模块")
print("="*80)

# 已有统一模块的
has_unified = ['documents', 'rag', 'chat', 'analysis', 'projects', 'skills', 'reports']

deletable = []
need_review = []

for module, routes in sorted_modules:
    if module in has_unified:
        deletable.append({'module': module, 'count': len(routes), 'reason': '已有统一模块'})
    elif any(keyword in module for keyword in ['old', 'test', 'demo', 'deprecated']):
        deletable.append({'module': module, 'count': len(routes), 'reason': '测试/废弃模块'})
    else:
        need_review.append({'module': module, 'count': len(routes)})

print(f"\n【可立即删除】 ({len(deletable)}个模块)")
for m in deletable:
    print(f"  ❌ v1/{m['module']:30s} {m['count']:2d} 个端点 - {m['reason']}")

print(f"\n【需要审查】 ({len(need_review)}个模块, 前15个)")
for m in need_review[:15]:
    print(f"  ⚠️  v1/{m['module']:30s} {m['count']:2d} 个端点")

# 查找这些模块的注册
print(f"\n" + "="*80)
print("🔍 查找注册位置")
print("="*80)

with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找前10个小模块的注册
target_modules = [module for module, routes in sorted_modules[:10]]

registrations = []
for i, line in enumerate(lines, 1):
    if 'include_router' in line and '/api/v1/' in line:
        for module in target_modules:
            # 检查各种可能的格式
            if f'v1/{module}' in line or f'v1.{module}' in line or module in line:
                registrations.append({
                    'line': i,
                    'module': module,
                    'content': line.strip()
                })

print(f"\n找到 {len(registrations)} 个注册:")
for reg in registrations[:10]:
    print(f"  第{reg['line']}行: v1/{reg['module']}")
    print(f"    {reg['content'][:80]}")

# 保存批量删除计划
batch_plan = {
    'step': '第3步',
    'description': '批量删除小型v1模块',
    'deletable_modules': deletable,
    'review_modules': need_review[:15],
    'total_deletable_endpoints': sum(m['count'] for m in deletable),
    'registrations': registrations
}

with open('step3_batch_delete_plan.json', 'w', encoding='utf-8') as f:
    json.dump(batch_plan, f, indent=2, ensure_ascii=False)

print(f"\n" + "="*80)
print("💡 第3步执行计划")
print("="*80)

print(f"\n可立即删除 (已有统一模块):")
print(f"  • 总模块数: {len(deletable)} 个")
print(f"  • 总端点数: {sum(m['count'] for m in deletable)} 个")

print(f"\n需要逐个审查的模块:")
print(f"  • workbench, audit, dashboard, learning等")
print(f"  • 建议: 逐个评估业务价值")

print(f"\n✅ 批量删除计划已保存到: step3_batch_delete_plan.json")

