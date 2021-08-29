from py_reportit.model.orm_base import Base
from sqlalchemy import Column, SmallInteger, Integer, ForeignKey, Unicode

class AnswerMetaTweet(Base):

    __tablename__ = 'answer_meta_tweet'

    id = Column(Integer, primary_key=True)
    answer_meta_id = Column(Integer, ForeignKey('answer_meta.id'), nullable=False)
    order = Column(SmallInteger, nullable=False)
    tweet_id = Column(Unicode(30), nullable=False)


    def __repr__(self):
        return f'<AnswerMetaTweet id={self.id!r}>'
