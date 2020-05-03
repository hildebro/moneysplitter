"""add currently selected checklist to users

Revision ID: 25f4d1494d68
Revises: bec64688ce20
Create Date: 2020-05-03 15:08:24.972822

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from moneysplitter.db import session_wrapper, User

revision = '25f4d1494d68'
down_revision = 'bec64688ce20'
branch_labels = None
depends_on = None


@session_wrapper
def upgrade(session):
    settings_table = op.create_table(
        'user_settings',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='set null'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.bulk_insert(settings_table, [{'user_id': user.id} for user in session.query(User).all()])


def downgrade():
    op.drop_table('user_settings')
