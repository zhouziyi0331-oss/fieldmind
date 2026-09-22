"""
Add TF-IDF and clustering tables

Revision ID: 008_add_tfidf_clustering
Revises: 007_add_business_dimensions
Create Date: 2026-08-21 17:00:00.000000

添加 TF-IDF 关键词表和主题聚类表
"""
from alembic import op
import sqlalchemy as sa

revision = '008_add_tfidf_clustering'
down_revision = '007_add_business_dimensions'
branch_labels = None
depends_on = None


def upgrade():
    """添加 TF-IDF 和聚类相关表"""

    print("\n" + "="*60)
    print("添加 TF-IDF + 聚类分析表")
    print("="*60)

    conn = op.get_bind()

    # 1. 创建 chunk_keywords 表
    print("\n创建 chunk_keywords 表...")
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS chunk_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            tfidf_score REAL,
            frequency INTEGER,
            is_top BOOLEAN DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
        )
    """))
    print("✅ chunk_keywords 表创建成功")

    # 2. 创建索引
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_chunk_keywords_chunk_id
        ON chunk_keywords(chunk_id)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_chunk_keywords_tfidf
        ON chunk_keywords(tfidf_score DESC)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_chunk_keywords_is_top
        ON chunk_keywords(is_top)
    """))
    print("✅ chunk_keywords 索引创建成功")

    # 3. 创建 topic_clusters 表
    print("\n创建 topic_clusters 表...")
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS topic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            cluster_id INTEGER NOT NULL,
            cluster_label TEXT,
            chunk_ids TEXT,
            top_keywords TEXT,
            chunk_count INTEGER,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, cluster_id)
        )
    """))
    print("✅ topic_clusters 表创建成功")

    # 4. 创建索引
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_topic_clusters_project
        ON topic_clusters(project_id)
    """))
    print("✅ topic_clusters 索引创建成功")

    # 5. 在 document_chunks 表添加 cluster_id 字段
    print("\n在 document_chunks 表添加 cluster_id 字段...")
    try:
        conn.execute(sa.text("""
            ALTER TABLE document_chunks
            ADD COLUMN cluster_id INTEGER
        """))
        print("✅ cluster_id 字段添加成功")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⏭  cluster_id 字段已存在")
        else:
            print(f"❌ 添加 cluster_id 字段失败: {e}")

    print("\n" + "="*60)
    print("✅ 完成！TF-IDF + 聚类分析表已创建")
    print("="*60)
    print("\n新增功能：")
    print("  ✓ chunk_keywords - 存储每个chunk的TF-IDF关键词")
    print("  ✓ topic_clusters - 存储无监督聚类结果")
    print("  ✓ cluster_id - chunk所属的聚类ID")
    print()


def downgrade():
    """删除表"""
    print("\n回滚：删除 TF-IDF + 聚类分析表")

    conn = op.get_bind()

    conn.execute(sa.text("DROP TABLE IF EXISTS chunk_keywords"))
    conn.execute(sa.text("DROP TABLE IF EXISTS topic_clusters"))

    print("✅ 表已删除")
