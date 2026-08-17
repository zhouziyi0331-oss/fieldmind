#!/usr/bin/env python3
"""
分析未使用的Python模块
找出定义了但从未被import的模块文件
"""

import os
import re
from pathlib import Path
from typing import Set, Dict, List

def get_all_python_files(root_dir: str) -> List[Path]:
    """获取所有Python文件"""
    root = Path(root_dir)
    return list(root.rglob("*.py"))

def extract_imports(file_path: Path) -> Set[str]:
    """从文件中提取所有import语句"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 from xxx import yyy
        from_imports = re.findall(r'^from\s+([\w.]+)\s+import', content, re.MULTILINE)
        imports.update(from_imports)

        # 匹配 import xxx
        direct_imports = re.findall(r'^import\s+([\w.]+)', content, re.MULTILINE)
        imports.update(direct_imports)

    except Exception as e:
        print(f"警告: 无法读取 {file_path}: {e}")

    return imports

def path_to_module(file_path: Path, root_dir: Path) -> str:
    """将文件路径转换为模块路径"""
    try:
        rel_path = file_path.relative_to(root_dir)
        parts = list(rel_path.parts)

        # 移除 .py 后缀
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]

        # 移除 __init__
        if parts[-1] == '__init__':
            parts = parts[:-1]

        return '.'.join(parts)
    except:
        return str(file_path)

def analyze_unused_modules(root_dir: str) -> Dict:
    """分析未使用的模块"""
    root = Path(root_dir)
    all_files = get_all_python_files(root_dir)

    print(f"📊 找到 {len(all_files)} 个Python文件")

    # 构建模块名到文件路径的映射
    module_to_file = {}
    for file_path in all_files:
        module_name = path_to_module(file_path, root)
        module_to_file[module_name] = file_path

    # 收集所有import语句
    all_imports = set()
    for file_path in all_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)

    print(f"📊 找到 {len(all_imports)} 个唯一的import语句")

    # 找出未被导入的模块
    unused_modules = []

    for module_name, file_path in module_to_file.items():
        # 跳过特殊文件
        if file_path.name in ['__init__.py', '__main__.py']:
            continue

        # 跳过测试文件和脚本文件
        if file_path.name.startswith('test_') or file_path.name.startswith('demo_'):
            continue

        # 检查是否有任何import语句引用此模块
        is_imported = False

        # 完整模块名匹配
        if module_name in all_imports:
            is_imported = True

        # 检查部分路径匹配（处理相对导入）
        module_parts = module_name.split('.')
        for i in range(len(module_parts)):
            partial_name = '.'.join(module_parts[i:])
            if partial_name in all_imports:
                is_imported = True
                break

            # 检查父包导入（from parent import *）
            if i < len(module_parts) - 1:
                parent_name = '.'.join(module_parts[i:-1])
                if parent_name in all_imports:
                    # 需要检查是否有 import * 或显式导入
                    is_imported = True
                    break

        if not is_imported:
            # 进一步验证：检查文件名是否出现在任何import中
            file_base_name = file_path.stem
            if any(file_base_name in imp for imp in all_imports):
                is_imported = True

        if not is_imported:
            unused_modules.append({
                'module': module_name,
                'file': str(file_path.relative_to(root)),
                'size': file_path.stat().st_size
            })

    return {
        'total_files': len(all_files),
        'total_imports': len(all_imports),
        'unused_modules': sorted(unused_modules, key=lambda x: x['size'], reverse=True)
    }

def main():
    root_dir = "/Users/alwan/FieldMind/backend/src/app"

    print("=" * 80)
    print("P1-3: 未使用模块分析")
    print("=" * 80)
    print()

    result = analyze_unused_modules(root_dir)

    print()
    print("=" * 80)
    print("分析结果")
    print("=" * 80)
    print(f"总文件数: {result['total_files']}")
    print(f"总导入数: {result['total_imports']}")
    print(f"未使用模块: {len(result['unused_modules'])}")
    print()

    if result['unused_modules']:
        print("未使用的模块列表：")
        print("-" * 80)
        for item in result['unused_modules']:
            print(f"📦 {item['module']}")
            print(f"   文件: {item['file']}")
            print(f"   大小: {item['size']} bytes")
            print()
    else:
        print("✅ 所有模块都被使用")

    # 保存详细报告
    report_path = "/Users/alwan/FieldMind/PHASE_6_P1_UNUSED_MODULES_ANALYSIS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# P1-3: 未使用模块分析报告\n\n")
        f.write(f"**分析时间**: {Path(__file__).stat().st_mtime}\n\n")
        f.write("## 统计数据\n\n")
        f.write(f"- 总文件数: {result['total_files']}\n")
        f.write(f"- 总导入语句: {result['total_imports']}\n")
        f.write(f"- 未使用模块: {len(result['unused_modules'])}\n\n")

        if result['unused_modules']:
            f.write("## 未使用模块详情\n\n")
            for item in result['unused_modules']:
                f.write(f"### {item['module']}\n\n")
                f.write(f"- **文件**: `{item['file']}`\n")
                f.write(f"- **大小**: {item['size']} bytes\n")
                f.write(f"- **状态**: 未被任何模块import\n\n")
        else:
            f.write("## 结果\n\n")
            f.write("✅ 所有模块都有被使用\n\n")

    print(f"📄 详细报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
