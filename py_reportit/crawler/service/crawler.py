from __future__ import annotations

import logging
import random
import sys
from datetime import datetime, timedelta, tzinfo
from typing import Optional

from arrow import Arrow
from requests.models import HTTPError
from sqlalchemy.orm import Session

from py_reportit.crawler.celery.tasks import chained_crawl
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.util.reportit_utils import extract_ids, filter_reports_by_state, \
    generate_random_times_between, generate_time_graph, pretty_format_time
from py_reportit.shared.model.crawl import Crawl
from py_reportit.shared.model.crawl_item import CrawlItem, CrawlItemState
from py_reportit.shared.model.report import Report
from py_reportit.shared.repository.crawl import CrawlRepository
from py_reportit.shared.repository.crawl_item import CrawlItemRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository

logger = logging.getLogger(f"py_reportit.{__name__}")


class CrawlerService:

    def __init__(self,
                 config: dict,
                 api_service: ReportItService,
                 photo_service: PhotoService,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 report_answer_repository: ReportAnswerRepository,
                 crawl_repository: CrawlRepository,
                 crawl_item_repository: CrawlItemRepository,
                 timezone: tzinfo
                 ):
        self.config = config
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.report_answer_repository = report_answer_repository
        self.api_service = api_service
        self.photo_service = photo_service
        self.crawl_repository = crawl_repository
        self.crawl_item_repository = crawl_item_repository
        self.timezone = timezone

    @staticmethod
    def filter_updated_reports(existing_reports: list[Report], new_reports: list[Report]) -> list[Report]:
        get_existing_report = lambda new_report: next(
            filter(lambda existing_report: existing_report.id == new_report.id, existing_reports),
            None
        )

        report_is_new_or_updated = \
            lambda new_report: get_existing_report(
                new_report).updated_at < new_report.updated_at if get_existing_report(new_report) else True

        return list(filter(lambda report: report_is_new_or_updated(report), new_reports))

    def get_active_crawl(self, session: Session) -> Optional[Crawl]:
        crawls = self.crawl_repository.get_by(session, Crawl.finished == False)

        if crawls and len(crawls) > 1:
            logger.error(f"More than one active crawl found ({len(crawls)})! Returning empty list.")
            logger.debug(f"Returned crawls: {crawls}")
            return None

        return crawls[0] if crawls else None

    def create_and_persist_new_crawl(
            self,
            session: Session,
            ids_and_crawl_times: list[tuple[int, Arrow]],
            scheduled_at: Arrow,
            raw_reports_data: Optional[dict],
    ) -> Crawl:
        crawl = Crawl(
            scheduled_at=scheduled_at,
            reports_data=raw_reports_data
        )

        crawl_items = list(
            map(
                lambda id_dt: CrawlItem(
                    report_id=id_dt[0],
                    scheduled_for=id_dt[1]
                ),
                ids_and_crawl_times
            )
        )

        crawl.items = crawl_items

        self.crawl_repository.create(session, crawl)

        return crawl

    def get_next_waiting_crawl_item(self, session: Session, crawl: Crawl) -> Optional[CrawlItem]:
        return self.crawl_item_repository.get_next_waiting(session, crawl.id)

    def set_skip_remaining_items(self, session: Session, last_processed_crawl_item: CrawlItem) -> None:
        self.crawl_item_repository.update_many(
            session,
            {"state": CrawlItemState.SKIPPED},
            CrawlItem.crawl_id == last_processed_crawl_item.crawl_id,
            CrawlItem.state == CrawlItemState.WAITING
        )

    def get_new_and_deleted_report_count(self, pre_crawl_ids: list[int], crawled_ids: list[int]) -> tuple[int, int]:
        added_count = len(list(set(crawled_ids) - set(pre_crawl_ids)))
        removed_count = len(list(set(pre_crawl_ids) - set(crawled_ids)))
        return added_count, removed_count

    def get_recent_reports(self, session: Session) -> list[Report]:
        recent_reports = self.report_repository.get_by(
            session,
            Report.created_at > datetime.today() - timedelta(days=int(self.config.get("FETCH_REPORTS_OF_LAST_DAYS")))
        )

        if not recent_reports:
            recent_reports = self.report_repository.get_latest(
                session,
                int(self.config.get("FETCH_REPORTS_FALLBACK_AMOUNT"))
            )

        if not recent_reports:
            recent_reports = []

        return recent_reports

    def generate_crawl_times(self, amount: int, immediate: bool = False) -> list[Arrow]:
        if immediate:
            crawl_offset_minutes = 0
        else:
            crawl_offset_minutes = random.randint(
                int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MIN")),
                int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MAX"))
            )

        crawl_duration_minutes = random.randint(
            int(self.config.get("CRAWL_DURATION_MINUTES_MIN")),
            int(self.config.get("CRAWL_DURATION_MINUTES_MAX"))
        )

        crawl_start_time = Arrow.now(self.timezone) + timedelta(minutes=crawl_offset_minutes)
        crawl_end_time = crawl_start_time + timedelta(minutes=crawl_duration_minutes)

        logger.info(f"Generating {amount} crawl times from {pretty_format_time(crawl_start_time)} to "
                    f"{pretty_format_time(crawl_end_time)}. Offset: {crawl_offset_minutes} min, "
                    f"duration: {crawl_duration_minutes} min")
        return generate_random_times_between(crawl_start_time, crawl_end_time, amount)

    def generate_time_graph_for_crawl(self, crawl: Crawl) -> str:
        times = list(map(lambda crawl_item: crawl_item.scheduled_for, crawl.items))

        return generate_time_graph(times, 5)

    @staticmethod
    def log_ids_and_crawl_times(ids_and_crawl_times: list[tuple[int, Arrow]]) -> None:
        for id_and_crawl_time in ids_and_crawl_times:
            pretty_time = pretty_format_time(id_and_crawl_time[1])
            logger.debug(f"Id {id_and_crawl_time[0]} will be crawled at {pretty_time} ({id_and_crawl_time[1]})")

    def crawl(self, session: Session, immediate: bool = False):
        logger.info("Fetching existing recent reports from database ...")
        recent_reports = self.get_recent_reports(session)

        closed_recent_report_ids = []
        amount_remaining = 0

        if recent_reports:
            recent_ids = extract_ids(recent_reports)
            closed_recent_report_ids = extract_ids(filter_reports_by_state(recent_reports, True))

            amount_fetched = len(recent_ids)
            amount_closed = len(closed_recent_report_ids)
            amount_remaining = amount_fetched - amount_closed

            logger.info(f"{amount_fetched} recent reports fetched, of which {amount_closed} are already closed, "
                        f"{amount_remaining} remaining")
        else:
            fallback_id = int(self.config.get("FETCH_REPORTS_FALLBACK_START_ID"))
            recent_ids = [fallback_id]
            logger.info(f"No recent reports found in database, beginning crawl from fallback id {fallback_id}")

        recent_ids_without_last = recent_ids[:-1]
        recent_ids_last_as_list = recent_ids[-1:]

        lookahead_ids = list(
            range(recent_ids[-1] + 1, recent_ids[-1] + 1 + int(self.config.get("FETCH_REPORTS_LOOKAHEAD_AMOUNT")))
        )

        # We want to keep the position of the last report in the db at the same position in case it matches the stop
        # condition.
        all_combined_ids = random.sample(
            recent_ids_without_last, len(recent_ids_without_last)
        ) + recent_ids_last_as_list + lookahead_ids

        # In a similar vein, we want to fetch the last report even if it has already been closed, so a potential
        # stop condition can trigger.
        closed_recent_report_ids_without_last = [
            r_id for r_id in closed_recent_report_ids if r_id not in recent_ids_last_as_list
        ]

        relevant_combined_ids = [r_id for r_id in all_combined_ids if r_id not in closed_recent_report_ids_without_last]

        crawl_times = self.generate_crawl_times(len(relevant_combined_ids), immediate=immediate)

        ids_and_crawl_times = list(zip(relevant_combined_ids, crawl_times))

        self.log_ids_and_crawl_times(ids_and_crawl_times)

        try:
            raw_reports_data = self.api_service.get_raw_reports_data()

        except HTTPError:
            logger.warning(f"Encountered error while trying to fetch latest raw reports data",
                           exc_info=True)

        try:
            logger.info(f"Processing {len(relevant_combined_ids)} reports,"
                        f"of which {amount_remaining} existing reports")

            logger.info("Persisting crawl planning to database ...")

            crawl = self.create_and_persist_new_crawl(
                session,
                ids_and_crawl_times,
                Arrow.now(self.timezone),
                raw_reports_data
            )

            next_crawl_item = self.get_next_waiting_crawl_item(session, crawl)

            if not next_crawl_item:
                logger.error("Next crawl item not found! Aborting.")
                return

            first_task_execution_time = next_crawl_item.scheduled_for

            logger.info(f"Queueing first crawl task, ETA {pretty_format_time(first_task_execution_time)}")

            logger.info("\n" + self.generate_time_graph_for_crawl(crawl))

            task = chained_crawl.apply_async(eta=first_task_execution_time)

            crawl.current_task_id = task.id

            session.commit()

        except (Exception,):
            logger.error("Unexpected error during crawl: ", sys.exc_info()[0])
            return
