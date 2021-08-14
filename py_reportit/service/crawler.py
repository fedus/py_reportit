import logging

from py_reportit.repository.report import ReportRepository
from py_reportit.repository.meta import MetaRepository
from py_reportit.repository.crawl_result import CrawlResultRepository
from py_reportit.service.reportit_api import ReportItService

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 post_processors,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 crawl_result_repository: CrawlResultRepository,
                 api_service: ReportItService):
        self.config = config
        self.post_processors = post_processors
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.crawl_result_repository = crawl_result_repository
        self.api_service = api_service

    def crawl(self):
        logger.info("Fetching reports")
        reports = self.api_service.get_reports()

        logger.info(f"{len(reports)} reports fetched")
        self.report_repository.update_or_create_all(reports)

        logger.info("Running post processors")
        for pp in self.post_processors:
            logger.info(f"Running post processor {pp}")
            pp(self.config, self.report_repository).process()
