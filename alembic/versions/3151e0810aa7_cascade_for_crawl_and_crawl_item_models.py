"""Cascade for crawl and crawl_item models

Revision ID: 3151e0810aa7
Revises: e63d193f2885
Create Date: 2022-01-27 21:00:30.311275

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3151e0810aa7'
down_revision = 'e63d193f2885'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('crawl_item_ibfk_1', 'crawl_item', type_='foreignkey')
    op.create_foreign_key(None, 'crawl_item', 'crawl', ['crawl_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'crawl_item', type_='foreignkey')
    op.create_foreign_key('crawl_item_ibfk_1', 'crawl_item', 'crawl', ['crawl_id'], ['id'])
    # ### end Alembic commands ###
