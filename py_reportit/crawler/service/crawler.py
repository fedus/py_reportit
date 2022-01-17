import logging, sys

from datetime import datetime, timedelta
from time import sleep
from typing import Callable, Optional
from requests.models import HTTPError
from requests.exceptions import RequestException, Timeout

from py_reportit.crawler.celery.tasks import add
from py_reportit.shared.model.report import Report
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.util.reportit_utils import extract_ids, filter_reports_by_state, reports_are_roughly_equal_by_position

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 post_processor_dispatcher: PostProcessorDispatcher,
                 api_service: ReportItService,
                 photo_service: PhotoService,
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
        self.photo_service = photo_service

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

    def process_report(self, reportId: int) -> Report:
        fetched_report = self.api_service.get_report_with_answers(reportId, self.photo_service.process_base64_photo_if_not_downloaded_yet)

        self.report_repository.update_or_create(fetched_report)
        self.report_answer_repository.update_or_create_all(fetched_report.answers)

        return fetched_report

    def process_bulk_reports(
        self,
        reportIds: list[int],
        stop_condition: Optional[Callable[[Report], bool]] = None,
    ) -> list[Report]:
        logger.info(f"Fetching bulk reports, {reportIds[0]} - {reportIds[-1]}")

        reports = []

        for reportId in reportIds:
            try:
                logger.debug(f"Fetching report with id {reportId}")
                processed_report = self.process_report(reportId)
                reports.append(processed_report)

                if stop_condition and stop_condition(processed_report):
                    logger.info(f"Stop condition hit at report with id {reportId}, stopping bulk crawl")
                    break

                sleep(float(self.config.get("FETCH_REPORTS_BULK_DELAY_SECONDS")))
            except KeyboardInterrupt:
                raise
            except ReportNotFoundException:
                logger.debug(f"No report found with id {reportId}, skipping.")
            except Timeout:
                logger.warn(f"Retrieval of report with id {reportId} timed out after {self.config('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds, skipping")
            except RequestException:
                logger.warn(f"Retrieval of report with id {reportId} failed, skipping", exc_info=True)
            except:
                logger.error(f"Error while trying to fetch report with id {reportId}, skipping", exc_info=True)

        return reports

    def crawl(self):
        new_or_updated_reports = []

        logger.info("Fetching recent reports from database")
        recent_reports = self.get_recent_reports()

        if recent_reports:
            recent_ids = extract_ids(recent_reports)
            closed_recent_report_ids = extract_ids(filter_reports_by_state(recent_reports, True))
            logger.info(f"{len(recent_ids)} recent reports fetched, of which {len(closed_recent_report_ids)} are already closed")
        else:
            fallback_id = int(self.config.get("FETCH_REPORTS_FALLBACK_START_ID"))
            recent_ids = [fallback_id]
            logger.info(f"No recent reports found in database, beginning crawl from fallback id {fallback_id}")

        lookahead_ids = list(range(recent_ids[-1] + 1, recent_ids[-1] + 1 + int(self.config.get("FETCH_REPORTS_LOOKAHEAD_AMOUNT"))))
        all_combined_ids = recent_ids + lookahead_ids
        relevant_combined_ids = [report_id for report_id in all_combined_ids if report_id not in closed_recent_report_ids]

        add.delay(1,1)
        return
        try:
            latest_truncated_report = self.api_service.get_latest_truncated_report()

            crawl_stop_condition = lambda current_report: reports_are_roughly_equal_by_position(current_report, latest_truncated_report, 5)
        except HTTPError:
            logger.warn(f"Encountered error while trying to fetch latest truncated report, not setting stop condition.", exc_info=True)
            crawl_stop_condition = None

        try:
            logger.info(f"Fetching {len(relevant_combined_ids)} reports, of which {len(relevant_combined_ids) - len(lookahead_ids)} existing reports")

            reports = self.process_bulk_reports(relevant_combined_ids, crawl_stop_condition)

            logger.info(f"{len(reports)} actual reports fetched")
            new_or_updated_reports = self.filter_updated_reports(recent_reports, reports)

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
