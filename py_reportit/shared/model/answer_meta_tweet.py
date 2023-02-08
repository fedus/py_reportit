from __future__ import annotations

from py_reportit.shared.model.orm_base import Base

from sqlalchemy.event import listen
from sqlalchemy.sql.functions import func
from sqlalchemy.orm import Session
from sqlalchemy import Column, SmallInteger, Integer, ForeignKey, Unicode

class AnswerMetaTweet(Base):

    __tablename__ = 'answer_meta_tweet'

    id = Column(Integer, primary_key=True)
    answer_meta_id = Column(Integer, ForeignKey('answer_meta.id'), nullable=False)
    type = Column(Unicode(20), nullable=False)
    part = Column(SmallInteger, nullable=False)
    order = Column(SmallInteger, nullable=False)
    tweet_id = Column(Unicode(30), nullable=False)


    def __repr__(self):
        return f'<AnswerMetaTweet id={self.id!r}>'

    @staticmethod
    def increment_order(mapper, connection, answer_meta: AnswerMetaTweet):
        last_order = Session.query(func.max(AnswerMetaTweet.order).label('order')\
            .filter(AnswerMetaTweet.answer_meta_id == answer_meta.answer_meta_id).first() )
        answer_meta.order = last_order.order + 1 if last_order else 0

listen(AnswerMetaTweet, "before_insert", AnswerMetaTweet.increment_order)
