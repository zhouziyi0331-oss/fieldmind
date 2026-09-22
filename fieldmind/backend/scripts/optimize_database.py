"""
数据库索引优化脚本

为关键表添加必要的索引，提升查询性能
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "/Users/alwan/FieldMind/backend/src/data/fieldmind.db"

def optimize_indexes():
    """优化数据库索引"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("🔧 开始优化数据库索引")
    print("="*80)

    # 索引列表
    indexes = [
        # 规范化相关索引（已创建，这里验证）
        ("idx_normalization_logs_file_id", "document_normalization_logs", "file_id"),
        ("idx_normalized_content_file_id", "file_normalized_content", "file_id"),
        ("idx_normalized_content_type", "file_normalized_content", "content_type"),
        ("idx_completeness_checks_file_id", "file_completeness_checks", "file_id"),

        # 文档处理相关（新增）
        ("idx_documents_project_id", "project_documents", "project_id"),
        ("idx_documents_status", "project_documents", "status"),
        ("idx_documents_created_at", "project_documents", "created_at DESC"),

        # 知识图谱相关（如果表存在）
        ("idx_entities_document_id", "entities_unified", "document_id"),
        ("idx_entities_type", "entities_unified", "entity_type"),
        ("idx_events_document_id", "events_unified", "document_id"),
        ("idx_relationships_source", "relationships_unified", "source_entity_id"),
        ("idx_relationships_target", "relationships_unified", "target_entity_id"),
    ]

    created_count = 0
    exists_count = 0
    error_count = 0

    for idx_name, table_name, columns in indexes:
        try:
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"⏭️  跳过 {idx_name}: 表 {table_name} 不存在")
                continue

            # 检查索引是否已存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx_name}'")
            if cursor.fetchone():
                print(f"✓ {idx_name} 已存在")
                exists_count += 1
                continue

            # 创建索引
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({columns})")
            print(f"✅ 创建索引: {idx_name} ON {table_name}({columns})")
            created_count += 1

        except Exception as e:
            print(f"❌ 索引 {idx_name} 创建失败: {e}")
            error_count += 1

    conn.commit()
    conn.close()

    # 总结
    print("\n" + "="*80)
    print("📊 索引优化总结")
    print("="*80)
    print(f"✅ 新创建: {created_count} 个")
    print(f"✓ 已存在: {exists_count} 个")
    print(f"❌ 失败: {error_count} 个")
    print(f"📈 总计: {created_count + exists_count} 个索引")
    print("="*80)

def analyze_query_performance():
    """分析查询性能"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("🔍 查询性能分析")
    print("="*80)

    # 检查各表的行数
    tables = [
        "document_normalization_logs",
        "file_normalized_content",
        "file_completeness_checks",
        "dirty_data_rules"
    ]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table}: {count} 行")
        except:
            print(f"⏭️  {table}: 表不存在")

    conn.close()
    print("="*80)

if __name__ == "__main__":
    optimize_indexes()
    analyze_query_performance()
