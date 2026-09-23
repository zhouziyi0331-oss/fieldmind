#!/usr/bin/env python3
"""第4步：识别可删除的中型v1模块"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第4步：识别可删除的中型v1模块")
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

# 筛选中型模块（15-25个端点）
medium_modules = {k: v for k, v in v1_modules.items() if 15 <= len(v) <= 25}

print(f"\n找到 {len(medium_modules)} 个中型v1模块 (15-25个端点):")
print("-"*80)

sorted_modules = sorted(medium_modules.items(), key=lambda x: len(x[1]), reverse=True)

for module, routes in sorted_modules:
    print(f"  v1/{module:30s} {len(routes):2d} 个端点")

total = sum(len(routes) for _, routes in sorted_modules)
print(f"\n  中型模块总计: {total} 个端点")

# 评估每个模块
print(f"\n" + "="*80)
print("📋 评估中型模块")
print("="*80)

evaluation = {
    'workbench': {
        'count': 19,
        'type': '工作台/前端展示',
        'risk': '低',
        'action': '可删除',
        'reason': '前端展示功能，可由新前端替代'
    },
    'audit': {
        'count': 16,
        'type': '审计日志',
        'risk': '中',
        'action': '保留',
        'reason': '审计是重要的合规功能'
    },
    'dashboard': {
        'count': 16,
        'type': '仪表板',
        'risk': '低',
        'action': '可删除',
        'reason': '仪表板展示，可由统一分析模块替代'
    },
    'learning': {
        'count': 15,
        'type': '学习引擎',
        'risk': '中',
        'action': '审查',
        'reason': '学习功能可能仍在使用'
    },
    'agents': {
        'count': 15,
        'type': 'Agent管理',
        'risk': '中',
        'action': '审查',
        'reason': 'Agent是核心功能，需要评估'
    }
}

deletable = []
keep = []

for module, routes in sorted_modules:
    if module in evaluation:
        eval_info = evaluation[module]
        if eval_info['action'] == '可删除':
            deletable.append({
                'module': module,
                'count': len(routes),
                'type': eval_info['type'],
                'reason': eval_info['reason']
            })
        else:
            keep.append({
                'module': module,
                'count': len(routes),
                'type': eval_info['type'],
                'reason': eval_info['reason']
            })

print(f"\n【可立即删除】")
print("-"*80)
deletable_total = 0
for m in deletable:
    print(f"  ❌ v1/{m['module']:30s} {m['count']:2d} 个端点")
    print(f"     类型: {m['type']}")
    print(f"     原因: {m['reason']}\n")
    deletable_total += m['count']

print(f"  可删除总计: {deletable_total} 个端点")

print(f"\n【建议保留/审查】")
print("-"*80)
for m in keep:
    print(f"  ⚠️  v1/{m['module']:30s} {m['count']:2d} 个端点")
    print(f"     类型: {m['type']}")
    print(f"     原因: {m['reason']}\n")

# 查找注册
print(f"\n" + "="*80)
print("🔍 查找可删除模块的注册位置")
print("="*80)

with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

target_modules = [m['module'] for m in deletable]

registrations = []
for i, line in enumerate(lines, 1):
    if 'include_router' in line:
        for module in target_modules:
            if (f'/{module}' in line or 
                f'{module}.' in line or
                f'{module}_' in line or
                module in line.lower()):
                registrations.append({
                    'line': i,
                    'module': module,
                    'content': line.strip()
                })
                break

print(f"\n找到 {len(registrations)} 个注册:")
for reg in registrations:
    print(f"\n  第{reg['line']}行: {reg['module']}")
    print(f"    {reg['content']}")

# 保存执行计划
plan = {
    'step': '第4步',
    'description': '清理中型v1模块',
    'deletable': deletable,
    'keep': keep,
    'registrations': registrations,
    'total_deletable': deletable_total
}

with open('step4_execution_plan.json', 'w', encoding='utf-8') as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

print(f"\n" + "="*80)
print("💡 第4步执行计划")
print("="*80)

print(f"\n立即删除:")
print(f"  • 模块数: {len(deletable)} 个")
print(f"  • 端点数: {deletable_total} 个")
print(f"  • workbench, dashboard")

print(f"\n暂时保留:")
print(f"  • audit (审计日志)")
print(f"  • learning, agents (需要进一步评估)")

print(f"\n预期结果:")
print(f"  • 当前: 675 个端点")
print(f"  • 删除后: ~{675 - deletable_total} 个端点")
print(f"  • 进度: ~{((118 + deletable_total) / 373 * 100):.1f}%")

print(f"\n✅ 执行计划已保存到: step4_execution_plan.json")

