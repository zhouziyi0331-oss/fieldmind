#!/usr/bin/env python3
"""
验证未使用模块的真实性
需要排除以下情况的误报：
1. 在main.py中注册的API路由
2. 通过动态导入使用的模块
3. 作为入口点的模块（如main_simple.py）
"""

import os
import re
from pathlib import Path

def check_if_registered_in_main(module_file: str) -> bool:
    """检查模块是否在main.py中注册"""
    main_file = Path("/Users/alwan/FieldMind/backend/src/app/main.py")

    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            main_content = f.read()

        # 提取模块名（去掉.py后缀和路径）
        module_name = Path(module_file).stem

        # 检查import语句
        if f"import {module_name}" in main_content or f"from app.api import {module_name}" in main_content:
            return True

        # 检查include_router调用
        if f"{module_name}.router" in main_content:
            return True

        return False
    except Exception as e:
        print(f"警告: 无法读取main.py: {e}")
        return False

def check_dynamic_imports(root_dir: str, module_file: str) -> list:
    """检查是否有动态导入此模块"""
    module_path = Path(module_file)
    module_name = module_path.stem

    # 搜索动态导入模式
    patterns = [
        rf'importlib\.import_module.*{module_name}',
        rf'__import__.*{module_name}',
        rf'exec.*import.*{module_name}',
        rf'eval.*import.*{module_name}',
    ]

    matches = []
    root = Path(root_dir)

    for py_file in root.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in patterns:
                if re.search(pattern, content):
                    matches.append(str(py_file.relative_to(root)))
        except:
            pass

    return matches

def is_entry_point(module_file: str) -> bool:
    """检查是否是入口点模块"""
    entry_points = [
        'main.py',
        'main_simple.py',
        'main_v2.py',
        '__main__.py',
    ]

    return Path(module_file).name in entry_points

def categorize_unused_modules():
    """对未使用模块进行分类"""

    # 从分析报告中读取未使用模块列表
    report_file = Path("/Users/alwan/FieldMind/PHASE_6_P1_UNUSED_MODULES_ANALYSIS.md")

    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取所有模块文件路径
    module_files = re.findall(r'\*\*文件\*\*: `([^`]+)`', content)

    print(f"📊 总共 {len(module_files)} 个未使用模块")
    print()

    # 分类
    registered_in_main = []
    dynamic_imported = []
    entry_points = []
    truly_unused = []

    for module_file in module_files:
        full_path = f"backend/src/app/{module_file}"

        # 检查是否在main.py中注册
        if check_if_registered_in_main(module_file):
            registered_in_main.append(module_file)
            continue

        # 检查是否是入口点
        if is_entry_point(module_file):
            entry_points.append(module_file)
            continue

        # 检查动态导入
        dynamic_matches = check_dynamic_imports("/Users/alwan/FieldMind/backend/src/app", module_file)
        if dynamic_matches:
            dynamic_imported.append((module_file, dynamic_matches))
            continue

        # 真正未使用
        truly_unused.append(module_file)

    print("=" * 80)
    print("分类结果")
    print("=" * 80)
    print()

    print(f"1️⃣ 在main.py中注册的路由 ({len(registered_in_main)}个):")
    for f in registered_in_main:
        print(f"   ✓ {f}")
    print()

    print(f"2️⃣ 入口点模块 ({len(entry_points)}个):")
    for f in entry_points:
        print(f"   ✓ {f}")
    print()

    print(f"3️⃣ 动态导入的模块 ({len(dynamic_imported)}个):")
    for f, matches in dynamic_imported:
        print(f"   ✓ {f}")
        for m in matches:
            print(f"      被动态导入于: {m}")
    print()

    print(f"4️⃣ 真正未使用的模块 ({len(truly_unused)}个):")
    for f in truly_unused:
        print(f"   ❌ {f}")
    print()

    # 生成详细报告
    output_file = Path("/Users/alwan/FieldMind/PHASE_6_P1_UNUSED_MODULES_VERIFIED.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# P1-3: 未使用模块验证报告\n\n")
        f.write("## 分析说明\n\n")
        f.write("对初步分析报告中的112个\"未使用模块\"进行二次验证，排除误报。\n\n")

        f.write("## 分类结果\n\n")
        f.write(f"- **在main.py中注册**: {len(registered_in_main)}个 (实际被使用)\n")
        f.write(f"- **入口点模块**: {len(entry_points)}个 (实际被使用)\n")
        f.write(f"- **动态导入**: {len(dynamic_imported)}个 (实际被使用)\n")
        f.write(f"- **真正未使用**: {len(truly_unused)}个 ⚠️\n\n")

        f.write("---\n\n")

        f.write("## 1. 在main.py中注册的路由\n\n")
        f.write("这些模块通过`include_router`在main.py中注册，实际被使用。\n\n")
        for module in registered_in_main:
            f.write(f"- `{module}` ✓\n")
        f.write("\n")

        f.write("## 2. 入口点模块\n\n")
        f.write("这些是应用的入口点，被直接执行而非import。\n\n")
        for module in entry_points:
            f.write(f"- `{module}` ✓\n")
        f.write("\n")

        f.write("## 3. 动态导入的模块\n\n")
        for module, matches in dynamic_imported:
            f.write(f"### `{module}` ✓\n\n")
            f.write("被动态导入于:\n")
            for m in matches:
                f.write(f"- `{m}`\n")
            f.write("\n")

        f.write("## 4. 真正未使用的模块 ⚠️\n\n")
        f.write(f"共 {len(truly_unused)} 个模块从未被导入或使用，可以考虑删除。\n\n")

        # 按大小排序
        truly_unused_with_size = []
        for module in truly_unused:
            full_path = Path(f"/Users/alwan/FieldMind/backend/src/app/{module}")
            if full_path.exists():
                size = full_path.stat().st_size
                truly_unused_with_size.append((module, size))

        truly_unused_with_size.sort(key=lambda x: x[1], reverse=True)

        for module, size in truly_unused_with_size:
            f.write(f"- `{module}` ({size} bytes)\n")
        f.write("\n")

        total_size = sum(size for _, size in truly_unused_with_size)
        f.write(f"**总计**: {len(truly_unused)} 个文件，{total_size:,} bytes ({total_size/1024:.1f} KB)\n\n")

    print(f"📄 详细报告已保存到: {output_file}")

    return {
        'registered': len(registered_in_main),
        'entry_points': len(entry_points),
        'dynamic': len(dynamic_imported),
        'truly_unused': len(truly_unused),
        'total_size': sum(size for _, size in truly_unused_with_size)
    }

if __name__ == "__main__":
    result = categorize_unused_modules()

    print()
    print("=" * 80)
    print("📊 汇总")
    print("=" * 80)
    print(f"实际使用: {result['registered'] + result['entry_points'] + result['dynamic']} 个")
    print(f"真正未使用: {result['truly_unused']} 个")
    print(f"可清理空间: {result['total_size']:,} bytes ({result['total_size']/1024:.1f} KB)")
