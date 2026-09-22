#!/usr/bin/env python3
"""检查缺失的功能和工作流"""

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(".")

# 期望的功能清单
EXPECTED_FEATURES = {
    "数据采集": ["upload", "drag_drop", "batch_upload"],
    "内容提取": ["transcript", "ocr", "pdf_extract", "video_extract"],
    "文本处理": ["chunking", "cleaning", "normalization"],
    "量化分析": ["word_count", "emotion", "subjectivity", "tfidf"],
    "语义处理": ["embedding", "vector_search", "semantic_similarity"],
    "知识构建": ["entity_extraction", "relation_extraction", "event_extraction"],
    "知识图谱": ["graph_build", "graph_query", "graph_visualization"],
    "工作流": ["orchestrator", "task_queue", "retry"],
    "报告": ["layer1_report", "layer2_report", "layer3_report"],
    "对话": ["chat", "qa", "context_memory"],
    "权限": ["auth", "permission", "audit"],
    "溯源": ["citation", "traceback", "lineage"],
    "资产": ["skill", "template", "asset_deposit"],
    "评测": ["test_cases", "metrics", "evaluation"],
}

def check_feature_implemented(keyword):
    """检查功能是否实现"""
    for ext in ['*.py', '*.js']:
        for f in PROJECT_ROOT.rglob(ext):
            if 'venv' in str(f) or '.git' in str(f) or 'node_modules' in str(f):
                continue
            if keyword.lower() in f.name.lower():
                return True
            try:
                if keyword.lower() in f.read_text(encoding='utf-8', errors='ignore').lower():
                    return True
            except:
                pass
    return False

def check_db_tables():
    """检查数据库表"""
    db_paths = [
        os.path.expanduser("~/Library/Application Support/FieldMind/fieldmind.db"),
        "./user_data/fieldmind.db",
        "./fieldmind.db",
    ]

    for db_path in db_paths:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()
            return tables
    return set()

def main():
    print("🔍 检查功能缺口...\n")
    print("=" * 60)

    tables = check_db_tables()

    missing_features = []
    for category, features in EXPECTED_FEATURES.items():
        print(f"\n📌 {category}")
        for feature in features:
            implemented = check_feature_implemented(feature)
            status = "✅" if implemented else "❌"
            print(f"   {status} {feature}")
            if not implemented:
                missing_features.append(f"{category}/{feature}")

    print("\n" + "=" * 60)
    print(f"\n📊 缺口总结：{len(missing_features)} 个功能未实现")
    for f in missing_features[:30]:
        print(f"   ❌ {f}")
    if len(missing_features) > 30:
        print(f"   ... 还有 {len(missing_features) - 30} 个")

    # 检查数据库表缺口
    expected_tables = {
        "projects", "project_documents", "chunks", "keywords",
        "entities", "entity_relations", "events", "timeline_events",
        "evaluation_test_cases", "evaluation_runs",
        "knowledge_sources", "agent_traces",
    }

    missing_tables = expected_tables - tables
    if missing_tables:
        print(f"\n📊 缺失的数据库表：")
        for t in missing_tables:
            print(f"   ❌ {t}")
    else:
        print(f"\n✅ 所有预期数据库表都存在")

if __name__ == "__main__":
    main()
