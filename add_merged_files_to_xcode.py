#!/usr/bin/env python3
"""
将所有 *_Merged.swift 文件添加到 Xcode 项目
这些文件包含了两个版本的合并代码，需要手动审查
"""

import os
import sys
from pbxproj import XcodeProject

PROJECT_PATH = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj'
BASE_PATH = '/Users/alwan/FieldMind/fieldmind/fieldmind'

def find_merged_files():
    """查找所有 *_Merged.swift 文件"""
    merged_files = []
    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.endswith('_Merged.swift'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_PATH)
                merged_files.append(rel_path)
    return sorted(merged_files)

def main():
    print("="*60)
    print("🔧 添加合并文件到 Xcode 项目")
    print("="*60)

    # 查找所有合并文件
    merged_files = find_merged_files()
    print(f"\n📁 找到 {len(merged_files)} 个合并文件")

    if not merged_files:
        print("✅ 没有需要添加的合并文件")
        return 0

    # 打开项目
    try:
        project = XcodeProject.load(PROJECT_PATH + '/project.pbxproj')
    except Exception as e:
        print(f"❌ 无法打开项目: {e}")
        return 1

    added_count = 0
    skipped_count = 0

    print("\n开始处理:")
    for rel_path in merged_files:
        full_path = os.path.join(BASE_PATH, rel_path)
        file_name = os.path.basename(rel_path)

        # 检查是否已在项目中
        if project.get_files_by_name(file_name):
            print(f"⏭️  {rel_path}")
            skipped_count += 1
            continue

        # 添加文件
        try:
            rel_dir = os.path.dirname(rel_path)
            project.add_file(full_path, parent=project.get_or_create_group(rel_dir) if rel_dir else None)
            print(f"✅ {rel_path}")
            added_count += 1
        except Exception as e:
            print(f"❌ {rel_path}: {e}")

    # 保存项目
    if added_count > 0:
        try:
            project.save()
            print("\n💾 项目已保存")
        except Exception as e:
            print(f"\n❌ 保存失败: {e}")
            return 1

    # 统计
    print("\n" + "="*60)
    print("📊 统计")
    print("="*60)
    print(f"✅ 成功添加: {added_count} 个")
    print(f"⏭️  已存在: {skipped_count} 个")
    print("="*60)

    if added_count > 0:
        print("\n⚠️  重要提示:")
        print("   这些 *_Merged.swift 文件包含两个版本的代码合并")
        print("   你需要:")
        print("   1. 在 Xcode 中审查每个文件")
        print("   2. 保留有价值的代码")
        print("   3. 删除重复/无用的代码")
        print("   4. 重命名文件（去掉 _Merged 后缀）")
        print("   5. 更新原始文件或删除原始文件")

    return 0

if __name__ == '__main__':
    sys.exit(main())
