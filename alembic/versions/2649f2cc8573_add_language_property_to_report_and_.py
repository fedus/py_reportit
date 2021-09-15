"""Add language property to report and answer metas

Revision ID: 2649f2cc8573
Revises: 5a69174b2172
Create Date: 2021-09-15 23:17:19.512954

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2649f2cc8573'
down_revision = '5a69174b2172'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('answer_meta', sa.Column('language', sa.Unicode(length=4), nullable=True))
    op.add_column('meta', sa.Column('language', sa.Unicode(length=4), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('meta', 'language')
    op.drop_column('answer_meta', 'language')
    # ### end Alembic commands ###