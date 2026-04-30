"""Initial migration for OpenClaw-Harness.

Revision ID: 001_initial
Create Date: 2026-04-07 01:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('agents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text(), default=''),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('model', sa.String(64), default='claude-sonnet-4-20250514'),
        sa.Column('max_turns', sa.Integer(), default=8),
        sa.Column('max_tokens', sa.Integer(), default=4096),
        sa.Column('workspace', sa.String(512), default='./workspace'),
        sa.Column('config', sa.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                   onupdate=sa.func.now()),
    )

    op.create_table('sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('status', sa.String(16), default='active'),
        sa.Column('title', sa.String(256), default=''),
        sa.Column('total_messages', sa.Integer(), default=0),
        sa.Column('total_turns', sa.Integer(), default=0),
        sa.Column('total_tokens_input', sa.Integer(), default=0),
        sa.Column('total_tokens_output', sa.Integer(), default=0),
        sa.Column('total_cost_usd', sa.Float(), default=0.0),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                   onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_sessions_agent_id', 'sessions', ['agent_id'])
    op.create_index('ix_sessions_status', 'sessions', ['status'])

    op.create_table('messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_uses', sa.JSON(), default=list),
        sa.Column('stop_reason', sa.String(32), nullable=True),
        sa.Column('tokens_input', sa.Integer(), default=0),
        sa.Column('tokens_output', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])
    op.create_index('ix_messages_role', 'messages', ['role'])

    op.create_table('tool_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(36), sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('tool_name', sa.String(64), nullable=False),
        sa.Column('tool_input', sa.JSON(), default=dict),
        sa.Column('tool_output', sa.Text(), default=''),
        sa.Column('is_error', sa.Boolean(), default=False),
        sa.Column('duration_ms', sa.Integer(), default=0),
        sa.Column('permission_decision', sa.String(16), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_tool_results_message_id', 'tool_results', ['message_id'])

    op.create_table('tool_permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('tool_name', sa.String(64), nullable=False),
        sa.Column('permission', sa.String(16), default='ask'),
        sa.Column('path_rules', sa.JSON(), nullable=True),
        sa.Column('approved_commands', sa.JSON(), nullable=True),
        sa.Column('denied_commands', sa.JSON(), nullable=True),
    )
    op.create_index('ix_tool_permissions_agent_id', 'tool_permissions', ['agent_id'])

    op.create_table('tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('sessions.id'), nullable=True),
        sa.Column('task_type', sa.String(32), nullable=False),
        sa.Column('command', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), default='pending'),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('output_path', sa.String(512), nullable=True),
        sa.Column('cwd', sa.String(512), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    op.create_table('task_dependencies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('dep_task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('auto_unlock', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('permission_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('pattern', sa.String(512), nullable=False),
        sa.Column('allow', sa.Boolean(), default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.JSON(), default=dict),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(256), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    op.create_table('plugins',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('version', sa.String(32), default='0.0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(16), default='local'),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('install_path', sa.String(512), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=False),
        sa.Column('config', sa.JSON(), default=dict),
        sa.Column('has_commands', sa.Boolean(), default=False),
        sa.Column('has_hooks', sa.Boolean(), default=False),
        sa.Column('has_agents', sa.Boolean(), default=False),
        sa.Column('integrity_hash', sa.String(128), nullable=True),
        sa.Column('installed_by', sa.String(36), nullable=True),
        sa.Column('installed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(),
                   onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('plugins')
    op.drop_table('audit_logs')
    op.drop_table('permission_rules')
    op.drop_table('task_dependencies')
    op.drop_table('tasks')
    op.drop_table('tool_permissions')
    op.drop_table('tool_results')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('agents')
