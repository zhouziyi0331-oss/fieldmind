"""Add document_chunks and chunk_entities for complete data flow traceability

Revision ID: 006
Revises: 005
Create Date: 2026-08-15 00:00:00.000000

这个迁移文件修复数据流断点：
1. document_chunks表 - 存储Chunk数据（断点1修复）
2. chunk_entities关联表 - 连接Chunk和Entity（断点2修复）

数据流完整链路：
Document → Chunk (数据库✅) → Entity (数据库✅) → Knowledge → Synthesis → Report
           ↓ 全部可追溯      ↓ 全部可验证

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_chunk_traceability'
down_revision: Union[str, None] = '005_phase5_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建document_chunks和chunk_entities表"""

    # 检查表是否存在
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. document_chunks表 - 存储所有切分后的chunk
    if 'document_chunks' not in existing_tables:
        op.create_table(
            'document_chunks',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
            sa.Column('chunk_id', sa.String(50), nullable=False, unique=True, index=True,
                      comment='Chunk唯一标识，格式：doc_{document_id}_chunk_{index}'),

            # 关联字段
            sa.Column('document_id', sa.Integer(),
                      sa.ForeignKey('project_documents.id', ondelete='CASCADE'),
                      nullable=False,
                      comment='来源文档ID，外键关联project_documents.id'),
            sa.Column('project_id', sa.Integer(),
                      sa.ForeignKey('projects.id', ondelete='CASCADE'),
                      nullable=False,
                      comment='所属项目ID，外键关联projects.id'),

            # Chunk内容
            sa.Column('text', sa.Text(), nullable=False,
                      comment='Chunk的文本内容'),
            sa.Column('embedding', sa.JSON(), nullable=True,
                      comment='向量表示（768维），JSON格式存储'),

            # Chunk元数据
            sa.Column('chunk_metadata', sa.JSON(), nullable=True,
                      comment='元数据：start_char, end_char, token_count, entities, relations, domain_tags等'),

            # 链表结构（用于追溯上下文）
            sa.Column('prev_chunk_id', sa.String(50), nullable=True,
                      comment='前一个chunk的ID'),
            sa.Column('next_chunk_id', sa.String(50), nullable=True,
                      comment='后一个chunk的ID'),

            # 时间戳
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                      onupdate=sa.func.now(), nullable=False),

            # 索引
            sa.Index('idx_document_chunks_document_id', 'document_id'),
            sa.Index('idx_document_chunks_project_id', 'project_id'),
            sa.Index('idx_document_chunks_created_at', 'created_at'),
        )

    # 2. chunk_entities关联表 - 连接chunk和entity（多对多）
    if 'chunk_entities' not in existing_tables:
        op.create_table(
            'chunk_entities',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),

            # 关联字段（SQLite中外键必须在列定义时声明）
            sa.Column('chunk_id', sa.String(50),
                      sa.ForeignKey('document_chunks.chunk_id', ondelete='CASCADE'),
                      nullable=False,
                      comment='Chunk ID，外键关联document_chunks.chunk_id'),
            sa.Column('entity_id', sa.Integer(),
                      sa.ForeignKey('entities.id', ondelete='CASCADE'),
                      nullable=False,
                      comment='Entity ID，外键关联entities.id'),

            # Entity在Chunk中的信息
            sa.Column('confidence', sa.Float(), nullable=True,
                      comment='置信度分数 0.0-1.0'),
            sa.Column('mention_context', sa.Text(), nullable=True,
                      comment='Entity在Chunk中的上下文片段'),
            sa.Column('position_start', sa.Integer(), nullable=True,
                      comment='Entity在Chunk文本中的起始位置'),
            sa.Column('position_end', sa.Integer(), nullable=True,
                      comment='Entity在Chunk文本中的结束位置'),

            # 时间戳
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),

            # 联合唯一索引（同一个chunk不能重复关联同一个entity）
            sa.UniqueConstraint('chunk_id', 'entity_id', name='uq_chunk_entity'),

            # 查询索引
            sa.Index('idx_chunk_entities_chunk_id', 'chunk_id'),
            sa.Index('idx_chunk_entities_entity_id', 'entity_id'),
        )


def downgrade() -> None:
    """回滚迁移"""
    op.drop_table('chunk_entities')
    op.drop_table('document_chunks')
