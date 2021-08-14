from abc import ABC, abstractmethod

from py_reportit.repository.crawl_result import CrawlResultRepository
from py_reportit.repository.meta import MetaRepository
from py_reportit.repository.report import ReportRepository

class AbstractPostProcessor(ABC):

    def __init__(self,
                 config: dict,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 crawl_result_repository: CrawlResultRepository):
        self.config = config
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.crawl_result_repository = crawl_result_repository
        super().__init__()

    @abstractmethod
    def process(self):
        pass
