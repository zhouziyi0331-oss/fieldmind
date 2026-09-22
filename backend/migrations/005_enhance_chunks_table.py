"""
数据库迁移：完善 chunks 表结构 + 添加 FTS5 全文搜索

执行: python migrations/005_enhance_chunks_table.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from app.core.database import engine, get_db_session


def upgrade():
    """升级数据库结构"""
    print("开始迁移: 完善 chunks 表...")

    with engine.connect() as conn:
        # 1. 添加 project_id 字段（如果不存在）
        try:
            conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN project_id INT,
                ADD FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            """))
            print("✓ 添加 project_id 字段")
        except Exception as e:
            print(f"⚠ project_id 字段可能已存在: {e}")

        # 2. 添加溯源字段
        trace_fields = [
            ("page_number", "INT"),
            ("speaker", "VARCHAR(100)"),
            ("timestamp_start", "INT"),
            ("timestamp_end", "INT"),
        ]

        for field_name, field_type in trace_fields:
            try:
                conn.execute(text(f"""
                    ALTER TABLE document_chunks
                    ADD COLUMN {field_name} {field_type}
                """))
                print(f"✓ 添加 {field_name} 字段")
            except Exception as e:
                print(f"⚠ {field_name} 字段可能已存在: {e}")

        # 3. 重命名字段（如果需要）
        try:
            conn.execute(text("""
                ALTER TABLE document_chunks
                CHANGE COLUMN content text TEXT NOT NULL
            """))
            print("✓ 重命名 content → text")
        except Exception as e:
            print(f"⚠ 字段重命名可能不需要: {e}")

        # 4. 添加索引
        indexes = [
            ("idx_chunk_project", "project_id, created_at"),
            ("idx_chunk_page", "document_id, page_number"),
            ("idx_chunk_timestamp", "document_id, timestamp_start"),
        ]

        for idx_name, idx_cols in indexes:
            try:
                conn.execute(text(f"""
                    CREATE INDEX {idx_name} ON document_chunks({idx_cols})
                """))
                print(f"✓ 创建索引 {idx_name}")
            except Exception as e:
                print(f"⚠ 索引 {idx_name} 可能已存在: {e}")

        # 5. 填充 project_id（从 documents 表关联）
        try:
            conn.execute(text("""
                UPDATE document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                SET dc.project_id = d.project_id
                WHERE dc.project_id IS NULL
            """))
            conn.commit()
            print("✓ 填充 project_id")
        except Exception as e:
            print(f"⚠ 填充 project_id 失败: {e}")

    print("\n✅ chunks 表结构完善完成")


def create_fts_table():
    """创建 FTS5 全文搜索表"""
    print("\n开始创建 FTS5 全文搜索表...")

    # 注意：MySQL 不支持 FTS5，这是 SQLite 特性
    # 对于 MySQL，我们使用 FULLTEXT 索引

    with engine.connect() as conn:
        try:
            # 检查是否是 MySQL
            if "mysql" in str(engine.url):
                # MySQL 使用 FULLTEXT 索引
                conn.execute(text("""
                    ALTER TABLE document_chunks
                    ADD FULLTEXT INDEX idx_chunk_fulltext (text)
                """))
                print("✓ 创建 MySQL FULLTEXT 索引")
            else:
                # SQLite 使用 FTS5
                conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                        chunk_text,
                        content=document_chunks,
                        content_rowid=id
                    )
                """))
                print("✓ 创建 SQLite FTS5 虚拟表")

            conn.commit()
            print("✅ 全文搜索表创建完成")

        except Exception as e:
            print(f"❌ 创建全文搜索表失败: {e}")


def verify():
    """验证迁移结果"""
    print("\n验证迁移结果...")

    db = get_db_session()

    try:
        # 检查表结构
        result = db.execute(text("DESCRIBE document_chunks"))
        columns = [row[0] for row in result]

        required_columns = [
            "id", "document_id", "project_id", "chunk_index", "text",
            "page_number", "speaker", "timestamp_start", "timestamp_end"
        ]

        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"❌ 缺少字段: {missing}")
        else:
            print("✓ 所有必需字段都存在")

        # 检查索引
        result = db.execute(text("SHOW INDEX FROM document_chunks"))
        indexes = [row[2] for row in result]

        required_indexes = ["idx_chunk_project", "idx_chunk_page", "idx_chunk_timestamp"]
        missing_indexes = [idx for idx in required_indexes if idx not in indexes]

        if missing_indexes:
            print(f"⚠ 缺少索引: {missing_indexes}")
        else:
            print("✓ 所有索引都已创建")

        print("\n✅ 验证完成")

    except Exception as e:
        print(f"❌ 验证失败: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("数据库迁移: 完善 chunks 表结构")
    print("="*60)

    try:
        upgrade()
        create_fts_table()
        verify()

        print("\n" + "="*60)
        print("✅ 迁移成功完成")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
