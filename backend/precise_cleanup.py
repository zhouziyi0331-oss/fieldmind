#!/usr/bin/env python3
"""精确清理已删除的模块"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 精确的已删除模块列表（只删除这些）
deleted_exact = [
    'chat.router',
    'documents.router',
    'document_processing.router',
    'conversation_memory.router',
    'creative_analysis.router',
    'business_analysis.router',
    'analytics.router',
    'export_summaries.router',
    'ocr.router',
    'chat_rag.router',
    'deep_rag.router',
    'rag_p3.router',
    'hierarchical_retrieval.router',
    'knowledge_graph.router',
    'knowledge_graph_v3.router',
    'knowledge_graph_p3.router',
    'knowledge_graph_api.router',
    'knowledge_graph_enhanced.router',
    'document_processing_v2.router',
    'rag.router',
    'v1_projects.router',
    'project_documents.router',
    'project_chat.router',
    'enhanced_chat.router',
    'skills.router',
    'skill_generation.router',
    'skill_optimization.router',
    'reports.router',
    'conversation.router',
]

new_lines = []
removed_count = 0

i = 0
while i < len(lines):
    line = lines[i]
    should_remove = False
    
    # 检查路由注册
    if 'app.include_router' in line:
        for module in deleted_exact:
            if module in line:
                should_remove = True
                print(f"删除第{i+1}行: {line.strip()[:80]}")
                removed_count += 1
                break
    
    if not should_remove:
        new_lines.append(line)
    
    i += 1

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行路由注册")
