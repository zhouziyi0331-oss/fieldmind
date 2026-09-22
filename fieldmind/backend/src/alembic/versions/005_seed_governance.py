"""seed data governance predefined data

Revision ID: 005_seed_governance
Revises: 004_data_governance_safe
Create Date: 2026-08-20 23:55:00.000000

预置指标字典、血缘模板和质量规则
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json

revision = '005_seed_governance'
down_revision = '004_data_governance_safe'
branch_labels = None
depends_on = None


def upgrade():
    """插入预置数据"""
    conn = op.get_bind()

    # ===== 1. 预置指标字典 (26个指标) =====
    metrics = [
        # BASIC 类型
        ('word_count', 'basic', '文本中的词数', 'len(text.split())', 'words', 10.0, 10000.0),
        ('char_count', 'basic', '字符总数', 'len(text)', 'characters', 50.0, 50000.0),
        ('sentence_count', 'basic', '句子数量', 'count by punctuation', 'sentences', 1.0, 1000.0),
        ('paragraph_count', 'basic', '段落数量', 'count by double newlines', 'paragraphs', 1.0, 500.0),
        ('line_count', 'basic', '行数', 'text.count("\\n")+1', 'lines', 1.0, 5000.0),
        ('token_count', 'basic', 'LLM Token数量', 'tiktoken encoding', 'tokens', 10.0, 100000.0),

        # SEMANTIC 类型
        ('semantic_density', 'semantic', '语义密度', '(entity+keyword)/words', 'ratio', 0.05, 0.30),
        ('topic_coherence', 'semantic', '主题连贯性', 'cosine_similarity(embeddings)', 'score', 0.5, 1.0),
        ('information_gain', 'semantic', '信息增益', '1-similarity(context)', 'score', 0.2, 1.0),
        ('topic_relevance', 'semantic', '主题相关性', 'similarity(document_topic)', 'score', 0.5, 1.0),
        ('semantic_uniqueness', 'semantic', '语义唯一性', '1-max(similarity)', 'score', 0.3, 1.0),
        ('entity_density', 'semantic', '实体密度', 'entities/words', 'ratio', 0.01, 0.20),
        ('keyword_density', 'semantic', '关键词密度', 'keywords/words', 'ratio', 0.02, 0.15),
        ('sentiment_score', 'semantic', '情感得分', 'sentiment_analyzer', 'score', -1.0, 1.0),

        # QUALITY 类型
        ('readability_score', 'quality', '可读性得分', 'Flesch Reading Ease', 'score', 30.0, 100.0),
        ('grammar_score', 'quality', '语法正确性', 'grammar_checker', 'score', 0.7, 1.0),
        ('completeness_score', 'quality', '完整性得分', 'sentence boundary check', 'score', 0.8, 1.0),
        ('clarity_score', 'quality', '清晰度得分', 'LLM assessment', 'score', 0.6, 1.0),
        ('noise_ratio', 'quality', '噪音比例', 'garbled/total', 'ratio', 0.0, 0.1),
        ('formality_score', 'quality', '正式程度', 'formality_classifier', 'score', 0.0, 1.0),

        # COMPLEXITY 类型
        ('avg_sentence_length', 'complexity', '平均句长', 'words/sentences', 'words', 5.0, 30.0),
        ('lexical_diversity', 'complexity', '词汇多样性', 'unique/total words', 'ratio', 0.3, 1.0),
        ('nested_depth', 'complexity', '嵌套深度', 'dependency parse depth', 'levels', 1.0, 10.0),
        ('technical_term_density', 'complexity', '专业术语密度', 'technical_terms/words', 'ratio', 0.0, 0.5),
        ('cognitive_load', 'complexity', '认知负荷', 'weighted complexity', 'score', 0.0, 10.0),
        ('abbreviation_density', 'complexity', '缩写密度', 'abbreviations/words', 'ratio', 0.0, 0.3),
    ]

    for metric in metrics:
        conn.execute(
            sa.text("""
                INSERT INTO metric_dictionary
                (metric_name, metric_type, description, calculation_method, unit, threshold_low, threshold_high, enabled, created_at, updated_at)
                VALUES (:name, :type, :desc, :calc, :unit, :low, :high, 1, :now, :now)
            """),
            {
                'name': metric[0], 'type': metric[1], 'desc': metric[2],
                'calc': metric[3], 'unit': metric[4], 'low': metric[5],
                'high': metric[6], 'now': datetime.utcnow()
            }
        )

    print(f"✅ 成功预置 {len(metrics)} 个指标")

    # ===== 2. 预置血缘模板 (6个模板) =====
    templates = [
        ('file_to_chunk', 'file', 'chunk', 'extract',
         json.dumps({'source': ['id', 'content'], 'target': ['document_id', 'text']}),
         '文件切分为chunk的标准模板'),

        ('chunk_to_embedding', 'chunk', 'embedding', 'model',
         json.dumps({'source': ['id', 'text'], 'target': ['entity_id', 'vector']}),
         'Chunk向量化的标准模板'),

        ('chunk_to_entity', 'chunk', 'entity', 'extract',
         json.dumps({'source': ['text'], 'target': ['text', 'type']}),
         'Chunk实体提取的标准模板'),

        ('chunk_to_metric', 'chunk', 'metric', 'derive',
         json.dumps({'source': ['text', 'metadata'], 'target': ['metric_value']}),
         'Chunk指标计算的标准模板'),

        ('chunks_to_report', 'chunk', 'report', 'aggregate',
         json.dumps({'source': ['multiple'], 'target': ['summary', 'insights']}),
         '多个Chunk聚合生成报告的标准模板'),

        ('file_to_metadata', 'file', 'metadata', 'extract',
         json.dumps({'source': ['file_path'], 'target': ['metadata']}),
         '文件元数据提取的标准模板'),
    ]

    for tpl in templates:
        conn.execute(
            sa.text("""
                INSERT INTO lineage_templates
                (template_name, source_type, target_type, transform_pattern, field_mappings, description, enabled, created_at, updated_at)
                VALUES (:name, :src, :tgt, :pattern, :mappings, :desc, 1, :now, :now)
            """),
            {
                'name': tpl[0], 'src': tpl[1], 'tgt': tpl[2],
                'pattern': tpl[3], 'mappings': tpl[4], 'desc': tpl[5],
                'now': datetime.utcnow()
            }
        )

    print(f"✅ 成功预置 {len(templates)} 个血缘模板")

    # ===== 3. 预置质量规则 (15个规则) =====
    rules = [
        # Completeness
        ('file_required_fields', 'completeness', 'file',
         json.dumps({'required': ['id', 'name', 'file_path', 'mime_type']}),
         'critical', '文件必填字段检查'),

        ('chunk_required_fields', 'completeness', 'chunk',
         json.dumps({'required': ['id', 'document_id', 'text']}),
         'critical', 'Chunk必填字段检查'),

        ('chunk_min_length', 'completeness', 'chunk',
         json.dumps({'field': 'text', 'min_length': 10}),
         'medium', 'Chunk最小长度检查'),

        # Accuracy
        ('metric_value_range', 'accuracy', 'metric',
         json.dumps({'field': 'metric_value', 'check': 'threshold'}),
         'high', '指标值范围检查'),

        ('confidence_range', 'accuracy', 'all',
         json.dumps({'field': 'confidence', 'min': 0.0, 'max': 1.0}),
         'medium', '置信度范围检查'),

        ('quality_score_range', 'accuracy', 'file',
         json.dumps({'field': 'quality_score', 'min': 0.0, 'max': 100.0}),
         'medium', '质量得分范围检查'),

        # Consistency
        ('chunk_document_reference', 'consistency', 'chunk',
         json.dumps({'field': 'document_id', 'reference': 'files.id'}),
         'critical', 'Chunk文档引用一致性'),

        ('lineage_entities_exist', 'consistency', 'lineage',
         json.dumps({'check': 'both_exist'}),
         'high', '血缘关系实体存在性检查'),

        ('parent_chunk_exists', 'consistency', 'chunk',
         json.dumps({'field': 'parent_chunk_id', 'allow_null': True}),
         'medium', '父chunk引用检查'),

        # Timeliness
        ('file_access_tracking', 'timeliness', 'file',
         json.dumps({'field': 'last_accessed_at', 'max_days': 365}),
         'low', '文件访问时效性检查'),

        ('future_timestamp_check', 'timeliness', 'all',
         json.dumps({'fields': ['created_at', 'updated_at'], 'not_future': True}),
         'critical', '时间戳不能在未来'),

        # Uniqueness
        ('file_hash_unique', 'uniqueness', 'file',
         json.dumps({'field': 'hash', 'unique': True}),
         'high', '文件哈希唯一性检查'),

        ('chunk_index_unique', 'uniqueness', 'chunk',
         json.dumps({'fields': ['document_id', 'chunk_index'], 'composite_unique': True}),
         'critical', 'Chunk索引唯一性检查'),

        # Business rules
        ('high_quality_threshold', 'accuracy', 'file',
         json.dumps({'field': 'quality_score', 'min': 70.0}),
         'low', '高质量文件阈值'),

        ('semantic_density_threshold', 'accuracy', 'chunk',
         json.dumps({'field': 'semantic_density', 'min': 0.05, 'max': 0.30}),
         'low', '语义密度阈值检查'),
    ]

    for rule in rules:
        conn.execute(
            sa.text("""
                INSERT INTO quality_rules
                (rule_name, rule_type, target_entity, validation_logic, severity, description, enabled, created_at, updated_at)
                VALUES (:name, :type, :entity, :logic, :severity, :desc, 1, :now, :now)
            """),
            {
                'name': rule[0], 'type': rule[1], 'entity': rule[2],
                'logic': rule[3], 'severity': rule[4], 'desc': rule[5],
                'now': datetime.utcnow()
            }
        )

    print(f"✅ 成功预置 {len(rules)} 个质量规则")
    print("\n✅✅✅ 数据治理预置数据创建完成！")


def downgrade():
    """删除预置数据"""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM quality_rules"))
    conn.execute(sa.text("DELETE FROM lineage_templates"))
    conn.execute(sa.text("DELETE FROM metric_dictionary"))
    print("✅ 删除所有预置数据")
