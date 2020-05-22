"""add payoff user to transactions

Revision ID: 34b10e2ef7d7
Revises: 25f4d1494d68
Create Date: 2020-05-22 12:16:51.898294

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '34b10e2ef7d7'
down_revision = '25f4d1494d68'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transactions', sa.Column('payoff_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'transactions', 'users', ['payoff_user_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'payoff_user_id')
