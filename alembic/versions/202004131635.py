"""purchase flags not null

Revision ID: 591ffdcf0637
Revises: 73f4efcb6afa
Create Date: 2020-04-13 16:35:04.005185

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '591ffdcf0637'
down_revision = '73f4efcb6afa'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('purchases', 'equalized',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.alter_column('purchases', 'in_progress',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)


def downgrade():
    op.alter_column('purchases', 'in_progress',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('purchases', 'equalized',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
