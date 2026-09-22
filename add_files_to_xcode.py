#!/usr/bin/env python3
"""
自动将核心集成文件添加到 Xcode 项目
使用 pbxproj 库来操作 .xcodeproj 文件
"""

import os
import sys

try:
    from pbxproj import XcodeProject
except ImportError:
    print("正在安装 pbxproj...")
    os.system("pip3 install pbxproj")
    from pbxproj import XcodeProject

# 项目路径
PROJECT_PATH = '/Users/alwan/FieldMind/fieldmind/fieldmind.xcodeproj'
BASE_PATH = '/Users/alwan/FieldMind/fieldmind/fieldmind'

# 核心文件列表（相对于 BASE_PATH）
CORE_FILES = [
    'Core/UnifiedAppState.swift',
    'Core/DataPipeline/DataPipeline.swift',
    'Services/BackendService.swift',
    'Services/KnowledgeVaultService.swift',
    'Views/KnowledgeVaultView.swift',
]

# 这些文件在外层 fieldmind/ 目录
OUTER_FILES = [
    '../Services/DistillationService.swift',
    '../Views/MainNavigationView.swift',
    '../Views/DistillationView.swift',
]

def main():
    print("="*60)
    print("🔧 开始添加文件到 Xcode 项目")
    print("="*60)

    # 打开项目
    try:
        project = XcodeProject.load(PROJECT_PATH + '/project.pbxproj')
    except Exception as e:
        print(f"❌ 无法打开项目: {e}")
        return 1

    added_count = 0
    skipped_count = 0
    missing_count = 0

    # 处理所有文件
    all_files = CORE_FILES + OUTER_FILES

    for file_path in all_files:
        full_path = os.path.join(BASE_PATH, file_path)
        # 标准化路径
        full_path = os.path.normpath(full_path)

        # 用于显示的相对路径
        display_path = os.path.relpath(full_path, '/Users/alwan/FieldMind/fieldmind')

        # 检查文件是否存在
        if not os.path.exists(full_path):
            print(f"⚠️  文件不存在: {display_path}")
            missing_count += 1
            continue

        # 检查是否已在项目中（使用文件名检查）
        file_name = os.path.basename(file_path)
        if project.get_files_by_name(file_name):
            print(f"⏭️  已存在: {display_path}")
            skipped_count += 1
            continue

        # 添加文件
        try:
            # 获取文件的相对目录
            rel_dir = os.path.dirname(display_path)
            project.add_file(full_path, parent=project.get_or_create_group(rel_dir) if rel_dir else None)
            print(f"✅ 已添加: {display_path}")
            added_count += 1
        except Exception as e:
            print(f"❌ 添加失败 {display_path}: {e}")
            continue

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
    print("📊 文件添加统计")
    print("="*60)
    print(f"✅ 成功添加: {added_count} 个文件")
    print(f"⏭️  已存在跳过: {skipped_count} 个文件")
    print(f"⚠️  文件缺失: {missing_count} 个文件")
    print("="*60)

    if added_count > 0:
        print("\n🎉 Xcode 项目已更新！")
        print("📝 下一步:")
        print("   1. 在 Xcode 中打开项目: open fieldmind/fieldmind.xcodeproj")
        print("   2. 编译项目: ⌘+B")
        print("   3. 运行测试: ⌘+R")

    return 0

if __name__ == '__main__':
    sys.exit(main())
