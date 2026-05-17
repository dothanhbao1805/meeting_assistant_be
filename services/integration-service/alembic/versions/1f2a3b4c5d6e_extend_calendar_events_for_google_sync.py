"""extend calendar events for google sync

Revision ID: 1f2a3b4c5d6e
Revises: efccc6e92383
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f2a3b4c5d6e'
down_revision: Union[str, Sequence[str], None] = 'efccc6e92383'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('calendar_events', sa.Column('company_id', sa.UUID(), nullable=True))
    op.add_column('calendar_events', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('calendar_events', sa.Column('retries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('calendar_events', sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.alter_column('calendar_events', 'user_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('calendar_events', 'user_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('calendar_events', 'created_at')
    op.drop_column('calendar_events', 'retries')
    op.drop_column('calendar_events', 'error_message')
    op.drop_column('calendar_events', 'company_id')
