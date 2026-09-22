"""
创建知识图谱相关表

Revision ID: 001_knowledge_graph
Revises:
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_knowledge_graph'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建实体表
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=False),
        sa.Column('entity_name', sa.String(length=200), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('mention_count', sa.Integer(), default=1),
        sa.Column('documents', sa.JSON(), default=list),
        sa.Column('contexts', sa.JSON(), default=list),
        sa.Column('related_entities', sa.JSON(), default=list),
        sa.Column('first_timestamp', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_id')
    )

    # 创建索引
    op.create_index('idx_entity_name', 'entities', ['entity_name'])
    op.create_index('idx_entity_type', 'entities', ['entity_type'])
    op.create_index('idx_entity_name_type', 'entities', ['entity_name', 'entity_type'])
    op.create_index('idx_entity_type_mention', 'entities', ['entity_type', 'mention_count'])

    # 创建关系表
    op.create_table(
        'relations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('relation_id', sa.String(length=50), nullable=False),
        sa.Column('subject_entity_id', sa.String(length=50), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('object_entity_id', sa.String(length=50), nullable=False),
        sa.Column('context', sa.Text()),
        sa.Column('timestamp', sa.Float(), default=0.0),
        sa.Column('source_document', sa.String(length=200)),
        sa.Column('confidence', sa.Float(), default=1.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('relation_id'),
        sa.ForeignKeyConstraint(['subject_entity_id'], ['entities.entity_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['object_entity_id'], ['entities.entity_id'], ondelete='CASCADE')
    )

    # 创建索引
    op.create_index('idx_relation_id', 'relations', ['relation_id'])
    op.create_index('idx_relation_type', 'relations', ['relation_type'])
    op.create_index('idx_relation_subject_type', 'relations', ['subject_entity_id', 'relation_type'])
    op.create_index('idx_relation_type_confidence', 'relations', ['relation_type', 'confidence'])

    # 创建共现关系表
    op.create_table(
        'co_occurrences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entities', sa.JSON(), nullable=False),
        sa.Column('frequency', sa.Integer(), default=1),
        sa.Column('window_type', sa.String(length=20), default='sentence'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('idx_cooccurrence_freq', 'co_occurrences', ['frequency'])

    # 创建知识图谱元数据表
    op.create_table(
        'knowledge_graphs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('graph_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200)),
        sa.Column('description', sa.Text()),
        sa.Column('entity_count', sa.Integer(), default=0),
        sa.Column('relation_count', sa.Integer(), default=0),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('statistics', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('graph_id')
    )

    # 创建索引
    op.create_index('idx_graph_id', 'knowledge_graphs', ['graph_id'])


def downgrade():
    # 删除表（按依赖顺序反向删除）
    op.drop_table('knowledge_graphs')
    op.drop_table('co_occurrences')
    op.drop_table('relations')
    op.drop_table('entities')
