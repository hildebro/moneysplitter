"""move deleting_user_id to participant table

Revision ID: 2d991a3aa117
Revises: 8c14751599e0
Create Date: 2020-05-01 21:44:54.533087

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2d991a3aa117'
down_revision = '8c14751599e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('checklist_participants', sa.Column('deleting_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'checklist_participants', 'users', ['deleting_user_id'], ['id'], ondelete='set null')
    op.drop_constraint('users_deleting_user_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'deleting_user_id')


def downgrade():
    op.add_column('users', sa.Column('deleting_user_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('users_deleting_user_id_fkey', 'users', 'users', ['deleting_user_id'], ['id'],
                          ondelete='SET NULL')
    op.drop_constraint(None, 'checklist_participants', type_='foreignkey')
    op.drop_column('checklist_participants', 'deleting_user_id')
