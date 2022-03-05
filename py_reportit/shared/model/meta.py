import logging
from typing import Optional

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Boolean, ForeignKey, String, text, select, func
from sqlalchemy.ext.hybrid import hybrid_property

from py_reportit.shared.model.category import Category
from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.model.meta_category_vote import MetaCategoryVote
from py_reportit.shared.util.language import detect_most_likely_language

logger = logging.getLogger(f"py_reportit.{__name__}")

class Meta(Base):

    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=False)
    do_tweet = Column(Boolean, default=True, server_default=text('true'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    closed_without_answer = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    tweet_ids = relationship('MetaTweet', uselist=True)
    address_polled = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    address_street = Column(String(100))
    address_postcode = Column(Integer)
    address_neighbourhood = Column(String(100))
    category_votes = relationship('MetaCategoryVote')

    @property
    def language(self):
        try:
            return detect_most_likely_language(f"{self.report.title} {self.report.description}")
        except Exception as e:
            logger.warn(f"Could not detect language for report id {self.report.id}, exception: {e}")
            return "un"
    
    @hybrid_property
    def category(self) -> Optional[Category]:
        votes = sorted(self.category_votes, key=lambda vote: vote.timestamp, reverse=True)[-50:]
        category_ids = list(map(lambda vote: vote.category_id, votes))  

        if len(votes):
            most_frequent_category_id = max(set(category_ids), key=category_ids.count)

            return next(filter(lambda vote: vote.category_id == most_frequent_category_id, votes), None).category

        return None

    @category.expression
    def category(cls):
        sub = select(MetaCategoryVote).where(MetaCategoryVote.meta_id == cls.id).limit(50).subquery()

        return select(sub.c.category_id).where(sub.c.meta_id == cls.id).group_by(sub.c.category_id).order_by(func.count(sub.c.category_id).desc()).limit(1).as_scalar()

    def __repr__(self):
        return f'<Meta id={self.id!r} do_tweet={self.do_tweet!r}>'

    @hybrid_property
    def vote_count(self) -> int:
        return len(self.category_votes)

    @vote_count.expression
    def vote_count(cls):
        return select(func.count(MetaCategoryVote.timestamp)).where(MetaCategoryVote.meta_id == cls.id).as_scalar()
