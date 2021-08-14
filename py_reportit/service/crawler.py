import logging, sys

from datetime import datetime

from py_reportit.model.crawl_result import CrawlResult
from py_reportit.model.report import Report
from py_reportit.repository.report import ReportRepository
from py_reportit.repository.meta import MetaRepository
from py_reportit.repository.crawl_result import CrawlResultRepository
from py_reportit.service.reportit_api import ReportItService
from py_reportit.util.reportit_utils import get_lowest_and_highest_ids

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
        last_reports = []

        logger.info("Fetching last crawl result")
        last_crawl_result = self.crawl_result_repository.get_most_recent_successful_crawl()

        if last_crawl_result:
            logger.info("Last crawl result found, fetching related reports from database (starting from id {%d})", last_crawl_result.lowest_id)
            last_reports = self.report_repository.get_by(Report.id >= last_crawl_result.lowest_id)

        try:
            logger.info("Fetching reports")
            reports = self.api_service.get_reports()

            logger.info(f"{len(reports)} reports fetched")
            self.report_repository.update_or_create_all(reports)
        except KeyboardInterrupt:
            raise
        except:
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            self.crawl_result_repository.create(CrawlResult(
                timestamp=datetime.now(),
                successful=False,
            ))
            return

        lowest_id, highest_id = get_lowest_and_highest_ids(reports)

        self.crawl_result_repository.create(CrawlResult(
            timestamp=datetime.now(),
            successful=True,
            total=len(reports),
            added=None,
            removed=None,
            modified=None,
            marked_done=None,
            highest_id=highest_id,
            lowest_id=lowest_id,
        ))

        logger.info("Running post processors")
        for pp in self.post_processors:
            logger.info(f"Running post processor {pp}")
            pp(self.config, self.report_repository).process()
