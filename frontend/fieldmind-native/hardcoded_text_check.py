#!/usr/bin/env python3
"""
检查 Swift 文件中的硬编码中文文本
"""
import re
import os
from pathlib import Path

def find_hardcoded_text(file_path):
    """查找文件中的硬编码中文文本"""
    hardcoded = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 查找字符串中的中文
            matches = re.findall(r'"([^"]*[一-鿿]+[^"]*)"', line)
            for match in matches:
                # 排除 URL、文件路径等
                if not any(x in match for x in ['http://', 'https://', '.com', '.cn']):
                    hardcoded.append({
                        'line': i,
                        'text': match,
                        'context': line.strip()
                    })

    return hardcoded

def main():
    pages_dir = Path('Sources/Pages')
    results = {}

    for swift_file in pages_dir.glob('*.swift'):
        hardcoded = find_hardcoded_text(swift_file)
        if hardcoded:
            results[swift_file.name] = hardcoded

    # 输出结果
    print("=" * 80)
    print("硬编码中文文本检查报告")
    print("=" * 80)

    total_count = sum(len(items) for items in results.values())
    print(f"\n总共发现 {total_count} 处硬编码中文文本，分布在 {len(results)} 个文件中\n")

    for filename, items in sorted(results.items()):
        print(f"\n📄 {filename} ({len(items)} 处):")
        print("-" * 80)
        for item in items[:10]:  # 只显示前10个
            print(f"  行 {item['line']}: \"{item['text']}\"")
        if len(items) > 10:
            print(f"  ... 还有 {len(items) - 10} 处")

if __name__ == '__main__':
    main()
