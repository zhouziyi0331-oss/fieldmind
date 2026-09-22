"""
补充治理元数据表和扩展字段 (SQLite兼容版本)
添加缺失的 governance_metadata 表和 documents/document_chunks 的扩展字段
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from app.core.database import engine


def add_governance_metadata_table():
    """添加治理元数据表"""

    print("="*60)
    print("添加治理元数据表和扩展字段 (SQLite)")
    print("="*60)

    with engine.connect() as conn:

        # 1. 创建 governance_metadata 表
        print("\n1. 创建治理元数据表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS governance_metadata (
                metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(100) NOT NULL,
                metadata_key VARCHAR(100) NOT NULL,
                metadata_value TEXT,
                metadata_type VARCHAR(50),
                source VARCHAR(100),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gov_entity
            ON governance_metadata(entity_type, entity_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gov_key
            ON governance_metadata(metadata_key)
        """))
        print("✓ 治理元数据表创建完成")

        # 2. 为 documents 表添加扩展字段
        print("\n2. 为 documents 表添加扩展字段...")

        # 检查列是否存在
        def column_exists(table, column):
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            columns = [row[1] for row in result.fetchall()]
            return column in columns

        # 添加字段 (SQLite 语法：无 COMMENT，无 AFTER)
        fields_to_add = [
            ('file_hash', 'VARCHAR(64)'),
            ('total_words', 'INTEGER'),
            ('total_sentences', 'INTEGER'),
            ('total_paragraphs', 'INTEGER'),
            ('language', 'VARCHAR(20)'),
            ('speaker_count', 'INTEGER'),
            ('collection_device', 'VARCHAR(100)'),
            ('collection_location', 'VARCHAR(200)'),
        ]

        for field_name, field_type in fields_to_add:
            if not column_exists('documents', field_name):
                conn.execute(text(f"""
                    ALTER TABLE documents
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"  ✓ 添加 {field_name} 字段")
            else:
                print(f"  - {field_name} 字段已存在")

        print("✓ documents 表扩展字段添加完成")

        # 3. 为 document_chunks 表添加扩展字段
        print("\n3. 为 document_chunks 表添加扩展字段...")

        chunk_fields_to_add = [
            ('quality_score', 'FLOAT'),
            ('emotion_polarity', 'FLOAT'),
            ('keyword_density', 'FLOAT'),
            ('entity_count', 'INTEGER'),
            ('relation_count', 'INTEGER'),
        ]

        for field_name, field_type in chunk_fields_to_add:
            if not column_exists('document_chunks', field_name):
                conn.execute(text(f"""
                    ALTER TABLE document_chunks
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"  ✓ 添加 {field_name} 字段")
            else:
                print(f"  - {field_name} 字段已存在")

        print("✓ document_chunks 表扩展字段添加完成")

        conn.commit()

    print("\n" + "="*60)
    print("✅ 治理元数据表和扩展字段添加完成")
    print("="*60)


if __name__ == "__main__":
    try:
        add_governance_metadata_table()
    except Exception as e:
        print(f"\n❌ 添加失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
