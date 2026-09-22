"""Initial migration: create all tables

Revision ID: 001
Revises:
Create Date: 2026-07-31 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有数据表"""

    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('email', sa.String(200), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # 创建 projects 表
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_index('ix_projects_name', 'projects', ['name'])

    # 创建 project_documents 表
    op.create_table(
        'project_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_project_documents_project_id', 'project_documents', ['project_id'])

    # 创建 project_contexts 表
    op.create_table(
        'project_contexts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('context_id', sa.String(36), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
    )

    # 创建 project_chat_sessions 表
    op.create_table(
        'project_chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
    )

    # 创建 project_chat_messages 表
    op.create_table(
        'project_chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('message_id', sa.String(36), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
    )

    # 创建 project_memories 表
    op.create_table(
        'project_memories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 创建 documents 表
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_format', sa.String(50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('process_status', sa.String(50), nullable=False),
        sa.Column('process_error', sa.Text(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('embeddings_generated', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_documents_title', 'documents', ['title'])
    op.create_index('ix_documents_doc_type', 'documents', ['doc_type'])
    op.create_index('ix_documents_status', 'documents', ['process_status'])

    # 创建 entities 表
    op.create_table(
        'entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_ids', sa.JSON(), nullable=True),
        sa.Column('first_mentioned_doc', sa.String(36), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('mention_count', sa.Integer(), default=1),
        sa.Column('neo4j_node_id', sa.String(100), nullable=True),
        sa.Column('related_entities', sa.JSON(), nullable=True),
        sa.Column('vector_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_entity_name', 'entities', ['name'])
    op.create_index('idx_entity_type', 'entities', ['entity_type'])

    # 创建 contexts 表
    op.create_table(
        'contexts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_main', sa.Boolean(), default=False),
        sa.Column('parent_context_id', sa.String(36), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('timeline', sa.JSON(), nullable=True),
        sa.Column('graph_data', sa.JSON(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('entity_count', sa.Integer(), default=0),
        sa.Column('document_count', sa.Integer(), default=0),
        sa.Column('event_count', sa.Integer(), default=0),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_findings', sa.JSON(), nullable=True),
        sa.Column('visualization_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
    )

    # 创建 chat_sessions 表
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
    )

    # 创建 chat_messages 表
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])

    # 创建 skills 表
    op.create_table(
        'skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skill_type', sa.String(50), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('examples', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('success_rate', sa.Float(), default=0.0),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_skills_name', 'skills', ['name'])
    op.create_index('ix_skills_type', 'skills', ['skill_type'])

    # 创建 skill_validations 表
    op.create_table(
        'skill_validations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('skill_id', sa.String(36), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=True),
        sa.Column('actual_output', sa.Text(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 创建 timeline_events 表
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('document_ids', sa.JSON(), nullable=True),
        sa.Column('location', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_timeline_events_date', 'timeline_events', ['date'])
    op.create_index('ix_timeline_events_category', 'timeline_events', ['category'])

    # 创建 analysis_reports 表
    op.create_table(
        'analysis_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('report_type', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('source_documents', sa.JSON(), nullable=True),
        sa.Column('generated_by', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_analysis_reports_type', 'analysis_reports', ['report_type'])
    op.create_index('ix_analysis_reports_status', 'analysis_reports', ['status'])

    # 创建 reports 表
    op.create_table(
        'reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('report_type', sa.String(100), nullable=False),
        sa.Column('source_ids', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # 创建 industry_categories 表
    op.create_table(
        'industry_categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('category_id', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_count', sa.Integer(), default=0, nullable=False),
        sa.Column('entity_count', sa.Integer(), default=0, nullable=False),
        sa.Column('overview', sa.JSON(), nullable=True),
        sa.Column('detailed_analysis', sa.JSON(), nullable=True),
        sa.Column('statistics', sa.JSON(), nullable=True),
        sa.Column('trends', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_analyzed', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_industry_categories_category_id', 'industry_categories', ['category_id'])


def downgrade() -> None:
    """删除所有数据表"""

    op.drop_table('industry_categories')
    op.drop_table('reports')
    op.drop_table('analysis_reports')
    op.drop_table('timeline_events')
    op.drop_table('skill_validations')
    op.drop_table('skills')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('contexts')
    op.drop_table('entities')
    op.drop_table('documents')
    op.drop_table('project_memories')
    op.drop_table('project_chat_messages')
    op.drop_table('project_chat_sessions')
    op.drop_table('project_contexts')
    op.drop_table('project_documents')
    op.drop_table('projects')
    op.drop_table('users')
