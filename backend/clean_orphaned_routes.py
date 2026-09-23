#!/usr/bin/env python3
"""清理孤立的路由注册（导入已删除但路由注册仍存在）"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 这些模块的导入已被删除，但路由注册可能还在
orphaned_modules = [
    'deep_rag_optimization',
    'rag_enhanced',
    'rag_system',
    'knowledge_graph_p3',
    'knowledge_graph_api',
    'knowledge_graph_enhanced',
    'document_processing_v2',
    'knowledge_graph_v3',
]

new_lines = []
removed_count = 0
in_try_block = False
try_block_module = None

for i, line in enumerate(lines, start=1):
    should_remove = False
    
    # 检查路由注册
    if 'app.include_router' in line:
        for module in orphaned_modules:
            if f'{module}.router' in line:
                should_remove = True
                print(f"删除第{i}行: {line.strip()[:80]}")
                removed_count += 1
                break
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行孤立路由")
