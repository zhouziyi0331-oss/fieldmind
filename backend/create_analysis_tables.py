"""
创建分析溯源相关表的迁移脚本
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data/fieldmind.db")

CREATE_TABLES_SQL = """
-- 分析结果表
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    created_by VARCHAR(36),
    analysis_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    parameters JSON,
    result JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    rating FLOAT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_analysis_project ON analysis_results(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_results(created_at);

-- 分析陈述表
CREATE TABLE IF NOT EXISTS analysis_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    statement_text TEXT NOT NULL,
    statement_type VARCHAR(50),
    section VARCHAR(100),
    order_index INTEGER,
    confidence_score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analysis_results(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_statement_analysis ON analysis_statements(analysis_id);

-- 陈述来源表
CREATE TABLE IF NOT EXISTS statement_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_chunk_id INTEGER,
    source_document_id INTEGER,
    position_info JSON,
    relevance_score FLOAT,
    confidence_score FLOAT,
    quoted_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_id) REFERENCES analysis_statements(id) ON DELETE CASCADE,
    FOREIGN KEY (source_chunk_id) REFERENCES document_chunks(id) ON DELETE SET NULL,
    FOREIGN KEY (source_document_id) REFERENCES project_documents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_source_statement ON statement_sources(statement_id);
CREATE INDEX IF NOT EXISTS idx_source_chunk ON statement_sources(source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_source_document ON statement_sources(source_document_id);

-- 来源验证表
CREATE TABLE IF NOT EXISTS source_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_source_id INTEGER NOT NULL,
    verified_by VARCHAR(36),
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (statement_source_id) REFERENCES statement_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_verification_source ON source_verifications(statement_source_id);
"""

def upgrade():
    """创建溯源相关表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("正在创建分析溯源相关表...")
        cursor.executescript(CREATE_TABLES_SQL)
        conn.commit()
        print("✅ 分析溯源表创建成功")

        # 验证表是否创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'analysis%' OR name LIKE '%source%'")
        tables = cursor.fetchall()
        print(f"✅ 创建了 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table[0]}")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def downgrade():
    """删除溯源相关表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("正在删除分析溯源相关表...")
        cursor.execute("DROP TABLE IF EXISTS source_verifications")
        cursor.execute("DROP TABLE IF EXISTS statement_sources")
        cursor.execute("DROP TABLE IF EXISTS analysis_statements")
        cursor.execute("DROP TABLE IF EXISTS analysis_results")
        conn.commit()
        print("✅ 分析溯源表已删除")
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
        print("  python create_analysis_tables.py upgrade    # 创建表")
        print("  python create_analysis_tables.py downgrade  # 删除表")
