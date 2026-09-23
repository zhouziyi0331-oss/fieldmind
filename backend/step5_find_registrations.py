#!/usr/bin/env python3
"""第5步：查找需要删除的模块的注册位置"""
import json

print("="*80)
print("🔍 查找第5步目标模块的注册位置")
print("="*80)

# 读取执行计划
with open('step5_execution_plan.json', 'r', encoding='utf-8') as f:
    plan = json.load(f)

target_modules = [m['module'] for m in plan['deletable']]

print(f"\n目标模块 ({len(target_modules)}个):")
for m in target_modules:
    print(f"  • v1/{m}")

# 读取main.py
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找注册
print(f"\n" + "="*80)
print("📋 查找注册位置")
print("="*80)

registrations = []
for i, line in enumerate(lines, 1):
    if 'include_router' in line and not line.strip().startswith('#'):
        for module in target_modules:
            # 多种匹配模式
            module_patterns = [
                f'/{module}',
                f'{module}.',
                f'{module}_',
                f'"{module}"',
                f"'{module}'",
            ]
            
            # 特殊处理
            if module == 'api':
                module_patterns.append('api_management')
            
            if any(pattern in line for pattern in module_patterns):
                registrations.append({
                    'line': i,
                    'module': module,
                    'content': line.strip()
                })
                break

print(f"\n找到 {len(registrations)} 个注册需要删除:")
print("-"*80)

grouped = {}
for reg in registrations:
    module = reg['module']
    if module not in grouped:
        grouped[module] = []
    grouped[module].append(reg)

for module in sorted(grouped.keys()):
    regs = grouped[module]
    print(f"\nv1/{module} ({len(regs)}个注册):")
    for reg in regs:
        print(f"  第{reg['line']}行: {reg['content'][:70]}")

# 保存注册信息
registration_info = {
    'target_modules': target_modules,
    'registrations': registrations,
    'lines_to_delete': sorted([r['line'] for r in registrations])
}

with open('step5_registrations.json', 'w', encoding='utf-8') as f:
    json.dump(registration_info, f, indent=2, ensure_ascii=False)

print(f"\n" + "="*80)
print("💡 执行策略")
print("="*80)

print(f"\n需要注释的行号: {sorted([r['line'] for r in registrations])}")
print(f"\n建议: 从后往前注释，避免行号变化")

print(f"\n✅ 注册信息已保存到: step5_registrations.json")

