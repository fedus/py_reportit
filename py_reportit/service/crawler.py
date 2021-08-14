import logging, sys

from datetime import datetime

from py_reportit.model.crawl_result import CrawlResult
from py_reportit.model.report import Report
from py_reportit.model.meta import Meta
from py_reportit.repository.report import ReportRepository
from py_reportit.repository.meta import MetaRepository
from py_reportit.repository.crawl_result import CrawlResultRepository
from py_reportit.service.reportit_api import ReportItService
from py_reportit.util.reportit_utils import extract_ids, get_lowest_and_highest_ids

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

    def get_online_reports_count(self) -> int:
        return self.meta_repository.count_by(Meta.is_online==True)

    def get_offline_reports_count(self) -> int:
        return self.meta_repository.count_by(Meta.is_online==False)

    def get_finished_reports_count(self) -> int:
        return self.report_repository.count_by(Report.status=="finished")

    def crawl(self):
        logger.info("Fetching last crawl result")

        pre_crawl_online_reports_count = self.get_online_reports_count()
        pre_crawl_offline_reports_count = self.get_offline_reports_count()
        pre_crawl_finished_reports_count = self.get_finished_reports_count()

        try:
            logger.info("Fetching reports")
            reports = self.api_service.get_reports()

            logger.info(f"{len(reports)} reports fetched")
            self.report_repository.update_or_create_all(reports)
            self.meta_repository.update_many({"is_online": False}, Meta.report_id.notin_(extract_ids(reports)), Meta.is_online == True)
        except KeyboardInterrupt:
            raise
        except:
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            self.crawl_result_repository.create(CrawlResult(
                timestamp=datetime.now(),
                successful=False,
            ))
            return

        post_crawl_online_reports_count = self.get_online_reports_count()
        post_crawl_offline_reports_count = self.get_offline_reports_count()
        post_crawl_finished_reports_count = self.get_finished_reports_count()

        added_reports_count = post_crawl_online_reports_count - pre_crawl_online_reports_count
        removed_reports_count = post_crawl_offline_reports_count - pre_crawl_offline_reports_count
        marked_done_count = post_crawl_finished_reports_count - pre_crawl_finished_reports_count

        lowest_id, highest_id = get_lowest_and_highest_ids(reports)

        crawl_result = CrawlResult(
            timestamp=datetime.now(),
            successful=True,
            total=len(reports),
            added=added_reports_count,
            removed=removed_reports_count,
            marked_done=marked_done_count,
            highest_id=highest_id,
            lowest_id=lowest_id,
        )

        logger.info(f"Saving successful crawl result {crawl_result}")
        self.crawl_result_repository.create(crawl_result)

        logger.info("Running post processors")
        for pp in self.post_processors:
            logger.info(f"Running post processor {pp}")
            pp(self.config, self.report_repository, self.meta_repository, self.crawl_result_repository).process()
