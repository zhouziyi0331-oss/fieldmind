"""fix_document_chunks_schema

Revision ID: 54ce86695f64
Revises: 006_chunk_traceability
Create Date: 2026-08-15 10:54:11.901008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54ce86695f64'
down_revision: Union[str, None] = '006_chunk_traceability'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加document_chunks表缺失的字段"""
    # SQLite不支持直接ALTER TABLE ADD COLUMN，使用op.execute
    op.execute("ALTER TABLE document_chunks ADD COLUMN text_length INTEGER")
    op.execute("ALTER TABLE document_chunks ADD COLUMN chunk_index INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE document_chunks ADD COLUMN total_chunks INTEGER")
    op.execute("ALTER TABLE document_chunks ADD COLUMN start_pos INTEGER")
    op.execute("ALTER TABLE document_chunks ADD COLUMN end_pos INTEGER")
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding_model VARCHAR(100)")
    op.execute("ALTER TABLE document_chunks ADD COLUMN vectorized_at DATETIME")


def downgrade() -> None:
    """移除添加的字段（SQLite不支持DROP COLUMN，需要重建表）"""
    pass
