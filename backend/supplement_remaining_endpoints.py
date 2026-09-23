#!/usr/bin/env python3
"""补充剩余的6个缺失端点"""
from pathlib import Path

print("="*80)
print("🔧 补充剩余的缺失端点")
print("="*80)

# 1. 文档处理模块 - 缺失3个端点
print("\n模块1: 文档处理 (3个缺失端点)")
print("-" * 80)

doc_old = Path("archive/old_modules/documents.py")
with open(doc_old, 'r') as f:
    lines = f.readlines()

# 查找缺失的端点
endpoints = [
    'GET /aggregate/skills',
    'GET /aggregate/keywords', 
    'GET /knowledge-base/status'
]

for endpoint in endpoints:
    print(f"\n查找: {endpoint}")
    for i, line in enumerate(lines, 1):
        if 'aggregate/skills' in line and '@router' in line:
            print(f"   找到位置: 第{i}行")
            # 提取端点代码
            start = i - 1
            end = start + 30
            print("   代码片段:")
            for j in range(start, min(end, len(lines))):
                print(f"   {lines[j]}", end='')
            break

print("\n" + "="*80)

# 2. 工具模块 - 缺失3个端点  
print("\n模块2: 工具 (3个缺失端点)")
print("-" * 80)

export_old = Path("archive/old_modules/export_summaries.py")
with open(export_old, 'r') as f:
    lines = f.readlines()

endpoints = [
    'GET /documents/{document_id}/word',
    'GET /documents/{document_id}/pdf',
    'GET /projects/{project_id}/pdf'
]

for endpoint in endpoints:
    print(f"\n查找: {endpoint}")
    keyword = endpoint.split('/')[-1]  # word, pdf
    for i, line in enumerate(lines, 1):
        if keyword in line and '@router' in line and 'document' in line.lower():
            print(f"   找到位置: 第{i}行")
            start = i - 1
            end = start + 30
            print("   代码片段:")
            for j in range(start, min(end, len(lines))):
                print(f"   {lines[j]}", end='')
            break

