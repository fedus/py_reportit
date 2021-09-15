"""Add closed_without_answer property to Report Meta

Revision ID: 5a69174b2172
Revises: c9b03285f2b7
Create Date: 2021-09-08 23:48:23.146224

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a69174b2172'
down_revision = 'c9b03285f2b7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('meta', sa.Column('closed_without_answer', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('meta', 'closed_without_answer')
    # ### end Alembic commands ###