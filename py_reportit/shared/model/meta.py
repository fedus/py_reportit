import logging

from sqlalchemy.orm import relationship
from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.language import detect_most_likely_language
from sqlalchemy import Column, Integer, Boolean, ForeignKey, String, text

logger = logging.getLogger(f"py_reportit.{__name__}")

class Meta(Base):

    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=False)
    do_tweet = Column(Boolean, default=True, server_default=text('true'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    photo_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    thumb_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    closed_without_answer = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    tweet_ids = relationship('MetaTweet', uselist=True)
    address_polled = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    address_street = Column(String(100))
    address_postcode = Column(Integer)
    address_neighbourhood = Column(String(100))

    @property
    def language(self):
        try:
            return detect_most_likely_language(f"{self.report.title} {self.report.description}")
        except Exception as e:
            logger.warn(f"Could not detect language for report id {self.report.id}, exception: {e}")
            return "un"

    def __repr__(self):
        return f'<Meta id={self.id!r} do_tweet={self.do_tweet!r}>'

