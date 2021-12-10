import logging
from enum import Enum, auto

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.language import detect_most_likely_language
from py_reportit.shared.util.partial_closure import text_indicates_partial_closure

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Boolean, ForeignKey, text

logger = logging.getLogger(f"py_reportit.{__name__}")

class ClosingType(Enum):
    CLOSED = auto()
    NOT_CLOSED = auto()
    PARTIALLY_CLOSED = auto()

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

    @property
    def closing_type(self) -> ClosingType:
        if not self.answer.closing:
            return ClosingType.NOT_CLOSED
        
        return ClosingType.PARTIALLY_CLOSED if text_indicates_partial_closure(self.answer.text) else ClosingType.CLOSED

    def __repr__(self):
        return f'<ReportAnswerMeta id={self.id!r} do_tweet={self.do_tweet!r} closing_type={self.closing_type!r}>'
