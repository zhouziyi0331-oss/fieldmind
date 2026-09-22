#!/usr/bin/env python3
"""
批量迁移剩余API文件的辅助脚本
生成每个文件需要的具体修改命令
"""

import json
from pathlib import Path

# 加载迁移计划
plan_file = "/Users/alwan/FieldMind/migration_plan_phase1.json"
with open(plan_file, 'r') as f:
    plan = json.load(f)

# 已完成的文件
completed = [
    "app/api/aggregate.py",
    "app/api/analytics.py",
    "app/api/batch_processing.py",
    "app/api/business_analysis.py",
    "app/api/chat.py",
    "app/api/chat_rag.py"
]

# 生成剩余文件的迁移指令
remaining_files = [f for f in plan['files'] if f['path'] not in completed]

print(f"剩余需要迁移的文件: {len(remaining_files)}")
print()

# 按端点数量排序（先处理小文件）
remaining_files.sort(key=lambda x: len(x['endpoints']))

print("迁移顺序（按端点数从少到多）:")
print("=" * 80)

for i, file_info in enumerate(remaining_files[:10], 1):
    path = file_info['path']
    endpoint_count = len(file_info['endpoints'])
    needs_import = file_info['needs_import']

    print(f"{i}. {path}")
    print(f"   端点数: {endpoint_count}")
    print(f"   需要添加导入: {'是' if needs_import else '否'}")
    print(f"   端点列表:")

    for ep in file_info['endpoints']:
        print(f"     - {ep['method']} {ep['path']} ({ep['function']})")

    print()

print("\n下一批要处理的10个文件:")
for i, file_info in enumerate(remaining_files[:10], 1):
    print(f"{i}. {file_info['path']} ({len(file_info['endpoints'])} 端点)")
