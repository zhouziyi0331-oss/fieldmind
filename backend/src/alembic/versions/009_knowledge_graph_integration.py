"""009_knowledge_graph_integration

整合9步骤管道与知识图谱可视化系统

Revision ID: 009_knowledge_graph_integration
Revises: 008_unified_pipeline
Create Date: 2024-01-XX 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '009_knowledge_graph_integration'
down_revision = '008_unified_pipeline'
branch_labels = None
depends_on = None


def upgrade():
    """创建知识图谱表结构"""

    # 1. 知识图谱节点表（从9步骤的实体生成）
    op.create_table(
        'kg_nodes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('node_id', sa.String(255), unique=True, nullable=False, comment='节点唯一ID'),
        sa.Column('name', sa.String(500), nullable=False, comment='节点名称'),
        sa.Column('type', sa.String(100), nullable=False, comment='节点类型'),

        # 核心属性
        sa.Column('description', sa.Text(), nullable=True, comment='节点描述'),
        sa.Column('importance_score', sa.Float(), default=0.0, comment='重要性分数 0-1'),
        sa.Column('is_core', sa.Boolean(), default=False, comment='是否核心节点'),

        # 消歧属性
        sa.Column('actions', sa.JSON(), nullable=True, comment='做的事情列表'),
        sa.Column('context_summary', sa.Text(), nullable=True, comment='上下文摘要'),
        sa.Column('timeline', sa.JSON(), nullable=True, comment='时间线事件'),

        # 来源追踪（连接到统一管道）
        sa.Column('dirty_doc_id', sa.Integer(), nullable=True, comment='关联的脏数据文档ID'),
        sa.Column('clean_event_ids', sa.JSON(), nullable=True, comment='关联的干净事件ID列表'),
        sa.Column('pipeline_step', sa.Integer(), nullable=True, comment='来自管道第几步'),

        # 文化属性
        sa.Column('region', sa.String(200), nullable=True, comment='地域'),
        sa.Column('category', sa.String(200), nullable=True, comment='分类'),

        # 向量嵌入
        sa.Column('embedding', sa.JSON(), nullable=True, comment='向量嵌入'),

        # 可视化坐标
        sa.Column('x', sa.Float(), nullable=True, comment='可视化X坐标'),
        sa.Column('y', sa.Float(), nullable=True, comment='可视化Y坐标'),
        sa.Column('layer', sa.Integer(), default=1, comment='层级：1核心 2次要 3细节'),

        # 元数据
        sa.Column('confidence', sa.Float(), default=1.0, comment='置信度'),
        sa.Column('verified', sa.Boolean(), default=False, comment='是否人工确认'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.Index('idx_kg_nodes_type', 'type'),
        sa.Index('idx_kg_nodes_dirty_doc_id', 'dirty_doc_id'),
        sa.Index('idx_kg_nodes_is_core', 'is_core'),
        sa.ForeignKeyConstraint(['dirty_doc_id'], ['dirty_channel_documents.id'], ondelete='CASCADE')
    )

    # 2. 知识图谱边表（从9步骤的关系生成）
    op.create_table(
        'kg_edges',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('edge_id', sa.String(255), unique=True, nullable=False, comment='边唯一ID'),
        sa.Column('source_node_id', sa.String(255), nullable=False, comment='源节点ID'),
        sa.Column('target_node_id', sa.String(255), nullable=False, comment='目标节点ID'),
        sa.Column('relation_type', sa.String(200), nullable=False, comment='关系类型'),

        # 关系属性
        sa.Column('description', sa.Text(), nullable=True, comment='关系描述'),
        sa.Column('weight', sa.Float(), default=1.0, comment='关系权重'),
        sa.Column('confidence', sa.Float(), default=1.0, comment='置信度'),

        # 时间属性
        sa.Column('start_time', sa.DateTime(), nullable=True, comment='关系开始时间'),
        sa.Column('end_time', sa.DateTime(), nullable=True, comment='关系结束时间'),

        # 来源追踪
        sa.Column('dirty_doc_id', sa.Integer(), nullable=True, comment='关联的脏数据文档ID'),
        sa.Column('clean_relation_id', sa.Integer(), nullable=True, comment='关联的干净关系ID'),
        sa.Column('pipeline_step', sa.Integer(), nullable=True, comment='来自管道第几步'),
        sa.Column('evidence', sa.JSON(), nullable=True, comment='证据文本列表'),

        # 元数据
        sa.Column('verified', sa.Boolean(), default=False, comment='是否人工确认'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.Index('idx_kg_edges_source', 'source_node_id'),
        sa.Index('idx_kg_edges_target', 'target_node_id'),
        sa.Index('idx_kg_edges_type', 'relation_type'),
        sa.Index('idx_kg_edges_dirty_doc', 'dirty_doc_id'),
        sa.ForeignKeyConstraint(['dirty_doc_id'], ['dirty_channel_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['clean_relation_id'], ['clean_channel_relations.id'], ondelete='SET NULL')
    )

    # 3. 知识图谱快照表（用于版本管理和可视化）
    op.create_table(
        'kg_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('snapshot_id', sa.String(255), unique=True, nullable=False, comment='快照ID'),
        sa.Column('name', sa.String(500), nullable=False, comment='快照名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='快照描述'),

        # 范围
        sa.Column('dirty_doc_ids', sa.JSON(), nullable=True, comment='包含的脏数据文档ID列表'),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='关联的项目ID'),

        # 统计信息
        sa.Column('total_nodes', sa.Integer(), default=0, comment='节点总数'),
        sa.Column('total_edges', sa.Integer(), default=0, comment='边总数'),
        sa.Column('core_nodes', sa.Integer(), default=0, comment='核心节点数'),
        sa.Column('node_type_stats', sa.JSON(), nullable=True, comment='节点类型统计'),
        sa.Column('edge_type_stats', sa.JSON(), nullable=True, comment='边类型统计'),

        # 可视化布局
        sa.Column('layout_algorithm', sa.String(100), nullable=True, comment='布局算法'),
        sa.Column('layout_data', sa.JSON(), nullable=True, comment='布局数据'),

        # 元数据
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建者ID'),

        sa.Index('idx_kg_snapshots_project', 'project_id')
    )

    # 4. 9步骤到图谱的映射配置表
    op.create_table(
        'pipeline_to_graph_mapping',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pipeline_step', sa.Integer(), nullable=False, comment='管道步骤 1-9'),
        sa.Column('output_type', sa.String(100), nullable=False, comment='输出类型：entity/relation/event'),
        sa.Column('graph_element', sa.String(100), nullable=False, comment='图谱元素：node/edge'),

        # 映射规则
        sa.Column('mapping_rules', sa.JSON(), nullable=False, comment='映射规则JSON'),
        sa.Column('transform_function', sa.String(200), nullable=True, comment='转换函数名'),

        # 配置
        sa.Column('enabled', sa.Boolean(), default=True, comment='是否启用'),
        sa.Column('priority', sa.Integer(), default=0, comment='优先级'),

        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.Index('idx_mapping_step', 'pipeline_step'),
        sa.Index('idx_mapping_enabled', 'enabled')
    )

    # 5. 图谱构建任务表
    op.create_table(
        'kg_build_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.String(255), unique=True, nullable=False, comment='任务ID'),
        sa.Column('dirty_doc_id', sa.Integer(), nullable=False, comment='源文档ID'),
        sa.Column('route_id', sa.Integer(), nullable=True, comment='路由ID'),

        # 任务状态
        sa.Column('status', sa.String(50), nullable=False, comment='状态：pending/building/completed/failed'),
        sa.Column('current_step', sa.String(100), nullable=True, comment='当前步骤'),
        sa.Column('progress', sa.Float(), default=0.0, comment='进度 0-1'),

        # 结果
        sa.Column('nodes_created', sa.Integer(), default=0, comment='创建的节点数'),
        sa.Column('edges_created', sa.Integer(), default=0, comment='创建的边数'),
        sa.Column('snapshot_id', sa.String(255), nullable=True, comment='生成的快照ID'),

        # 错误信息
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),

        # 时间戳
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        sa.Index('idx_kg_build_status', 'status'),
        sa.Index('idx_kg_build_dirty_doc', 'dirty_doc_id'),
        sa.ForeignKeyConstraint(['dirty_doc_id'], ['dirty_channel_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['unified_processing_routes.id'], ondelete='SET NULL')
    )


def downgrade():
    """删除知识图谱表"""
    op.drop_table('kg_build_tasks')
    op.drop_table('pipeline_to_graph_mapping')
    op.drop_table('kg_snapshots')
    op.drop_table('kg_edges')
    op.drop_table('kg_nodes')
