"""
Week 2 - Day 4: 扫描所有引用 entities 的外键
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"

def scan_foreign_keys():
    """扫描所有可能引用 entities 表的外键"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("扫描所有可能引用 entities 的外键")
    print("=" * 60)

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    foreign_key_references = []

    for table_name in tables:
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 查找可能的外键列（包含 entity 关键字的列）
        entity_columns = []
        for col in columns:
            col_name = col[1].lower()
            if 'entity' in col_name and 'id' in col_name:
                entity_columns.append({
                    'column_name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4]
                })

        if entity_columns:
            # 获取这个表的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

            # 对每个可能的外键列进行分析
            for col_info in entity_columns:
                col_name = col_info['column_name']

                # 检查是否有非空值
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NOT NULL")
                non_null_count = cursor.fetchone()[0]

                # 如果有数据，检查是否匹配 entities.id
                matches_old_id = 0
                matches_new_id = 0
                sample_values = []

                if non_null_count > 0:
                    # 获取样本值
                    cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 5")
                    sample_values = [row[0] for row in cursor.fetchall()]

                    # 检查是否匹配旧 ID (entities.id)
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT t.{col_name})
                        FROM {table_name} t
                        INNER JOIN entities e ON t.{col_name} = e.id
                        WHERE t.{col_name} IS NOT NULL
                    """)
                    matches_old_id = cursor.fetchone()[0]

                    # 检查是否匹配新 ID (entities.entity_id)
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT t.{col_name})
                        FROM {table_name} t
                        INNER JOIN entities e ON t.{col_name} = e.entity_id
                        WHERE t.{col_name} IS NOT NULL
                    """)
                    matches_new_id = cursor.fetchone()[0]

                foreign_key_references.append({
                    'table': table_name,
                    'column': col_name,
                    'total_records': count,
                    'non_null_count': non_null_count,
                    'matches_old_id': matches_old_id,
                    'matches_new_id': matches_new_id,
                    'sample_values': sample_values,
                    'needs_update': matches_old_id > 0 and matches_new_id == 0
                })

    conn.close()

    return foreign_key_references


def generate_update_report(references):
    """生成外键更新报告"""

    print("\n" + "=" * 60)
    print("外键引用分析报告")
    print("=" * 60)

    needs_update = [ref for ref in references if ref['needs_update']]
    already_updated = [ref for ref in references if ref['matches_new_id'] > 0]
    no_data = [ref for ref in references if ref['non_null_count'] == 0]

    print(f"\n总共发现 {len(references)} 个可能的外键列")
    print(f"  - 需要更新: {len(needs_update)}")
    print(f"  - 已经更新: {len(already_updated)}")
    print(f"  - 无数据: {len(no_data)}")

    if needs_update:
        print("\n" + "-" * 60)
        print("需要更新的外键:")
        print("-" * 60)
        print(f"{'表名':<25} {'列名':<25} {'记录数':<10} {'匹配旧ID':<10}")
        print("-" * 60)

        for ref in needs_update:
            print(f"{ref['table']:<25} {ref['column']:<25} {ref['non_null_count']:<10} {ref['matches_old_id']:<10}")
            if ref['sample_values']:
                print(f"  示例值: {ref['sample_values'][0]}")

    if already_updated:
        print("\n" + "-" * 60)
        print("已经使用新 ID 的外键:")
        print("-" * 60)
        for ref in already_updated:
            print(f"  ✅ {ref['table']}.{ref['column']} (匹配 {ref['matches_new_id']} 条)")

    return needs_update


def generate_update_script(references_to_update):
    """生成外键更新脚本"""

    script = """#!/usr/bin/env python3
\"\"\"
Week 2 - Day 4: 自动生成的外键更新脚本
更新所有引用 entities.id 的外键为 entities.entity_id
\"\"\"

import sqlite3
from datetime import datetime

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_ID = f"foreign_key_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def update_foreign_keys():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("更新外键引用")
    print("=" * 60)

    # 记录日志
    cursor.execute(\"\"\"
        INSERT INTO migration_log (batch_id, table_name, operation, started_at, status)
        VALUES (?, 'multiple', 'update_foreign_keys', ?, 'running')
    \"\"\", (BATCH_ID, datetime.now()))
    log_id = cursor.lastrowid
    conn.commit()

    total_updated = 0
    errors = []

"""

    for ref in references_to_update:
        table = ref['table']
        column = ref['column']

        script += f"""
    # 更新 {table}.{column}
    print(f"\\n更新 {table}.{column}...")
    try:
        cursor.execute(\"\"\"
            UPDATE {table}
            SET {column} = (
                SELECT entity_id
                FROM entities
                WHERE id = {table}.{column}
            )
            WHERE {column} IN (SELECT id FROM entities)
        \"\"\")

        updated = cursor.rowcount
        total_updated += updated
        print(f"  ✅ 更新了 {{updated}} 条记录")
        conn.commit()
    except Exception as e:
        error_msg = f"{table}.{column}: {{e}}"
        errors.append(error_msg)
        print(f"  ❌ {{error_msg}}")
        conn.rollback()
"""

    script += """
    # 更新日志
    status = "completed" if len(errors) == 0 else "completed_with_errors"
    error_message = "\\n".join(errors[:10]) if errors else None

    cursor.execute(\"\"\"
        UPDATE migration_log
        SET completed_at = ?,
            status = ?,
            records_affected = ?,
            error_message = ?
        WHERE id = ?
    \"\"\", (datetime.now(), status, total_updated, error_message, log_id))

    conn.commit()
    conn.close()

    print(f"\\n✅ 总共更新了 {total_updated} 条记录")
    if errors:
        print(f"⚠️  遇到 {len(errors)} 个错误")

if __name__ == "__main__":
    update_foreign_keys()
"""

    return script


def main():
    """主函数"""

    # 扫描外键
    references = scan_foreign_keys()

    # 生成报告
    needs_update = generate_update_report(references)

    # 生成更新脚本
    if needs_update:
        script_content = generate_update_script(needs_update)

        script_path = Path("/Users/alwan/Downloads/FieldMind/fieldmind/scripts/week2_update_foreign_keys.py")
        script_path.write_text(script_content, encoding='utf-8')

        print(f"\n✅ 已生成外键更新脚本:")
        print(f"   {script_path}")
        print(f"\n运行命令:")
        print(f"   python3 {script_path}")
    else:
        print("\n✅ 没有需要更新的外键")

    # 保存完整报告
    report_path = Path("/Users/alwan/Downloads/FieldMind/fieldmind/WEEK2_FOREIGN_KEY_SCAN.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(references, f, indent=2, ensure_ascii=False)

    print(f"\n完整报告已保存到:")
    print(f"   {report_path}")


if __name__ == "__main__":
    main()
