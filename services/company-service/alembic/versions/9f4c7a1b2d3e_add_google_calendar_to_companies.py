"""add google calendar to companies

Revision ID: 9f4c7a1b2d3e
Revises: 57730085a48f
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f4c7a1b2d3e'
down_revision: Union[str, Sequence[str], None] = '57730085a48f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('companies', sa.Column('google_access_token', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('google_refresh_token', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('google_token_expiry', sa.DateTime(), nullable=True))
    op.add_column('companies', sa.Column('google_calendar_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('companies', 'google_calendar_id')
    op.drop_column('companies', 'google_token_expiry')
    op.drop_column('companies', 'google_refresh_token')
    op.drop_column('companies', 'google_access_token')
