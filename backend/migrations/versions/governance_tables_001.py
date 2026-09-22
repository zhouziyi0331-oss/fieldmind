"""
添加治理框架数据库表

包含：
- 版本控制表
- 回滚历史表
- 故障记录表
- 健康检查表
- 配置管理表
- 合规检查表
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'governance_tables_001'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    """创建治理框架表"""

    # ==================== 版本控制表 ====================
    op.create_table(
        'versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('version_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('version_type', sa.String(32), nullable=False, index=True),
        sa.Column('resource_id', sa.String(128), nullable=False, index=True),
        sa.Column('resource_name', sa.String(256)),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('parent_version_id', sa.String(64)),
        sa.Column('content', postgresql.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('diff_from_parent', postgresql.JSON()),
        sa.Column('status', sa.String(32), default='active'),
        sa.Column('project_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSON()),
        sa.Column('tags', postgresql.JSON()),
        sa.Column('description', sa.Text())
    )

    # 版本控制索引
    op.create_index('idx_version_resource', 'versions', ['resource_id', 'version_number'])
    op.create_index('idx_version_project', 'versions', ['project_id', 'version_type'])
    op.create_index('idx_version_status', 'versions', ['status', 'version_type'])

    # 回滚历史表
    op.create_table(
        'rollback_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('rollback_id', sa.String(64), unique=True, nullable=False),
        sa.Column('from_version_id', sa.String(64), nullable=False),
        sa.Column('to_version_id', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(128), nullable=False),
        sa.Column('resource_type', sa.String(32), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('rollback_by', sa.Integer(), nullable=False),
        sa.Column('rollback_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('affected_resources', postgresql.JSON()),
        sa.Column('rollback_result', postgresql.JSON()),
        sa.Column('project_id', sa.Integer(), nullable=False)
    )

    op.create_index('idx_rollback_resource', 'rollback_history', ['resource_id', 'rollback_at'])

    # ==================== 故障恢复表 ====================
    op.create_table(
        'failure_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('failure_id', sa.String(64), unique=True, nullable=False),
        sa.Column('service_name', sa.String(128), nullable=False, index=True),
        sa.Column('operation', sa.String(128), nullable=False),
        sa.Column('failure_type', sa.String(32), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('stack_trace', sa.Text()),
        sa.Column('occurred_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('recovery_attempts', sa.Integer(), default=0),
        sa.Column('recovery_strategy', sa.String(64)),
        sa.Column('recovery_result', postgresql.JSON()),
        sa.Column('project_id', sa.Integer(), index=True),
        sa.Column('user_id', sa.Integer()),
        sa.Column('context', postgresql.JSON()),
        sa.Column('metadata', postgresql.JSON())
    )

    # 健康检查日志表
    op.create_table(
        'health_check_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('check_id', sa.String(64), unique=True, nullable=False),
        sa.Column('service_name', sa.String(128), nullable=False, index=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('response_time_ms', sa.Float()),
        sa.Column('error_message', sa.Text()),
        sa.Column('checked_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('details', postgresql.JSON())
    )

    # ==================== 配置管理表 ====================
    op.create_table(
        'configurations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('config_id', sa.String(128), unique=True, nullable=False, index=True),
        sa.Column('key', sa.String(128), nullable=False, index=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('encrypted_value', sa.Text()),
        sa.Column('config_type', sa.String(32), nullable=False),
        sa.Column('config_scope', sa.String(32), nullable=False, index=True),
        sa.Column('scope_id', sa.String(64)),
        sa.Column('description', sa.Text()),
        sa.Column('default_value', sa.Text()),
        sa.Column('is_secret', sa.Boolean(), default=False),
        sa.Column('is_readonly', sa.Boolean(), default=False),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('validation_rules', postgresql.JSON()),
        sa.Column('metadata', postgresql.JSON()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.Integer()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('version', sa.Integer(), default=1)
    )

    op.create_index('idx_config_scope_key', 'configurations', ['config_scope', 'scope_id', 'key'])

    # 配置变更历史表
    op.create_table(
        'configuration_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('config_id', sa.String(128), nullable=False, index=True),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('change_reason', sa.Text()),
        sa.Column('metadata', postgresql.JSON())
    )

    # ==================== 合规检查表 ====================
    op.create_table(
        'compliance_checks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('check_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('compliance_type', sa.String(32), nullable=False, index=True),
        sa.Column('check_name', sa.String(128), nullable=False),
        sa.Column('check_description', sa.Text()),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('violations_count', sa.Integer(), default=0),
        sa.Column('checked_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('checked_by', sa.Integer()),
        sa.Column('project_id', sa.Integer(), index=True),
        sa.Column('resource_type', sa.String(64)),
        sa.Column('resource_id', sa.String(128)),
        sa.Column('details', postgresql.JSON()),
        sa.Column('metadata', postgresql.JSON())
    )

    op.create_index('idx_compliance_project', 'compliance_checks', ['project_id', 'compliance_type'])

    # 合规违规表
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('violation_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('check_id', sa.String(64), nullable=False, index=True),
        sa.Column('compliance_type', sa.String(32), nullable=False),
        sa.Column('rule_name', sa.String(128), nullable=False),
        sa.Column('rule_description', sa.Text()),
        sa.Column('severity', sa.String(32), nullable=False, index=True),
        sa.Column('violation_message', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('project_id', sa.Integer(), index=True),
        sa.Column('resource_type', sa.String(64)),
        sa.Column('resource_id', sa.String(128)),
        sa.Column('remediation_steps', postgresql.JSON()),
        sa.Column('context', postgresql.JSON())
    )

    op.create_index('idx_violation_status', 'compliance_violations', ['is_resolved', 'severity'])

    # 合规策略表
    op.create_table(
        'compliance_policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('policy_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('policy_name', sa.String(128), nullable=False),
        sa.Column('compliance_type', sa.String(32), nullable=False),
        sa.Column('rules', postgresql.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('scope', sa.String(32)),
        sa.Column('scope_id', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('metadata', postgresql.JSON())
    )


def downgrade():
    """删除治理框架表"""

    # 按相反顺序删除表
    op.drop_table('compliance_policies')
    op.drop_table('compliance_violations')
    op.drop_table('compliance_checks')
    op.drop_table('configuration_history')
    op.drop_table('configurations')
    op.drop_table('health_check_logs')
    op.drop_table('failure_records')
    op.drop_table('rollback_history')
    op.drop_table('versions')
