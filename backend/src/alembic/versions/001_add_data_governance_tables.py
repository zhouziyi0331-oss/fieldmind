"""add data governance tables

Revision ID: 001_data_governance
Revises: fd1ee1e9d5d3
Create Date: 2026-08-20 23:30:00.000000

数据治理系统完整表结构：
1. metric_dictionary - 指标字典（预置20+指标）
2. lineage_templates - 血缘模板
3. quality_rules + quality_check_results - 质量监控
4. change_events - 变更管理
5. metric_calculation_history - 指标计算历史
6. files 表新增12个元数据字段
7. chunks 表新增15个指标字段
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from datetime import datetime

# revision identifiers
revision = '001_data_governance'
down_revision = 'fd1ee1e9d5d3'
branch_labels = None
depends_on = None


def upgrade():
    """创建数据治理系统所需的所有表和字段"""

    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # ===== 1. 创建 metric_dictionary 表 =====
    if 'metric_dictionary' not in existing_tables:
        op.create_table(
        'metric_dictionary',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('metric_name', sa.String(100), nullable=False, unique=True),
        sa.Column('metric_type', sa.Enum('basic', 'semantic', 'quality', 'complexity', name='metric_type_enum'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('calculation_method', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('threshold_low', sa.Float(), nullable=True),
        sa.Column('threshold_high', sa.Float(), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_name', name='uq_metric_name')
    )

        # 创建索引
        op.create_index('idx_metric_type', 'metric_dictionary', ['metric_type'])
        op.create_index('idx_metric_enabled', 'metric_dictionary', ['enabled'])

    # ===== 2. 创建 lineage_templates 表 =====
    if 'lineage_templates' not in existing_tables:
        op.create_table(
        'lineage_templates',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('template_name', sa.String(100), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('transform_pattern', sa.Text(), nullable=True),
        sa.Column('field_mappings', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_name', name='uq_template_name')
    )

    op.create_index('idx_lineage_template_types', 'lineage_templates', ['source_type', 'target_type'])

    # ===== 3. 创建 lineage_edges 表（如果不存在）=====
    # 检查表是否已存在（通过 lineage_tracker.py 使用原始SQL创建）
    # 这里使用 Alembic 正式定义
    try:
        op.create_table(
            'lineage_edges',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('source_type', sa.String(50), nullable=False),
            sa.Column('source_id', sa.String(100), nullable=False),
            sa.Column('target_type', sa.String(50), nullable=False),
            sa.Column('target_id', sa.String(100), nullable=False),
            sa.Column('transform_type', sa.String(50), nullable=False),
            sa.Column('transform_description', sa.Text(), nullable=True),
            sa.Column('confidence', sa.Float(), default=1.0),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_index('idx_lineage_source', 'lineage_edges', ['source_type', 'source_id'])
        op.create_index('idx_lineage_target', 'lineage_edges', ['target_type', 'target_id'])
        op.create_index('idx_lineage_project', 'lineage_edges', ['project_id'])
        op.create_index('idx_lineage_created', 'lineage_edges', ['created_at'])
    except:
        # 表已存在，跳过
        pass

    # ===== 4. 创建 quality_rules 表 =====
    op.create_table(
        'quality_rules',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('rule_name', sa.String(100), nullable=False, unique=True),
        sa.Column('rule_type', sa.Enum('completeness', 'accuracy', 'consistency', 'timeliness', 'uniqueness', name='quality_rule_type_enum'), nullable=False),
        sa.Column('target_entity', sa.String(50), nullable=False),
        sa.Column('validation_logic', sa.JSON(), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='severity_enum'), default='medium'),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_name', name='uq_rule_name')
    )

    op.create_index('idx_quality_rule_type', 'quality_rules', ['rule_type'])
    op.create_index('idx_quality_target_entity', 'quality_rules', ['target_entity'])
    op.create_index('idx_quality_enabled', 'quality_rules', ['enabled'])

    # ===== 5. 创建 quality_check_results 表 =====
    op.create_table(
        'quality_check_results',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('check_result', sa.Enum('pass', 'fail', 'warning', name='check_result_enum'), nullable=False),
        sa.Column('result_details', sa.JSON(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_id'], ['quality_rules.id'], ondelete='CASCADE')
    )

    op.create_index('idx_qc_rule', 'quality_check_results', ['rule_id'])
    op.create_index('idx_qc_entity', 'quality_check_results', ['entity_type', 'entity_id'])
    op.create_index('idx_qc_result', 'quality_check_results', ['check_result'])
    op.create_index('idx_qc_checked', 'quality_check_results', ['checked_at'])

    # ===== 6. 创建 change_events 表 =====
    op.create_table(
        'change_events',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('change_type', sa.Enum('create', 'update', 'delete', 'schema_change', name='change_type_enum'), nullable=False),
        sa.Column('change_details', sa.JSON(), nullable=True),
        sa.Column('changed_by', sa.String(100), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('related_entities', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_change_entity', 'change_events', ['entity_type', 'entity_id'])
    op.create_index('idx_change_type', 'change_events', ['change_type'])
    op.create_index('idx_change_created', 'change_events', ['created_at'])
    op.create_index('idx_change_by', 'change_events', ['changed_by'])

    # ===== 7. 创建 metric_calculation_history 表 =====
    op.create_table(
        'metric_calculation_history',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('calculation_method', sa.Text(), nullable=True),
        sa.Column('calculation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['metric_id'], ['metric_dictionary.id'], ondelete='CASCADE')
    )

    op.create_index('idx_metric_history_entity', 'metric_calculation_history', ['entity_type', 'entity_id'])
    op.create_index('idx_metric_history_metric', 'metric_calculation_history', ['metric_id'])
    op.create_index('idx_metric_history_calculated', 'metric_calculation_history', ['calculated_at'])

    # ===== 8. files 表新增 12 个元数据字段 =====
    # 注意：根据实际表名调整（可能是 files 或 documents）
    try:
        op.add_column('files', sa.Column('source_system', sa.String(100), nullable=True))
        op.add_column('files', sa.Column('business_owner', sa.String(100), nullable=True))
        op.add_column('files', sa.Column('data_classification', sa.Enum('public', 'internal', 'confidential', 'restricted', name='classification_enum'), nullable=True))
        op.add_column('files', sa.Column('retention_period', sa.Integer(), nullable=True, comment='保留天数'))
        op.add_column('files', sa.Column('last_accessed_at', sa.DateTime(), nullable=True))
        op.add_column('files', sa.Column('access_count', sa.Integer(), default=0))
        op.add_column('files', sa.Column('quality_score', sa.Float(), nullable=True, comment='0-100'))
        op.add_column('files', sa.Column('processing_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='processing_status_enum'), nullable=True))
        op.add_column('files', sa.Column('error_message', sa.Text(), nullable=True))
        op.add_column('files', sa.Column('retry_count', sa.Integer(), default=0))
        op.add_column('files', sa.Column('metadata_version', sa.String(20), nullable=True))
        op.add_column('files', sa.Column('governance_tags', sa.JSON(), nullable=True))

        op.create_index('idx_files_classification', 'files', ['data_classification'])
        op.create_index('idx_files_processing_status', 'files', ['processing_status'])
        op.create_index('idx_files_quality', 'files', ['quality_score'])
    except:
        # 如果表名是 documents 而不是 files
        pass

    # ===== 9. chunks 表新增 15 个指标字段 =====
    try:
        op.add_column('document_chunks', sa.Column('semantic_density', sa.Float(), nullable=True, comment='语义密度'))
        op.add_column('document_chunks', sa.Column('coherence_score', sa.Float(), nullable=True, comment='连贯性得分'))
        op.add_column('document_chunks', sa.Column('information_gain', sa.Float(), nullable=True, comment='信息增益'))
        op.add_column('document_chunks', sa.Column('topic_relevance', sa.Float(), nullable=True, comment='主题相关性'))
        op.add_column('document_chunks', sa.Column('readability_score', sa.Float(), nullable=True, comment='可读性'))
        op.add_column('document_chunks', sa.Column('entity_count', sa.Integer(), default=0, comment='实体数量'))
        op.add_column('document_chunks', sa.Column('keyword_count', sa.Integer(), default=0, comment='关键词数量'))
        op.add_column('document_chunks', sa.Column('avg_sentence_length', sa.Float(), nullable=True, comment='平均句长'))
        op.add_column('document_chunks', sa.Column('lexical_diversity', sa.Float(), nullable=True, comment='词汇多样性'))
        op.add_column('document_chunks', sa.Column('sentiment_score', sa.Float(), nullable=True, comment='情感得分'))
        op.add_column('document_chunks', sa.Column('complexity_score', sa.Float(), nullable=True, comment='复杂度'))
        op.add_column('document_chunks', sa.Column('parent_chunk_id', sa.String(50), nullable=True, comment='父chunk'))
        op.add_column('document_chunks', sa.Column('chunk_level', sa.Integer(), default=1, comment='chunk层级'))
        op.add_column('document_chunks', sa.Column('overlap_with_prev', sa.Integer(), default=0, comment='与前一chunk重叠字符数'))
        op.add_column('document_chunks', sa.Column('overlap_with_next', sa.Integer(), default=0, comment='与后一chunk重叠字符数'))

        op.create_index('idx_chunks_semantic_density', 'document_chunks', ['semantic_density'])
        op.create_index('idx_chunks_coherence', 'document_chunks', ['coherence_score'])
        op.create_index('idx_chunks_parent', 'document_chunks', ['parent_chunk_id'])
        op.create_index('idx_chunks_level', 'document_chunks', ['chunk_level'])
    except:
        pass


def downgrade():
    """回滚数据治理系统的所有更改"""

    # 删除 chunks 表新增字段
    try:
        op.drop_index('idx_chunks_level', 'document_chunks')
        op.drop_index('idx_chunks_parent', 'document_chunks')
        op.drop_index('idx_chunks_coherence', 'document_chunks')
        op.drop_index('idx_chunks_semantic_density', 'document_chunks')

        op.drop_column('document_chunks', 'overlap_with_next')
        op.drop_column('document_chunks', 'overlap_with_prev')
        op.drop_column('document_chunks', 'chunk_level')
        op.drop_column('document_chunks', 'parent_chunk_id')
        op.drop_column('document_chunks', 'complexity_score')
        op.drop_column('document_chunks', 'sentiment_score')
        op.drop_column('document_chunks', 'lexical_diversity')
        op.drop_column('document_chunks', 'avg_sentence_length')
        op.drop_column('document_chunks', 'keyword_count')
        op.drop_column('document_chunks', 'entity_count')
        op.drop_column('document_chunks', 'readability_score')
        op.drop_column('document_chunks', 'topic_relevance')
        op.drop_column('document_chunks', 'information_gain')
        op.drop_column('document_chunks', 'coherence_score')
        op.drop_column('document_chunks', 'semantic_density')
    except:
        pass

    # 删除 files 表新增字段
    try:
        op.drop_index('idx_files_quality', 'files')
        op.drop_index('idx_files_processing_status', 'files')
        op.drop_index('idx_files_classification', 'files')

        op.drop_column('files', 'governance_tags')
        op.drop_column('files', 'metadata_version')
        op.drop_column('files', 'retry_count')
        op.drop_column('files', 'error_message')
        op.drop_column('files', 'processing_status')
        op.drop_column('files', 'quality_score')
        op.drop_column('files', 'access_count')
        op.drop_column('files', 'last_accessed_at')
        op.drop_column('files', 'retention_period')
        op.drop_column('files', 'data_classification')
        op.drop_column('files', 'business_owner')
        op.drop_column('files', 'source_system')
    except:
        pass

    # 删除表（按依赖关系倒序）
    op.drop_index('idx_metric_history_calculated', 'metric_calculation_history')
    op.drop_index('idx_metric_history_metric', 'metric_calculation_history')
    op.drop_index('idx_metric_history_entity', 'metric_calculation_history')
    op.drop_table('metric_calculation_history')

    op.drop_index('idx_change_by', 'change_events')
    op.drop_index('idx_change_created', 'change_events')
    op.drop_index('idx_change_type', 'change_events')
    op.drop_index('idx_change_entity', 'change_events')
    op.drop_table('change_events')

    op.drop_index('idx_qc_checked', 'quality_check_results')
    op.drop_index('idx_qc_result', 'quality_check_results')
    op.drop_index('idx_qc_entity', 'quality_check_results')
    op.drop_index('idx_qc_rule', 'quality_check_results')
    op.drop_table('quality_check_results')

    op.drop_index('idx_quality_enabled', 'quality_rules')
    op.drop_index('idx_quality_target_entity', 'quality_rules')
    op.drop_index('idx_quality_rule_type', 'quality_rules')
    op.drop_table('quality_rules')

    op.drop_index('idx_lineage_template_types', 'lineage_templates')
    op.drop_table('lineage_templates')

    op.drop_index('idx_metric_enabled', 'metric_dictionary')
    op.drop_index('idx_metric_type', 'metric_dictionary')
    op.drop_table('metric_dictionary')
