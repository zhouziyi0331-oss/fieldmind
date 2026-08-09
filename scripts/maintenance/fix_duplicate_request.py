#!/usr/bin/env python3
"""
批量修复API文件中重复的request参数问题

问题：在添加速率限制时，某些函数同时有：
  - request: Request (用于速率限制)
  - request: SomeRequestModel (业务逻辑)

解决方案：将速率限制的Request重命名为http_request
"""

import re
from pathlib import Path


def fix_duplicate_request(file_path: Path) -> bool:
    """
    修复文件中的重复request参数

    返回：是否进行了修改
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 模式1: 匹配有两个request参数的函数定义
    # async def func_name(
    #     request: Request,
    #     [空行]
    #     其他参数,
    #     request: OtherType,
    pattern1 = re.compile(
        r'(async def \w+\(\s*\n\s*)request: Request,(\s*\n\s*\n\s*)(\w+[^,]*,\s*\n\s*)request: (\w+)',
        re.MULTILINE
    )

    # 替换第一个request为http_request
    content = pattern1.sub(
        r'\1http_request: Request,\2\3request: \4',
        content
    )

    # 模式2: 更通用的匹配（处理没有空行的情况）
    pattern2 = re.compile(
        r'(async def \w+\(\s*\n\s*)request: Request,(\s*\n\s*)(\w+[^,]*,\s*\n\s*)request: (\w+)',
        re.MULTILINE
    )

    content = pattern2.sub(
        r'\1http_request: Request,\2\3request: \4',
        content
    )

    # 检查是否需要添加Request导入
    if 'http_request: Request' in content and 'from fastapi import' in content:
        # 检查是否已经导入了Request
        if ', Request' not in content and 'Request,' not in content and 'Request)' not in content:
            # 在fastapi导入中添加Request
            content = re.sub(
                r'from fastapi import ([^)]+?)(\))',
                r'from fastapi import \1, Request\2',
                content
            )

    # 如果内容有变化，写回文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True

    return False


def main():
    """主函数"""
    print("🔧 批量修复重复request参数\n")

    # 查找所有API文件
    api_dir = Path("app/api/v1")

    if not api_dir.exists():
        print("❌ 未找到 app/api/v1 目录")
        return

    python_files = list(api_dir.glob("*.py"))

    if not python_files:
        print("❌ 未找到Python文件")
        return

    print(f"📁 找到 {len(python_files)} 个Python文件\n")

    fixed_count = 0

    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue

        print(f"检查: {file_path.name}...", end=" ")

        try:
            if fix_duplicate_request(file_path):
                print("✓ 已修复")
                fixed_count += 1
            else:
                print("- 无需修复")
        except Exception as e:
            print(f"✗ 错误: {e}")

    print(f"\n📊 总结:")
    print(f"  - 检查文件: {len(python_files) - 1}")  # 排除__init__.py
    print(f"  - 修复文件: {fixed_count}")
    print(f"  - 状态: {'✅ 完成' if fixed_count > 0 else '✓ 无需修复'}")


if __name__ == "__main__":
    main()
