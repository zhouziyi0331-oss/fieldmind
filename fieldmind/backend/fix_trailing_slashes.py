#!/usr/bin/env python3
"""
批量修复所有API路由的尾部斜杠问题
自动为所有带路径参数的路由添加尾部斜杠，防止307重定向
"""
import re
import os
from pathlib import Path

def fix_route_trailing_slashes(file_path):
    """修复单个文件中的路由定义"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 匹配所有路由装饰器：@router.get/post/put/delete/patch("路径")
    # 如果路径包含 {参数} 且不以 / 结尾，则添加 /

    pattern = r'(@router\.(get|post|put|delete|patch)\("([^"]+)"\))'

    def replace_route(match):
        full_decorator = match.group(1)
        method = match.group(2)
        path = match.group(3)

        # 如果路径包含路径参数 {...} 且不以 / 结尾
        if '{' in path and '}' in path and not path.endswith('/'):
            new_path = path + '/'
            new_decorator = f'@router.{method}("{new_path}")'
            print(f"  修复: {path} -> {new_path}")
            return new_decorator

        return full_decorator

    content = re.sub(pattern, replace_route, content)

    # 如果有变化，保存文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    return False

def main():
    """主函数：扫描并修复所有API文件"""
    api_dir = Path('/Users/alwan/FieldMind/backend/src/app/api')

    print("🔧 开始批量修复路由尾部斜杠问题...")
    print(f"📂 扫描目录: {api_dir}\n")

    fixed_files = []
    total_files = 0

    # 递归扫描所有.py文件
    for py_file in api_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue

        total_files += 1
        print(f"📄 检查文件: {py_file.relative_to(api_dir.parent.parent)}")

        if fix_route_trailing_slashes(py_file):
            fixed_files.append(py_file)
            print(f"  ✅ 已修复\n")
        else:
            print(f"  ⏭️  无需修复\n")

    print("\n" + "="*60)
    print(f"✅ 完成！共扫描 {total_files} 个文件")
    print(f"🔧 修复了 {len(fixed_files)} 个文件")

    if fixed_files:
        print("\n修复的文件列表:")
        for f in fixed_files:
            print(f"  - {f.relative_to(api_dir.parent.parent)}")

    print("="*60)

if __name__ == '__main__':
    main()
