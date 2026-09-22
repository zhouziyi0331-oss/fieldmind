"""
Week 2 - Day 3: 执行 entities 表的 ID 迁移
内嵌版本 - 不依赖外部导入
"""

import sqlite3
import uuid
import re
from datetime import datetime

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_SIZE = 100
BATCH_ID = f"entities_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ===== 内嵌 ID 生成函数 =====

def generate_id(entity_type: str) -> str:
    """生成统一格式的 ID"""
    prefixes = {
        "project": "proj", "document": "doc", "chunk": "chk",
        "entity": "ent", "relation": "rel", "skill": "sk",
        "knowledge_asset": "ka", "user": "usr", "workflow": "wf",
        "task": "tsk", "report": "rpt", "session": "ses",
        "message": "msg", "tag": "tag", "annotation": "ann"
    }

    prefix = prefixes.get(entity_type)
    if not prefix:
        raise ValueError(f"不支持的实体类型: {entity_type}")

    unique_part = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique_part}"


def validate_id(id_string: str) -> bool:
    """验证 ID 格式"""
    pattern = r'^[a-z]{2,4}_[a-f0-9]{12}$'
    return bool(re.match(pattern, id_string))

# ===== 迁移步骤 =====

def step1_add_column_without_unique():
    """步骤1: 添加 entity_id 列"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("步骤1: 添加 entity_id 列")
    print("-" * 60)

    try:
        cursor.execute("ALTER TABLE entities ADD COLUMN entity_id TEXT")
        conn.commit()
        print("✅ entity_id 列添加成功")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  entity_id 列已存在，跳过此步骤")
        else:
            print(f"❌ 错误: {e}")
            conn.close()
            return False

    conn.close()
    return True


def step2_migrate_entity_ids():
    """步骤2: 为所有 entities 生成新 ID"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n步骤2: 生成并填充新 ID")
    print("-" * 60)

    # 查询需要迁移的记录
    cursor.execute("""
        SELECT id, name, type
        FROM entities
        WHERE entity_id IS NULL
        ORDER BY id
    """)

    records = cursor.fetchall()
    total_count = len(records)

    print(f"需要迁移的记录数: {total_count}")

    if total_count == 0:
        print("✅ 所有记录已迁移")
        conn.close()
        return True

    # 记录迁移日志
    cursor.execute("""
        INSERT INTO migration_log (batch_id, table_name, operation, started_at, status)
        VALUES (?, 'entities', 'add_entity_id', ?, 'running')
    """, (BATCH_ID, datetime.now()))
    log_id = cursor.lastrowid
    conn.commit()

    # 分批处理
    migrated_count = 0
    errors = []

    for i in range(0, total_count, BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n处理批次 {batch_num}/{total_batches} ({len(batch)} 条记录)...")

        for old_id, name, entity_type in batch:
            try:
                # 生成新 ID
                new_id = generate_id("entity")

                # 确保新 ID 唯一（重试最多3次）
                for retry in range(3):
                    cursor.execute("SELECT COUNT(*) FROM entities WHERE entity_id = ?", (new_id,))
                    if cursor.fetchone()[0] == 0:
                        break
                    new_id = generate_id("entity")

                # 更新记录
                cursor.execute("""
                    UPDATE entities
                    SET entity_id = ?
                    WHERE id = ?
                """, (new_id, old_id))

                # 记录到映射表
                cursor.execute("""
                    INSERT INTO id_mapping (old_id, new_id, entity_type, table_name, migration_batch)
                    VALUES (?, ?, 'entity', 'entities', ?)
                """, (str(old_id), new_id, BATCH_ID))

                migrated_count += 1

            except Exception as e:
                error_msg = f"迁移失败 (old_id={old_id}): {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        # 每批次提交一次
        conn.commit()
        print(f"  已迁移: {migrated_count}/{total_count}")

    # 更新迁移日志
    status = "completed" if len(errors) == 0 else "completed_with_errors"
    error_message = "\n".join(errors[:10]) if errors else None

    cursor.execute("""
        UPDATE migration_log
        SET completed_at = ?,
            status = ?,
            records_affected = ?,
            error_message = ?
        WHERE id = ?
    """, (datetime.now(), status, migrated_count, error_message, log_id))

    conn.commit()

    print(f"\n✅ 迁移完成: {migrated_count}/{total_count} 条记录")
    if errors:
        print(f"⚠️  遇到 {len(errors)} 个错误")

    conn.close()
    return len(errors) == 0


def step3_verify_migration():
    """步骤3: 验证迁移结果"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n步骤3: 验证迁移结果")
    print("-" * 60)

    # 检查是否所有记录都有新 ID
    cursor.execute("SELECT COUNT(*) FROM entities WHERE entity_id IS NULL")
    null_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entities")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT entity_id) FROM entities WHERE entity_id IS NOT NULL")
    unique_count = cursor.fetchone()[0]

    print(f"总记录数: {total_count}")
    print(f"已分配新 ID: {total_count - null_count}")
    print(f"NULL 的记录: {null_count}")
    print(f"唯一 ID 数量: {unique_count}")

    # 检查 ID 格式
    cursor.execute("SELECT entity_id FROM entities WHERE entity_id IS NOT NULL LIMIT 10")
    sample_ids = [row[0] for row in cursor.fetchall()]

    print(f"\n示例新 ID:")
    invalid_count = 0
    for new_id in sample_ids[:5]:
        is_valid = validate_id(new_id)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {new_id} (valid: {is_valid})")
        if not is_valid:
            invalid_count += 1

    # 检查映射表
    cursor.execute("SELECT COUNT(*) FROM id_mapping WHERE table_name = 'entities'")
    mapping_count = cursor.fetchone()[0]

    print(f"\nID 映射表记录数: {mapping_count}")

    conn.close()

    # 验证结果
    success = (null_count == 0 and invalid_count == 0 and mapping_count == total_count)

    if success:
        print("\n✅ 验证通过：所有记录都已成功迁移")
    else:
        print("\n⚠️  验证未完全通过")
        if null_count > 0:
            print(f"   - 还有 {null_count} 条记录未分配新 ID")
        if invalid_count > 0:
            print(f"   - 有 {invalid_count} 个 ID 格式不正确")
        if mapping_count != total_count:
            print(f"   - 映射表记录数 ({mapping_count}) 与总记录数 ({total_count}) 不匹配")

    return success


def step4_create_unique_index():
    """步骤4: 为 entity_id 创建唯一索引"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n步骤4: 创建唯一索引")
    print("-" * 60)

    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_entity_id_unique
            ON entities(entity_id)
        """)
        conn.commit()
        print("✅ 唯一索引创建成功")

        # 验证索引
        cursor.execute("PRAGMA index_list(entities)")
        indexes = cursor.fetchall()

        print(f"\nentities 表的索引:")
        for idx in indexes:
            print(f"  - {idx[1]} (unique: {idx[2]})")

    except sqlite3.IntegrityError as e:
        print(f"❌ 创建唯一索引失败（可能有重复值）: {e}")

        # 检查重复值
        cursor.execute("""
            SELECT entity_id, COUNT(*) as cnt
            FROM entities
            WHERE entity_id IS NOT NULL
            GROUP BY entity_id
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()

        if duplicates:
            print(f"\n发现 {len(duplicates)} 个重复的 entity_id:")
            for dup_id, count in duplicates[:5]:
                print(f"  {dup_id}: {count} 次")

        conn.close()
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        conn.close()
        return False

    conn.close()
    return True


