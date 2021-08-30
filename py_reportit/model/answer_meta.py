from py_reportit.model.orm_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Boolean, ForeignKey, text

class ReportAnswerMeta(Base):

    __tablename__ = 'answer_meta'

    id = Column(Integer, primary_key=True)
    report_answer_id = Column(Integer, ForeignKey('report_answer.id'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    tweet_ids = relationship('AnswerMetaTweet', uselist=True)

    def __repr__(self):
        return f'<ReportAnswerMeta id={self.id!r}>'