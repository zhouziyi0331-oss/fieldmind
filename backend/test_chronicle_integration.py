#!/usr/bin/env python3
"""
测试编年史和关键词集成 - 完整的端到端验证
"""
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def test_integration():
    """测试集成状态"""

    # 连接数据库
    db_path = Path(__file__).parent / 'src' / 'data' / 'fieldmind.db'
    if not db_path.exists():
        print(f"❌ 数据库不存在: {db_path}")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    db = Session()

    print("=" * 80)
    print("📊 FieldMind 编年史和关键词集成测试")
    print("=" * 80)
    print()

    # 1. 检查数据库表结构
    print("1️⃣ 检查数据库表结构")
    print("-" * 80)

    # 检查 timeline_events 表
    result = db.execute(text("PRAGMA table_info(timeline_events)")).fetchall()
    timeline_columns = [row[1] for row in result]
    print(f"✅ timeline_events 表字段 ({len(timeline_columns)}个):")
    required_fields = ['id', 'project_id', 'document_id', 'event_type', 'date',
                      'title', 'description', 'confidence_score', 'source_type', 'metadata', 'narrative']
    for field in required_fields:
        status = "✅" if field in timeline_columns else "❌"
        print(f"   {status} {field}")

    print()

    # 检查 document_keywords 表
    result = db.execute(text("PRAGMA table_info(document_keywords)")).fetchall()
    if result:
        keyword_columns = [row[1] for row in result]
        print(f"✅ document_keywords 表字段 ({len(keyword_columns)}个):")
        for col in keyword_columns[:5]:  # 显示前5个
            print(f"   • {col}")
        print(f"   ... 共 {len(keyword_columns)} 个字段")
    else:
        print("❌ document_keywords 表不存在")

    print()

    # 2. 检查现有文档数量
    print("2️⃣ 检查现有文档")
    print("-" * 80)

    doc_count = db.execute(text("SELECT COUNT(*) FROM project_documents")).scalar()
    print(f"📄 总文档数: {doc_count}")

    # 显示前5个文档
    docs = db.execute(text("""
        SELECT id, filename, file_path, created_at
        FROM project_documents
        ORDER BY created_at DESC
        LIMIT 5
    """)).fetchall()

    print(f"\n最近的文档:")
    for doc in docs:
        filename = doc[1] if doc[1] else "未命名"
        created = doc[3] if doc[3] else "未知时间"
        print(f"  • ID {doc[0]}: {filename[:50]} ({created})")

    print()

    # 3. 检查时间线事件提取情况
    print("3️⃣ 检查时间线事件提取")
    print("-" * 80)

    total_events = db.execute(text("SELECT COUNT(*) FROM timeline_events")).scalar()
    print(f"📅 总时间线事件数: {total_events}")

    # 按 document_id 分组统计
    events_by_doc = db.execute(text("""
        SELECT document_id, COUNT(*) as cnt
        FROM timeline_events
        WHERE document_id IS NOT NULL
        GROUP BY document_id
        ORDER BY cnt DESC
        LIMIT 5
    """)).fetchall()

    if events_by_doc:
        print(f"\n已提取事件的文档:")
        for doc_id, cnt in events_by_doc:
            print(f"  • 文档 {doc_id}: {cnt} 个事件")
    else:
        print("⚠️ 没有文档级别的时间线事件（需要批量提取）")

    # 检查事件类型分布
    event_types = db.execute(text("""
        SELECT event_type, COUNT(*) as cnt
        FROM timeline_events
        WHERE event_type IS NOT NULL
        GROUP BY event_type
        ORDER BY cnt DESC
    """)).fetchall()

    if event_types:
        print(f"\n事件类型分布:")
        for event_type, cnt in event_types:
            print(f"  • {event_type}: {cnt} 个")

    print()

    # 4. 检查关键词提取情况
    print("4️⃣ 检查关键词提取")
    print("-" * 80)

    total_keywords = db.execute(text("SELECT COUNT(*) FROM document_keywords")).scalar()
    print(f"🔑 总关键词数: {total_keywords}")

    # 按文档统计
    keywords_by_doc = db.execute(text("""
        SELECT document_id, COUNT(*) as cnt
        FROM document_keywords
        GROUP BY document_id
        ORDER BY cnt DESC
        LIMIT 5
    """)).fetchall()

    if keywords_by_doc:
        print(f"\n已提取关键词的文档:")
        for doc_id, cnt in keywords_by_doc:
            print(f"  • 文档 {doc_id}: {cnt} 个关键词")
    else:
        print("⚠️ 没有文档关键词（需要批量提取）")

    # 显示高权重关键词
    top_keywords = db.execute(text("""
        SELECT dk.keyword_id, dk.weight, dk.extraction_method, COUNT(*) as doc_count
        FROM document_keywords dk
        GROUP BY dk.keyword_id
        ORDER BY dk.weight DESC
        LIMIT 10
    """)).fetchall()

    if top_keywords:
        print(f"\n高权重关键词 (Top 10):")
        for keyword_id, weight, method, doc_count in top_keywords:
            print(f"  • 关键词ID {keyword_id} (权重: {weight:.3f}, 方法: {method}, 出现在 {doc_count} 个文档)")

    print()

    # 5. 统计需要补充提取的文档
    print("5️⃣ 需要补充提取的文档")
    print("-" * 80)

    # 没有时间线事件的文档
    docs_without_events = db.execute(text("""
        SELECT COUNT(*)
        FROM project_documents pd
        LEFT JOIN timeline_events te ON pd.id = te.document_id
        WHERE te.id IS NULL
    """)).scalar()

    print(f"📄 缺少时间线事件的文档: {docs_without_events}/{doc_count}")

    # 没有关键词的文档
    docs_without_keywords = db.execute(text("""
        SELECT COUNT(*)
        FROM project_documents pd
        LEFT JOIN document_keywords dk ON pd.id = dk.document_id
        WHERE dk.id IS NULL
    """)).scalar()

    print(f"📄 缺少关键词的文档: {docs_without_keywords}/{doc_count}")

    print()

    # 6. 总结
    print("=" * 80)
    print("📋 集成状态总结")
    print("=" * 80)

    issues = []

    if all(f in timeline_columns for f in required_fields):
        print("✅ 数据库结构完整")
    else:
        print("❌ 数据库结构缺少字段")
        issues.append("数据库结构")

    if total_events > 0 and events_by_doc:
        print("✅ 时间线事件提取正常工作")
    else:
        print("⚠️ 时间线事件提取需要验证")
        issues.append("时间线提取")

    if total_keywords > 0 and keywords_by_doc:
        print("✅ 关键词提取正常工作")
    else:
        print("⚠️ 关键词提取需要验证")
        issues.append("关键词提取")

    if docs_without_events > 0 or docs_without_keywords > 0:
        print(f"⚠️ 需要为 {max(docs_without_events, docs_without_keywords)} 个文档补充提取")
        issues.append("批量补充")

    print()

    if not issues:
        print("🎉 集成完美！所有功能正常工作")
    else:
        print(f"📝 待处理项: {', '.join(issues)}")

    print()

    db.close()

if __name__ == '__main__':
    test_integration()
