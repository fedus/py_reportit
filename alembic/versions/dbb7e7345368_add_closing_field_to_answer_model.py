"""Add 'closing' field to answer model

Revision ID: dbb7e7345368
Revises: 627451339463
Create Date: 2021-08-29 14:53:47.598271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbb7e7345368'
down_revision = '627451339463'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('report_answer', sa.Column('closing', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('report_answer', 'closing')
    # ### end Alembic commands ###
