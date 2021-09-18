from sqlalchemy import select

from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.crawl_result import CrawlResult

class CrawlResultRepository(AbstractRepository[CrawlResult]):

    model = CrawlResult

    def get_most_recent_successful_crawl(self) -> CrawlResult:
        return self.session.execute(select(self.model).where(self.model.successful==True).order_by(self.model.id.desc()).limit(1)).scalar()
