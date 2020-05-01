"""in progress item deletions

Revision ID: 4ab03f3beff0
Revises: 591ffdcf0637
Create Date: 2020-05-01 11:16:35.292436

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4ab03f3beff0'
down_revision = '591ffdcf0637'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('items', sa.Column('deleting_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'items', 'users', ['deleting_user_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'items', type_='foreignkey')
    op.drop_column('items', 'deleting_user_id')
