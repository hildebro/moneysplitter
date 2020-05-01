"""in progress user kicking

Revision ID: 8c14751599e0
Revises: 4ab03f3beff0
Create Date: 2020-05-01 16:19:56.259116

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8c14751599e0'
down_revision = '4ab03f3beff0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('deleting_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'users', ['deleting_user_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'deleting_user_id')
