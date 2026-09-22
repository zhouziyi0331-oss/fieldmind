"""add_federation_tables

Revision ID: b2f65e1dffbe
Revises: 116f3df30673
Create Date: 2026-08-06 21:21:14.013269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f65e1dffbe'
down_revision: Union[str, None] = '116f3df30673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 fieldmind_objects 表
    op.create_table(
        'fieldmind_objects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fid', sa.String(length=100), nullable=False),
        sa.Column('object_type', sa.String(length=50), nullable=False),
        sa.Column('source_fid', sa.String(length=100), nullable=True),
        sa.Column('derived_from_chain', sa.JSON(), nullable=True),
        sa.Column('storage_info', sa.JSON(), nullable=False),
        sa.Column('object_metadata', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fid')
    )
    op.create_index('idx_fid_project', 'fieldmind_objects', ['fid', 'project_id'])
    op.create_index('idx_project_type', 'fieldmind_objects', ['project_id', 'object_type'])
    op.create_index(op.f('ix_fieldmind_objects_created_at'), 'fieldmind_objects', ['created_at'])
    op.create_index(op.f('ix_fieldmind_objects_fid'), 'fieldmind_objects', ['fid'])
    op.create_index(op.f('ix_fieldmind_objects_object_type'), 'fieldmind_objects', ['object_type'])
    op.create_index(op.f('ix_fieldmind_objects_project_id'), 'fieldmind_objects', ['project_id'])
    op.create_index(op.f('ix_fieldmind_objects_source_fid'), 'fieldmind_objects', ['source_fid'])

    # 创建 object_relations 表
    op.create_table(
        'object_relations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('from_fid', sa.String(length=100), nullable=False),
        sa.Column('to_fid', sa.String(length=100), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('strength', sa.Float(), nullable=True),
        sa.Column('evidence_fids', sa.JSON(), nullable=True),
        sa.Column('relation_data', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_from_to', 'object_relations', ['from_fid', 'to_fid'])
    op.create_index('idx_from_type', 'object_relations', ['from_fid', 'relation_type'])
    op.create_index('idx_project_relation', 'object_relations', ['project_id', 'relation_type'])
    op.create_index(op.f('ix_object_relations_from_fid'), 'object_relations', ['from_fid'])
    op.create_index(op.f('ix_object_relations_project_id'), 'object_relations', ['project_id'])
    op.create_index(op.f('ix_object_relations_relation_type'), 'object_relations', ['relation_type'])
    op.create_index(op.f('ix_object_relations_to_fid'), 'object_relations', ['to_fid'])

    # 创建 fact_statements 表
    op.create_table(
        'fact_statements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fid', sa.String(length=100), nullable=False),
        sa.Column('source_fid', sa.String(length=100), nullable=True),
        sa.Column('derived_from_chain', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('statement_text', sa.Text(), nullable=False),
        sa.Column('statement_type', sa.String(length=50), nullable=True),
        sa.Column('start_sec', sa.Float(), nullable=True),
        sa.Column('end_sec', sa.Float(), nullable=True),
        sa.Column('entity_names', sa.JSON(), nullable=True),
        sa.Column('entity_fids', sa.JSON(), nullable=True),
        sa.Column('event_summary', sa.String(length=500), nullable=True),
        sa.Column('event_fid', sa.String(length=100), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('context_before', sa.Text(), nullable=True),
        sa.Column('context_after', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('vector_id', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fid')
    )
    op.create_index('idx_document_time', 'fact_statements', ['document_id', 'start_sec'])
    op.create_index('idx_project_time', 'fact_statements', ['project_id', 'start_sec'])
    op.create_index(op.f('ix_fact_statements_document_id'), 'fact_statements', ['document_id'])
    op.create_index(op.f('ix_fact_statements_event_fid'), 'fact_statements', ['event_fid'])
    op.create_index(op.f('ix_fact_statements_fid'), 'fact_statements', ['fid'])
    op.create_index(op.f('ix_fact_statements_project_id'), 'fact_statements', ['project_id'])
    op.create_index(op.f('ix_fact_statements_source_fid'), 'fact_statements', ['source_fid'])
    op.create_index(op.f('ix_fact_statements_start_sec'), 'fact_statements', ['start_sec'])


def downgrade() -> None:
    # 删除 fact_statements 表
    op.drop_index(op.f('ix_fact_statements_start_sec'), table_name='fact_statements')
    op.drop_index(op.f('ix_fact_statements_source_fid'), table_name='fact_statements')
    op.drop_index(op.f('ix_fact_statements_project_id'), table_name='fact_statements')
    op.drop_index(op.f('ix_fact_statements_fid'), table_name='fact_statements')
    op.drop_index(op.f('ix_fact_statements_event_fid'), table_name='fact_statements')
    op.drop_index(op.f('ix_fact_statements_document_id'), table_name='fact_statements')
    op.drop_index('idx_project_time', table_name='fact_statements')
    op.drop_index('idx_document_time', table_name='fact_statements')
    op.drop_table('fact_statements')

    # 删除 object_relations 表
    op.drop_index(op.f('ix_object_relations_to_fid'), table_name='object_relations')
    op.drop_index(op.f('ix_object_relations_relation_type'), table_name='object_relations')
    op.drop_index(op.f('ix_object_relations_project_id'), table_name='object_relations')
    op.drop_index(op.f('ix_object_relations_from_fid'), table_name='object_relations')
    op.drop_index('idx_project_relation', table_name='object_relations')
    op.drop_index('idx_from_type', table_name='object_relations')
    op.drop_index('idx_from_to', table_name='object_relations')
    op.drop_table('object_relations')

    # 删除 fieldmind_objects 表
    op.drop_index(op.f('ix_fieldmind_objects_source_fid'), table_name='fieldmind_objects')
    op.drop_index(op.f('ix_fieldmind_objects_project_id'), table_name='fieldmind_objects')
    op.drop_index(op.f('ix_fieldmind_objects_object_type'), table_name='fieldmind_objects')
    op.drop_index(op.f('ix_fieldmind_objects_fid'), table_name='fieldmind_objects')
    op.drop_index(op.f('ix_fieldmind_objects_created_at'), table_name='fieldmind_objects')
    op.drop_index('idx_project_type', table_name='fieldmind_objects')
    op.drop_index('idx_fid_project', table_name='fieldmind_objects')
    op.drop_table('fieldmind_objects')
