"""添加定时任务表

Revision ID: 004_scheduled_tasks
Revises: 003_batch_operations
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_scheduled_tasks'
down_revision = '003_batch_operations'
branch_labels = None
depends_on = None


def upgrade():
    # 创建scheduled_tasks表
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index(op.f('ix_scheduled_tasks_id'), 'scheduled_tasks', ['id'])
    op.create_index(op.f('ix_scheduled_tasks_task_id'), 'scheduled_tasks', ['task_id'], unique=True)
    op.create_index(op.f('ix_scheduled_tasks_project_id'), 'scheduled_tasks', ['project_id'])
    op.create_index(op.f('ix_scheduled_tasks_task_type'), 'scheduled_tasks', ['task_type'])
    op.create_index(op.f('ix_scheduled_tasks_is_active'), 'scheduled_tasks', ['is_active'])
    op.create_index(op.f('ix_scheduled_tasks_next_run_at'), 'scheduled_tasks', ['next_run_at'])

    # 创建scheduled_task_executions表
    op.create_table(
        'scheduled_task_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='running'),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['scheduled_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建执行记录索引
    op.create_index(op.f('ix_scheduled_task_executions_id'), 'scheduled_task_executions', ['id'])
    op.create_index(op.f('ix_scheduled_task_executions_task_id'), 'scheduled_task_executions', ['task_id'])
    op.create_index(op.f('ix_scheduled_task_executions_status'), 'scheduled_task_executions', ['status'])
    op.create_index(op.f('ix_scheduled_task_executions_started_at'), 'scheduled_task_executions', ['started_at'])


def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_scheduled_task_executions_started_at'), table_name='scheduled_task_executions')
    op.drop_index(op.f('ix_scheduled_task_executions_status'), table_name='scheduled_task_executions')
    op.drop_index(op.f('ix_scheduled_task_executions_task_id'), table_name='scheduled_task_executions')
    op.drop_index(op.f('ix_scheduled_task_executions_id'), table_name='scheduled_task_executions')

    # 删除表
    op.drop_table('scheduled_task_executions')

    # 删除scheduled_tasks索引
    op.drop_index(op.f('ix_scheduled_tasks_next_run_at'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_is_active'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_task_type'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_project_id'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_task_id'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_id'), table_name='scheduled_tasks')

    # 删除scheduled_tasks表
    op.drop_table('scheduled_tasks')
