"""add checklist delete to user settings

Revision ID: 684d5c08fd23
Revises: 34b10e2ef7d7
Create Date: 2020-05-23 11:19:00.220622

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '684d5c08fd23'
down_revision = '34b10e2ef7d7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_settings', sa.Column('deleting_checklist_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_settings', 'checklists', ['deleting_checklist_id'], ['id'], ondelete='set null')


def downgrade():
    op.drop_constraint(None, 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'deleting_checklist_id')
