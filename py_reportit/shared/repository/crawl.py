from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.crawl import Crawl

class CrawlRepository(AbstractRepository[Crawl]):

    model = Crawl
