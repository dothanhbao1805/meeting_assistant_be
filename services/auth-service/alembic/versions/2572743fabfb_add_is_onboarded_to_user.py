# alembic/versions/2572743fabfb_add_is_onboarded_to_user.py

from alembic import op
import sqlalchemy as sa

revision = '2572743fabfb'
down_revision = 'f66c2a3c72b9'  # revision init của bạn
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_onboarded', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_onboarded')