def show_summary():
    """显示迁移总结"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("迁移总结")
    print("=" * 60)

    # 显示迁移日志
    cursor.execute("""
        SELECT * FROM migration_log
        WHERE batch_id = ?
        ORDER BY started_at DESC
        LIMIT 1
    """, (BATCH_ID,))

    log = cursor.fetchone()
    if log:
        print(f"\n批次 ID: {log[1]}")
        print(f"表名: {log[2]}")
        print(f"操作: {log[3]}")
        print(f"影响记录数: {log[4]}")
        print(f"开始时间: {log[5]}")
        print(f"完成时间: {log[6]}")
        print(f"状态: {log[7]}")
        if log[8]:
            print(f"错误信息: {log[8][:200]}...")

    # 显示映射表示例
    cursor.execute("""
        SELECT old_id, new_id, migrated_at
        FROM id_mapping
        WHERE table_name = 'entities'
        ORDER BY migrated_at DESC
        LIMIT 5
    """)

    mappings = cursor.fetchall()
    if mappings:
        print(f"\n映射表示例 (最新5条):")
        print(f"{'旧 ID':<40} {'新 ID':<20} {'迁移时间':<20}")
        print("-" * 80)
        for old_id, new_id, migrated_at in mappings:
            print(f"{old_id:<40} {new_id:<20} {migrated_at:<20}")

    conn.close()


def main():
    """主执行流程"""

    print("=" * 60)
    print("FieldMind Entities 表 ID 迁移")
    print("Week 2 - Day 3")
    print("=" * 60)
    print(f"批次 ID: {BATCH_ID}")
    print(f"数据库: {DB_PATH}")
    print("=" * 60)

    # 执行迁移步骤
    if not step1_add_column_without_unique():
        print("\n❌ 步骤1失败，终止迁移")
        return

    if not step2_migrate_entity_ids():
        print("\n⚠️  步骤2有错误，但继续验证")

    if not step3_verify_migration():
        print("\n❌ 步骤3验证失败")
        return

    if not step4_create_unique_index():
        print("\n⚠️  步骤4失败（唯一索引创建失败）")

    # 显示总结
    show_summary()

    print("\n" + "=" * 60)
    print("✅ Entities 表 ID 迁移完成")
    print("=" * 60)

    print("\n下一步:")
    print("1. 查看迁移日志: sqlite3 " + DB_PATH + " 'SELECT * FROM migration_log WHERE batch_id = \"" + BATCH_ID + "\"'")
    print("2. 查看映射表: sqlite3 " + DB_PATH + " 'SELECT * FROM id_mapping WHERE table_name = \"entities\" LIMIT 10'")
    print("3. 运行下一步: python3 week2_update_foreign_keys.py")


if __name__ == "__main__":
    main()
