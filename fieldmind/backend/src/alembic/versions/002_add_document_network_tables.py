"""add document network tables

Revision ID: 002_document_network
Revises: b2f65e1dffbe
Create Date: 2026-08-06 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_document_network'
down_revision = 'b2f65e1dffbe'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 document_relations 表
    op.create_table(
        'document_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('source_document_id', sa.Integer(), nullable=False),
        sa.Column('target_document_id', sa.Integer(), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['source_document_id'], ['project_documents.id'], ),
        sa.ForeignKeyConstraint(['target_document_id'], ['project_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_relations_project_id'), 'document_relations', ['project_id'], unique=False)
    op.create_index(op.f('ix_document_relations_source_document_id'), 'document_relations', ['source_document_id'], unique=False)
    op.create_index(op.f('ix_document_relations_target_document_id'), 'document_relations', ['target_document_id'], unique=False)
    op.create_index(op.f('ix_document_relations_relation_type'), 'document_relations', ['relation_type'], unique=False)

    # 创建 entity_alignments 表
    op.create_table(
        'entity_alignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('canonical_name', sa.String(length=500), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('original_names', sa.JSON(), nullable=False),
        sa.Column('document_ids', sa.JSON(), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('algorithm_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entity_alignments_project_id'), 'entity_alignments', ['project_id'], unique=False)
    op.create_index(op.f('ix_entity_alignments_canonical_name'), 'entity_alignments', ['canonical_name'], unique=False)
    op.create_index(op.f('ix_entity_alignments_entity_type'), 'entity_alignments', ['entity_type'], unique=False)


def downgrade():
    # 删除 entity_alignments 表
    op.drop_index(op.f('ix_entity_alignments_entity_type'), table_name='entity_alignments')
    op.drop_index(op.f('ix_entity_alignments_canonical_name'), table_name='entity_alignments')
    op.drop_index(op.f('ix_entity_alignments_project_id'), table_name='entity_alignments')
    op.drop_table('entity_alignments')

    # 删除 document_relations 表
    op.drop_index(op.f('ix_document_relations_relation_type'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_target_document_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_source_document_id'), table_name='document_relations')
    op.drop_index(op.f('ix_document_relations_project_id'), table_name='document_relations')
    op.drop_table('document_relations')
