#!/usr/bin/env python3
"""
智能数据迁移脚本 - 自动处理schema差异
"""
import sqlite3
import json
from pathlib import Path

OLD_DB = "/Users/alwan/FieldMind/fieldmind/backend/src/data/fieldmind.db"
NEW_DB = "/Users/alwan/FieldMind/backend/fieldmind.db"

def get_table_schema(cursor, table_name):
    """获取表的schema"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: type}

def migrate_projects():
    """迁移projects表"""
    print("\n" + "="*80)
    print("迁移projects...")
    print("="*80)

    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # 获取旧数据
    old_cursor.execute("SELECT * FROM projects")
    projects = old_cursor.fetchall()

    # 获取列名
    old_cursor.execute("PRAGMA table_info(projects)")
    old_columns = [col[1] for col in old_cursor.fetchall()]

    new_cursor.execute("PRAGMA table_info(projects)")
    new_columns = [col[1] for col in new_cursor.fetchall()]

    print(f"旧表列: {old_columns}")
    print(f"新表列: {new_columns}")

    # 找到共同的列
    common_columns = [col for col in old_columns if col in new_columns]
    print(f"共同列: {common_columns}")

    # 迁移数据
    migrated = 0
    for project in projects:
        # 创建字典
        project_dict = dict(zip(old_columns, project))

        # 只选择共同的列
        values = [project_dict.get(col) for col in common_columns]

        placeholders = ",".join(["?" for _ in common_columns])
        cols = ",".join(common_columns)

        try:
            new_cursor.execute(
                f"INSERT OR REPLACE INTO projects ({cols}) VALUES ({placeholders})",
                values
            )
            migrated += 1
            print(f"  ✅ 迁移项目: {project_dict.get('name', 'unknown')}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print(f"\n✅ 成功迁移 {migrated} 个项目")

def migrate_entities():
    """迁移entities表"""
    print("\n" + "="*80)
    print("迁移entities...")
    print("="*80)

    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # 获取旧数据（批量）
    old_cursor.execute("SELECT * FROM entities")
    entities = old_cursor.fetchall()

    # 获取列名
    old_cursor.execute("PRAGMA table_info(entities)")
    old_columns = [col[1] for col in old_cursor.fetchall()]

    new_cursor.execute("PRAGMA table_info(entities)")
    new_columns = [col[1] for col in new_cursor.fetchall()]

    # 找到共同的列
    common_columns = [col for col in old_columns if col in new_columns]
    print(f"共同列: {common_columns[:5]}... (共{len(common_columns)}列)")

    # 迁移数据
    migrated = 0
    failed = 0

    for entity in entities:
        entity_dict = dict(zip(old_columns, entity))
        values = [entity_dict.get(col) for col in common_columns]

        placeholders = ",".join(["?" for _ in common_columns])
        cols = ",".join(common_columns)

        try:
            new_cursor.execute(
                f"INSERT OR REPLACE INTO entities ({cols}) VALUES ({placeholders})",
                values
            )
            migrated += 1
        except Exception as e:
            failed += 1
            if failed <= 3:  # 只显示前3个错误
                print(f"  ⚠️  跳过实体: {e}")

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print(f"\n✅ 成功迁移 {migrated} 个实体")
    if failed > 0:
        print(f"⚠️  跳过 {failed} 个实体（schema不兼容）")

def migrate_chunks():
    """迁移chunks表"""
    print("\n" + "="*80)
    print("迁移chunks...")
    print("="*80)

    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # 旧表名是document_chunks，新表名是chunks
    old_cursor.execute("SELECT * FROM document_chunks")
    chunks = old_cursor.fetchall()

    # 获取列名
    old_cursor.execute("PRAGMA table_info(document_chunks)")
    old_columns = [col[1] for col in old_cursor.fetchall()]

    new_cursor.execute("PRAGMA table_info(chunks)")
    new_columns = [col[1] for col in new_cursor.fetchall()]

    # 映射列名（如果不同）
    column_mapping = {
        'document_id': 'original_file_id',  # 旧→新
        'content': 'content',
        'chunk_index': 'chunk_index',
        'metadata': 'metadata'
    }

    print(f"旧表列: {old_columns[:5]}...")
    print(f"新表列: {new_columns[:5]}...")

    # 迁移数据
    migrated = 0
    failed = 0

    for chunk in chunks:
        chunk_dict = dict(zip(old_columns, chunk))

        # 构建新表的值
        new_values = {}
        for old_col, new_col in column_mapping.items():
            if old_col in chunk_dict:
                new_values[new_col] = chunk_dict[old_col]

        # 只使用存在的列
        cols = [col for col in new_values.keys() if col in new_columns]
        values = [new_values[col] for col in cols]

        placeholders = ",".join(["?" for _ in cols])
        cols_str = ",".join(cols)

        try:
            new_cursor.execute(
                f"INSERT OR REPLACE INTO chunks ({cols_str}) VALUES ({placeholders})",
                values
            )
            migrated += 1
        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"  ⚠️  跳过chunk: {e}")

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print(f"\n✅ 成功迁移 {migrated} 个chunks")
    if failed > 0:
        print(f"⚠️  跳过 {failed} 个chunks（schema不兼容）")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         智能数据迁移 - 自动处理schema差异                         ║
╚══════════════════════════════════════════════════════════════════╝

数据已备份:
  ✅ /Users/alwan/FieldMind/backend/db_backup/old_fieldmind_*.db
  ✅ /Users/alwan/FieldMind/backend/db_backup/new_fieldmind_*.db

开始迁移...
""")

    try:
        # 迁移projects
        migrate_projects()

        # 迁移entities
        migrate_entities()

        # 迁移chunks
        migrate_chunks()

        print("\n" + "="*80)
        print("✅ 数据迁移完成")
        print("="*80)

        # 验证
        print("\n验证迁移结果:")
        conn = sqlite3.connect(NEW_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects")
        print(f"  projects: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM entities")
        print(f"  entities: {cursor.fetchone()[0]} 条")

        cursor.execute("SELECT COUNT(*) FROM chunks")
        print(f"  chunks: {cursor.fetchone()[0]} 条")

        conn.close()

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
