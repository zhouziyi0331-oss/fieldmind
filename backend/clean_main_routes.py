#!/usr/bin/env python3
"""清理main.py中已删除模块的路由注册"""
from pathlib import Path

# 读取main.py
main_file = Path("src/app/main.py")
with open(main_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 需要删除的路由注册行（包含这些关键词的行）
remove_keywords = [
    "chat.router",
    "chat_rag.router",
    "deep_rag.router",
    "rag_p3.router",
    "hierarchical_retrieval.router",
    "knowledge_graph.router",
    "documents.router",
    "document_processing.router",
    "conversation_memory.router",
    "creative_analysis.router",
    "business_analysis.router",
    "analytics.router",
    "export_summaries.router",
    "ocr.router",
    "v1_projects.router",
    "project_documents.router",
    "project_chat.router",
    "enhanced_chat.router",
]

new_lines = []
removed_count = 0

for i, line in enumerate(lines):
    # 检查是否需要删除这一行
    should_remove = False
    for keyword in remove_keywords:
        if keyword in line and "app.include_router" in line:
            # 跳过已注释的行
            if line.strip().startswith("#"):
                continue
            should_remove = True
            print(f"删除第{i+1}行: {line.strip()}")
            removed_count += 1
            break
    
    if not should_remove:
        new_lines.append(line)

# 写回文件
with open(main_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 完成！删除了 {removed_count} 行路由注册")
