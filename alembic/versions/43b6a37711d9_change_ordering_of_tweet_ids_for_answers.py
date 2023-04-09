"""Change ordering of tweet ids for answers

Revision ID: 43b6a37711d9
Revises: d42f295baf1c
Create Date: 2023-02-08 22:49:53.901621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43b6a37711d9'
down_revision = 'd42f295baf1c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('answer_meta_tweet', 'order', new_column_name='part', existing_type=sa.SmallInteger())
    op.add_column('answer_meta_tweet', sa.Column('order', sa.SmallInteger()))
    op.execute('UPDATE answer_meta_tweet t, (SELECT id, row_number() OVER (PARTITION BY answer_meta_id ORDER BY answer_meta_id, tweet_id) as rn FROM `answer_meta_tweet` ORDER BY answer_meta_id, rn) r SET t.order = r.rn - 1 WHERE t.id=r.id')

def downgrade():
    op.drop_column('answer_meta_tweet', 'order')
    op.alter_column('answer_meta_tweet', 'part', new_column_name='order', existing_type=sa.SmallInteger())
