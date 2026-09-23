#!/usr/bin/env python3
"""执行第三批模块迁移和清理"""
from pathlib import Path
import shutil

# 第三批：复杂模块
batch_3_removals = [
    # 聊天模块
    "src/app/api/chat.py",
    "src/app/api/conversation_memory.py",
    "src/app/api/v1/enhanced_chat.py",
    "src/app/api/v1/project_chat.py",
    "src/app/api/v1/conversation.py",
    # RAG模块
    "src/app/api/deep_rag.py",
    "src/app/api/chat_rag.py",
    "src/app/api/rag_p3.py",
    "src/app/api/hierarchical_retrieval.py",
    "src/app/api/v1/rag.py",
    # 知识图谱模块
    "src/app/api/knowledge_graph.py",
    "src/app/api/knowledge_graph_v3.py",
    # 报告模块
    "src/app/api/v1/reports.py",
]

print("="*80)
print("阶段5: 模块迁移和清理 - 第三批")
print("="*80)

removed = []
not_found = []

for module_path in batch_3_removals:
    path = Path(module_path)
    if path.exists():
        # 备份到archive
        archive_path = Path("archive/old_modules") / path.name
        shutil.copy2(path, archive_path)
        print(f"✓ 备份: {path.name}")
        
        # 删除原文件
        path.unlink()
        print(f"✓ 删除: {module_path}")
        removed.append(module_path)
    else:
        print(f"✗ 未找到: {module_path}")
        not_found.append(module_path)

print(f"\n📊 第三批统计:")
print(f"   已删除: {len(removed)} 个文件")
print(f"   未找到: {len(not_found)} 个文件")

print("\n✅ 第三批完成！")
