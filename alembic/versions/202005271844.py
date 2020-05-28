"""add create dates to all models

Revision ID: 31c1973cc58e
Revises: 684d5c08fd23
Create Date: 2020-05-27 18:44:12.085952

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.

revision = '31c1973cc58e'
down_revision = '684d5c08fd23'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('checklist_participants', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('checklists', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('items', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('purchases', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('transactions', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))

    op.execute('UPDATE checklist_participants SET created_at = NOW()')
    op.execute('UPDATE checklists SET created_at = NOW()')
    op.execute('UPDATE items SET created_at = NOW()')
    op.execute('UPDATE purchases SET created_at = NOW()')
    op.execute('UPDATE transactions SET created_at = NOW()')
    op.execute('UPDATE users SET created_at = NOW()')

    op.alter_column('checklist_participants', 'created_at', nullable=False)
    op.alter_column('checklists', 'created_at', nullable=False)
    op.alter_column('items', 'created_at', nullable=False)
    op.alter_column('purchases', 'created_at', nullable=False)
    op.alter_column('transactions', 'created_at', nullable=False)
    op.alter_column('users', 'created_at', nullable=False)


def downgrade():
    op.drop_column('users', 'created_at')
    op.drop_column('transactions', 'created_at')
    op.drop_column('purchases', 'created_at')
    op.drop_column('items', 'created_at')
    op.drop_column('checklists', 'created_at')
    op.drop_column('checklist_participants', 'created_at')
