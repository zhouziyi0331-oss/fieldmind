#!/usr/bin/env python3
"""第5步：识别并清理大型v1模块"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第5步：识别可删除的大型v1模块")
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

# 筛选大型模块（>=25个端点）和剩余模块
large_modules = {k: v for k, v in v1_modules.items() if len(v) >= 25}
remaining_modules = {k: v for k, v in v1_modules.items() if len(v) > 0}

print(f"\n找到 {len(large_modules)} 个大型v1模块 (>=25个端点):")
print("-"*80)

sorted_large = sorted(large_modules.items(), key=lambda x: len(x[1]), reverse=True)
for module, routes in sorted_large:
    print(f"  v1/{module:30s} {len(routes):3d} 个端点")

total_large = sum(len(routes) for _, routes in sorted_large)
print(f"\n  大型模块总计: {total_large} 个端点")

# 统计所有剩余的v1模块
print(f"\n" + "="*80)
print("📊 所有剩余v1模块统计")
print("="*80)

sorted_all = sorted(remaining_modules.items(), key=lambda x: len(x[1]), reverse=True)
print(f"\n剩余v1模块总数: {len(sorted_all)}")
print(f"剩余端点总数: {sum(len(routes) for _, routes in sorted_all)}")

print(f"\n前20个模块:")
for module, routes in sorted_all[:20]:
    print(f"  v1/{module:30s} {len(routes):3d} 个端点")

# 评估可删除的模块
print(f"\n" + "="*80)
print("📋 评估策略")
print("="*80)

# 已删除的模块（用于对比）
already_deleted = [
    'chat-enhancement', 'analysis', 'topic-analysis',  # 第1步
    'workflows',  # 第2步
    'distillation', 'hermes', 'lineage', 'feeding',  # 第3步
    'api-management', 'annotation', 'tagging', 'sop',  # 第3步
    'workbench', 'dashboard'  # 第4步
]

# 核心保留模块
core_modules = ['auth', 'users', 'permissions']

# 分类
deletable = []
review_needed = []

for module, routes in sorted_all[:30]:
    if module in already_deleted:
        continue
    
    count = len(routes)
    
    # 判断逻辑
    if module in core_modules:
        review_needed.append({
            'module': module,
            'count': count,
            'reason': '核心功能，需要保留'
        })
    elif module == 'projects':
        review_needed.append({
            'module': module,
            'count': count,
            'reason': '复杂模块，需要仔细评估'
        })
    elif count >= 20:
        deletable.append({
            'module': module,
            'count': count,
            'reason': f'大型v1模块，{count}个端点可批量删除'
        })
    elif count >= 10:
        deletable.append({
            'module': module,
            'count': count,
            'reason': f'中型v1模块，{count}个端点可删除'
        })
    elif count >= 5:
        deletable.append({
            'module': module,
            'count': count,
            'reason': f'小型v1模块，{count}个端点可删除'
        })

print(f"\n【可批量删除】 ({len(deletable)}个模块)")
print("-"*80)
deletable_total = 0
for m in sorted(deletable, key=lambda x: x['count'], reverse=True)[:15]:
    print(f"  ❌ v1/{m['module']:30s} {m['count']:3d} 个端点")
    deletable_total += m['count']

print(f"\n  前15个模块总计: {deletable_total} 个端点")

print(f"\n【需要评估/保留】 ({len(review_needed)}个模块)")
print("-"*80)
for m in review_needed:
    print(f"  ⚠️  v1/{m['module']:30s} {m['count']:3d} 个端点 - {m['reason']}")

# 生成执行计划
plan = {
    'step': '第5步',
    'description': '批量删除大型和剩余v1模块',
    'deletable': deletable[:15],  # 前15个
    'review': review_needed,
    'total_deletable': deletable_total,
    'expected_result': 635 - deletable_total
}

with open('step5_execution_plan.json', 'w', encoding='utf-8') as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

print(f"\n" + "="*80)
print("💡 第5步执行计划")
print("="*80)

print(f"\n目标: 批量删除前15个v1模块")
print(f"  • 模块数: {len(deletable[:15])} 个")
print(f"  • 端点数: {deletable_total} 个")

print(f"\n预期结果:")
print(f"  • 当前: 635 个端点")
print(f"  • 删除后: {635 - deletable_total} 个端点")
print(f"  • 累计减少: {158 + deletable_total} 个端点")
print(f"  • 完成进度: {((158 + deletable_total) / 373 * 100):.1f}%")

if 635 - deletable_total < 420:
    print(f"\n  🎉 预计可以达到420个端点目标！")
elif 635 - deletable_total < 500:
    print(f"\n  ✅ 预计可以突破500端点大关！")

print(f"\n✅ 执行计划已保存到: step5_execution_plan.json")

