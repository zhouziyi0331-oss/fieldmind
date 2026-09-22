#!/usr/bin/env python3
"""
Week 2 - Day 4: 自动生成的外键更新脚本
更新所有引用 entities.id 的外键为 entities.entity_id
"""

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
    cursor.execute("""
        INSERT INTO migration_log (batch_id, table_name, operation, started_at, status)
        VALUES (?, 'multiple', 'update_foreign_keys', ?, 'running')
    """, (BATCH_ID, datetime.now()))
    log_id = cursor.lastrowid
    conn.commit()

    total_updated = 0
    errors = []


    # 更新 entity_relations.source_entity_id
    print(f"\n更新 entity_relations.source_entity_id...")
    try:
        cursor.execute("""
            UPDATE entity_relations
            SET source_entity_id = (
                SELECT entity_id
                FROM entities
                WHERE id = entity_relations.source_entity_id
            )
            WHERE source_entity_id IN (SELECT id FROM entities)
        """)

        updated = cursor.rowcount
        total_updated += updated
        print(f"  ✅ 更新了 {updated} 条记录")
        conn.commit()
    except Exception as e:
        error_msg = f"entity_relations.source_entity_id: {e}"
        errors.append(error_msg)
        print(f"  ❌ {error_msg}")
        conn.rollback()

    # 更新 entity_relations.target_entity_id
    print(f"\n更新 entity_relations.target_entity_id...")
    try:
        cursor.execute("""
            UPDATE entity_relations
            SET target_entity_id = (
                SELECT entity_id
                FROM entities
                WHERE id = entity_relations.target_entity_id
            )
            WHERE target_entity_id IN (SELECT id FROM entities)
        """)

        updated = cursor.rowcount
        total_updated += updated
        print(f"  ✅ 更新了 {updated} 条记录")
        conn.commit()
    except Exception as e:
        error_msg = f"entity_relations.target_entity_id: {e}"
        errors.append(error_msg)
        print(f"  ❌ {error_msg}")
        conn.rollback()

    # 更新日志
    status = "completed" if len(errors) == 0 else "completed_with_errors"
    error_message = "\n".join(errors[:10]) if errors else None

    cursor.execute("""
        UPDATE migration_log
        SET completed_at = ?,
            status = ?,
            records_affected = ?,
            error_message = ?
        WHERE id = ?
    """, (datetime.now(), status, total_updated, error_message, log_id))

    conn.commit()
    conn.close()

    print(f"\n✅ 总共更新了 {total_updated} 条记录")
    if errors:
        print(f"⚠️  遇到 {len(errors)} 个错误")

if __name__ == "__main__":
    update_foreign_keys()
