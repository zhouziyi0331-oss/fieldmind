"""
Week 2 - Day 2: 创建 ID 映射表和迁移框架
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"

def create_id_mapping_table():
    """创建 ID 映射表"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("创建 ID 映射表...")

    # 创建映射表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS id_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_id TEXT NOT NULL,
            new_id TEXT NOT NULL UNIQUE,
            entity_type TEXT NOT NULL,
            table_name TEXT NOT NULL,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            migration_batch TEXT,
            notes TEXT
        )
    """)

    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_id_mapping_old_id
        ON id_mapping(old_id, table_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_id_mapping_new_id
        ON id_mapping(new_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_id_mapping_entity_type
        ON id_mapping(entity_type)
    """)

    conn.commit()
    print("✅ ID 映射表创建成功")

    # 验证表结构
    cursor.execute("PRAGMA table_info(id_mapping)")
    columns = cursor.fetchall()

    print("\n表结构:")
    for col in columns:
        print(f"  {col[1]:20} {col[2]:15}")

    conn.close()


def create_migration_log_table():
    """创建迁移日志表"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n创建迁移日志表...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            records_affected INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            metadata TEXT
        )
    """)

    conn.commit()
    print("✅ 迁移日志表创建成功")

    conn.close()


def verify_current_ids():
    """验证当前数据库中的 ID 格式"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("验证当前 ID 格式")
    print("=" * 60)

    # 检查 entities 表
    print("\n📊 entities 表:")
    cursor.execute("SELECT id, name, type FROM entities LIMIT 5")
    entities = cursor.fetchall()

    print(f"  记录数: {len(entities)}")
    print(f"  ID 类型: {type(entities[0][0]).__name__ if entities else 'N/A'}")
    print(f"  示例:")
    for ent in entities[:3]:
        print(f"    ID={ent[0]}, name={ent[1]}, type={ent[2]}")

    # 检查 document_chunks 表
    print("\n📊 document_chunks 表:")
    cursor.execute("SELECT id FROM document_chunks LIMIT 5")
    chunks = cursor.fetchall()

    print(f"  记录数: {len(chunks)}")
    print(f"  ID 类型: {type(chunks[0][0]).__name__ if chunks else 'N/A'}")
    if chunks:
        print(f"  示例: {chunks[0][0]}")

    # 检查是否有 entity_id 或 chunk_id 列
    cursor.execute("PRAGMA table_info(entities)")
    entity_columns = [col[1] for col in cursor.fetchall()]

    has_entity_id = 'entity_id' in entity_columns
    print(f"\n  entities 表是否有 entity_id 列: {'✅' if has_entity_id else '❌'}")

    cursor.execute("PRAGMA table_info(document_chunks)")
    chunk_columns = [col[1] for col in cursor.fetchall()]

    has_chunk_id = 'chunk_id' in chunk_columns
    print(f"  document_chunks 表是否有 chunk_id 列: {'✅' if has_chunk_id else '❌'}")

    conn.close()

    return {
        "entities_has_new_id": has_entity_id,
        "chunks_has_new_id": has_chunk_id
    }


def add_new_id_columns():
    """为现有表添加新的 ID 列"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("为表添加新 ID 列")
    print("=" * 60)

    # 为 entities 表添加 entity_id 列
    try:
        print("\n为 entities 表添加 entity_id 列...")
        cursor.execute("""
            ALTER TABLE entities
            ADD COLUMN entity_id TEXT UNIQUE
        """)
        print("✅ entity_id 列添加成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️  entity_id 列已存在")
        else:
            print(f"❌ 错误: {e}")

    # 为 document_chunks 表添加 chunk_id 列
    try:
        print("\n为 document_chunks 表添加 chunk_id 列...")
        cursor.execute("""
            ALTER TABLE document_chunks
            ADD COLUMN chunk_id TEXT UNIQUE
        """)
        print("✅ chunk_id 列添加成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️  chunk_id 列已存在")
        else:
            print(f"❌ 错误: {e}")

    # 创建索引
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_entity_id ON entities(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chunk_id ON document_chunks(chunk_id)")
        print("✅ 索引创建成功")
    except Exception as e:
        print(f"⚠️  索引创建: {e}")

    conn.commit()
    conn.close()


def generate_migration_plan():
    """生成迁移计划"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("生成迁移计划")
    print("=" * 60)

    # 统计需要迁移的表
    tables_to_migrate = [
        ("entities", "entity", "entity_id"),
        ("document_chunks", "chunk", "chunk_id"),
        ("entity_relations", "relation", "id"),  # 这个表需要确认
    ]

    migration_plan = []

    for table_name, entity_type, id_column in tables_to_migrate:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

            # 检查是否已有新 ID
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            has_new_id = id_column in columns

            # 如果有新 ID 列，检查有多少已填充
            filled_count = 0
            if has_new_id:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {id_column} IS NOT NULL")
                filled_count = cursor.fetchone()[0]

            migration_plan.append({
                "table": table_name,
                "entity_type": entity_type,
                "id_column": id_column,
                "total_records": count,
                "has_new_id_column": has_new_id,
                "filled_records": filled_count,
                "needs_migration": count - filled_count
            })

        except sqlite3.OperationalError as e:
            print(f"⚠️  表 {table_name} 不存在或无法访问: {e}")

    # 显示迁移计划
    print("\n迁移计划:")
    print("-" * 80)
    print(f"{'表名':<20} {'类型':<10} {'总记录':<10} {'已迁移':<10} {'待迁移':<10} {'状态':<10}")
    print("-" * 80)

    for plan in migration_plan:
        status = "✅" if plan['needs_migration'] == 0 else "⏳"
        print(f"{plan['table']:<20} {plan['entity_type']:<10} {plan['total_records']:<10} "
              f"{plan['filled_records']:<10} {plan['needs_migration']:<10} {status:<10}")

    conn.close()

    return migration_plan


if __name__ == "__main__":
    print("=" * 60)
    print("FieldMind ID 迁移准备")
    print("Week 2 - Day 2")
    print("=" * 60)

    # 步骤 1: 创建映射表
    create_id_mapping_table()

    # 步骤 2: 创建迁移日志表
    create_migration_log_table()

    # 步骤 3: 验证当前 ID 格式
    current_status = verify_current_ids()

    # 步骤 4: 添加新 ID 列
    add_new_id_columns()

    # 步骤 5: 生成迁移计划
    migration_plan = generate_migration_plan()

    print("\n" + "=" * 60)
    print("✅ 准备工作完成")
    print("=" * 60)
    print("\n下一步: 执行实际的 ID 迁移")
    print("运行: python3 week2_migrate_ids.py")
