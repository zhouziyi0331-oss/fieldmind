"""
蒸馏系统数据库迁移

创建蒸馏相关表
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'distillation_v1'
down_revision = None  # 替换为你的最新版本号
branch_labels = None
depends_on = None


def upgrade():
    # 创建蒸馏任务表
    op.create_table(
        'distillation_jobs',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('generation_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('input_mode', sa.String(32), nullable=False),
        sa.Column('source_kind', sa.String(32), nullable=False),
        sa.Column('source_mode', sa.String(64), nullable=False),
        sa.Column('source_metadata', sa.JSON, nullable=False),
        sa.Column('status', sa.String(32), nullable=False, index=True),
        sa.Column('current_stage', sa.String(64)),
        sa.Column('progress', sa.JSON),
        sa.Column('normalized_source_path', sa.Text),
        sa.Column('book_overview_path', sa.Text),
        sa.Column('verified_methods_path', sa.Text),
        sa.Column('knowledge_units_path', sa.Text),
        sa.Column('methods_path', sa.Text),
        sa.Column('audit_path', sa.Text),
        sa.Column('package_path', sa.Text),
        sa.Column('knowledge_count', sa.Integer, default=0),
        sa.Column('method_count', sa.Integer, default=0),
        sa.Column('candidate_count', sa.Integer, default=0),
        sa.Column('verified_count', sa.Integer, default=0),
        sa.Column('rejected_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('error_message', sa.Text),
        sa.Column('error_traceback', sa.Text),
    )

    # 创建知识单元表
    op.create_table(
        'extracted_knowledge',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('distillation_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('generation_id', sa.String(64), nullable=False, index=True),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('statement', sa.Text, nullable=False),
        sa.Column('explanation', sa.Text, nullable=False),
        sa.Column('why_it_matters', sa.Text),
        sa.Column('scope', sa.Text),
        sa.Column('conditions', sa.JSON),
        sa.Column('boundaries', sa.JSON),
        sa.Column('counterexamples', sa.JSON),
        sa.Column('evidence_anchors', sa.JSON, nullable=False),
        sa.Column('evidence_route', sa.String(64)),
        sa.Column('source_certainty', sa.String(32)),
        sa.Column('claim_attribution', sa.String(64)),
        sa.Column('extraction_certainty', sa.Float),
        sa.Column('external_verification_status', sa.String(32), default='not-verified'),
        sa.Column('tags', sa.JSON),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # 创建方法单元表
    op.create_table(
        'extracted_methods',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('distillation_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('generation_id', sa.String(64), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('reading_quote', sa.Text, nullable=False),
        sa.Column('reading_source', sa.String(255)),
        sa.Column('interpretation', sa.Text, nullable=False),
        sa.Column('past_applications', sa.JSON),
        sa.Column('trigger_scenarios', sa.JSON),
        sa.Column('trigger_language_signals', sa.JSON),
        sa.Column('distinction_from_neighbors', sa.JSON),
        sa.Column('execution_steps', sa.JSON, nullable=False),
        sa.Column('boundary_anti_scenarios', sa.JSON),
        sa.Column('boundary_failure_modes', sa.JSON),
        sa.Column('boundary_author_blindspots', sa.JSON),
        sa.Column('boundary_confusion_risks', sa.JSON),
        sa.Column('source_book', sa.String(255)),
        sa.Column('source_chapter', sa.String(255)),
        sa.Column('tags', sa.JSON),
        sa.Column('related_methods', sa.JSON),
        sa.Column('test_suite', sa.JSON),
        sa.Column('test_results', sa.JSON),
        sa.Column('test_pass_rate', sa.Float),
        sa.Column('canonical_sha256', sa.String(71)),
        sa.Column('is_frozen', sa.Boolean, default=False),
        sa.Column('frozen_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # 创建知识-方法关系表
    op.create_table(
        'knowledge_method_relations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('generation_id', sa.String(64), nullable=False, index=True),
        sa.Column('knowledge_unit_id', sa.String(64), sa.ForeignKey('extracted_knowledge.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('method_unit_id', sa.String(64), sa.ForeignKey('extracted_methods.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('relation_type', sa.String(32), nullable=False),
        sa.Column('evidence_anchors', sa.JSON),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # 创建方法-方法关系表
    op.create_table(
        'method_method_relations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('generation_id', sa.String(64), nullable=False, index=True),
        sa.Column('source_method_id', sa.String(64), sa.ForeignKey('extracted_methods.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('target_method_id', sa.String(64), sa.ForeignKey('extracted_methods.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('relation_type', sa.String(32), nullable=False),
        sa.Column('evidence', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # 创建生产快照表
    op.create_table(
        'production_snapshots',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('distillation_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('generation_id', sa.String(64), nullable=False, index=True),
        sa.Column('producer_id', sa.String(128), nullable=False),
        sa.Column('role', sa.String(128), nullable=False),
        sa.Column('tool', sa.String(128)),
        sa.Column('version', sa.String(64)),
        sa.Column('run_id', sa.String(64), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('ended_at', sa.DateTime),
        sa.Column('platform', sa.String(64)),
        sa.Column('model', sa.String(64)),
        sa.Column('interface', sa.String(64)),
        sa.Column('inputs', sa.JSON),
        sa.Column('outputs', sa.JSON),
        sa.Column('prompts', sa.JSON),
        sa.Column('config', sa.JSON),
        sa.Column('methodology_version', sa.String(64)),
        sa.Column('success', sa.Boolean, default=False),
        sa.Column('failures', sa.JSON),
        sa.Column('rework_count', sa.Integer, default=0),
        sa.Column('snapshot_sha256', sa.String(71)),
        sa.Column('snapshot_path', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

    # 创建索引
    op.create_index('idx_distillation_jobs_status', 'distillation_jobs', ['status'])
    op.create_index('idx_distillation_jobs_generation_id', 'distillation_jobs', ['generation_id'])
    op.create_index('idx_extracted_knowledge_job_id', 'extracted_knowledge', ['job_id'])
    op.create_index('idx_extracted_methods_job_id', 'extracted_methods', ['job_id'])


def downgrade():
    # 删除索引
    op.drop_index('idx_extracted_methods_job_id')
    op.drop_index('idx_extracted_knowledge_job_id')
    op.drop_index('idx_distillation_jobs_generation_id')
    op.drop_index('idx_distillation_jobs_status')

    # 删除表
    op.drop_table('production_snapshots')
    op.drop_table('method_method_relations')
    op.drop_table('knowledge_method_relations')
    op.drop_table('extracted_methods')
    op.drop_table('extracted_knowledge')
    op.drop_table('distillation_jobs')
