"""添加编年史智能关联字段到 timeline_events 表

Revision ID: add_chronicle_fields
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'add_chronicle_fields'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    """添加编年史相关字段"""
    with op.batch_alter_table('timeline_events', schema=None) as batch_op:
        # 添加关联关系字段
        batch_op.add_column(sa.Column('relations', sa.JSON(), nullable=True))

        # 添加主题标签字段
        batch_op.add_column(sa.Column('theme_tags', sa.JSON(), nullable=True))

        # 添加关键人物字段
        batch_op.add_column(sa.Column('key_persons', sa.JSON(), nullable=True))

        # 添加关键地点字段
        batch_op.add_column(sa.Column('key_locations', sa.JSON(), nullable=True))

        # 添加叙事摘要字段
        batch_op.add_column(sa.Column('narrative_summary', sa.Text(), nullable=True))


def downgrade():
    """回滚：删除编年史相关字段"""
    with op.batch_alter_table('timeline_events', schema=None) as batch_op:
        batch_op.drop_column('narrative_summary')
        batch_op.drop_column('key_locations')
        batch_op.drop_column('key_persons')
        batch_op.drop_column('theme_tags')
        batch_op.drop_column('relations')
