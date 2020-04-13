"""purchases in progress

Revision ID: 73f4efcb6afa
Revises: 
Create Date: 2020-04-05 10:22:49.588250

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '73f4efcb6afa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('purchases', sa.Column('in_progress', sa.Boolean(), nullable=True))
    op.alter_column('purchases', 'price',
                    existing_type=sa.INTEGER(),
                    nullable=True)


def downgrade():
    op.alter_column('purchases', 'price',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.drop_column('purchases', 'in_progress')
