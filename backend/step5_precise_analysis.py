#!/usr/bin/env python3
"""第5步：精确分析需要删除的模块"""
import json

print("="*80)
print("🔍 第5步：精确分析可删除的v1模块")
print("="*80)

# 目标：只删除明确废弃的v1模块
target_modules = {
    'audit': {'endpoints': 16, 'reason': '审计功能，但可能有新版本'},
    'learning': {'endpoints': 15, 'reason': '学习引擎，可能已废弃'},
    'agents': {'endpoints': 15, 'reason': 'Agent管理，检查是否有统一版本'},
}

print(f"\n本轮目标模块 (3个):")
for module, info in target_modules.items():
    print(f"  • v1/{module:20s} {info['endpoints']:2d}个端点 - {info['reason']}")

# 读取main.py并精确查找
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"\n" + "="*80)
print("📋 精确查找注册位置")
print("="*80)

# 手动精确匹配
registrations = []

for i, line in enumerate(lines, 1):
    content = line.strip()
    
    # 跳过注释行
    if content.startswith('#'):
        continue
    
    if 'include_router' not in line:
        continue
    
    # 精确匹配audit
    if 'audit.router' in line or 'audit_enhancement.router' in line:
        if 'v1/audit' in line or 'prefix="/api/v1"' in line:
            registrations.append({
                'line': i,
                'module': 'audit',
                'content': content
            })
    
    # 精确匹配learning
    elif 'learning.router' in line:
        if 'v1/learning' in line or ('v1' in line and '学习引擎' in line):
            registrations.append({
                'line': i,
                'module': 'learning',
                'content': content
            })
    
    # 精确匹配background_learning
    elif 'background_learning.router' in line:
        registrations.append({
            'line': i,
            'module': 'learning',
            'content': content
        })
    
    # 精确匹配agents
    elif 'agents_p3.router' in line or 'super_agents.router' in line:
        registrations.append({
            'line': i,
            'module': 'agents',
            'content': content
        })

print(f"\n找到 {len(registrations)} 个精确匹配的注册:")
for reg in registrations:
    print(f"\n  第{reg['line']}行: v1/{reg['module']}")
    print(f"    {reg['content'][:75]}")

print(f"\n" + "="*80)
print("💡 保守策略")
print("="*80)

print(f"\n考虑到audit和learning可能是核心功能，")
print(f"本轮只删除明确废弃的模块：")
print(f"  • v1/agents相关 (agents_p3, super_agents)")
print(f"  • v1/learning的部分端点")

conservative_targets = ['agents']
total_endpoints = sum(target_modules[m]['endpoints'] for m in conservative_targets if m in target_modules)

print(f"\n预计删除: ~{total_endpoints} 个端点")
print(f"当前: 635个端点")
print(f"删除后: ~{635 - total_endpoints}个端点")

