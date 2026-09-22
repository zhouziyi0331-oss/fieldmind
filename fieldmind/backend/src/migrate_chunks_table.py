"""
数据库迁移脚本 - 创建document_chunks表
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings

Base = declarative_base()


def upgrade():
    """创建document_chunks表"""
    from app.core.database import engine
    from app.models.document_chunk import DocumentChunk

    print("创建document_chunks表...")
    Base.metadata.create_all(bind=engine, tables=[DocumentChunk.__table__])
    print("✅ document_chunks表创建成功")


def downgrade():
    """删除document_chunks表"""
    from app.core.database import engine
    from app.models.document_chunk import DocumentChunk

    print("删除document_chunks表...")
    DocumentChunk.__table__.drop(engine)
    print("✅ document_chunks表已删除")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "upgrade":
        upgrade()
    elif len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        print("使用方法:")
        print("  python migrate_chunks_table.py upgrade    # 创建表")
        print("  python migrate_chunks_table.py downgrade  # 删除表")
