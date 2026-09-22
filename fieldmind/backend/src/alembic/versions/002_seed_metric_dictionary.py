"""seed metric dictionary with 20+ predefined metrics

Revision ID: 002_seed_metrics
Revises: 001_data_governance
Create Date: 2026-08-20 23:35:00.000000

预置20+个文本量化指标到 metric_dictionary 表
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '002_seed_metrics'
down_revision = '001_data_governance'
branch_labels = None
depends_on = None


def upgrade():
    """插入预置指标"""

    # 获取连接
    conn = op.get_bind()

    # 预置指标数据
    metrics = [
        # === BASIC 类型指标（基础统计） ===
        {
            'metric_name': 'word_count',
            'metric_type': 'basic',
            'description': '文本中的词数（中文按字符数，英文按空格分隔）',
            'calculation_method': 'len(text.split()) for English, len(text) for Chinese',
            'unit': 'words',
            'threshold_low': 10.0,
            'threshold_high': 10000.0,
            'enabled': True
        },
        {
            'metric_name': 'char_count',
            'metric_type': 'basic',
            'description': '文本中的字符总数（包括空格和标点）',
            'calculation_method': 'len(text)',
            'unit': 'characters',
            'threshold_low': 50.0,
            'threshold_high': 50000.0,
            'enabled': True
        },
        {
            'metric_name': 'sentence_count',
            'metric_type': 'basic',
            'description': '文本中的句子数量',
            'calculation_method': 'count sentences by punctuation marks (。！？.!?)',
            'unit': 'sentences',
            'threshold_low': 1.0,
            'threshold_high': 1000.0,
            'enabled': True
        },
        {
            'metric_name': 'paragraph_count',
            'metric_type': 'basic',
            'description': '文本中的段落数量',
            'calculation_method': 'count by double newlines (\\n\\n)',
            'unit': 'paragraphs',
            'threshold_low': 1.0,
            'threshold_high': 500.0,
            'enabled': True
        },
        {
            'metric_name': 'line_count',
            'metric_type': 'basic',
            'description': '文本中的行数',
            'calculation_method': 'text.count("\\n") + 1',
            'unit': 'lines',
            'threshold_low': 1.0,
            'threshold_high': 5000.0,
            'enabled': True
        },
        {
            'metric_name': 'token_count',
            'metric_type': 'basic',
            'description': 'LLM Token数量（用于估算成本）',
            'calculation_method': 'tiktoken encoding',
            'unit': 'tokens',
            'threshold_low': 10.0,
            'threshold_high': 100000.0,
            'enabled': True
        },

        # === SEMANTIC 类型指标（语义质量） ===
        {
            'metric_name': 'semantic_density',
            'metric_type': 'semantic',
            'description': '语义密度：单位文本中的信息量（实体+关键词密度）',
            'calculation_method': '(entity_count + keyword_count) / word_count',
            'unit': 'ratio',
            'threshold_low': 0.05,
            'threshold_high': 0.30,
            'enabled': True
        },
        {
            'metric_name': 'topic_coherence',
            'metric_type': 'semantic',
            'description': '主题连贯性：文本主题的一致性得分',
            'calculation_method': 'cosine_similarity(sentence_embeddings)',
            'unit': 'score',
            'threshold_low': 0.5,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'information_gain',
            'metric_type': 'semantic',
            'description': '信息增益：相比上下文chunk的新信息量',
            'calculation_method': '1 - cosine_similarity(current_embedding, context_embedding)',
            'unit': 'score',
            'threshold_low': 0.2,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'topic_relevance',
            'metric_type': 'semantic',
            'description': '主题相关性：与文档主题的相关度',
            'calculation_method': 'cosine_similarity(chunk_embedding, document_topic_embedding)',
            'unit': 'score',
            'threshold_low': 0.5,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'semantic_uniqueness',
            'metric_type': 'semantic',
            'description': '语义唯一性：与其他chunk的差异度',
            'calculation_method': '1 - max(cosine_similarity(current, all_others))',
            'unit': 'score',
            'threshold_low': 0.3,
            'threshold_high': 1.0,
            'enabled': True
        },

        # === QUALITY 类型指标（质量评估） ===
        {
            'metric_name': 'readability_score',
            'metric_type': 'quality',
            'description': '可读性得分（Flesch Reading Ease或类似算法）',
            'calculation_method': '206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)',
            'unit': 'score',
            'threshold_low': 30.0,
            'threshold_high': 100.0,
            'enabled': True
        },
        {
            'metric_name': 'grammar_score',
            'metric_type': 'quality',
            'description': '语法正确性得分（通过语言模型评估）',
            'calculation_method': 'grammar_checker.check(text)',
            'unit': 'score',
            'threshold_low': 0.7,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'completeness_score',
            'metric_type': 'quality',
            'description': '完整性得分：chunk是否完整（不截断句子）',
            'calculation_method': 'check if starts and ends with complete sentences',
            'unit': 'score',
            'threshold_low': 0.8,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'clarity_score',
            'metric_type': 'quality',
            'description': '清晰度得分：表达是否清晰明确',
            'calculation_method': 'LLM-based assessment or lexical clarity metrics',
            'unit': 'score',
            'threshold_low': 0.6,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'noise_ratio',
            'metric_type': 'quality',
            'description': '噪音比例：无意义内容占比（重复字符、乱码等）',
            'calculation_method': '(repeated_chars + garbled_text) / total_chars',
            'unit': 'ratio',
            'threshold_low': 0.0,
            'threshold_high': 0.1,
            'enabled': True
        },

        # === COMPLEXITY 类型指标（复杂度） ===
        {
            'metric_name': 'avg_sentence_length',
            'metric_type': 'complexity',
            'description': '平均句长（词数）',
            'calculation_method': 'word_count / sentence_count',
            'unit': 'words',
            'threshold_low': 5.0,
            'threshold_high': 30.0,
            'enabled': True
        },
        {
            'metric_name': 'lexical_diversity',
            'metric_type': 'complexity',
            'description': '词汇多样性（Type-Token Ratio）',
            'calculation_method': 'unique_words / total_words',
            'unit': 'ratio',
            'threshold_low': 0.3,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'nested_depth',
            'metric_type': 'complexity',
            'description': '嵌套深度（句子结构复杂度）',
            'calculation_method': 'max_depth of dependency parse tree',
            'unit': 'levels',
            'threshold_low': 1.0,
            'threshold_high': 10.0,
            'enabled': True
        },
        {
            'metric_name': 'technical_term_density',
            'metric_type': 'complexity',
            'description': '专业术语密度',
            'calculation_method': 'technical_terms_count / total_words',
            'unit': 'ratio',
            'threshold_low': 0.0,
            'threshold_high': 0.5,
            'enabled': True
        },
        {
            'metric_name': 'cognitive_load',
            'metric_type': 'complexity',
            'description': '认知负荷：综合难度评估',
            'calculation_method': 'weighted_sum(sentence_length, lexical_diversity, technical_density)',
            'unit': 'score',
            'threshold_low': 0.0,
            'threshold_high': 10.0,
            'enabled': True
        },

        # === 额外指标 ===
        {
            'metric_name': 'entity_density',
            'metric_type': 'semantic',
            'description': '实体密度：命名实体数量/总词数',
            'calculation_method': 'entity_count / word_count',
            'unit': 'ratio',
            'threshold_low': 0.01,
            'threshold_high': 0.20,
            'enabled': True
        },
        {
            'metric_name': 'keyword_density',
            'metric_type': 'semantic',
            'description': '关键词密度：关键词数量/总词数',
            'calculation_method': 'keyword_count / word_count',
            'unit': 'ratio',
            'threshold_low': 0.02,
            'threshold_high': 0.15,
            'enabled': True
        },
        {
            'metric_name': 'sentiment_score',
            'metric_type': 'semantic',
            'description': '情感得分：-1(负面) 到 +1(正面)',
            'calculation_method': 'sentiment_analyzer.polarity_scores(text)',
            'unit': 'score',
            'threshold_low': -1.0,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'formality_score',
            'metric_type': 'quality',
            'description': '正式程度：0(口语化) 到 1(正式)',
            'calculation_method': 'formality_classifier.predict(text)',
            'unit': 'score',
            'threshold_low': 0.0,
            'threshold_high': 1.0,
            'enabled': True
        },
        {
            'metric_name': 'abbreviation_density',
            'metric_type': 'complexity',
            'description': '缩写密度：缩写词占比',
            'calculation_method': 'abbreviation_count / word_count',
            'unit': 'ratio',
            'threshold_low': 0.0,
            'threshold_high': 0.3,
            'enabled': True
        }
    ]

    # 批量插入
    for metric in metrics:
        metric['created_at'] = datetime.utcnow()
        metric['updated_at'] = datetime.utcnow()

    # 使用 bulk insert
    op.bulk_insert(
        sa.table('metric_dictionary',
            sa.column('metric_name', sa.String),
            sa.column('metric_type', sa.String),
            sa.column('description', sa.Text),
            sa.column('calculation_method', sa.Text),
            sa.column('unit', sa.String),
            sa.column('threshold_low', sa.Float),
            sa.column('threshold_high', sa.Float),
            sa.column('enabled', sa.Boolean),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime)
        ),
        metrics
    )

    print(f"✅ 成功预置 {len(metrics)} 个指标到 metric_dictionary 表")


def downgrade():
    """删除预置指标"""
    conn = op.get_bind()

    # 删除所有预置指标
    metric_names = [
        'word_count', 'char_count', 'sentence_count', 'paragraph_count', 'line_count', 'token_count',
        'semantic_density', 'topic_coherence', 'information_gain', 'topic_relevance', 'semantic_uniqueness',
        'readability_score', 'grammar_score', 'completeness_score', 'clarity_score', 'noise_ratio',
        'avg_sentence_length', 'lexical_diversity', 'nested_depth', 'technical_term_density', 'cognitive_load',
        'entity_density', 'keyword_density', 'sentiment_score', 'formality_score', 'abbreviation_density'
    ]

    for metric_name in metric_names:
        conn.execute(
            sa.text(f"DELETE FROM metric_dictionary WHERE metric_name = :name"),
            {'name': metric_name}
        )

    print(f"✅ 成功删除 {len(metric_names)} 个预置指标")
