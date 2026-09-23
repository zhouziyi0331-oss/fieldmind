#!/usr/bin/env python3
"""删除剩余的已删除模块引用"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 需要删除的行号（从grep结果）
lines_to_remove = [471, 693, 700]

new_lines = []
removed_count = 0

for i, line in enumerate(lines, start=1):
    if i in lines_to_remove:
        print(f"删除第{i}行: {line.strip()}")
        removed_count += 1
    else:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行")
