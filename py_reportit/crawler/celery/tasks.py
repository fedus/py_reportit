from __future__ import annotations

import sys

from arrow import Arrow
from datetime import datetime, timedelta, tzinfo
from dependency_injector.wiring import inject, Provide
from celery import shared_task, Task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session, sessionmaker
from requests.exceptions import RequestException, Timeout
from urllib3.exceptions import MaxRetryError

import py_reportit.crawler.service.crawler as crawler_service
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.shared.model.crawl_item import CrawlItemState
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.crawler.util.reportit_utils import filter_pp,\
    generate_random_times_between, is_last_in_reports_data, pretty_format_time

logger = get_task_logger(__name__)


class DBTask(Task):

    def __init__(self, session_maker: sessionmaker = Provide["sessionmaker"]):
        self.session_maker = session_maker
        self._session: Session | None = None

    def after_return(self, *args, **kwargs):
        if self._session is not None:
            logger.debug("Closing session")
            self._session.close()

    @property
    def session(self):
        if self._session is None:
            logger.debug("Opening session ...")
            self._session = self.session_maker()

        logger.debug("Returning session")
        return self._session


@shared_task(name="tasks.chained_crawl", base=DBTask, bind=True)
@inject
def chained_crawl(
    self,
    config: dict = Provide['config'],
    crawler: crawler_service.CrawlerService = Provide['crawler_service'],
    api_service: ReportItService = Provide['reportit_service'],
    photo_service: PhotoService = Provide['photo_service'],
    report_repository: ReportRepository = Provide['report_repository'],
    report_answer_repository: ReportAnswerRepository = Provide['report_answer_repository']
) -> None:
    current_crawl = crawler.get_active_crawl(self.session)

    if not current_crawl:
        logger.error("Worker found no active crawl! Aborting")
        return

    current_crawl_item = crawler.get_next_waiting_crawl_item(self.session, current_crawl)

    if not current_crawl_item:
        logger.error(f"Expected crawl item to process, but none found. Crawl id: {current_crawl.id}. Aborting")
        return

    current_crawl_item.state = CrawlItemState.PROCESSING
    self.session.commit()

    current_report_id = current_crawl_item.report_id

    logger.info(f"Processing report with id {current_report_id}")
    logger.debug(f"Scheduled for: {current_crawl_item.scheduled_for}")

    try:
        existing_report = report_repository.get_by_id(self.session, current_report_id)

        fetched_report = api_service.get_report_with_answers(
            current_report_id,
            existing_report,
            current_crawl.reports_data,
            photo_service.process_base64_photo_if_not_downloaded_yet,
        )

        report_repository.update_or_create(self.session, fetched_report)
        report_answer_repository.update_or_create_all(self.session, fetched_report.answers)

        current_crawl_item.report_found = True
        current_crawl_item.state = CrawlItemState.SUCCESS

        logger.info(f"Successfully processed report with id {current_report_id}, title: {fetched_report.title}")

        run_post_processors.delay(immediate_run=True)

        if is_last_in_reports_data(fetched_report, current_crawl.reports_data):
            logger.info(f"Stop condition hit at report with id {current_report_id}, not queueing next crawl")

            current_crawl_item.stop_condition_hit = True
            crawler.set_skip_remaining_items(self.session, current_crawl_item)
            self.session.commit()

            return

    except ReportNotFoundException:
        current_crawl_item.report_found = False
        current_crawl_item.state = CrawlItemState.SUCCESS
        logger.info(f"No report found with id {current_report_id}, skipping. (This can hide a failed nonce verification!)")
    except Timeout or MaxRetryError:
        current_crawl_item.state = CrawlItemState.FAILURE
        logger.warn(f"Retrieval of report with id {current_report_id} timed out "
                    f"after {config.get('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds or max retries reached, skipping")
    except RequestException:
        current_crawl_item.state = CrawlItemState.FAILURE
        logger.warn(f"Retrieval of report with id {current_report_id} failed, skipping", exc_info=True)
    except (Exception,):
        current_crawl_item.state = CrawlItemState.FAILURE
        logger.error(f"Error while trying to fetch report with id {current_report_id}, skipping", exc_info=True)

    current_crawl_item.stop_condition_hit = False
    self.session.commit()

    next_crawl_item = crawler.get_next_waiting_crawl_item(self.session, current_crawl)

    if not next_crawl_item:
        current_crawl.current_task_id = None
        self.session.commit()
        logger.info(f"No more reports in queue, crawl finished without hitting stop condition.")
        return

    next_task_execution_report_id = next_crawl_item.report_id
    next_task_execution_time = next_crawl_item.scheduled_for

    logger.info(f"Scheduling next crawl for report id {next_task_execution_report_id} at "
                f"{pretty_format_time(next_task_execution_time)}")

    done_items = len(current_crawl.items) - len(current_crawl.waiting_items)
    percentage_done = done_items / len(current_crawl.items) * 100
    percentage_done_rounded = round(percentage_done, 2)

    logger.info(f"{len(current_crawl.waiting_items)} of {len(current_crawl.items)} items remaining, "
                f"{percentage_done_rounded}% done")
    logger.info("\n" + crawler.generate_time_graph_for_crawl(current_crawl))

    next_task = chained_crawl.apply_async(eta=next_task_execution_time)

    current_crawl.current_task_id = next_task.id

    self.session.commit()


@shared_task(name="tasks.launch_chained_crawl", base=DBTask, bind=True)
@inject
def launch_chained_crawl(
    self,
    immediate: bool = False,
    crawler: crawler_service.CrawlerService = Provide['crawler_service'],
    timezone: tzinfo = Provide['timezone']
) -> None:
    logger.info(f"Starting crawl scheduler at {datetime.now(timezone)}")

    try:
        crawler.crawl(self.session, immediate=immediate)
    except (Exception,):
        logger.error("Error during crawl: ", sys.exc_info()[0])

    logger.info("Crawl scheduler finished")


@shared_task(name="tasks.schedule_crawl")
@inject
def schedule_crawl(offset_minutes_min: int, offset_minutes_max: int, timezone: tzinfo = Provide["timezone"]) -> None:
    logger.debug(f"Generating start time for next crawl, offset min: {offset_minutes_min} max: {offset_minutes_max}")

    current_base_time = Arrow.now(timezone)
    earliest_start_time = current_base_time + timedelta(minutes=offset_minutes_min)
    latest_start_time = current_base_time + timedelta(minutes=offset_minutes_max)

    logger.debug(f"Generating random start time between {pretty_format_time(earliest_start_time)} and"
                 f"{pretty_format_time(latest_start_time)}")

    next_crawl_time = generate_random_times_between(earliest_start_time, latest_start_time, 1)[0]

    logger.info(f"Crawl scheduled to begin at {pretty_format_time(next_crawl_time)} (offsets were min:"
                f"{offset_minutes_min} max: {offset_minutes_max})")

    launch_chained_crawl.apply_async(eta=next_crawl_time)


@shared_task(name="tasks.post_processors", base=DBTask, bind=True)
@inject
def run_post_processors(
        self,
        immediate_run: bool = False,
        pp_dispatcher: PostProcessorDispatcher = Provide["post_processor_dispatcher"]
) -> None:
    logger.info(f"Running post processors (immediate run: {immediate_run})")

    for pp in filter_pp(pp_dispatcher.post_processors, immediate_run):
        logger.info(f"Running post processor {pp}")
        pp.process(self.session, [])  # TODO: Provide new or updated reports (not necessary with current post procs)
