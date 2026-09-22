"""003_add_batch_operations_table

Revision ID: 003_batch_operations
Revises: 002_add_document_network_tables
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_batch_operations'
down_revision = '002_document_network'
branch_labels = None
depends_on = None


def upgrade():
    """添加批量操作表"""
    op.create_table(
        'batch_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=True, default=0),
        sa.Column('completed_items', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_items', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_batch_operations_id', 'batch_operations', ['id'])
    op.create_index('ix_batch_operations_batch_id', 'batch_operations', ['batch_id'], unique=True)
    op.create_index('ix_batch_operations_project_id', 'batch_operations', ['project_id'])
    op.create_index('ix_batch_operations_status', 'batch_operations', ['status'])
    op.create_index('ix_batch_operations_created_at', 'batch_operations', ['created_at'])


def downgrade():
    """删除批量操作表"""
    op.drop_index('ix_batch_operations_created_at', table_name='batch_operations')
    op.drop_index('ix_batch_operations_status', table_name='batch_operations')
    op.drop_index('ix_batch_operations_project_id', table_name='batch_operations')
    op.drop_index('ix_batch_operations_batch_id', table_name='batch_operations')
    op.drop_index('ix_batch_operations_id', table_name='batch_operations')
    op.drop_table('batch_operations')
