from sqlalchemy.orm import relationship
from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.language import detect_most_likely_language
from sqlalchemy import Column, Integer, Boolean, ForeignKey, text

class Meta(Base):

    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=False)
    is_online = Column(Boolean, default=True, server_default=text('true'), nullable=False)
    do_tweet = Column(Boolean, default=True, server_default=text('true'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    photo_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    thumb_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    closed_without_answer = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    tweet_ids = relationship('MetaTweet', uselist=True)

    @property
    def language(self):
        return detect_most_likely_language(f"{self.report.title} {self.report.description}")

    def __repr__(self):
        return f'<Meta id={self.id!r} do_tweet={self.do_tweet!r}>'

