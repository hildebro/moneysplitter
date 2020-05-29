"""add user setting for kicking users

Revision ID: 1bd8e8372632
Revises: d142cbfe83fa
Create Date: 2020-05-29 12:07:56.185427

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1bd8e8372632'
down_revision = 'd142cbfe83fa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_settings', sa.Column('participant_delete_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_settings', 'checklists', ['participant_delete_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'participant_delete_id')
