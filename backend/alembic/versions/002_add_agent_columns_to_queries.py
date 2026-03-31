"""Add agent_results_json and agent_mode columns to queries table

Revision ID: 002_add_agent_columns
Revises: ae144af9c1e1
Create Date: 2026-03-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_agent_columns'
down_revision: Union[str, Sequence[str], None] = 'ae144af9c1e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add agent columns to queries table."""
    op.add_column('queries', sa.Column('agent_results_json', sa.Text(), nullable=True))
    op.add_column('queries', sa.Column('agent_mode', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema: remove agent columns from queries table."""
    op.drop_column('queries', 'agent_mode')
    op.drop_column('queries', 'agent_results_json')
