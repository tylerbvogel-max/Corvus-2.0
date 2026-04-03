"""Add integrity_scans and integrity_findings tables, plus last_accessed_at on neurons.

Revision ID: 005_add_integrity_system
Revises: 004_add_autopilot_proposals
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_integrity_system'
down_revision: Union[str, Sequence[str], None] = '004_add_autopilot_proposals'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """Check if a table already exists (handles create_all pre-creation)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table_name})
    return result.scalar() is not None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column already exists on a table."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table_name, "c": column_name})
    return result.scalar() is not None


def upgrade() -> None:
    """Create integrity tables and add last_accessed_at to neurons."""
    if not _table_exists('integrity_scans'):
        op.create_table(
            'integrity_scans',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('scan_type', sa.String(30), nullable=False),
            sa.Column('scope', sa.String(100), nullable=False, server_default='global'),
            sa.Column('status', sa.String(20), nullable=False, server_default='running'),
            sa.Column('parameters_json', sa.Text(), nullable=True),
            sa.Column('findings_count', sa.Integer(), server_default='0'),
            sa.Column('initiated_by', sa.String(100), nullable=True),
            sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_integrity_scans_scan_type', 'integrity_scans', ['scan_type'])

    if not _table_exists('integrity_findings'):
        op.create_table(
            'integrity_findings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('scan_id', sa.Integer(), sa.ForeignKey('integrity_scans.id'), nullable=False),
            sa.Column('finding_type', sa.String(30), nullable=False),
            sa.Column('severity', sa.String(20), nullable=False, server_default='warning'),
            sa.Column('priority_score', sa.Float(), server_default='0.0'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('detail_json', sa.Text(), nullable=True),
            sa.Column('neuron_ids_json', sa.Text(), nullable=True),
            sa.Column('edge_ids_json', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='open'),
            sa.Column('resolution', sa.String(30), nullable=True),
            sa.Column('proposal_id', sa.Integer(), sa.ForeignKey('autopilot_proposals.id'), nullable=True),
            sa.Column('resolved_by', sa.String(100), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_integrity_findings_scan_id', 'integrity_findings', ['scan_id'])
        op.create_index('ix_integrity_findings_status', 'integrity_findings', ['status'])
        op.create_index('ix_integrity_findings_finding_type', 'integrity_findings', ['finding_type'])

    # Add last_accessed_at to neurons for age-based review
    if not _column_exists('neurons', 'last_accessed_at'):
        op.add_column('neurons', sa.Column('last_accessed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Drop integrity tables and last_accessed_at column."""
    op.drop_column('neurons', 'last_accessed_at')
    op.drop_table('integrity_findings')
    op.drop_table('integrity_scans')
