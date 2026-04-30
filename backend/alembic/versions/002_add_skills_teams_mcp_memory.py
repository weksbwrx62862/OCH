"""Add skills, teams, team_members, mcp_servers, memory_facts tables.

Revision ID: 002_add_skills_teams_mcp_memory
Create Date: 2026-04-11 01:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = '002_add_skills_teams_mcp_memory'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('skills',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(32), default='general'),
        sa.Column('version', sa.String(16), default='1.0.0'),
        sa.Column('source', sa.String(16), default='builtin'),
        sa.Column('path', sa.String(512), nullable=True),
        sa.Column('url', sa.String(1024), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('content_md', sa.Text(), nullable=True),
        sa.Column('triggers', sa.JSON(), default=list),
        sa.Column('dependencies', sa.JSON(), default=list),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('installed_by', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table('teams',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), default='active'),
        sa.Column('config', sa.JSON(), default=dict),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_by', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('dissolved_at', sa.DateTime(), nullable=True),
    )

    op.create_table('team_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role', sa.String(32), default='member'),
        sa.Column('capabilities', sa.JSON(), default=list),
        sa.Column('status', sa.String(16), default='idle'),
        sa.Column('assigned_task_id', sa.String(36), nullable=True),
        sa.Column('task_count', sa.Integer(), default=0),
        sa.Column('completed_tasks', sa.Integer(), default=0),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_agent_id', 'team_members', ['agent_id'])

    op.create_table('mcp_servers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('server_type', sa.String(16), default='stdio'),
        sa.Column('command', sa.Text(), nullable=True),
        sa.Column('args', sa.JSON(), default=list),
        sa.Column('env', sa.JSON(), default=dict),
        sa.Column('url', sa.String(1024), nullable=True),
        sa.Column('headers', sa.JSON(), default=dict),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('auto_start', sa.Boolean(), default=False),
        sa.Column('status', sa.String(16), default='configured'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_test_at', sa.DateTime(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('discovered_tools', sa.JSON(), default=list),
        sa.Column('discovered_resources', sa.JSON(), default=list),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_by', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table('memory_facts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(32), nullable=False, default='knowledge'),
        sa.Column('confidence', sa.Float(), default=0.8),
        sa.Column('source', sa.String(32), default='manual'),
        sa.Column('tags', sa.JSON(), default=list),
        sa.Column('importance', sa.Integer(), default=5),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_index('ix_memory_facts_content', 'memory_facts', ['content'])
    op.create_index('ix_memory_facts_category', 'memory_facts', ['category'])
    op.create_index('ix_memory_facts_confidence', 'memory_facts', ['confidence'])
    op.create_index('ix_memory_facts_source', 'memory_facts', ['source'])
    op.create_index('ix_memory_facts_active', 'memory_facts', ['is_active'])


def downgrade() -> None:
    op.drop_table('memory_facts')
    op.drop_table('mcp_servers')
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('skills')
