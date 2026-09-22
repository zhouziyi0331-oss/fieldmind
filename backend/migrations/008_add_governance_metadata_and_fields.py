"""
补充治理元数据表和扩展字段
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
    print("添加治理元数据表和扩展字段")
    print("="*60)

    with engine.connect() as conn:

        # 检查数据库类型
        db_type = str(engine.url).split(':')[0]
        is_sqlite = 'sqlite' in db_type

        # 1. 创建 governance_metadata 表
        print(f"\n1. 创建治理元数据表 (数据库类型: {db_type})...")

        if is_sqlite:
            # SQLite 语法
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
            # SQLite 的索引需要单独创建
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_gov_entity
                ON governance_metadata(entity_type, entity_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_gov_key
                ON governance_metadata(metadata_key)
            """))
        else:
            # MySQL 语法
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS governance_metadata (
                    metadata_id INT PRIMARY KEY AUTO_INCREMENT,
                    entity_type VARCHAR(50) NOT NULL COMMENT '实体类型: file/chunk/project',
                    entity_id VARCHAR(100) NOT NULL COMMENT '实体ID',
                    metadata_key VARCHAR(100) NOT NULL COMMENT '元数据键',
                    metadata_value TEXT COMMENT '元数据值',
                    metadata_type VARCHAR(50) COMMENT '数据类型: string/number/json',
                    source VARCHAR(100) COMMENT '来源: auto/manual/system',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_gov_entity (entity_type, entity_id),
                    INDEX idx_gov_key (metadata_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='治理元数据表'
            """))
        print("✓ 治理元数据表创建完成")

        # 2. 为 documents 表添加扩展字段
        print("\n2. 为 documents 表添加扩展字段...")

        # 检查列是否存在的辅助函数
        def column_exists(table, column):
            if is_sqlite:
                # SQLite 使用 PRAGMA table_info
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result.fetchall()]
                return column in columns
            else:
                # MySQL 使用 information_schema
                result = conn.execute(text(f"""
                    SELECT COUNT(*) as cnt FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = '{table}'
                    AND COLUMN_NAME = '{column}'
                """))
                return result.fetchone()[0] > 0

        # 添加 file_hash
        if not column_exists('documents', 'file_hash'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN file_hash VARCHAR(64) COMMENT 'MD5文件哈希' AFTER name
            """))
            print("  ✓ 添加 file_hash 字段")

        # 添加 total_words
        if not column_exists('documents', 'total_words'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN total_words INT COMMENT '总字数' AFTER file_hash
            """))
            print("  ✓ 添加 total_words 字段")

        # 添加 total_sentences
        if not column_exists('documents', 'total_sentences'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN total_sentences INT COMMENT '总句数' AFTER total_words
            """))
            print("  ✓ 添加 total_sentences 字段")

        # 添加 total_paragraphs
        if not column_exists('documents', 'total_paragraphs'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN total_paragraphs INT COMMENT '总段落数' AFTER total_sentences
            """))
            print("  ✓ 添加 total_paragraphs 字段")

        # 添加 language
        if not column_exists('documents', 'language'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN language VARCHAR(20) COMMENT '语言' AFTER total_paragraphs
            """))
            print("  ✓ 添加 language 字段")

        # 添加 speaker_count
        if not column_exists('documents', 'speaker_count'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN speaker_count INT COMMENT '说话人数量（音视频）' AFTER language
            """))
            print("  ✓ 添加 speaker_count 字段")

        # 添加 collection_device
        if not column_exists('documents', 'collection_device'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN collection_device VARCHAR(100) COMMENT '采集设备' AFTER speaker_count
            """))
            print("  ✓ 添加 collection_device 字段")

        # 添加 collection_location
        if not column_exists('documents', 'collection_location'):
            conn.execute(text("""
                ALTER TABLE documents
                ADD COLUMN collection_location VARCHAR(200) COMMENT '采集地点' AFTER collection_device
            """))
            print("  ✓ 添加 collection_location 字段")

        print("✓ documents 表扩展字段添加完成")

        # 3. 为 document_chunks 表添加扩展字段
        print("\n3. 为 document_chunks 表添加扩展字段...")

        # 添加 quality_score
        if not column_exists('document_chunks', 'quality_score'):
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN quality_score FLOAT COMMENT '质量分数 0-1' AFTER text
            """))
            print("  ✓ 添加 quality_score 字段")

        # 添加 emotion_polarity
        if not column_exists('document_chunks', 'emotion_polarity'):
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN emotion_polarity FLOAT COMMENT '情感极性 -1到1' AFTER quality_score
            """))
            print("  ✓ 添加 emotion_polarity 字段")

        # 添加 keyword_density
        if not column_exists('document_chunks', 'keyword_density'):
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN keyword_density FLOAT COMMENT '关键词密度' AFTER emotion_polarity
            """))
            print("  ✓ 添加 keyword_density 字段")

        # 添加 entity_count
        if not column_exists('document_chunks', 'entity_count'):
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN entity_count INT COMMENT '实体数量' AFTER keyword_density
            """))
            print("  ✓ 添加 entity_count 字段")

        # 添加 relation_count
        if not column_exists('document_chunks', 'relation_count'):
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN relation_count INT COMMENT '关系数量' AFTER entity_count
            """))
            print("  ✓ 添加 relation_count 字段")

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
