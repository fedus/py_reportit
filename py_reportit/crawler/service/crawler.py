from __future__ import annotations

import logging, sys, random

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from requests.models import HTTPError

from py_reportit.crawler.celery.tasks import chained_crawl
from py_reportit.shared.model.report import Report
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.util.reportit_utils import extract_ids, filter_reports_by_state, generate_random_times_between, format_time, to_utc

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 api_service: ReportItService,
                 photo_service: PhotoService,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 report_answer_repository: ReportAnswerRepository,
                 ):
        self.config = config
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.report_answer_repository = report_answer_repository
        self.api_service = api_service
        self.photo_service = photo_service

    @staticmethod
    def filter_updated_reports(existing_reports: list[Report], new_reports: list[Report]) -> list[Report]:
        get_existing_report = lambda new_report: next(filter(lambda existing_report: existing_report.id == new_report.id, existing_reports), None)
        report_is_new_or_updated = lambda new_report: get_existing_report(new_report).updated_at < new_report.updated_at if get_existing_report(new_report) else True
        return list(filter(lambda report: report_is_new_or_updated(report), new_reports))

    def get_new_and_deleted_report_count(self, pre_crawl_ids: list[int], crawled_ids: list[int]) -> tuple[int]:
        added_count = len(list(set(crawled_ids) - set(pre_crawl_ids)))
        removed_count = len(list(set(pre_crawl_ids) - set(crawled_ids)))
        return (added_count, removed_count)

    def get_recent_reports(self, session: Session) -> list[Report]:
        recent_reports = self.report_repository.get_by(session, Report.created_at > datetime.today() - timedelta(days=int(self.config.get("FETCH_REPORTS_OF_LAST_DAYS"))))

        if not recent_reports:
            recent_reports = self.report_repository.get_latest(session, int(self.config.get("FETCH_REPORTS_FALLBACK_AMOUNT")))

        if not recent_reports:
            recent_reports = []

        return recent_reports

    def generate_crawl_times(self, amount: int) -> list[datetime]:
        crawl_offset_minutes = random.randint(int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MIN")), int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MAX")))
        crawl_duration_minutes = random.randint(int(self.config.get("CRAWL_DURATION_MINUTES_MIN")), int(self.config.get("CRAWL_DURATION_MINUTES_MAX")))
        crawl_start_time = datetime.now() + timedelta(minutes=crawl_offset_minutes)
        crawl_end_time = crawl_start_time + timedelta(minutes=crawl_duration_minutes)

        logger.info(f"Generating {amount} crawl times from {format_time(crawl_start_time)} to {format_time(crawl_end_time)}. Offset: {crawl_offset_minutes} min, duration: {crawl_duration_minutes} min")
        return generate_random_times_between(crawl_start_time, crawl_end_time, amount)

    @staticmethod
    def log_ids_and_crawl_times(ids_and_crawl_times: list[tuple[int, datetime]]) -> None:
        for id_and_crawl_time in ids_and_crawl_times:
            pretty_time = format_time(id_and_crawl_time[1])
            logger.debug(f"Id {id_and_crawl_time[0]} will be crawled at {pretty_time}")

    def crawl(self, session: Session):
        #new_or_updated_reports = []

        logger.info("Fetching existing recent reports from database ...")
        recent_reports = self.get_recent_reports(session)

        if recent_reports:
            recent_ids = extract_ids(recent_reports)
            closed_recent_report_ids = extract_ids(filter_reports_by_state(recent_reports, True))

            amount_fetched = len(recent_ids)
            amount_closed = len(closed_recent_report_ids)
            amount_remaining = amount_fetched - amount_closed

            logger.info(f"{amount_fetched} recent reports fetched, of which {amount_closed} are already closed, {amount_remaining} remaining")
        else:
            fallback_id = int(self.config.get("FETCH_REPORTS_FALLBACK_START_ID"))
            recent_ids = [fallback_id]
            logger.info(f"No recent reports found in database, beginning crawl from fallback id {fallback_id}")

        lookahead_ids = list(range(recent_ids[-1] + 1, recent_ids[-1] + 1 + int(self.config.get("FETCH_REPORTS_LOOKAHEAD_AMOUNT"))))
        all_combined_ids = random.sample(recent_ids, len(recent_ids)) + lookahead_ids
        relevant_combined_ids = [report_id for report_id in all_combined_ids if report_id not in closed_recent_report_ids]

        crawl_times = self.generate_crawl_times(len(relevant_combined_ids))

        ids_and_crawl_times = list(zip(relevant_combined_ids, crawl_times))

        self.log_ids_and_crawl_times(ids_and_crawl_times)

        last_lat = None
        last_lon = None

        try:
            latest_truncated_report = self.api_service.get_latest_truncated_report()

            last_lat = float(latest_truncated_report.latitude) if latest_truncated_report.latitude else None
            last_lon = float(latest_truncated_report.longitude) if latest_truncated_report.longitude else None

            logger.info(f"Setting stop condition at lat / lon: {last_lat} / {last_lon}")

        except HTTPError:
            logger.warn(f"Encountered error while trying to fetch latest truncated report, not setting stop condition.", exc_info=True)

        try:
            logger.info(f"Processing {len(relevant_combined_ids)} reports, of which {amount_remaining} existing reports")

            first_task_execution_time = ids_and_crawl_times[0][1]

            logger.info(f"Queueing first crawl task, ETA {format_time(first_task_execution_time)}")

            chained_crawl.apply_async([ids_and_crawl_times, last_lat, last_lon], eta=to_utc(first_task_execution_time))

        except:
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            return
