#!/usr/bin/env python3
"""彻底清理所有已删除模块的导入"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 已删除模块的完整列表
deleted_imports = [
    'from app.api import chat_rag',
    'from app.api import deep_rag',
    'from app.api import knowledge_graph_p3',
    'from app.api import rag_p3',
    'from app.api import hierarchical_retrieval',
    'from app.api import analytics',
    'from app.api import ocr',
    'from app.api import knowledge_graph as kg_new',
    'from app.api import knowledge_graph as kg_api',
    'from app.api import document_processing_v2',
    'from app.api import knowledge_graph_v3',
    'from app.api.v1 import knowledge_graph',
    'from app.api.v1 import knowledge_graph_api',
    'from app.api.v1 import knowledge_graph_enhanced',
    'from app.api.v1 import deep_rag_optimization',
    'from app.api.v1 import rag_enhanced',
    'from app.api.v1 import rag_system',
]

new_lines = []
removed_count = 0

for i, line in enumerate(lines, start=1):
    should_remove = False
    
    # 检查是否是需要删除的导入
    for imp in deleted_imports:
        if imp in line:
            should_remove = True
            print(f"删除第{i}行: {line.strip()}")
            removed_count += 1
            break
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行导入")
