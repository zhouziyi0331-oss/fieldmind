#!/usr/bin/env python3
"""执行第二批模块迁移和清理"""
from pathlib import Path
import shutil

# 第二批：中等复杂度
batch_2_removals = [
    # 文档模块
    "src/app/api/documents.py",
    "src/app/api/document_processing.py",
    # 技能模块
    "src/app/api/v1/skills.py",
    "src/app/api/v1/skill_generation.py",
    "src/app/api/v1/skill_optimization.py",
    # 项目模块
    "src/app/api/v1/projects.py",
    "src/app/api/v1/project_documents.py",
]

print("="*80)
print("阶段5: 模块迁移和清理 - 第二批")
print("="*80)

removed = []
not_found = []

for module_path in batch_2_removals:
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

print(f"\n📊 第二批统计:")
print(f"   已删除: {len(removed)} 个文件")
print(f"   未找到: {len(not_found)} 个文件")

print("\n✅ 第二批完成！")
