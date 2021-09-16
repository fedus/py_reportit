import logging

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.language import detect_most_likely_language

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Boolean, ForeignKey, text

logger = logging.getLogger(f"py_reportit.{__name__}")

class ReportAnswerMeta(Base):

    __tablename__ = 'answer_meta'

    id = Column(Integer, primary_key=True)
    report_answer_id = Column(Integer, ForeignKey('report_answer.id'), nullable=False)
    do_tweet = Column(Boolean, default=True, server_default=text('true'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    tweet_ids = relationship('AnswerMetaTweet', uselist=True)

    @property
    def language(self):
        try:
            return detect_most_likely_language(self.answer.text)
        except Exception as e:
            logger.warn(f"Could not detect language for answer id {self.report_answer_id} of report id {self.answer.report.id}, exception: {e}")
            return "un"

    def __repr__(self):
        return f'<ReportAnswerMeta id={self.id!r} do_tweet={self.do_tweet!r}>'
