"""
创建document_chunks表的SQL脚本
"""

import sqlite3
import os

# 数据库路径 - 使用环境变量
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/fieldmind.db").replace("sqlite:///", "")

# 创建表的SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id VARCHAR(50) UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    text_length INTEGER,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER,
    start_pos INTEGER,
    end_pos INTEGER,
    embedding JSON,
    embedding_model VARCHAR(100),
    chunk_metadata JSON,
    prev_chunk_id VARCHAR(50),
    next_chunk_id VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    vectorized_at DATETIME,
    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_project ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_id ON document_chunks(chunk_id);
"""

def upgrade():
    """创建表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("正在创建document_chunks表...")
        cursor.executescript(CREATE_TABLE_SQL)
        conn.commit()
        print("✅ document_chunks表创建成功")

        # 验证表是否创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks'")
        if cursor.fetchone():
            print("✅ 表已成功创建并验证")
        else:
            print("❌ 表创建失败")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def downgrade():
    """删除表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("正在删除document_chunks表...")
        cursor.execute("DROP TABLE IF EXISTS document_chunks")
        conn.commit()
        print("✅ document_chunks表已删除")
    except Exception as e:
        print(f"❌ 删除表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "upgrade":
        upgrade()
    elif len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        print("使用方法:")
        print("  python create_chunks_table.py upgrade    # 创建表")
        print("  python create_chunks_table.py downgrade  # 删除表")
