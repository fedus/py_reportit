from typing import Text

from py_reportit.model.orm_base import Base
from sqlalchemy import Column, SmallInteger, Integer, ForeignKey, Unicode

class MetaTweet(Base):

    __tablename__ = 'meta_tweet'

    id = Column(Integer, primary_key=True)
    meta_id = Column(Integer, ForeignKey('meta.id'), nullable=False)
    type = Column(Unicode(20), nullable=False)
    order = Column(SmallInteger, nullable=False)
    tweet_id = Column(Unicode(30), nullable=False)


    def __repr__(self):
        return f'<MetaTweet id={self.id!r}>'

