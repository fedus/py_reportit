from py_reportit.shared.model.orm_base import Base
from sqlalchemy import Column, Integer, DateTime, Boolean

class CrawlResult(Base):

    __tablename__ = 'crawl_result'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    successful = Column(Boolean, nullable=False)
    total = Column(Integer)
    added = Column(Integer)
    removed = Column(Integer)
    marked_done = Column(Integer)
    highest_id = Column(Integer)
    lowest_id = Column(Integer)

    def __repr__(self):
        repr = f'<CrawlResult id={self.id!r}\
            timestamp={self.timestamp!r}\
            successful={self.successful!r}\
            total={self.total!r}\
            added={self.added!r}\
            removed={self.removed!r}\
            marked_done={self.marked_done!r}\
            highest_id={self.highest_id!r}\
            lowest_id={self.lowest_id!r}>'
        return ' '.join(repr.split())
