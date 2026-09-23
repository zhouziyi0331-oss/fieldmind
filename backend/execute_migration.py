#!/usr/bin/env python3
"""执行模块迁移和清理"""
from pathlib import Path
import shutil

# 第一批：最简单的模块
batch_1_removals = [
    # 分析模块
    "src/app/api/creative_analysis.py",
    "src/app/api/business_analysis.py",
    "src/app/api/analytics.py",
    # 报告模块
    "src/app/api/export_summaries.py",
    # 工具模块
    "src/app/api/ocr.py",
]

print("="*80)
print("阶段5: 模块迁移和清理 - 第一批")
print("="*80)

removed = []
not_found = []

for module_path in batch_1_removals:
    path = Path(module_path)
    if path.exists():
        # 备份到archive
        archive_path = Path("archive/old_modules") / path.name
        shutil.copy2(path, archive_path)
        print(f"✓ 备份: {path.name}")
        
        # 删除原文件
        path.unlink()
        print(f"✓ 删除: {module_path}")
        removed.append(module_path)
    else:
        print(f"✗ 未找到: {module_path}")
        not_found.append(module_path)

print(f"\n📊 第一批统计:")
print(f"   已删除: {len(removed)} 个文件")
print(f"   未找到: {len(not_found)} 个文件")

print("\n✅ 第一批完成！")
