"""Add knowledge graph tables

Revision ID: 003
Revises: 002
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002_document_network'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建知识图谱相关表"""

    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 创建 relations 表（entities表已存在，跳过）
    if 'relations' not in existing_tables:
        op.create_table(
            'relations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('relation_id', sa.String(50), nullable=False, unique=True, comment='关系唯一ID'),
            sa.Column('subject_entity_id', sa.String(50), nullable=False, comment='主体实体ID'),
            sa.Column('relation_type', sa.String(50), nullable=False, comment='关系类型'),
            sa.Column('object_entity_id', sa.String(50), nullable=False, comment='客体实体ID'),
            sa.Column('context', sa.Text(), nullable=True, comment='上下文'),
            sa.Column('timestamp', sa.Float(), default=0.0, comment='时间戳'),
            sa.Column('source_document', sa.String(200), nullable=True, comment='来源文档'),
            sa.Column('confidence', sa.Float(), default=1.0, comment='置信度'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )

        # 创建索引（SQLite不支持外键约束，只创建索引）
        op.create_index('ix_relations_relation_id', 'relations', ['relation_id'])
        op.create_index('ix_relations_subject_entity_id', 'relations', ['subject_entity_id'])
        op.create_index('ix_relations_object_entity_id', 'relations', ['object_entity_id'])
        op.create_index('ix_relations_relation_type', 'relations', ['relation_type'])
        op.create_index('idx_relation_subject_type', 'relations', ['subject_entity_id', 'relation_type'])
        op.create_index('idx_relation_type_confidence', 'relations', ['relation_type', 'confidence'])

    # 创建 co_occurrences 表
    if 'co_occurrences' not in existing_tables:
        op.create_table(
            'co_occurrences',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('entities', sa.JSON(), nullable=False, comment='共现实体列表'),
            sa.Column('frequency', sa.Integer(), default=1, comment='共现频次'),
            sa.Column('window_type', sa.String(20), default='sentence', comment='窗口类型'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )

        op.create_index('idx_cooccurrence_freq', 'co_occurrences', ['frequency'])

    # 创建 knowledge_graphs 元数据表
    if 'knowledge_graphs' not in existing_tables:
        op.create_table(
            'knowledge_graphs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('graph_id', sa.String(50), nullable=False, unique=True, comment='图谱ID'),
            sa.Column('name', sa.String(200), nullable=True, comment='图谱名称'),
            sa.Column('description', sa.Text(), nullable=True, comment='图谱描述'),
            sa.Column('entity_count', sa.Integer(), default=0, comment='实体总数'),
            sa.Column('relation_count', sa.Integer(), default=0, comment='关系总数'),
            sa.Column('document_count', sa.Integer(), default=0, comment='文档总数'),
            sa.Column('statistics', sa.JSON(), nullable=True, comment='统计信息'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )

        op.create_index('ix_knowledge_graphs_graph_id', 'knowledge_graphs', ['graph_id'])


def downgrade() -> None:
    """删除知识图谱相关表"""

    # 删除表（按依赖顺序反向删除）
    op.drop_table('knowledge_graphs')
    op.drop_table('co_occurrences')
    op.drop_table('relations')
    op.drop_table('entities')
