"""add activity model

Revision ID: d142cbfe83fa
Revises: 31c1973cc58e
Create Date: 2020-05-28 14:11:05.013016

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd142cbfe83fa'
down_revision = '31c1973cc58e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('activities',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('checklist_id', sa.Integer(), nullable=True),
                    sa.Column('message', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='cascade'),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('activities')
