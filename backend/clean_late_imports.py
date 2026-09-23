#!/usr/bin/env python3
"""清理main.py中已删除模块的延迟导入"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 需要删除的延迟导入关键词
remove_imports = [
    "from app.api import chat_rag",
    "from app.api import deep_rag",
    "from app.api.v1 import deep_rag_optimization",
    "from app.api.v1 import rag_enhanced",
    "from app.api.v1 import rag_system",
    "from app.api.v1 import conversation",
]

new_lines = []
removed_count = 0
skip_next = False

for i, line in enumerate(lines):
    # 检查是否需要删除这一行
    should_remove = False
    for keyword in remove_imports:
        if keyword in line:
            should_remove = True
            print(f"删除第{i+1}行: {line.strip()}")
            removed_count += 1
            # 如果下一行是路由注册，也要删除
            if i+1 < len(lines) and "app.include_router" in lines[i+1]:
                skip_next = True
            break
    
    if skip_next:
        print(f"删除第{i+1}行(关联): {line.strip()}")
        removed_count += 1
        skip_next = False
        continue
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行延迟导入")
