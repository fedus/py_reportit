from enum import Enum, auto

from sqlalchemy import Column, Integer, Enum as SqlEnum, DateTime, Boolean, ForeignKey

from py_reportit.shared.model.orm_base import Base


class CrawlItemState(Enum):
    WAITING = auto()
    SUCCESS = auto()
    FAILURE = auto()

class CrawlItem(Base):

    __tablename__ = 'crawl_item'

    id = Column(Integer, primary_key=True)
    crawl_id = Column(Integer, ForeignKey('crawl.id', ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    state = Column(SqlEnum(CrawlItemState), nullable=False, default=CrawlItemState.WAITING)
    report_found = Column(Boolean, nullable=True)
    stop_condition_hit = Column(Boolean, nullable=True)
