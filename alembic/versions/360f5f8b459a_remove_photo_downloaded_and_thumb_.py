"""Remove photo_downloaded and thumb_downloaded from meta

Revision ID: 360f5f8b459a
Revises: 3f0abbafe5a9
Create Date: 2022-01-09 14:41:40.742495

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '360f5f8b459a'
down_revision = '3f0abbafe5a9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('meta', 'photo_downloaded')
    op.drop_column('meta', 'thumb_downloaded')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('meta', sa.Column('thumb_downloaded', mysql.TINYINT(display_width=1), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('meta', sa.Column('photo_downloaded', mysql.TINYINT(display_width=1), server_default=sa.text('0'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###