"""init

Revision ID: 6c5b895023c9
Revises: 
Create Date: 2026-04-16 08:49:26.890224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '6c5b895023c9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table('companies',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('logo_url', sa.Text(), nullable=True),
    sa.Column('trello_token', sa.Text(), nullable=True),
    sa.Column('trello_workspace_id', sa.String(length=100), nullable=True),
    sa.Column('owner_account_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('active', 'inactive', name='companystatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('members',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('account_id', sa.UUID(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('owner', 'admin', 'member', name='memberrole'), nullable=False),
    sa.Column('trello_user_id', sa.String(length=100), nullable=True),
    sa.Column('trello_username', sa.String(length=100), nullable=True),
    sa.Column('google_email', sa.String(length=255), nullable=True),
    sa.Column('voice_embedding', Vector(512), nullable=True),  # đã sửa
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('members')
    op.drop_table('companies')
    op.execute('DROP EXTENSION IF EXISTS vector')