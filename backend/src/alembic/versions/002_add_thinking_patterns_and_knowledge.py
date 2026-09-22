"""
Database Migration: Add thinking_patterns, skill_knowledge_base, domain_knowledge tables
创建思维模式、Skill知识库、领域知识表（Phase 4: 外部知识关联）
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_thinking_patterns_and_knowledge'
down_revision = '001_add_skill_versions'
branch_labels = None
depends_on = None


def upgrade():
    """创建思维模式和知识库表"""

    # 1. 创建 thinking_patterns 表
    op.create_table(
        'thinking_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),

        # 模式信息
        sa.Column('pattern_name', sa.String(200), nullable=False),
        sa.Column('pattern_type', sa.String(50), nullable=False),
        sa.Column('pattern_description', sa.Text(), nullable=False),
        sa.Column('pattern_context', sa.Text(), nullable=True),

        # 模式内容
        sa.Column('trigger_conditions', sa.JSON(), nullable=True),
        sa.Column('thought_process', sa.Text(), nullable=False),
        sa.Column('expected_outcome', sa.Text(), nullable=True),
        sa.Column('implementation_steps', sa.JSON(), nullable=True),

        # 来源信息
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=False),

        # 使用统计
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('failure_count', sa.Integer(), default=0),
        sa.Column('avg_effectiveness', sa.Float(), nullable=True),

        # 状态
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_validated', sa.Boolean(), default=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),

        # 关联知识
        sa.Column('related_patterns', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # thinking_patterns 索引
    op.create_index('ix_thinking_patterns_id', 'thinking_patterns', ['id'])
    op.create_index('ix_thinking_patterns_project_id', 'thinking_patterns', ['project_id'])
    op.create_index('ix_thinking_patterns_skill_id', 'thinking_patterns', ['skill_id'])
    op.create_index('ix_thinking_patterns_user_id', 'thinking_patterns', ['user_id'])
    op.create_index('ix_thinking_patterns_pattern_name', 'thinking_patterns', ['pattern_name'])
    op.create_index('ix_thinking_patterns_pattern_type', 'thinking_patterns', ['pattern_type'])
    op.create_index('ix_thinking_patterns_is_active', 'thinking_patterns', ['is_active'])
    op.create_index('ix_thinking_patterns_is_validated', 'thinking_patterns', ['is_validated'])

    # 2. 创建 skill_knowledge_base 表
    op.create_table(
        'skill_knowledge_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),

        # 知识条目
        sa.Column('knowledge_title', sa.String(200), nullable=False),
        sa.Column('knowledge_type', sa.String(50), nullable=False),
        sa.Column('knowledge_content', sa.Text(), nullable=False),
        sa.Column('knowledge_context', sa.Text(), nullable=True),

        # 来源
        sa.Column('source_patterns', sa.JSON(), nullable=True),
        sa.Column('source_executions', sa.JSON(), nullable=True),
        sa.Column('derived_from', sa.String(200), nullable=True),

        # 应用指导
        sa.Column('when_to_use', sa.Text(), nullable=True),
        sa.Column('when_not_to_use', sa.Text(), nullable=True),
        sa.Column('prerequisites', sa.JSON(), nullable=True),
        sa.Column('expected_benefits', sa.JSON(), nullable=True),

        # 统计
        sa.Column('application_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),

        # 状态
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('confidence_level', sa.String(20), nullable=True),

        # 元数据
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_applied_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # skill_knowledge_base 索引
    op.create_index('ix_skill_knowledge_base_id', 'skill_knowledge_base', ['id'])
    op.create_index('ix_skill_knowledge_base_project_id', 'skill_knowledge_base', ['project_id'])
    op.create_index('ix_skill_knowledge_base_skill_id', 'skill_knowledge_base', ['skill_id'])
    op.create_index('ix_skill_knowledge_base_user_id', 'skill_knowledge_base', ['user_id'])
    op.create_index('ix_skill_knowledge_base_knowledge_title', 'skill_knowledge_base', ['knowledge_title'])
    op.create_index('ix_skill_knowledge_base_knowledge_type', 'skill_knowledge_base', ['knowledge_type'])

    # 3. 创建 domain_knowledge 表
    op.create_table(
        'domain_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),

        # 知识信息
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('knowledge_content', sa.Text(), nullable=False),
        sa.Column('knowledge_type', sa.String(50), nullable=False),

        # 来源
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_reliability', sa.String(20), nullable=True),

        # 使用约束（关键）
        sa.Column('usage_constraint', sa.String(50), nullable=False, server_default='background_only'),
        sa.Column('can_influence_decision', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_influence_analysis', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_influence_report', sa.Boolean(), nullable=False, server_default='false'),

        # 元数据
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # domain_knowledge 索引
    op.create_index('ix_domain_knowledge_id', 'domain_knowledge', ['id'])
    op.create_index('ix_domain_knowledge_domain', 'domain_knowledge', ['domain'])
    op.create_index('ix_domain_knowledge_topic', 'domain_knowledge', ['topic'])


def downgrade():
    """删除思维模式和知识库表"""

    # 删除索引
    op.drop_index('ix_domain_knowledge_topic', table_name='domain_knowledge')
    op.drop_index('ix_domain_knowledge_domain', table_name='domain_knowledge')
    op.drop_index('ix_domain_knowledge_id', table_name='domain_knowledge')

    op.drop_index('ix_skill_knowledge_base_knowledge_type', table_name='skill_knowledge_base')
    op.drop_index('ix_skill_knowledge_base_knowledge_title', table_name='skill_knowledge_base')
    op.drop_index('ix_skill_knowledge_base_user_id', table_name='skill_knowledge_base')
    op.drop_index('ix_skill_knowledge_base_skill_id', table_name='skill_knowledge_base')
    op.drop_index('ix_skill_knowledge_base_project_id', table_name='skill_knowledge_base')
    op.drop_index('ix_skill_knowledge_base_id', table_name='skill_knowledge_base')

    op.drop_index('ix_thinking_patterns_is_validated', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_is_active', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_pattern_type', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_pattern_name', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_user_id', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_skill_id', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_project_id', table_name='thinking_patterns')
    op.drop_index('ix_thinking_patterns_id', table_name='thinking_patterns')

    # 删除表
    op.drop_table('domain_knowledge')
    op.drop_table('skill_knowledge_base')
    op.drop_table('thinking_patterns')
