"""Initial schema with tenant, report_definition, schedule, execution_run, artifact, delivery_receipt, audit_event tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create tenant table
    op.create_table(
        'tenant',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create report_definition table
    op.create_table(
        'report_definition',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('query_spec', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('template_ref', sa.String(500), nullable=False),
        sa.Column('output_format', sa.String(50), nullable=False, server_default='pdf'),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_report_tenant_id', 'report_definition', ['tenant_id'])

    # Create schedule table
    op.create_table(
        'schedule',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('report_definition_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_delivery_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_schedule_tenant_id', 'schedule', ['tenant_id'])
    op.create_index('idx_schedule_next_run', 'schedule', ['next_run_at', 'is_active'])
    op.create_index('idx_schedule_report_id', 'schedule', ['report_definition_id'])

    # Create execution_run table
    op.create_table(
        'execution_run',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('schedule_id', sa.String(36), nullable=True),
        sa.Column('report_definition_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
        sa.ForeignKeyConstraint(['report_definition_id'], ['report_definition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_execution_tenant_id', 'execution_run', ['tenant_id'])
    op.create_index('idx_execution_schedule_id', 'execution_run', ['schedule_id'])
    op.create_index('idx_execution_status', 'execution_run', ['status'])
    op.create_index('idx_execution_created_at', 'execution_run', ['created_at'])

    # Create artifact table
    op.create_table(
        'artifact',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('execution_run_id', sa.String(36), nullable=False),
        sa.Column('blob_path', sa.String(1000), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('file_format', sa.String(50), nullable=False),
        sa.Column('signed_url', sa.Text(), nullable=True),
        sa.Column('signed_url_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['execution_run_id'], ['execution_run.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_run_id')
    )
    op.create_index('idx_artifact_tenant_id', 'artifact', ['tenant_id'])
    op.create_index('idx_artifact_created_at', 'artifact', ['created_at'])

    # Create delivery_receipt table
    op.create_table(
        'delivery_receipt',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('artifact_id', sa.String(36), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('recipient', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifact.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_delivery_tenant_id', 'delivery_receipt', ['tenant_id'])
    op.create_index('idx_delivery_artifact_id', 'delivery_receipt', ['artifact_id'])

    # Create audit_event table
    op.create_table(
        'audit_event',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=False),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_tenant_id', 'audit_event', ['tenant_id'])
    op.create_index('idx_audit_created_at', 'audit_event', ['created_at'])
    op.create_index('idx_audit_event_type', 'audit_event', ['event_type'])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table('audit_event')
    op.drop_table('delivery_receipt')
    op.drop_table('artifact')
    op.drop_table('execution_run')
    op.drop_table('schedule')
    op.drop_table('report_definition')
    op.drop_table('tenant')
