"""seed lineage templates and quality rules

Revision ID: 003_seed_governance_data
Revises: 002_seed_metrics
Create Date: 2026-08-20 23:40:00.000000

预置血缘模板和质量规则
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json

# revision identifiers
revision = '003_seed_governance_data'
down_revision = '002_seed_metrics'
branch_labels = None
depends_on = None


def upgrade():
    """插入预置血缘模板和质量规则"""

    # ===== 1. 预置血缘模板 =====
    lineage_templates = [
        {
            'template_name': 'file_to_chunk',
            'source_type': 'file',
            'target_type': 'chunk',
            'transform_pattern': 'extract',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'name', 'content', 'metadata'],
                'target_fields': ['document_id', 'text', 'metadata'],
                'mappings': [
                    {'from': 'id', 'to': 'document_id'},
                    {'from': 'content', 'to': 'text', 'transform': 'chunk_split'}
                ]
            }),
            'description': '文件切分为chunk的标准模板',
            'enabled': True
        },
        {
            'template_name': 'chunk_to_embedding',
            'source_type': 'chunk',
            'target_type': 'embedding',
            'transform_pattern': 'model',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'text'],
                'target_fields': ['entity_id', 'vector'],
                'mappings': [
                    {'from': 'id', 'to': 'entity_id'},
                    {'from': 'text', 'to': 'vector', 'transform': 'embedding_model'}
                ]
            }),
            'description': 'Chunk向量化的标准模板',
            'enabled': True
        },
        {
            'template_name': 'chunk_to_entity',
            'source_type': 'chunk',
            'target_type': 'entity',
            'transform_pattern': 'extract',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'text'],
                'target_fields': ['text', 'type'],
                'mappings': [
                    {'from': 'text', 'to': 'text', 'transform': 'ner_extraction'}
                ]
            }),
            'description': 'Chunk实体提取的标准模板',
            'enabled': True
        },
        {
            'template_name': 'chunk_to_metric',
            'source_type': 'chunk',
            'target_type': 'metric',
            'transform_pattern': 'derive',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'text', 'metadata'],
                'target_fields': ['entity_id', 'metric_value'],
                'mappings': [
                    {'from': 'text', 'to': 'metric_value', 'transform': 'metric_calculation'}
                ]
            }),
            'description': 'Chunk指标计算的标准模板',
            'enabled': True
        },
        {
            'template_name': 'chunks_to_report',
            'source_type': 'chunk',
            'target_type': 'report',
            'transform_pattern': 'aggregate',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'text', 'metadata', 'metrics'],
                'target_fields': ['content', 'summary', 'insights'],
                'mappings': [
                    {'from': 'multiple_chunks', 'to': 'summary', 'transform': 'llm_summarization'},
                    {'from': 'metrics', 'to': 'insights', 'transform': 'aggregation'}
                ]
            }),
            'description': '多个Chunk聚合生成报告的标准模板',
            'enabled': True
        },
        {
            'template_name': 'file_to_metadata',
            'source_type': 'file',
            'target_type': 'metadata',
            'transform_pattern': 'extract',
            'field_mappings': json.dumps({
                'source_fields': ['id', 'file_path', 'mime_type'],
                'target_fields': ['document_id', 'metadata_type', 'metadata'],
                'mappings': [
                    {'from': 'file_path', 'to': 'metadata', 'transform': 'metadata_extraction'}
                ]
            }),
            'description': '文件元数据提取的标准模板',
            'enabled': True
        }
    ]

    for template in lineage_templates:
        template['created_at'] = datetime.utcnow()
        template['updated_at'] = datetime.utcnow()

    op.bulk_insert(
        sa.table('lineage_templates',
            sa.column('template_name', sa.String),
            sa.column('source_type', sa.String),
            sa.column('target_type', sa.String),
            sa.column('transform_pattern', sa.Text),
            sa.column('field_mappings', sa.JSON),
            sa.column('description', sa.Text),
            sa.column('enabled', sa.Boolean),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime)
        ),
        lineage_templates
    )

    print(f"✅ 成功预置 {len(lineage_templates)} 个血缘模板")

    # ===== 2. 预置质量规则 =====
    quality_rules = [
        # === Completeness 规则 ===
        {
            'rule_name': 'file_required_fields',
            'rule_type': 'completeness',
            'target_entity': 'file',
            'validation_logic': json.dumps({
                'required_fields': ['id', 'name', 'file_path', 'mime_type', 'created_at'],
                'validation': 'all_fields_not_null'
            }),
            'severity': 'critical',
            'enabled': True,
            'description': '文件必填字段完整性检查'
        },
        {
            'rule_name': 'chunk_required_fields',
            'rule_type': 'completeness',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'required_fields': ['id', 'document_id', 'text', 'chunk_index'],
                'validation': 'all_fields_not_null'
            }),
            'severity': 'critical',
            'enabled': True,
            'description': 'Chunk必填字段完整性检查'
        },
        {
            'rule_name': 'chunk_min_length',
            'rule_type': 'completeness',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'field': 'text',
                'validation': 'min_length',
                'threshold': 10
            }),
            'severity': 'medium',
            'enabled': True,
            'description': 'Chunk文本最小长度检查（至少10个字符）'
        },

        # === Accuracy 规则 ===
        {
            'rule_name': 'metric_value_range',
            'rule_type': 'accuracy',
            'target_entity': 'metric',
            'validation_logic': json.dumps({
                'field': 'metric_value',
                'validation': 'within_threshold',
                'reference_table': 'metric_dictionary',
                'reference_fields': ['threshold_low', 'threshold_high']
            }),
            'severity': 'high',
            'enabled': True,
            'description': '指标值应在定义的阈值范围内'
        },
        {
            'rule_name': 'confidence_score_range',
            'rule_type': 'accuracy',
            'target_entity': 'all',
            'validation_logic': json.dumps({
                'field': 'confidence',
                'validation': 'range',
                'min': 0.0,
                'max': 1.0
            }),
            'severity': 'medium',
            'enabled': True,
            'description': '置信度得分必须在0-1之间'
        },
        {
            'rule_name': 'quality_score_range',
            'rule_type': 'accuracy',
            'target_entity': 'file',
            'validation_logic': json.dumps({
                'field': 'quality_score',
                'validation': 'range',
                'min': 0.0,
                'max': 100.0
            }),
            'severity': 'medium',
            'enabled': True,
            'description': '质量得分必须在0-100之间'
        },

        # === Consistency 规则 ===
        {
            'rule_name': 'chunk_document_reference',
            'rule_type': 'consistency',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'field': 'document_id',
                'validation': 'foreign_key_exists',
                'reference_table': 'files',
                'reference_field': 'id'
            }),
            'severity': 'critical',
            'enabled': True,
            'description': 'Chunk的document_id必须存在于files表中'
        },
        {
            'rule_name': 'lineage_source_target_exist',
            'rule_type': 'consistency',
            'target_entity': 'lineage',
            'validation_logic': json.dumps({
                'validation': 'both_entities_exist',
                'source_check': True,
                'target_check': True
            }),
            'severity': 'high',
            'enabled': True,
            'description': '血缘关系的源和目标实体都必须存在'
        },
        {
            'rule_name': 'parent_chunk_exists',
            'rule_type': 'consistency',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'field': 'parent_chunk_id',
                'validation': 'self_reference_exists',
                'allow_null': True
            }),
            'severity': 'medium',
            'enabled': True,
            'description': '父chunk_id（如果存在）必须引用有效的chunk'
        },

        # === Timeliness 规则 ===
        {
            'rule_name': 'file_access_tracking',
            'rule_type': 'timeliness',
            'target_entity': 'file',
            'validation_logic': json.dumps({
                'field': 'last_accessed_at',
                'validation': 'not_too_old',
                'max_days': 365
            }),
            'severity': 'low',
            'enabled': True,
            'description': '文件超过365天未访问应标记（用于归档决策）'
        },
        {
            'rule_name': 'future_timestamp_check',
            'rule_type': 'timeliness',
            'target_entity': 'all',
            'validation_logic': json.dumps({
                'fields': ['created_at', 'updated_at', 'calculated_at'],
                'validation': 'not_future',
            }),
            'severity': 'critical',
            'enabled': True,
            'description': '时间戳不能在未来'
        },

        # === Uniqueness 规则 ===
        {
            'rule_name': 'file_hash_unique',
            'rule_type': 'uniqueness',
            'target_entity': 'file',
            'validation_logic': json.dumps({
                'field': 'hash',
                'validation': 'unique_across_table',
                'allow_null': False
            }),
            'severity': 'high',
            'enabled': True,
            'description': '文件哈希值必须唯一（防重复上传）'
        },
        {
            'rule_name': 'chunk_index_unique_per_document',
            'rule_type': 'uniqueness',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'fields': ['document_id', 'chunk_index'],
                'validation': 'composite_unique'
            }),
            'severity': 'critical',
            'enabled': True,
            'description': '同一文档内chunk_index必须唯一'
        },

        # === 自定义业务规则 ===
        {
            'rule_name': 'high_quality_file_threshold',
            'rule_type': 'accuracy',
            'target_entity': 'file',
            'validation_logic': json.dumps({
                'field': 'quality_score',
                'validation': 'threshold',
                'min': 70.0,
                'action': 'warn_if_below'
            }),
            'severity': 'low',
            'enabled': True,
            'description': '文件质量得分低于70应警告'
        },
        {
            'rule_name': 'chunk_semantic_density_threshold',
            'rule_type': 'accuracy',
            'target_entity': 'chunk',
            'validation_logic': json.dumps({
                'field': 'semantic_density',
                'validation': 'threshold',
                'min': 0.05,
                'max': 0.30,
                'action': 'warn_if_outside'
            }),
            'severity': 'low',
            'enabled': True,
            'description': 'Chunk语义密度应在0.05-0.30之间'
        }
    ]

    for rule in quality_rules:
        rule['created_at'] = datetime.utcnow()
        rule['updated_at'] = datetime.utcnow()

    op.bulk_insert(
        sa.table('quality_rules',
            sa.column('rule_name', sa.String),
            sa.column('rule_type', sa.String),
            sa.column('target_entity', sa.String),
            sa.column('validation_logic', sa.JSON),
            sa.column('severity', sa.String),
            sa.column('enabled', sa.Boolean),
            sa.column('description', sa.Text),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime)
        ),
        quality_rules
    )

    print(f"✅ 成功预置 {len(quality_rules)} 个质量规则")


def downgrade():
    """删除预置数据"""
    conn = op.get_bind()

    # 删除质量规则
    conn.execute(sa.text("DELETE FROM quality_rules"))
    print("✅ 删除所有预置质量规则")

    # 删除血缘模板
    conn.execute(sa.text("DELETE FROM lineage_templates"))
    print("✅ 删除所有预置血缘模板")
