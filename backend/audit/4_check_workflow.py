#!/usr/bin/env python3
"""检查工作流是否形成闭环"""

import os
from pathlib import Path

PROJECT_ROOT = Path(".")

# 期望的工作流节点
EXPECTED_WORKFLOW = {
    "采集": ["upload", "ingestion", "document_processing"],
    "处理": ["transcript", "chunking", "vectorization", "quantification"],
    "理解": ["entity", "relation", "keyword", "knowledge_graph"],
    "分析": ["analysis", "report", "business"],
    "协同": ["chat", "conversation", "qa"],
    "复用": ["skill", "template", "asset"],
}

def find_implementations(keyword):
    """查找某个功能的所有实现文件"""
    matches = []
    for ext in ['*.py', '*.js', '*.html']:
        for f in PROJECT_ROOT.rglob(ext):
            if 'venv' in str(f) or '.git' in str(f) or 'node_modules' in str(f):
                continue
            if keyword.lower() in f.name.lower():
                matches.append(str(f))
            else:
                try:
                    content = f.read_text(encoding='utf-8', errors='ignore')
                    if keyword.lower() in content.lower():
                        matches.append(str(f))
                        break  # 只记录一次
                except:
                    pass
    return list(set(matches))[:5]  # 最多返回5个

def main():
    print("🔍 检查工作流完整性...\n")
    print("=" * 60)

    for stage, keywords in EXPECTED_WORKFLOW.items():
        print(f"\n📌 {stage}阶段")
        print("-" * 60)

        for kw in keywords:
            files = find_implementations(kw)
            if files:
                status = "✅"
                print(f"   {status} {kw}: {len(files)} 个文件")
                # 显示前3个
                for f in files[:3]:
                    print(f"       └─ {f}")
            else:
                print(f"   ❌ {kw}: 未找到实现")

    print("\n" + "=" * 60)
    print("\n📋 数据流检查：")

    # 检查关键表是否存在
    import sqlite3
    db_paths = [
        os.path.expanduser("~/Library/Application Support/FieldMind/fieldmind.db"),
        "./user_data/fieldmind.db",
        "./fieldmind.db",
    ]

    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\n数据库: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "projects", "project_documents", "chunks", "keywords",
                "entities", "entity_relations", "events",
                "evaluation_test_cases", "evaluation_runs",
                "agent_traces", "knowledge_sources"
            ]

            for t in expected_tables:
                if t in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {t}")
                    count = cursor.fetchone()[0]
                    status = "✅" if count > 0 else "⚠️"
                    print(f"   {status} {t}: {count} 条")
                else:
                    print(f"   ❌ {t}: 表不存在")

            conn.close()
            break

if __name__ == "__main__":
    main()
