#!/usr/bin/env python3
"""检查数据库中的数据断连、空数据、未处理数据"""

import sqlite3
import os
import sys

DB_PATHS = [
    os.path.expanduser("~/Library/Application Support/FieldMind/fieldmind.db"),
    "./user_data/fieldmind.db",
    "./fieldmind.db",
    "../fieldmind.db",
]

def find_db():
    for p in DB_PATHS:
        if os.path.exists(p):
            return p
    return None

def check_table(cursor, table_name):
    """检查单张表的数据完整性"""
    result = {"table": table_name, "total": 0, "issues": []}

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        result["total"] = cursor.fetchone()[0]
    except Exception as e:
        result["issues"].append(f"表不存在或无法访问: {e}")
        return result

    if result["total"] == 0:
        result["issues"].append("⚠️ 完全空表")
        return result

    # 检查空字段（动态获取列名）
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]

        for col in columns:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL OR {col} = ''")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                pct = null_count / result["total"] * 100
                if pct > 50:
                    result["issues"].append(f"❌ {col}: {null_count}/{result['total']} 为空 ({pct:.0f}%)")
                elif pct > 10:
                    result["issues"].append(f"⚠️ {col}: {null_count}/{result['total']} 为空 ({pct:.0f}%)")
    except Exception as e:
        result["issues"].append(f"字段检查失败: {e}")

    return result

def check_relations(cursor):
    """检查表之间的关联是否断裂"""
    issues = []

    try:
        # chunks → project_documents 关联
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE original_file_id NOT IN (SELECT id FROM project_documents)")
        orphan_chunks = cursor.fetchone()[0]
        if orphan_chunks > 0:
            issues.append(f"❌ chunks 表有 {orphan_chunks} 条记录找不到对应的 project_documents")
    except:
        pass

    try:
        # project_documents → projects 关联
        cursor.execute("SELECT COUNT(*) FROM project_documents WHERE project_id NOT IN (SELECT id FROM projects)")
        orphan_files = cursor.fetchone()[0]
        if orphan_files > 0:
            issues.append(f"❌ project_documents 表有 {orphan_files} 条记录找不到对应的 project")
    except:
        pass

    return issues

def main():
    db_path = find_db()
    if not db_path:
        print("❌ 找不到数据库文件")
        print("尝试搜索的路径:")
        for p in DB_PATHS:
            print(f"   {p}")
        sys.exit(1)

    print(f"📊 数据库: {db_path}")
    print(f"   大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"共 {len(tables)} 张表\n")
    print("=" * 60)

    empty_tables = []
    dirty_tables = []

    for table in sorted(tables):
        result = check_table(cursor, table)
        status = "✅" if not result["issues"] else "⚠️"
        print(f"\n{status} {result['table']} ({result['total']} 条)")
        for issue in result["issues"]:
            print(f"   {issue}")

        if result["total"] == 0:
            empty_tables.append(table)
        elif result["issues"]:
            dirty_tables.append(table)

    print("\n" + "=" * 60)
    print("\n📋 表关联检查：")
    relation_issues = check_relations(cursor)
    if relation_issues:
        for issue in relation_issues:
            print(f"   {issue}")
    else:
        print("   ✅ 无断连")

    print("\n" + "=" * 60)
    print(f"\n📊 总结：")
    print(f"   空表: {len(empty_tables)} 张 → {', '.join(empty_tables) if empty_tables else '无'}")
    print(f"   脏表: {len(dirty_tables)} 张 → {', '.join(dirty_tables) if dirty_tables else '无'}")

    conn.close()

if __name__ == "__main__":
    main()
