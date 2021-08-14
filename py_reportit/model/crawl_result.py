from py_reportit.model.orm_base import Base
from sqlalchemy import Column, Integer, DateTime, Boolean

class CrawlResult(Base):

    __tablename__ = 'crawl_result'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    successful = Column(Boolean, nullable=False)
    total = Column(Integer)
    added = Column(Integer)
    removed = Column(Integer)
    modified = Column(Integer)
    marked_done = Column(Integer)
    highest_id = Column(Integer)
    lowest_id = Column(Integer)

    def __repr__(self):
        return f'<CrawlResult id={self.id!r} timestamp={self.timestamp!r}>'
