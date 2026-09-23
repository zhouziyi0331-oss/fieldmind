#!/usr/bin/env python3
"""第3步：执行批量删除小型v1模块"""
import json

print("="*80)
print("🔧 第3步：执行批量删除小型v1模块")
print("="*80)

# 读取批量删除计划
with open('step3_batch_delete_plan.json', 'r', encoding='utf-8') as f:
    plan = json.load(f)

# 目标模块
target_modules = [
    'annotation',
    'tagging', 
    'distillation',
    'feeding',
    'lineage',
    'sop',
    'hermes',
    'api-management'
]

print(f"\n目标删除的模块 ({len(target_modules)}个):")
print("-"*80)
for module in target_modules:
    print(f"  ❌ v1/{module}")

# 查找这些模块在main.py中的注册
print(f"\n" + "="*80)
print("🔍 查找注册位置")
print("="*80)

with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

registrations = []
for i, line in enumerate(lines, 1):
    if 'include_router' in line:
        for module in target_modules:
            # 检查各种格式
            module_normalized = module.replace('-', '_')
            if (f'/{module}' in line or 
                f'{module_normalized}.' in line or
                f'{module}.' in line or
                (module == 'annotation' and 'annotation' in line.lower()) or
                (module == 'tagging' and 'tagging' in line.lower()) or
                (module == 'distillation' and 'distill' in line.lower()) or
                (module == 'feeding' and 'feeding' in line.lower()) or
                (module == 'lineage' and 'lineage' in line.lower()) or
                (module == 'sop' and 'sop' in line.lower()) or
                (module == 'hermes' and 'hermes' in line.lower()) or
                (module == 'api-management' and 'api_management' in line)):
                
                registrations.append({
                    'line': i,
                    'module': module,
                    'content': line.strip()
                })
                break

print(f"\n找到 {len(registrations)} 个注册需要注释:")
for reg in registrations:
    print(f"\n  第{reg['line']}行: {reg['module']}")
    print(f"    {reg['content']}")

# 生成注释列表
print(f"\n" + "="*80)
print("📋 需要注释的行")
print("="*80)

lines_to_comment = [reg['line'] for reg in registrations]
print(f"\n需要注释的行号: {sorted(lines_to_comment)}")

# 保存执行计划
execution_plan = {
    'target_modules': target_modules,
    'registrations': registrations,
    'lines_to_comment': sorted(lines_to_comment)
}

with open('step3_execution_plan.json', 'w', encoding='utf-8') as f:
    json.dump(execution_plan, f, indent=2, ensure_ascii=False)

print(f"\n✅ 执行计划已保存到: step3_execution_plan.json")
print(f"\n接下来将逐个注释这些注册行...")

