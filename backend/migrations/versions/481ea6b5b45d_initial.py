"""initial

Revision ID: 481ea6b5b45d
Revises:
Create Date: 2026-05-18 22:17:46.744383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '481ea6b5b45d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'name'),
    )

    op.create_table(
        'runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('parent_run_id', sa.Uuid(), nullable=True),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='running', nullable=False),
        sa.Column('inputs', postgresql.JSONB(), nullable=True),
        sa.Column('outputs', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('serialized', postgresql.JSONB(), nullable=True),
        sa.Column('events', postgresql.JSONB(), nullable=True),
        sa.Column('extra', postgresql.JSONB(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completion_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('prompt_cost', sa.Numeric(precision=10, scale=6), server_default='0', nullable=False),
        sa.Column('completion_cost', sa.Numeric(precision=10, scale=6), server_default='0', nullable=False),
        sa.Column('first_token_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('start_time', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('modified_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_runs_parent_run_id', 'runs', ['parent_run_id'])
    op.create_index('ix_runs_project_id', 'runs', ['project_id'])
    op.create_index('ix_runs_status', 'runs', ['status'])

    op.create_table(
        'feedback',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Double(), nullable=True),
        sa.Column('value', postgresql.JSONB(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feedback_run_id', 'feedback', ['run_id'])

    op.create_table(
        'deployments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('config_path', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=20), server_default='local', nullable=False),
        sa.Column('env_vars', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='created', nullable=False),
        sa.Column('container_id', sa.String(length=255), nullable=True),
        sa.Column('container_url', sa.String(length=512), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('command', sa.Text(), nullable=True),
        sa.Column('image_tag', sa.String(length=255), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )


def downgrade() -> None:
    op.drop_table('deployments')
    op.drop_index('ix_feedback_run_id', table_name='feedback')
    op.drop_table('feedback')
    op.drop_index('ix_runs_status', table_name='runs')
    op.drop_index('ix_runs_project_id', table_name='runs')
    op.drop_index('ix_runs_parent_run_id', table_name='runs')
    op.drop_table('runs')
    op.drop_table('projects')
    op.drop_table('workspaces')
