from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.crawl_item import CrawlItem, CrawlItemState

class CrawlItemRepository(AbstractRepository[CrawlItem]):

    model = CrawlItem

    def get_next_waiting(self, session: Session, crawl_id: int) -> Optional[CrawlItem]:
        result = session.execute(
            select(CrawlItem).where(
                CrawlItem.crawl_id == crawl_id,
                CrawlItem.state == CrawlItemState.WAITING
            ).order_by(CrawlItem.scheduled_for.asc())).first()

        if result:
            return result[0]

        return None
