"""add user setting for transaction payoff

Revision ID: 34479800317c
Revises: 1bd8e8372632
Create Date: 2020-05-29 12:57:53.874077

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '34479800317c'
down_revision = '1bd8e8372632'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_settings', sa.Column('transaction_payoff_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_settings', 'checklists', ['transaction_payoff_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'transaction_payoff_id')
