"""add_performance_indexes_week1

Revision ID: 93e53fe4e26e
Revises: 6e100f21029c
Create Date: 2026-08-18 12:49:43.377235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93e53fe4e26e'
down_revision: Union[str, None] = '6e100f21029c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add performance indexes."""

    # 1. Projects 表索引
    # 优化：按用户查询项目并按时间排序
    op.create_index(
        'idx_projects_user_id_created_at',
        'projects',
        ['user_id', 'created_at'],
        unique=False
    )

    # 2. Documents 表索引
    # 优化：按项目和状态筛选文档
    op.create_index(
        'idx_documents_project_id_status',
        'documents',
        ['project_id', 'status'],
        unique=False
    )

    # 优化：按时间排序
    op.create_index(
        'idx_documents_created_at',
        'documents',
        ['created_at'],
        unique=False
    )

    # 3. Chunks 表索引
    # 优化：按文档查询分块
    op.create_index(
        'idx_chunks_document_id',
        'chunks',
        ['document_id'],
        unique=False
    )

    # 4. Entities 表索引
    # 优化：按名称搜索（支持前缀匹配）
    op.create_index(
        'idx_entities_name',
        'entities',
        ['name'],
        unique=False
    )

    # 优化：按类型和项目筛选
    op.create_index(
        'idx_entities_type_project_id',
        'entities',
        ['type', 'project_id'],
        unique=False
    )

    # 5. Project Chat Messages 表索引
    # 优化：按会话查询消息历史
    op.create_index(
        'idx_project_chat_messages_session_created',
        'project_chat_messages',
        ['session_id', 'created_at'],
        unique=False
    )

    # 6. Timeline Events 表索引
    # 优化：按项目和时间查询事件
    op.create_index(
        'idx_timeline_events_project_timestamp',
        'timeline_events',
        ['project_id', 'timestamp'],
        unique=False
    )

    # 7. Skills 表索引
    # 优化：按类别筛选技能
    op.create_index(
        'idx_skills_category',
        'skills',
        ['category'],
        unique=False
    )

    # 8. Workflow Executions 表索引
    # 优化：按工作流和状态查询执行记录
    op.create_index(
        'idx_workflow_executions_workflow_status',
        'workflow_executions',
        ['workflow_id', 'status'],
        unique=False
    )

    # 优化：按时间范围查询
    op.create_index(
        'idx_workflow_executions_started_at',
        'workflow_executions',
        ['started_at'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - Remove performance indexes."""

    # 删除索引（反向操作）
    op.drop_index('idx_workflow_executions_started_at', table_name='workflow_executions')
    op.drop_index('idx_workflow_executions_workflow_status', table_name='workflow_executions')
    op.drop_index('idx_skills_category', table_name='skills')
    op.drop_index('idx_timeline_events_project_timestamp', table_name='timeline_events')
    op.drop_index('idx_project_chat_messages_session_created', table_name='project_chat_messages')
    op.drop_index('idx_entities_type_project_id', table_name='entities')
    op.drop_index('idx_entities_name', table_name='entities')
    op.drop_index('idx_chunks_document_id', table_name='chunks')
    op.drop_index('idx_documents_created_at', table_name='documents')
    op.drop_index('idx_documents_project_id_status', table_name='documents')
    op.drop_index('idx_projects_user_id_created_at', table_name='projects')
