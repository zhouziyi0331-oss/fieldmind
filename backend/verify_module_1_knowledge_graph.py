#!/usr/bin/env python3
"""验证模块1: 知识图谱"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from module_comparison_framework import extract_endpoints, compare_modules, print_comparison_report

print("="*80)
print("🔍 模块验证 1/9: 知识图谱")
print("="*80)

# 定义对应关系
old_modules = [
    Path("archive/old_modules/knowledge_graph.py"),
    Path("archive/old_modules/knowledge_graph_v3.py"),
]

unified_module = Path("src/app/api/unified_knowledge_graph.py")

# 执行对比
result = compare_modules(old_modules, unified_module)
print_comparison_report(result)

# 详细分析
print("="*80)
print("📋 详细分析")
print("="*80)

print("\n1️⃣ 旧模块端点列表:")
for i, ep in enumerate(result['old_endpoints'], 1):
    print(f"   {i:2d}. {ep}")

print(f"\n2️⃣ 统一模块端点列表:")
for i, ep in enumerate(result['unified_endpoints'], 1):
    print(f"   {i:2d}. {ep}")

if result['matched_endpoints']:
    print(f"\n3️⃣ 匹配的端点对应关系:")
    for i, match in enumerate(result['matched_endpoints'], 1):
        print(f"   {i:2d}. {match['old']} ≈ {match['unified']}")

# 生成待办清单
print("\n" + "="*80)
print("📝 待办清单")
print("="*80)

if result['missing_endpoints']:
    print(f"\n需要补充的功能 ({len(result['missing_endpoints'])}个):")
    for i, ep in enumerate(result['missing_endpoints'], 1):
        print(f"   [ ] {i}. 从旧模块迁移: {ep.function}()")
        print(f"       {ep.method} {ep.path}")
        print(f"       位置: {result['old_modules'][0]} 第{ep.line}行")
        print()
else:
    print("\n✅ 无需补充功能")

print("\n" + "="*80)
print("🎯 下一步行动")
print("="*80)

if result['missing_endpoints']:
    print("\n1. 复制缺失的端点代码")
    print("2. 适配到统一模块的结构")
    print("3. 测试验证")
    print("4. 继续下一个模块")
else:
    print("\n✅ 知识图谱模块验证完成")
    print("✅ 可以继续验证下一个模块")

