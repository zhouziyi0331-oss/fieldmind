#!/usr/bin/env python3
"""最终清理：删除所有已删除模块的引用"""
from pathlib import Path
import re

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 已删除的模块列表
deleted_modules = [
    'skill_generation', 'skill_optimization', 'skills',
    'reports', 'conversation', 'rag', 
    'projects', 'project_chat', 'project_documents',
    'enhanced_chat', 'chat_rag', 'deep_rag',
    'rag_p3', 'hierarchical_retrieval',
    'knowledge_graph', 'documents', 'document_processing',
    'conversation_memory', 'creative_analysis',
    'business_analysis', 'analytics', 'export_summaries', 'ocr',
    'deep_rag_optimization', 'rag_enhanced', 'rag_system'
]

# 删除所有包含这些模块的import和router注册行
lines = content.split('\n')
new_lines = []
skip_next = False
removed_count = 0

for i, line in enumerate(lines):
    should_remove = False
    
    # 检查是否是延迟导入
    for module in deleted_modules:
        if f"from app.api.v1 import {module}" in line or f"from app.api import {module}" in line:
            should_remove = True
            print(f"删除导入: {line.strip()}")
            removed_count += 1
            break
    
    # 检查是否是路由注册
    if not should_remove:
        for module in deleted_modules:
            if f"{module}.router" in line and "app.include_router" in line:
                should_remove = True
                print(f"删除路由: {line.strip()}")
                removed_count += 1
                break
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n✅ 完成！删除了 {removed_count} 行")
