"""add transaction model

Revision ID: bec64688ce20
Revises: 2d991a3aa117
Create Date: 2020-05-02 17:59:31.835608

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bec64688ce20'
down_revision = '2d991a3aa117'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('transactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('checklist_id', sa.Integer(), nullable=True),
                    sa.Column('giver_id', sa.Integer(), nullable=True),
                    sa.Column('receiver_id', sa.Integer(), nullable=True),
                    sa.Column('amount', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='cascade'),
                    sa.ForeignKeyConstraint(['giver_id'], ['users.id'], ondelete='set null'),
                    sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='set null'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.alter_column('purchases', column_name='equalized', new_column_name='written_off')


def downgrade():
    op.alter_column('purchases', column_name='written_off', new_column_name='equalized')
    op.drop_table('transactions')
