"""add purchase distributions

Revision ID: cc23b3b81532
Revises: 433538191e96
Create Date: 2020-06-05 10:40:20.975410

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'cc23b3b81532'
down_revision = '433538191e96'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('purchase_distributions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('purchase_id', sa.Integer(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('amount', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ondelete='cascade'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='set null'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.add_column('purchases', sa.Column('leftover_price', sa.Integer(), nullable=True))
    op.execute('UPDATE purchases SET leftover_price = price')
    op.add_column('user_settings', sa.Column('purchase_distribution_id', sa.Integer(), nullable=True))
    op.add_column('user_settings', sa.Column('purchase_edit_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_settings', 'purchases', ['purchase_edit_id'], ['id'], ondelete='set null')
    op.create_foreign_key(None, 'user_settings', 'purchase_distributions', ['purchase_distribution_id'], ['id'],
                          ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'purchase_edit_id')
    op.drop_column('user_settings', 'purchase_distribution_id')
    op.drop_column('purchases', 'leftover_price')
    op.drop_table('purchase_distributions')
