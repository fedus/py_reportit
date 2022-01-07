import logging, sys

from datetime import datetime, timedelta

from py_reportit.shared.model.crawl_result import CrawlResult
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.meta import Meta
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.crawl_result import CrawlResultRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.util.reportit_utils import extract_ids, get_lowest_and_highest_ids

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 post_processor_dispatcher: PostProcessorDispatcher,
                 api_service: ReportItService,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 report_answer_repository: ReportAnswerRepository,
                 crawl_result_repository: CrawlResultRepository,
                 ):
        self.config = config
        self.post_processors = post_processor_dispatcher.post_processors
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.report_answer_repository = report_answer_repository
        self.crawl_result_repository = crawl_result_repository
        self.api_service = api_service

    def get_online_reports_count(self) -> int:
        return self.meta_repository.count_by(Meta.is_online==True)

    def get_offline_reports_count(self) -> int:
        return self.meta_repository.count_by(Meta.is_online==False)

    def get_finished_reports_count(self) -> int:
        return self.report_repository.count_by(Report.status=="finished")

    def get_report_ids_since_crawl(self, crawl: CrawlResult) -> list[int]:
        return self.report_repository.get_ids_by(Report.id >= crawl.lowest_id)

    def get_reports_since_crawl(self, crawl: CrawlResult) -> list[Report]:
        return self.report_repository.get_by(Report.id >= crawl.lowest_id)

    @staticmethod
    def filter_updated_reports(existing_reports: list[Report], new_reports: list[Report]) -> list[Report]:
        get_existing_report = lambda new_report: next(filter(lambda existing_report: existing_report.id == new_report.id, existing_reports), None)
        report_is_new_or_updated = lambda new_report: get_existing_report(new_report).updated_at < new_report.updated_at if get_existing_report(new_report) else True
        return list(filter(lambda report: report_is_new_or_updated(report), new_reports))

    def get_new_and_deleted_report_count(self, pre_crawl_ids: list[int], crawled_ids: list[int]) -> tuple[int]:
        added_count = len(list(set(crawled_ids) - set(pre_crawl_ids)))
        removed_count = len(list(set(pre_crawl_ids) - set(crawled_ids)))
        return (added_count, removed_count)

    def crawl(self):
        logger.info("Fetching last crawl result")

        pre_crawl_finished_reports_count = self.get_finished_reports_count()

        logger.info("Fetching most recent successful crawl")
        last_successful_crawl = self.crawl_result_repository.get_most_recent_successful_crawl()

        pre_crawl_reports = []
        pre_crawl_ids = []
        new_or_updated_reports = []

        if last_successful_crawl:
            logger.info("Found most recent successful crawl, fetching reports of last crawl")
            pre_crawl_reports = self.get_reports_since_crawl(last_successful_crawl)
            pre_crawl_ids = extract_ids(pre_crawl_reports)

        try:
            logger.info("Fetching reports")

            recent_ids = self.report_repository.get_ids_by(Report.created_at > datetime.today() - timedelta(days=int(self.config.get("FETCH_REPORTS_OF_LAST_DAYS"))))

            if not recent_ids:
                recent_ids = self.report_repository.get_latest_ids(int(self.config.get("FETCH_REPORTS_FALLBACK_AMOUNT")))

            if not recent_ids:
                recent_ids = [int(self.config.get("FETCH_REPORTS_FALLBACK_START_ID"))]

            combined_ids = recent_ids + list(range(recent_ids[-1] + 1, recent_ids[-1] + 1 + int(self.config.get("FETCH_REPORTS_LOOKAHEAD_AMOUNT"))))

            reports = self.api_service.get_bulk_reports(combined_ids)

            logger.info(f"{len(reports)} reports fetched")
            new_or_updated_reports = self.filter_updated_reports(pre_crawl_reports, reports) # Make compatible with new crawl technique
            self.report_repository.update_or_create_all(reports)
            for report in reports:
                self.report_answer_repository.update_or_create_all(report.answers)
            self.meta_repository.update_many({"is_online": False}, Meta.report_id.notin_(extract_ids(reports)), Meta.is_online == True) # remove
        except KeyboardInterrupt:
            raise
        except:
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            self.crawl_result_repository.create(CrawlResult(
                timestamp=datetime.now(),
                successful=False,
            ))
            return

        logger.info("%d new or modified reports found", len(new_or_updated_reports))

        post_crawl_finished_reports_count = self.get_finished_reports_count()

        added_reports_count, removed_reports_count = self.get_new_and_deleted_report_count(pre_crawl_ids, extract_ids(reports))
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
            pp.process(new_or_updated_reports)
