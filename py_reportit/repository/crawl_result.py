from sqlalchemy import select

from py_reportit.repository.abstract_repository import AbstractRepository
from py_reportit.model.crawl_result import CrawlResult

class CrawlResultRepository(AbstractRepository):

    repository_type = CrawlResult

    def get_most_recent_successful_crawl(self) -> repository_type:
        return self.session.execute(select(self.repository_type).where(self.repository_type.successful==True).order_by(self.repository_type.id.desc()).limit(1)).scalar()
