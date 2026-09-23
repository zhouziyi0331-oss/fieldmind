#!/usr/bin/env python3
"""分析迁移计划"""
from pathlib import Path
import re

print("="*80)
print("迁移计划分析")
print("="*80)

# 统一模块映射
unified_modules = {
    "unified_knowledge_graph.py": [
        "knowledge_graph.py",
        "knowledge_graph_v2.py", 
        "knowledge_graph_v3.py",
        "v1/knowledge_extraction.py",
        "v1/entity_extraction.py",
        "v1/relation_extraction.py",
        "v1/graph_visualization.py"
    ],
    "unified_documents.py": [
        "documents.py",
        "document_processing.py",
        "v1/document_upload.py",
        "v1/document_metadata.py"
    ],
    "unified_rag.py": [
        "deep_rag.py",
        "chat_rag.py",
        "rag_p3.py",
        "hierarchical_retrieval.py",
        "v1/rag.py"
    ],
    "unified_chat.py": [
        "chat.py",
        "conversation_memory.py",
        "v1/enhanced_chat.py",
        "v1/project_chat.py",
        "v1/conversation.py"
    ],
    "unified_analysis.py": [
        "creative_analysis.py",
        "business_analysis.py",
        "analytics.py"
    ],
    "unified_projects.py": [
        "v1/projects.py",
        "v1/project_documents.py"
    ],
    "unified_skills.py": [
        "v1/skills.py",
        "v1/skill_generation.py",
        "v1/skill_optimization.py"
    ],
    "unified_reports.py": [
        "export_summaries.py",
        "v1/reports.py"
    ],
    "unified_tools.py": [
        "ocr.py"
    ]
}

print("\n📋 迁移映射:")
total_old_modules = 0
for unified, old_modules in unified_modules.items():
    print(f"\n✨ {unified}")
    for old in old_modules:
        exists = Path(f"src/app/api/{old}").exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {old}")
        if exists:
            total_old_modules += 1

print(f"\n📊 统计:")
print(f"   统一模块数: {len(unified_modules)}")
print(f"   需迁移的旧模块: {total_old_modules}")

print("\n🎯 迁移策略:")
print("   1. 保留统一模块的API结构")
print("   2. 从旧模块提取实际业务逻辑")
print("   3. 整合到统一模块中")
print("   4. 测试验证后删除旧模块")

