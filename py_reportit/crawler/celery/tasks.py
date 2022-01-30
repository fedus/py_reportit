from __future__ import annotations

import sys

from datetime import datetime, timedelta
from dependency_injector.wiring import inject, Provide
from celery import shared_task, Task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session, sessionmaker
from requests.exceptions import RequestException, Timeout

import py_reportit.crawler.service.crawler as crawler
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.shared.model.crawl_item import CrawlItemState
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.crawler.util.reportit_utils import filter_pp, generate_random_times_between, positions_are_rougly_equal, pretty_format_time, to_utc

logger = get_task_logger(__name__)

class DBTask(Task):

    def __init__(self, session_maker: sessionmaker = Provide["sessionmaker"]):
        self.session_maker = session_maker
        self._session: Session = None

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
    crawler: crawler.CrawlerService = Provide['crawler_service'],
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

    current_report_id = current_crawl_item.report_id

    logger.info(f"Processing report with id {current_report_id}")

    try:
        fetched_report = api_service.get_report_with_answers(current_report_id, photo_service.process_base64_photo_if_not_downloaded_yet)

        report_repository.update_or_create(self.session, fetched_report)
        report_answer_repository.update_or_create_all(self.session, fetched_report.answers)

        current_crawl_item.report_found = True
        current_crawl_item.state = CrawlItemState.SUCCESS

        logger.info(f"Successfully processed report with id {current_report_id}, title: {fetched_report.title}")

        if positions_are_rougly_equal(
            fetched_report.latitude,
            fetched_report.longitude,
            current_crawl.stop_at_lat,
            current_crawl.stop_at_lon,
            5
        ):
            logger.info(f"Stop condition hit at report with id {current_report_id}, not queueing next crawl")

            current_crawl_item.stop_condition_hit = True
            self.session.commit()

            return

    except ReportNotFoundException:
        current_crawl_item.report_found = False
        current_crawl_item.state = CrawlItemState.SUCCESS
        logger.info(f"No report found with id {current_report_id}, skipping.")
    except Timeout:
        current_crawl_item.state = CrawlItemState.FAILURE
        logger.warn(f"Retrieval of report with id {current_report_id} timed out after {config.get('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds, skipping")
    except RequestException:
        current_crawl_item.state = CrawlItemState.FAILURE
        logger.warn(f"Retrieval of report with id {current_report_id} failed, skipping", exc_info=True)
    except:
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

    logger.info(f"{len(current_crawl.waiting_items)} crawls remaining, scheduling crawl for report id {next_task_execution_report_id} at {pretty_format_time(next_task_execution_time)}")

    next_task = chained_crawl.apply_async(eta=to_utc(next_task_execution_time))

    current_crawl.current_task_id = next_task.id

    self.session.commit()

    run_post_processors.delay(immediate_run=True)

@shared_task(name="tasks.launch_chained_crawl", base=DBTask, bind=True)
@inject
def launch_chained_crawl(
    self,
    crawler: crawler.CrawlerService = Provide['crawler_service'],
) -> None:
    logger.info(f"Starting crawl scheduler at {datetime.now()}")

    try:
        crawler.crawl(self.session)
    except:
        logger.error("Error during crawl: ", sys.exc_info()[0])

    logger.info("Crawl scheduler finished")

@shared_task(name="tasks.schedule_crawl")
def schedule_crawl(offset_minutes_min: int, offset_minutes_max: int) -> None:
    logger.debug(f"Generating start time for next crawl, offset min: {offset_minutes_min} max: {offset_minutes_max}")

    current_base_time = datetime.now()
    earliest_start_time = current_base_time + timedelta(minutes=offset_minutes_min)
    latest_start_time = current_base_time + timedelta(minutes=offset_minutes_max)

    logger.debug(f"Generating random start time between {pretty_format_time(earliest_start_time)} and {pretty_format_time(latest_start_time)}")

    next_crawl_time = generate_random_times_between(earliest_start_time, latest_start_time, 1)[0]

    logger.info(f"Crawl scheduled to begin at {pretty_format_time(next_crawl_time)} (offsets were min: {offset_minutes_min} max: {offset_minutes_max})")

    launch_chained_crawl.apply_async(eta=to_utc(next_crawl_time))

@shared_task(name="tasks.post_processors", base=DBTask, bind=True)
@inject
def run_post_processors(self, immediate_run: bool = False, pp_dispatcher: PostProcessorDispatcher = Provide["post_processor_dispatcher"]) -> None:
    logger.info(f"Running post processors (immediate run: {immediate_run})")

    for pp in filter_pp(pp_dispatcher.post_processors, immediate_run):
        logger.info(f"Running post processor {pp}")
        pp.process(self.session, []) # TODO: Provide new or updated reports (not necessary with current post processors)
