"""unified dirty-clean pipeline schema

Revision ID: 008_unified_pipeline
Revises: 007_add_pipeline_execution_tracking
Create Date: 2024-01-15 10:00:00.000000

统一脏数据/干净数据通道的数据库结构
- 脏数据通道: 完整性优先，所有多模态内容转为完整文档
- 干净数据通道: 精准提取，1-3个核心事件+核心实体+核心关系
- 串联关系: dirty → clean
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import JSON

revision = '008_unified_pipeline'
down_revision = '007_pipeline_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # ==================== 脏数据通道表 ====================
    # 存储完整的、无损的文档转换结果
    op.create_table(
        'dirty_channel_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('project_documents.id'), nullable=False, index=True),
        sa.Column('source_type', sa.String(50), nullable=False, comment='audio/video/image/document'),
        sa.Column('full_text', sa.Text(), nullable=False, comment='完整的无损文本，可能8500字'),
        sa.Column('metadata', JSON(), comment='原始元数据：时长、分辨率、场景数等'),
        sa.Column('completeness_score', sa.Float(), comment='完整性评分 0-1'),
        sa.Column('word_count', sa.Integer(), comment='总字数'),
        sa.Column('processing_time', sa.Float(), comment='处理耗时（秒）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='脏数据通道：完整性优先，无损转换所有多模态内容为文档'
    )

    # ==================== 干净数据通道表 ====================
    # 核心事件表（只存储1-3个最核心的事件）
    op.create_table(
        'clean_channel_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dirty_doc_id', sa.Integer(), sa.ForeignKey('dirty_channel_documents.id'), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False, comment='会议/决策/讨论/计划等'),
        sa.Column('event_summary', sa.String(500), nullable=False, comment='事件摘要，200字以内'),

        # 5W1H 最小化节点
        sa.Column('who', JSON(), comment='核心人物列表'),
        sa.Column('what', sa.Text(), nullable=False, comment='核心事情'),
        sa.Column('when', sa.DateTime(), comment='时间'),
        sa.Column('where', sa.String(200), comment='地点'),
        sa.Column('why', sa.Text(), comment='原因/目的'),
        sa.Column('how', sa.Text(), comment='方式/过程'),

        sa.Column('importance_score', sa.Float(), comment='重要性评分 0-1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='干净数据通道：精准提取1-3个核心事件'
    )

    # 核心实体表（从核心事件中提取的核心实体）
    op.create_table(
        'clean_channel_entities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dirty_doc_id', sa.Integer(), sa.ForeignKey('dirty_channel_documents.id'), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False, comment='PERSON/LOCATION/ORGANIZATION/EVENT'),
        sa.Column('entity_name', sa.String(200), nullable=False),
        sa.Column('attributes', JSON(), comment='实体属性'),
        sa.Column('mention_count', sa.Integer(), default=1, comment='在原文中的提及次数'),
        sa.Column('importance_score', sa.Float(), comment='重要性评分'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='干净数据通道：核心实体（人、地点、组织）'
    )

    # 核心关系表（实体与事件之间的关系）
    op.create_table(
        'clean_channel_relations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dirty_doc_id', sa.Integer(), sa.ForeignKey('dirty_channel_documents.id'), nullable=False, index=True),
        sa.Column('source_entity_id', sa.Integer(), sa.ForeignKey('clean_channel_entities.id')),
        sa.Column('target_entity_id', sa.Integer(), sa.ForeignKey('clean_channel_entities.id')),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('clean_channel_events.id')),
        sa.Column('relation_type', sa.String(100), nullable=False, comment='参与/决策/负责/影响等'),
        sa.Column('relation_details', sa.Text(), comment='关系描述'),
        sa.Column('confidence', sa.Float(), comment='置信度 0-1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        comment='干净数据通道：核心关系'
    )

    # ==================== 9步骤知识管道集成表 ====================
    # 记录每个文档在9步骤中的处理状态
    op.create_table(
        'nine_step_pipeline_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dirty_doc_id', sa.Integer(), sa.ForeignKey('dirty_channel_documents.id'), nullable=False, unique=True),

        # 9个步骤的状态
        sa.Column('step1_text_cleaning', sa.String(20), default='pending', comment='文本校刊'),
        sa.Column('step2_structure_analysis', sa.String(20), default='pending', comment='结构分析'),
        sa.Column('step3_entity_building', sa.String(20), default='pending', comment='实体构建'),
        sa.Column('step4_event_extraction', sa.String(20), default='pending', comment='事件提取'),
        sa.Column('step5_relation_discovery', sa.String(20), default='pending', comment='关系发现'),
        sa.Column('step6_ontology_building', sa.String(20), default='pending', comment='本体构建'),
        sa.Column('step7_logic_inference', sa.String(20), default='pending', comment='逻辑推理'),
        sa.Column('step8_knowledge_unitization', sa.String(20), default='pending', comment='知识单元化'),
        sa.Column('step9_reader_generation', sa.String(20), default='pending', comment='阅读器生成'),

        sa.Column('current_step', sa.Integer(), default=0, comment='当前执行到第几步'),
        sa.Column('overall_status', sa.String(20), default='pending', comment='pending/processing/completed/failed'),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='9步骤知识管道的执行状态追踪'
    )

    # ==================== 统一处理路由表 ====================
    # 记录每个文档的完整处理流程
    op.create_table(
        'unified_processing_routes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('project_documents.id'), nullable=False, unique=True),

        # 脏数据通道状态
        sa.Column('dirty_channel_status', sa.String(20), default='pending', comment='pending/processing/completed/failed'),
        sa.Column('dirty_doc_id', sa.Integer(), sa.ForeignKey('dirty_channel_documents.id')),
        sa.Column('dirty_started_at', sa.DateTime()),
        sa.Column('dirty_completed_at', sa.DateTime()),

        # 干净数据通道状态
        sa.Column('clean_channel_status', sa.String(20), default='pending'),
        sa.Column('clean_events_count', sa.Integer(), default=0, comment='提取的核心事件数'),
        sa.Column('clean_entities_count', sa.Integer(), default=0, comment='提取的核心实体数'),
        sa.Column('clean_relations_count', sa.Integer(), default=0, comment='提取的核心关系数'),
        sa.Column('clean_started_at', sa.DateTime()),
        sa.Column('clean_completed_at', sa.DateTime()),

        # 9步骤管道状态
        sa.Column('nine_step_status', sa.String(20), default='pending'),
        sa.Column('nine_step_current_step', sa.Integer(), default=0),

        # 整体状态
        sa.Column('overall_status', sa.String(20), default='pending'),
        sa.Column('processing_route', JSON(), comment='完整的处理路径记录'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='统一处理路由：记录文档从脏通道→干净通道→9步骤的完整流程'
    )

    # 创建索引
    op.create_index('idx_dirty_doc_source_type', 'dirty_channel_documents', ['source_type'])
    op.create_index('idx_clean_events_type', 'clean_channel_events', ['event_type'])
    op.create_index('idx_clean_entities_type', 'clean_channel_entities', ['entity_type', 'entity_name'])
    op.create_index('idx_clean_relations_type', 'clean_channel_relations', ['relation_type'])
    op.create_index('idx_nine_step_status', 'nine_step_pipeline_status', ['overall_status', 'current_step'])
    op.create_index('idx_unified_route_status', 'unified_processing_routes', ['overall_status'])


def downgrade():
    op.drop_table('unified_processing_routes')
    op.drop_table('nine_step_pipeline_status')
    op.drop_table('clean_channel_relations')
    op.drop_table('clean_channel_entities')
    op.drop_table('clean_channel_events')
    op.drop_table('dirty_channel_documents')
