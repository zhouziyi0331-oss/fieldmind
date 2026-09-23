#!/usr/bin/env python3
"""执行第2步的立即删除操作"""
import json

print("="*80)
print("🔧 第2步：执行立即删除")
print("="*80)

# 读取决策
with open('step2_deletion_decision.json', 'r', encoding='utf-8') as f:
    decision = json.load(f)

can_delete = decision['can_delete']

print(f"\n准备删除 {len(can_delete)} 个端点:")
print("-"*80)
for r in can_delete:
    print(f"  ❌ {r['methods']:15s} {r['path']}")

# 查找这些端点的注册位置
print(f"\n" + "="*80)
print("🔍 查找注册代码")
print("="*80)

with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找包含这些路径的注册
keywords = ['keyword-relations', 'tables/statistics']

registrations = []
for i, line in enumerate(lines, 1):
    if 'include_router' in line:
        for keyword in keywords:
            if keyword in line or 'keyword_relations' in line or 'table' in line.lower():
                registrations.append({
                    'line': i,
                    'content': line.strip()
                })

if registrations:
    print(f"\n找到 {len(registrations)} 个相关注册:")
    for reg in registrations:
        print(f"  第{reg['line']}行: {reg['content']}")
else:
    print(f"\n⚠️  未找到明确的注册代码")
    print(f"   这些端点可能在子模块中定义")
    print(f"   建议: 检查v1/projects模块的子路由")

# 检查v1/projects的主注册
print(f"\n查找v1/projects的主注册:")
for i, line in enumerate(lines, 1):
    if 'include_router' in line and 'projects' in line and 'v1' in line:
        print(f"  第{i}行: {line.strip()}")
        # 显示上下文
        print(f"\n  上下文:")
        start = max(0, i-3)
        end = min(len(lines), i+2)
        for j in range(start, end):
            marker = ">>> " if j == i-1 else "    "
            print(f"  {marker}{j+1:4d}: {lines[j].rstrip()}")

print(f"\n" + "="*80)
print("💡 分析结果")
print("="*80)

print(f"\n这3个统计端点属于v1/projects的子路由")
print(f"它们在v1/projects模块的router中定义")
print(f"\n处理方式:")
print(f"  方案1: 保留v1/projects注册，但从模块中删除这3个端点定义")
print(f"  方案2: 暂时保留，在清理v1/projects整体时一起处理")
print(f"\n建议: 采用方案2，在第3步批量处理v1/projects")

