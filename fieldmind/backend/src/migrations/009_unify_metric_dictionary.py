"""
Migration 009: Unify metric_dictionary schema and initialize 20 predefined metrics
- Rename id to metric_id for consistency
- Add missing governance fields
- Initialize 20 quantitative metrics across 6 categories
"""

import sqlite3
from datetime import datetime

def upgrade(conn: sqlite3.Connection):
    cursor = conn.cursor()

    print("=== Migration 009: Unify Metric Dictionary ===")

    # Step 1: Create new metric_dictionary table with unified schema
    print("Creating new metric_dictionary_new table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_dictionary_new (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name VARCHAR(100) NOT NULL UNIQUE,
            metric_category VARCHAR(50) NOT NULL,
            definition TEXT,
            calculation_rule TEXT,
            unit VARCHAR(50),
            value_range VARCHAR(100),
            applicable_doc_types TEXT,
            priority INTEGER DEFAULT 5,
            enabled BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 2: Migrate existing data if any
    print("Migrating existing data...")
    cursor.execute("SELECT COUNT(*) FROM metric_dictionary")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        cursor.execute("""
            INSERT INTO metric_dictionary_new
            (metric_id, metric_name, metric_category, definition, calculation_rule,
             unit, enabled, created_at, updated_at)
            SELECT
                id,
                metric_name,
                metric_type,
                description,
                calculation_method,
                unit,
                enabled,
                created_at,
                updated_at
            FROM metric_dictionary
        """)
        print(f"  Migrated {existing_count} existing metrics")

    # Step 3: Drop old table and rename new one
    print("Replacing old table with new schema...")
    cursor.execute("DROP TABLE metric_dictionary")
    cursor.execute("ALTER TABLE metric_dictionary_new RENAME TO metric_dictionary")

    # Step 4: Create indexes
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_name ON metric_dictionary (metric_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_category ON metric_dictionary (metric_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_priority ON metric_dictionary (priority DESC)")

    # Step 5: Initialize 20 predefined metrics
    print("Initializing 20 predefined metrics...")

    metrics = [
        # 结构性指标 (Structural Metrics)
        ("word_count", "structural", "文档总字数", "统计文档中的总字符数（中文按字计，英文按单词计）", "characters", "0-∞", "all", 10),
        ("sentence_count", "structural", "句子总数", "统计文档中的句子数量", "count", "0-∞", "all", 8),
        ("paragraph_count", "structural", "段落总数", "统计文档中的段落数量", "count", "0-∞", "text,pdf,docx", 7),
        ("avg_sentence_length", "structural", "平均句长", "平均每个句子的字数", "words/sentence", "0-∞", "all", 6),

        # 情感性指标 (Emotion Metrics)
        ("emotion_polarity", "emotion", "情感极性", "文本的整体情感倾向（-1=负面, 0=中性, 1=正面）", "score", "-1~1", "text,audio,video", 9),
        ("emotion_intensity", "emotion", "情感强度", "情感表达的强烈程度", "score", "0~1", "text,audio,video", 8),
        ("subjectivity", "emotion", "主观性", "文本的主观程度（0=客观, 1=主观）", "score", "0~1", "text,audio", 7),

        # 风格性指标 (Style Metrics)
        ("formality", "style", "正式度", "语言的正式程度", "score", "0~1", "text,audio", 8),
        ("complexity", "style", "复杂度", "语言的复杂程度（词汇、句法）", "score", "0~1", "text", 7),
        ("readability", "style", "可读性", "文本的易读程度（flesch reading ease等）", "score", "0~100", "text,pdf,docx", 9),

        # 内容性指标 (Content Metrics)
        ("entity_count", "content", "实体数量", "识别出的命名实体总数（人名、地名、机构等）", "count", "0-∞", "all", 10),
        ("keyword_density", "content", "关键词密度", "关键词占总词数的比例", "percentage", "0~1", "text,pdf,docx", 8),
        ("topic_coherence", "content", "主题连贯性", "文档内容的主题一致性", "score", "0~1", "text,pdf,docx", 7),
        ("information_density", "content", "信息密度", "单位文本中的信息量", "score", "0~1", "all", 8),

        # 质量性指标 (Quality Metrics)
        ("completeness", "quality", "完整性", "文档内容的完整程度", "score", "0~1", "all", 9),
        ("accuracy", "quality", "准确性", "内容的准确程度（基于事实核查）", "score", "0~1", "all", 9),
        ("consistency", "quality", "一致性", "内容前后的一致性", "score", "0~1", "all", 8),

        # 时间性指标 (Temporal Metrics)
        ("recency", "temporal", "时效性", "内容的时间新近程度", "days", "0-∞", "all", 7),
        ("temporal_coverage", "temporal", "时间跨度", "内容涵盖的时间范围", "days", "0-∞", "text,audio,video", 6),
        ("update_frequency", "temporal", "更新频率", "内容更新的频率", "days", "0-∞", "all", 5),
    ]

    insert_sql = """
        INSERT OR IGNORE INTO metric_dictionary
        (metric_name, metric_category, definition, calculation_rule, unit, value_range, applicable_doc_types, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    inserted = 0
    for metric in metrics:
        cursor.execute(insert_sql, metric)
        if cursor.rowcount > 0:
            inserted += 1

    print(f"  Initialized {inserted} new metrics")

    conn.commit()
    print("✓ Migration 009 completed successfully")
    print(f"  Total metrics in dictionary: {existing_count + inserted}")


def downgrade(conn: sqlite3.Connection):
    cursor = conn.cursor()

    print("=== Rolling back Migration 009 ===")

    # Create old schema
    cursor.execute("""
        CREATE TABLE metric_dictionary_old (
            id INTEGER NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            description TEXT,
            calculation_method TEXT,
            unit VARCHAR(50),
            threshold_low FLOAT,
            threshold_high FLOAT,
            enabled BOOLEAN,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id)
        )
    """)

    # Migrate back (only pre-existing metrics, not the 20 new ones)
    cursor.execute("""
        INSERT INTO metric_dictionary_old
        (id, metric_name, metric_type, description, calculation_method, unit, enabled, created_at, updated_at)
        SELECT
            metric_id,
            metric_name,
            metric_category,
            definition,
            calculation_rule,
            unit,
            enabled,
            created_at,
            updated_at
        FROM metric_dictionary
        WHERE metric_id < 1000
    """)

    cursor.execute("DROP TABLE metric_dictionary")
    cursor.execute("ALTER TABLE metric_dictionary_old RENAME TO metric_dictionary")

    cursor.execute("CREATE UNIQUE INDEX idx_metric_name ON metric_dictionary (metric_name)")
    cursor.execute("CREATE INDEX idx_metric_type ON metric_dictionary (metric_type)")

    conn.commit()
    print("✓ Rollback completed")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add src to path
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

    from app.config import settings

    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)

    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
            downgrade(conn)
        else:
            upgrade(conn)
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
