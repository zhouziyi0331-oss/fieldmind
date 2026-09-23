#!/usr/bin/env python3
"""删除kg_new和kg_api的引用"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
removed_count = 0

for i, line in enumerate(lines, start=1):
    should_remove = False
    
    # 删除包含kg_new或kg_api的路由注册
    if ('kg_new.router' in line or 'kg_api.' in line) and ('app.include_router' in line or 'return await' in line):
        should_remove = True
        print(f"删除第{i}行: {line.strip()[:80]}")
        removed_count += 1
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行")
