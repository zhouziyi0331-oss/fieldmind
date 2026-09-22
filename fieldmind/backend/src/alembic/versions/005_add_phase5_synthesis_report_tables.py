"""Add Phase 5 synthesis and report tables for verifiable data flow

Revision ID: 005
Revises: 004
Create Date: 2026-08-14 00:00:00.000000

这个迁移文件实现了Phase 5的核心需求：
1. 数据流真实性 - 每一步都有数据库存储
2. 可验证性 - 每一步都可以独立查询
3. 可分析性 - 可以追溯数据来源和处理链路
4. SynthesisAgent与ReportAgent的强关联 - 通过外键和参数传递

核心表：
- synthesis_results: SynthesisAgent的决策数据（关键洞察、决策因素、应用的Skills等）
- report_analysis_cache: 15个分析服务的结果缓存
- report_layers: 三层报告内容（每层10000字，不同理论框架）

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_phase5_tables'
down_revision: Union[str, None] = ('004_scheduled_tasks', '002_add_thinking_patterns_and_knowledge')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建Phase 5的三个核心数据表"""

    # 1. synthesis_results 表 - SynthesisAgent的决策数据
    op.create_table(
        'synthesis_results',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('query', sa.Text(), nullable=True, comment='综合分析的查询问题'),

        # 决策数据 - 这些是SynthesisAgent的核心输出
        sa.Column('key_insights', sa.JSON(), nullable=True,
                  comment='关键洞察列表，每个包含insight、confidence、source'),
        sa.Column('decision_factors', sa.JSON(), nullable=True,
                  comment='决策因素列表，每个包含factor、weight、rationale'),
        sa.Column('recommendations', sa.JSON(), nullable=True,
                  comment='具体建议列表，每个包含action、priority、expected_impact'),

        # Phase 4 集成 - 外部知识
        sa.Column('thinking_patterns', sa.JSON(), nullable=True,
                  comment='应用的思维模式（费孝通、SOP等）'),
        sa.Column('skill_knowledge', sa.JSON(), nullable=True,
                  comment='从Skills知识库获取的知识'),
        sa.Column('domain_knowledge', sa.JSON(), nullable=True,
                  comment='领域知识集成结果'),

        # Skills使用记录
        sa.Column('applied_skills', sa.JSON(), nullable=True,
                  comment='自动调用的Skills列表及其结果'),

        # 数据来源追溯
        sa.Column('memory_fragments', sa.JSON(), nullable=True,
                  comment='使用的记忆片段ID列表'),
        sa.Column('knowledge_nodes', sa.JSON(), nullable=True,
                  comment='使用的知识图谱节点ID列表'),
        sa.Column('citations', sa.JSON(), nullable=True,
                  comment='引用的文档片段列表'),

        # 元数据
        sa.Column('context_summary', sa.Text(), nullable=True,
                  comment='综合上下文的简要总结'),
        sa.Column('confidence_score', sa.Float(), nullable=True,
                  comment='整体置信度评分 0-1'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True,
                  comment='处理耗时（毫秒）'),
        sa.Column('strategy_used', sa.String(100), nullable=True,
                  comment='使用的综合策略'),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # 索引
    op.create_index('ix_synthesis_results_project_id', 'synthesis_results', ['project_id'])
    op.create_index('ix_synthesis_results_created_at', 'synthesis_results', ['created_at'])
    op.create_index('ix_synthesis_results_confidence', 'synthesis_results', ['confidence_score'])


    # 2. report_analysis_cache 表 - 15个分析服务的结果缓存
    op.create_table(
        'report_analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('analysis_type', sa.String(100), nullable=False,
                  comment='分析类型：sentiment/theme/entity/relation/timeline/category/summary/keyword/anomaly/trend/comparison/impact/risk/opportunity/recommendation'),

        # 分析结果数据
        sa.Column('result_data', sa.JSON(), nullable=False,
                  comment='分析结果的JSON数据'),
        sa.Column('metadata', sa.JSON(), nullable=True,
                  comment='分析元数据（如模型版本、参数等）'),

        # 数据来源
        sa.Column('source_chunks', sa.JSON(), nullable=True,
                  comment='使用的chunk ID列表'),
        sa.Column('source_documents', sa.JSON(), nullable=True,
                  comment='使用的document ID列表'),

        # 质量指标
        sa.Column('confidence_score', sa.Float(), nullable=True,
                  comment='分析置信度 0-1'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True,
                  comment='处理耗时（毫秒）'),

        # 缓存控制
        sa.Column('is_valid', sa.Boolean(), nullable=False, default=True,
                  comment='缓存是否有效'),
        sa.Column('invalidated_at', sa.DateTime(), nullable=True,
                  comment='缓存失效时间'),
        sa.Column('invalidation_reason', sa.String(200), nullable=True,
                  comment='失效原因'),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # 索引
    op.create_index('ix_report_analysis_cache_project_id', 'report_analysis_cache', ['project_id'])
    op.create_index('ix_report_analysis_cache_type', 'report_analysis_cache', ['analysis_type'])
    op.create_index('ix_report_analysis_cache_project_type', 'report_analysis_cache',
                   ['project_id', 'analysis_type'], unique=True)
    op.create_index('ix_report_analysis_cache_valid', 'report_analysis_cache', ['is_valid'])


    # 3. report_layers 表 - 三层报告内容
    op.create_table(
        'report_layers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('layer_number', sa.Integer(), nullable=False,
                  comment='报告层级：1=数据驱动层, 2=理论框架层, 3=商业洞察层'),

        # 报告内容
        sa.Column('content', sa.Text(), nullable=False,
                  comment='报告正文内容（目标10000字）'),
        sa.Column('word_count', sa.Integer(), nullable=False,
                  comment='实际字数'),
        sa.Column('title', sa.String(500), nullable=True,
                  comment='报告标题'),
        sa.Column('abstract', sa.Text(), nullable=True,
                  comment='报告摘要'),

        # 数据来源追溯
        sa.Column('data_sources', sa.JSON(), nullable=True,
                  comment='使用的数据来源（analysis_cache IDs, synthesis_result_id等）'),
        sa.Column('analysis_types_used', sa.JSON(), nullable=True,
                  comment='使用的15个分析服务列表'),

        # Skills使用
        sa.Column('skills_used', sa.JSON(), nullable=True,
                  comment='使用的Skills列表及其贡献'),
        sa.Column('theoretical_frameworks', sa.JSON(), nullable=True,
                  comment='应用的理论框架（费孝通、SOP等）'),

        # 与SynthesisAgent的强关联
        sa.Column('synthesis_result_id', sa.Integer(), nullable=True,
                  comment='关联的synthesis_results记录ID（Layer 3必须有）'),

        # 质量指标
        sa.Column('quality_score', sa.Float(), nullable=True,
                  comment='报告质量评分 0-1'),
        sa.Column('coherence_score', sa.Float(), nullable=True,
                  comment='连贯性评分 0-1'),
        sa.Column('insight_depth_score', sa.Float(), nullable=True,
                  comment='洞察深度评分 0-1'),

        # 元数据
        sa.Column('generation_strategy', sa.String(100), nullable=True,
                  comment='生成策略'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True,
                  comment='生成耗时（毫秒）'),
        sa.Column('model_used', sa.String(100), nullable=True,
                  comment='使用的LLM模型'),

        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['synthesis_result_id'], ['synthesis_results.id'], ondelete='SET NULL'),
        sa.CheckConstraint('layer_number IN (1, 2, 3)', name='check_layer_number_valid'),
        sa.CheckConstraint('word_count >= 0', name='check_word_count_positive'),
    )

    # 索引
    op.create_index('ix_report_layers_project_id', 'report_layers', ['project_id'])
    op.create_index('ix_report_layers_layer_number', 'report_layers', ['layer_number'])
    op.create_index('ix_report_layers_project_layer', 'report_layers',
                   ['project_id', 'layer_number'], unique=True)
    op.create_index('ix_report_layers_synthesis_id', 'report_layers', ['synthesis_result_id'])
    op.create_index('ix_report_layers_created_at', 'report_layers', ['created_at'])


def downgrade() -> None:
    """删除Phase 5的三个核心数据表"""

    # 删除顺序：先删除有外键依赖的表
    op.drop_table('report_layers')
    op.drop_table('report_analysis_cache')
    op.drop_table('synthesis_results')
