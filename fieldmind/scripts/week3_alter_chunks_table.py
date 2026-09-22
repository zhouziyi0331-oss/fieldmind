"""
Week 3 - Day 4: 执行 document_chunks 表改造
添加新字段并创建索引
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
MIGRATION_BATCH = f"chunks_enhancement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def add_new_fields():
    """添加新字段到 document_chunks 表"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("开始添加新字段到 document_chunks 表")
    print("=" * 60)

    # 定义所有新字段
    new_fields = [
        # 说话人增强
        ("speaker_id", "VARCHAR(50)", "说话人实体ID"),
        ("speaker_role", "VARCHAR(100)", "说话人角色"),
        ("speaker_confidence", "FLOAT", "识别置信度"),

        # 情感量化
        ("emotion_polarity", "FLOAT", "情感极性 [-1, 1]"),
        ("emotion_intensity", "FLOAT", "情感强度 [0, 1]"),
        ("subjectivity", "FLOAT", "主观性 [0, 1]"),
        ("sentiment_label", "VARCHAR(50)", "情感标签"),

        # 维度分类增强
        ("dimension_category", "VARCHAR(100)", "维度类别"),
        ("dimension_sub_category", "VARCHAR(100)", "维度子类别"),
        ("dimension_tags", "JSON", "维度标签数组"),
        ("dimension_confidence", "FLOAT", "分类置信度"),

        # 关键词
        ("keywords", "JSON", "关键词数组"),
        ("entities_count", "INTEGER DEFAULT 0", "实体数量"),

        # 质量指标
        ("quality_score", "FLOAT", "综合质量评分"),
        ("completeness_score", "FLOAT", "完整性评分"),
        ("relevance_score", "FLOAT", "相关性评分"),
        ("has_context", "INTEGER DEFAULT 1", "是否有上下文"),

        # 同步状态
        ("synced_to_chromadb", "INTEGER DEFAULT 0", "是否同步到 ChromaDB"),
        ("chromadb_synced_at", "DATETIME", "ChromaDB 同步时间"),
        ("sync_version", "INTEGER DEFAULT 1", "同步版本"),
        ("updated_at", "DATETIME", "更新时间"),
        ("embedding_id", "VARCHAR(100)", "Embedding ID"),
    ]

    added_count = 0
    skipped_count = 0

    for field_name, field_type, description in new_fields:
        try:
            print(f"\n添加字段: {field_name} ({description})")

            # 检查字段是否已存在
            cursor.execute("PRAGMA table_info(document_chunks)")
            existing_fields = [col[1] for col in cursor.fetchall()]

            if field_name in existing_fields:
                print(f"  ⚠️  字段 {field_name} 已存在，跳过")
                skipped_count += 1
                continue

            # 添加字段
            sql = f"ALTER TABLE document_chunks ADD COLUMN {field_name} {field_type}"
            cursor.execute(sql)
            conn.commit()

            print(f"  ✅ 字段 {field_name} 添加成功")
            added_count += 1

        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  ⚠️  字段 {field_name} 已存在")
                skipped_count += 1
            else:
                print(f"  ❌ 添加字段 {field_name} 失败: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"字段添加完成: 新增 {added_count} 个, 跳过 {skipped_count} 个")
    print("=" * 60)

    return added_count, skipped_count


def create_indexes():
    """为新字段创建索引"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("创建索引")
    print("=" * 60)

    # 定义索引
    indexes = [
        ("idx_chunks_speaker_id", "speaker_id", "说话人ID"),
        ("idx_chunks_dimension_category", "dimension_category", "维度类别"),
        ("idx_chunks_sentiment", "emotion_polarity", "情感极性"),
        ("idx_chunks_quality", "quality_score", "质量评分"),
        ("idx_chunks_synced", "synced_to_chromadb", "同步状态"),
        ("idx_chunks_embedding_id", "embedding_id", "Embedding ID"),
        ("idx_chunks_updated_at", "updated_at", "更新时间"),
    ]

    created_count = 0

    for idx_name, column_name, description in indexes:
        try:
            print(f"\n创建索引: {idx_name} on {column_name} ({description})")

            sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON document_chunks({column_name})"
            cursor.execute(sql)
            conn.commit()

            print(f"  ✅ 索引 {idx_name} 创建成功")
            created_count += 1

        except Exception as e:
            print(f"  ❌ 创建索引 {idx_name} 失败: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"索引创建完成: {created_count} 个")
    print("=" * 60)

    return created_count


def verify_structure():
    """验证表结构"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("验证表结构")
    print("=" * 60)

    # 获取所有字段
    cursor.execute("PRAGMA table_info(document_chunks)")
    columns = cursor.fetchall()

    print(f"\n总字段数: {len(columns)}")

    # 按类别统计
    categories = {
        "speaker": 0,
        "emotion": 0,
        "dimension": 0,
        "keyword": 0,
        "quality": 0,
        "sync": 0,
    }

    for col in columns:
        col_name = col[1].lower()
        if "speaker" in col_name:
            categories["speaker"] += 1
        if "emotion" in col_name or "sentiment" in col_name or "subjectivity" in col_name:
            categories["emotion"] += 1
        if "dimension" in col_name:
            categories["dimension"] += 1
        if "keyword" in col_name or "entities_count" in col_name:
            categories["keyword"] += 1
        if "quality" in col_name or "completeness" in col_name or "relevance" in col_name:
            categories["quality"] += 1
        if "sync" in col_name or "chromadb" in col_name or "embedding_id" in col_name:
            categories["sync"] += 1

    print("\n字段分类统计:")
    for category, count in categories.items():
        print(f"  {category}: {count} 个字段")

    # 获取索引
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='document_chunks'")
    indexes = cursor.fetchall()

    print(f"\n索引数量: {len(indexes)}")
    print("\n索引列表:")
    for idx in indexes[:10]:
        print(f"  - {idx[0]}")

    if len(indexes) > 10:
        print(f"  ... 还有 {len(indexes) - 10} 个索引")

    conn.close()

    print("\n✅ 表结构验证完成")


def record_migration():
    """记录迁移日志"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO migration_log (
                batch_id,
                table_name,
                operation,
                started_at,
                completed_at,
                status,
                records_affected
            )
            VALUES (?, 'document_chunks', 'add_fields', ?, ?, 'completed', 0)
        """, (MIGRATION_BATCH, datetime.now(), datetime.now()))

        conn.commit()
        print(f"\n✅ 迁移日志已记录: {MIGRATION_BATCH}")

    except Exception as e:
        print(f"\n⚠️  记录迁移日志失败: {e}")

    conn.close()


def main():
    """主函数"""

    print("=" * 60)
    print("document_chunks 表改造")
    print(f"批次 ID: {MIGRATION_BATCH}")
    print("=" * 60)

    # 步骤 1: 添加新字段
    added, skipped = add_new_fields()

    # 步骤 2: 创建索引
    created = create_indexes()

    # 步骤 3: 验证结构
    verify_structure()

    # 步骤 4: 记录迁移
    record_migration()

    print("\n" + "=" * 60)
    print("✅ document_chunks 表改造完成")
    print("=" * 60)
    print(f"\n总结:")
    print(f"  - 新增字段: {added} 个")
    print(f"  - 跳过字段: {skipped} 个")
    print(f"  - 创建索引: {created} 个")
    print(f"  - 批次 ID: {MIGRATION_BATCH}")

    print("\n下一步:")
    print("1. 测试新字段的读写")
    print("2. 实现 create_enriched_chunk() 函数")
    print("3. 集成情感分析和维度分类")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
