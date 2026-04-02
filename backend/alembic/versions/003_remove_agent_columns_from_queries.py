"""Remove agent_results_json and agent_mode columns from queries table

Revision ID: 003_remove_agent_columns
Revises: 002_add_agent_columns
Create Date: 2026-04-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_remove_agent_columns'
down_revision: Union[str, Sequence[str], None] = '002_add_agent_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: remove agent columns from queries table."""
    op.drop_column('queries', 'agent_mode')
    op.drop_column('queries', 'agent_results_json')


def downgrade() -> None:
    """Downgrade schema: re-add agent columns to queries table."""
    op.add_column('queries', sa.Column('agent_results_json', sa.Text(), nullable=True))
    op.add_column('queries', sa.Column('agent_mode', sa.Boolean(), nullable=False, server_default=sa.text('false')))
