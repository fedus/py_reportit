from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, Numeric, Unicode, select, not_, exists

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.model.crawl_item import CrawlItem, CrawlItemState
from py_reportit.shared.util.localized_arrow import LocalizedArrow


class Crawl(Base):

    __tablename__ = 'crawl'

    id = Column(Integer, primary_key=True)
    scheduled_at = Column(LocalizedArrow, nullable=False)
    items = relationship("CrawlItem", cascade="save-update, merge, delete, delete-orphan", uselist=True, backref="crawl")
    stop_at_lat = Column(Numeric(8,6), nullable=True)
    stop_at_lon = Column(Numeric(9,6), nullable=True)
    current_task_id = Column(Unicode(50), nullable=True)

    @hybrid_property
    def finished(self) -> bool:
        return not any(item.state == CrawlItemState.WAITING for item in self.items)

    @finished.expression
    def finished(cls):
        #return not_(exists(select(cls).where(cls.items.any(CrawlItem.state == CrawlItemState.WAITING))))
        return not_(exists(select(CrawlItem).where(CrawlItem.crawl_id == cls.id, CrawlItem.state == CrawlItemState.WAITING)))

    @hybrid_property
    def waiting_items(self):
        return sorted(filter(lambda item: item.state == CrawlItemState.WAITING, self.items), key=lambda item: item.scheduled_for)

    @waiting_items.expression
    def waiting_items(cls):
        return select(CrawlItem).where(CrawlItem.crawl_id == cls.id, CrawlItem.state == CrawlItemState.WAITING).order_by(CrawlItem.scheduled_for.asc())