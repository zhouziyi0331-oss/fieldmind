"""
Database Migration: Add skill_versions table
创建技能版本表用于追踪Skill演化历史
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_skill_versions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建skill_versions表"""
    op.create_table(
        'skill_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),

        # 版本信息
        sa.Column('version_number', sa.Integer(), nullable=False, default=1),
        sa.Column('version_tag', sa.String(50), nullable=True),

        # Skill内容
        sa.Column('skill_name', sa.String(200), nullable=False),
        sa.Column('skill_content', sa.Text(), nullable=False),
        sa.Column('skill_type', sa.String(50), nullable=True),

        # 变更信息
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),

        # 优化信息
        sa.Column('optimization_reason', sa.Text(), nullable=True),
        sa.Column('optimization_metrics', sa.JSON(), nullable=True),

        # 使用统计
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('failure_count', sa.Integer(), default=0),
        sa.Column('avg_execution_time', sa.Float(), nullable=True),

        # 状态
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_deprecated', sa.Boolean(), default=False),

        # 元数据
        sa.Column('metadata', sa.JSON(), nullable=True),

        # 关系追踪
        sa.Column('parent_version_id', sa.Integer(), nullable=True),
        sa.Column('superseded_by_id', sa.Integer(), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),

        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_version_id'], ['skill_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['superseded_by_id'], ['skill_versions.id'], ondelete='SET NULL'),
    )

    # 创建索引
    op.create_index('idx_skill_versions_skill_id', 'skill_versions', ['skill_id'])
    op.create_index('idx_skill_versions_project_id', 'skill_versions', ['project_id'])
    op.create_index('idx_skill_versions_user_id', 'skill_versions', ['user_id'])
    op.create_index('idx_skill_versions_skill_name', 'skill_versions', ['skill_name'])
    op.create_index('idx_skill_versions_is_active', 'skill_versions', ['is_active'])
    op.create_index('idx_skill_versions_change_type', 'skill_versions', ['change_type'])
    op.create_index(
        'idx_skill_versions_skill_project',
        'skill_versions',
        ['skill_id', 'project_id', 'version_number'],
        unique=True
    )


def downgrade():
    """删除skill_versions表"""
    op.drop_index('idx_skill_versions_skill_project', table_name='skill_versions')
    op.drop_index('idx_skill_versions_change_type', table_name='skill_versions')
    op.drop_index('idx_skill_versions_is_active', table_name='skill_versions')
    op.drop_index('idx_skill_versions_skill_name', table_name='skill_versions')
    op.drop_index('idx_skill_versions_user_id', table_name='skill_versions')
    op.drop_index('idx_skill_versions_project_id', table_name='skill_versions')
    op.drop_index('idx_skill_versions_skill_id', table_name='skill_versions')
    op.drop_table('skill_versions')
