"""add data governance tables - safe version

Revision ID: 004_data_governance_safe
Revises: a2c76df802bf
Create Date: 2026-08-20 23:50:00.000000

数据治理系统完整表结构 - 安全版本（检查表是否存在）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from datetime import datetime

# revision identifiers
revision = '004_data_governance_safe'
down_revision = 'a2c76df802bf'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检查表是否存在"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """检查列是否存在"""
    if not table_exists(table_name):
        return False
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """创建数据治理系统所需的所有表和字段"""

    # ===== 1. 创建 metric_dictionary 表 =====
    if not table_exists('metric_dictionary'):
        op.create_table(
            'metric_dictionary',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('metric_name', sa.String(100), nullable=False),
            sa.Column('metric_type', sa.String(50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('calculation_method', sa.Text(), nullable=True),
            sa.Column('unit', sa.String(50), nullable=True),
            sa.Column('threshold_low', sa.Float(), nullable=True),
            sa.Column('threshold_high', sa.Float(), nullable=True),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_metric_name', 'metric_dictionary', ['metric_name'], unique=True)
        op.create_index('idx_metric_type', 'metric_dictionary', ['metric_type'])
        print("✅ 创建 metric_dictionary 表")

    # ===== 2. 创建 lineage_templates 表 =====
    if not table_exists('lineage_templates'):
        op.create_table(
            'lineage_templates',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('template_name', sa.String(100), nullable=False),
            sa.Column('source_type', sa.String(50), nullable=False),
            sa.Column('target_type', sa.String(50), nullable=False),
            sa.Column('transform_pattern', sa.Text(), nullable=True),
            sa.Column('field_mappings', sa.JSON(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_template_name', 'lineage_templates', ['template_name'], unique=True)
        op.create_index('idx_lineage_template_types', 'lineage_templates', ['source_type', 'target_type'])
        print("✅ 创建 lineage_templates 表")

    # ===== 3. 创建 lineage_edges 表 =====
    if not table_exists('lineage_edges'):
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
        print("✅ 创建 lineage_edges 表")

    # ===== 4. 创建 quality_rules 表 =====
    if not table_exists('quality_rules'):
        op.create_table(
            'quality_rules',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('rule_name', sa.String(100), nullable=False),
            sa.Column('rule_type', sa.String(50), nullable=False),
            sa.Column('target_entity', sa.String(50), nullable=False),
            sa.Column('validation_logic', sa.JSON(), nullable=False),
            sa.Column('severity', sa.String(20), default='medium'),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_rule_name', 'quality_rules', ['rule_name'], unique=True)
        op.create_index('idx_quality_rule_type', 'quality_rules', ['rule_type'])
        op.create_index('idx_quality_target_entity', 'quality_rules', ['target_entity'])
        print("✅ 创建 quality_rules 表")

    # ===== 5. 创建 quality_check_results 表 =====
    if not table_exists('quality_check_results'):
        op.create_table(
            'quality_check_results',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('rule_id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(50), nullable=False),
            sa.Column('entity_id', sa.String(100), nullable=False),
            sa.Column('check_result', sa.String(20), nullable=False),
            sa.Column('result_details', sa.JSON(), nullable=True),
            sa.Column('checked_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_qc_rule', 'quality_check_results', ['rule_id'])
        op.create_index('idx_qc_entity', 'quality_check_results', ['entity_type', 'entity_id'])
        op.create_index('idx_qc_result', 'quality_check_results', ['check_result'])
        print("✅ 创建 quality_check_results 表")

    # ===== 6. 创建 change_events 表 =====
    if not table_exists('change_events'):
        op.create_table(
            'change_events',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('entity_type', sa.String(50), nullable=False),
            sa.Column('entity_id', sa.String(100), nullable=False),
            sa.Column('change_type', sa.String(50), nullable=False),
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
        print("✅ 创建 change_events 表")

    # ===== 7. 创建 metric_calculation_history 表 =====
    if not table_exists('metric_calculation_history'):
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
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_metric_history_entity', 'metric_calculation_history', ['entity_type', 'entity_id'])
        op.create_index('idx_metric_history_metric', 'metric_calculation_history', ['metric_id'])
        op.create_index('idx_metric_history_calculated', 'metric_calculation_history', ['calculated_at'])
        print("✅ 创建 metric_calculation_history 表")

    # ===== 8. files 表新增字段 =====
    # 检查可能的表名
    files_table = None
    for name in ['files', 'documents', 'project_documents']:
        if table_exists(name):
            files_table = name
            break

    if files_table:
        new_columns = [
            ('source_system', sa.String(100)),
            ('business_owner', sa.String(100)),
            ('data_classification', sa.String(20)),
            ('retention_period', sa.Integer()),
            ('last_accessed_at', sa.DateTime()),
            ('access_count', sa.Integer()),
            ('quality_score', sa.Float()),
            ('processing_status', sa.String(20)),
            ('error_message', sa.Text()),
            ('retry_count', sa.Integer()),
            ('metadata_version', sa.String(20)),
            ('governance_tags', sa.JSON())
        ]

        for col_name, col_type in new_columns:
            if not column_exists(files_table, col_name):
                op.add_column(files_table, sa.Column(col_name, col_type, nullable=True))
                print(f"✅ 添加列 {files_table}.{col_name}")

    # ===== 9. chunks 表新增字段 =====
    chunks_table = None
    for name in ['chunks', 'document_chunks']:
        if table_exists(name):
            chunks_table = name
            break

    if chunks_table:
        new_columns = [
            ('semantic_density', sa.Float()),
            ('coherence_score', sa.Float()),
            ('information_gain', sa.Float()),
            ('topic_relevance', sa.Float()),
            ('readability_score', sa.Float()),
            ('entity_count', sa.Integer()),
            ('keyword_count', sa.Integer()),
            ('avg_sentence_length', sa.Float()),
            ('lexical_diversity', sa.Float()),
            ('sentiment_score', sa.Float()),
            ('complexity_score', sa.Float()),
            ('parent_chunk_id', sa.String(50)),
            ('chunk_level', sa.Integer()),
            ('overlap_with_prev', sa.Integer()),
            ('overlap_with_next', sa.Integer())
        ]

        for col_name, col_type in new_columns:
            if not column_exists(chunks_table, col_name):
                op.add_column(chunks_table, sa.Column(col_name, col_type, nullable=True))
                print(f"✅ 添加列 {chunks_table}.{col_name}")

    print("\n✅✅✅ 数据治理系统表结构创建完成！")


def downgrade():
    """回滚数据治理系统的所有更改"""

    # 删除新增字段
    if table_exists('document_chunks'):
        chunk_columns = ['semantic_density', 'coherence_score', 'information_gain',
                        'topic_relevance', 'readability_score', 'entity_count',
                        'keyword_count', 'avg_sentence_length', 'lexical_diversity',
                        'sentiment_score', 'complexity_score', 'parent_chunk_id',
                        'chunk_level', 'overlap_with_prev', 'overlap_with_next']
        for col in chunk_columns:
            if column_exists('document_chunks', col):
                op.drop_column('document_chunks', col)

    # 删除表
    tables_to_drop = [
        'metric_calculation_history',
        'change_events',
        'quality_check_results',
        'quality_rules',
        'lineage_edges',
        'lineage_templates',
        'metric_dictionary'
    ]

    for table in tables_to_drop:
        if table_exists(table):
            op.drop_table(table)
            print(f"✅ 删除表 {table}")
