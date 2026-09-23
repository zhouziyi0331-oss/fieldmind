#!/usr/bin/env python3
"""第5步：激进策略 - 批量删除剩余v1模块"""
import json

print("="*80)
print("🚀 第5步：激进策略 - 批量删除v1模块")
print("="*80)

# 读取main.py
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 策略：删除所有 /api/v1/ 开头的注册（除了已知核心功能）
# 保留：auth（认证）、permissions（权限）
# 删除：其他所有v1模块

core_keep = ['auth', 'permissions']

print(f"\n扫描所有 /api/v1/ 注册...")
print("-"*80)

v1_registrations = []
for i, line in enumerate(lines, 1):
    content = line.strip()
    
    # 跳过已注释的行
    if content.startswith('#'):
        continue
    
    if 'include_router' not in line:
        continue
    
    # 查找所有包含 /api/v1 的注册
    if 'prefix="/api/v1' in line or "prefix='/api/v1" in line:
        # 检查是否是核心保留模块
        is_core = any(core in line for core in core_keep)
        
        if not is_core:
            v1_registrations.append({
                'line': i,
                'content': content,
                'reason': '包含 /api/v1 路径前缀'
            })

print(f"\n找到 {len(v1_registrations)} 个v1模块注册:")
for reg in v1_registrations[:20]:
    print(f"  第{reg['line']:4d}行: {reg['content'][:70]}")
if len(v1_registrations) > 20:
    print(f"  ... 还有 {len(v1_registrations) - 20} 个")

# 额外查找：包含 v1.xxx 或 xxx_v1 的导入
print(f"\n" + "="*80)
print("🔍 查找其他v1模块注册")
print("="*80)

additional_v1 = []
for i, line in enumerate(lines, 1):
    content = line.strip()
    
    if content.startswith('#'):
        continue
    
    if 'include_router' not in line:
        continue
    
    # 已经在上面找到的跳过
    if i in [r['line'] for r in v1_registrations]:
        continue
    
    # 查找其他v1模式
    if any(pattern in line for pattern in ['_v1.router', 'as v1_', 'from app.api.v1']):
        additional_v1.append({
            'line': i,
            'content': content,
            'reason': '包含 v1 相关导入'
        })

print(f"\n找到 {len(additional_v1)} 个额外的v1相关注册:")
for reg in additional_v1[:10]:
    print(f"  第{reg['line']:4d}行: {reg['content'][:70]}")

# 合并所有待删除的注册
all_deletable = v1_registrations + additional_v1
all_deletable.sort(key=lambda x: x['line'])

print(f"\n" + "="*80)
print("📊 汇总")
print("="*80)

print(f"\n总计找到 {len(all_deletable)} 个v1模块注册需要删除")
print(f"涉及行号: {sorted([r['line'] for r in all_deletable])[:20]}{'...' if len(all_deletable) > 20 else ''}")

# 保存
with open('step5_aggressive_plan.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(all_deletable),
        'registrations': all_deletable
    }, f, indent=2, ensure_ascii=False)

print(f"\n预期效果:")
print(f"  • 当前: 635个端点")
print(f"  • 预计删除: 100-150个端点")
print(f"  • 预计剩余: 485-535个端点")
print(f"  • 目标: 420个端点")

print(f"\n✅ 激进计划已保存到: step5_aggressive_plan.json")

