"""add user setting for item delete

Revision ID: 433538191e96
Revises: 34479800317c
Create Date: 2020-05-29 14:40:21.718274

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '433538191e96'
down_revision = '34479800317c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_settings', sa.Column('item_delete_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_settings', 'checklists', ['item_delete_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'item_delete_id')
