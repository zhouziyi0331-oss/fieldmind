"""
数据库性能优化迁移
添加时间戳索引和复合索引
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """添加性能优化索引"""

    # 1. ProjectDocument 时间戳索引
    op.create_index(
        'ix_project_documents_created_at',
        'project_documents',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'ix_project_documents_processed_at',
        'project_documents',
        ['processed_at'],
        unique=False
    )

    # 2. Document 时间戳索引
    op.create_index(
        'ix_documents_uploaded_at',
        'documents',
        ['uploaded_at'],
        unique=False
    )
    op.create_index(
        'ix_documents_processed_at',
        'documents',
        ['processed_at'],
        unique=False
    )

    # 3. ChatSession 时间戳索引
    op.create_index(
        'ix_chat_sessions_created_at',
        'chat_sessions',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'ix_chat_sessions_last_message_at',
        'chat_sessions',
        ['last_message_at'],
        unique=False
    )

    # 4. ChatMessage 时间戳索引
    op.create_index(
        'ix_chat_messages_created_at',
        'chat_messages',
        ['created_at'],
        unique=False
    )

    # 5. 复合索引：ProjectDocument(project_id, status) - 优化高频组合查询
    op.create_index(
        'ix_project_documents_project_id_status',
        'project_documents',
        ['project_id', 'status'],
        unique=False
    )

    # 6. 复合索引：ProjectDocument(project_id, processed_at) - 优化时间范围查询
    op.create_index(
        'ix_project_documents_project_id_processed_at',
        'project_documents',
        ['project_id', 'processed_at'],
        unique=False
    )


def downgrade():
    """移除性能优化索引"""

    # 移除复合索引
    op.drop_index('ix_project_documents_project_id_processed_at', table_name='project_documents')
    op.drop_index('ix_project_documents_project_id_status', table_name='project_documents')

    # 移除时间戳索引
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_sessions_last_message_at', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_created_at', table_name='chat_sessions')
    op.drop_index('ix_documents_processed_at', table_name='documents')
    op.drop_index('ix_documents_uploaded_at', table_name='documents')
    op.drop_index('ix_project_documents_processed_at', table_name='project_documents')
    op.drop_index('ix_project_documents_created_at', table_name='project_documents')
