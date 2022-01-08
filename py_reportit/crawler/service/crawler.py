import logging, sys

from datetime import datetime, timedelta

from py_reportit.shared.model.report import Report
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.util.reportit_utils import extract_ids, filter_reports_by_state

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 post_processor_dispatcher: PostProcessorDispatcher,
                 api_service: ReportItService,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 report_answer_repository: ReportAnswerRepository,
                 ):
        self.config = config
        self.post_processors = post_processor_dispatcher.post_processors
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.report_answer_repository = report_answer_repository
        self.api_service = api_service

    def get_finished_reports_count(self) -> int:
        return self.report_repository.count_by(Report.status=="finished")

    @staticmethod
    def filter_updated_reports(existing_reports: list[Report], new_reports: list[Report]) -> list[Report]:
        get_existing_report = lambda new_report: next(filter(lambda existing_report: existing_report.id == new_report.id, existing_reports), None)
        report_is_new_or_updated = lambda new_report: get_existing_report(new_report).updated_at < new_report.updated_at if get_existing_report(new_report) else True
        return list(filter(lambda report: report_is_new_or_updated(report), new_reports))

    def get_new_and_deleted_report_count(self, pre_crawl_ids: list[int], crawled_ids: list[int]) -> tuple[int]:
        added_count = len(list(set(crawled_ids) - set(pre_crawl_ids)))
        removed_count = len(list(set(pre_crawl_ids) - set(crawled_ids)))
        return (added_count, removed_count)

    def get_recent_reports(self) -> list[Report]:
        recent_reports = self.report_repository.get_by(Report.created_at > datetime.today() - timedelta(days=int(self.config.get("FETCH_REPORTS_OF_LAST_DAYS"))))

        if not recent_reports:
            recent_reports = self.report_repository.get_latest(int(self.config.get("FETCH_REPORTS_FALLBACK_AMOUNT")))

        if not recent_reports:
            recent_reports = []

        return recent_reports

    def crawl(self):
        logger.info("Fetching last crawl result")

        new_or_updated_reports = []
        recent_reports = self.get_recent_reports()

        if recent_reports:
            recent_ids = extract_ids(recent_reports)
            closed_recent_report_ids = extract_ids(filter_reports_by_state(recent_reports, True))
        else:
            recent_ids = [int(self.config.get("FETCH_REPORTS_FALLBACK_START_ID"))]

        all_combined_ids = recent_ids + list(range(recent_ids[-1] + 1, recent_ids[-1] + 1 + int(self.config.get("FETCH_REPORTS_LOOKAHEAD_AMOUNT"))))
        relevant_combined_ids = [report_id for report_id in all_combined_ids if report_id not in closed_recent_report_ids]

        try:
            logger.info("Fetching reports")

            reports = self.api_service.get_bulk_reports(relevant_combined_ids)

            logger.info(f"{len(reports)} reports fetched")
            new_or_updated_reports = self.filter_updated_reports(recent_reports, reports)

            self.report_repository.update_or_create_all(reports)

            for report in reports:
                self.report_answer_repository.update_or_create_all(report.answers)

        except KeyboardInterrupt:
            raise

        except:
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            return

        logger.info("%d new or modified reports found", len(new_or_updated_reports))

        logger.info("Running post processors")
        for pp in self.post_processors:
            logger.info(f"Running post processor {pp}")
            pp.process(new_or_updated_reports)
