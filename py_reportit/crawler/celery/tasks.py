from __future__ import annotations

import sys

from datetime import datetime, timedelta
from dependency_injector.wiring import inject, Provide, Provider
from celery import shared_task, Task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session, sessionmaker
from requests.exceptions import RequestException, Timeout
from dependency_injector.providers import Resource

import py_reportit.crawler.service.crawler as crawler
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.crawler.util.reportit_utils import generate_random_times_between, positions_are_rougly_equal, format_time, to_utc

logger = get_task_logger(__name__)

class DBTask(Task):

    def __init__(self, session_maker: sessionmaker = Provide["sessionmaker"]):
        self.session_maker = session_maker
        self._session: Session = None

    def after_return(self, *args, **kwargs):
        if self._session is not None:
            self._session.close()

    @property
    def session(self):
        if self._session is None:
            self._session = self.session_maker()

        return self._session

@shared_task(name="tasks.chained_crawl", base=DBTask, bind=True)
@inject
def chained_crawl(
    self,
    ids_and_crawl_times: list[tuple[int, datetime]],
    stop_at_lat: float,
    stop_at_lon: float,
    config: dict = Provide['config'],
    api_service: ReportItService = Provide['reportit_service'],
    photo_service: PhotoService = Provide['photo_service'],
    report_repository: ReportRepository = Provide['report_repository'],
    report_answer_repository: ReportAnswerRepository = Provide['report_answer_repository']
) -> None:
    current_report_id = ids_and_crawl_times[0][0]

    logger.info(f"Processing report with id {current_report_id}")

    try:
        fetched_report = api_service.get_report_with_answers(current_report_id, photo_service.process_base64_photo_if_not_downloaded_yet)

        report_repository.update_or_create(self.session, fetched_report)
        report_answer_repository.update_or_create_all(self.session, fetched_report.answers)

        logger.info(f"Successfully processed report with id {current_report_id}, title: {fetched_report.title}")

        if positions_are_rougly_equal(fetched_report.latitude, fetched_report.longitude, stop_at_lat, stop_at_lon, 5):
            logger.info(f"Stop condition hit at report with id {current_report_id}, not queueing next crawl")
            return

    except ReportNotFoundException:
        logger.info(f"No report found with id {current_report_id}, skipping.")
    except Timeout:
        logger.warn(f"Retrieval of report with id {current_report_id} timed out after {config('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds, skipping")
    except RequestException:
        logger.warn(f"Retrieval of report with id {current_report_id} failed, skipping", exc_info=True)
    except:
        logger.error(f"Error while trying to fetch report with id {current_report_id}, skipping", exc_info=True)

    if len(ids_and_crawl_times) == 1:
        logger.info(f"No more reports in queue, crawl finished without hitting stop condition.")
        return

    popped_ids_and_crawl_times = ids_and_crawl_times[1:]
    next_task_execution_report_id = popped_ids_and_crawl_times[0][0]
    next_task_execution_time = popped_ids_and_crawl_times[0][1]

    logger.info(f"{len(popped_ids_and_crawl_times)} crawls remaining, scheduling crawl for report id {next_task_execution_report_id} at {format_time(next_task_execution_time)}")

    chained_crawl.apply_async([popped_ids_and_crawl_times, stop_at_lat, stop_at_lon], eta=to_utc(next_task_execution_time))

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

    logger.debug(f"Generating random start time between {format_time(earliest_start_time)} and {format_time(latest_start_time)}")

    next_crawl_time = generate_random_times_between(earliest_start_time, latest_start_time, 1)[0]

    logger.info(f"Crawl scheduled to begin at {format_time(next_crawl_time)} (offsets were min: {offset_minutes_min} max: {offset_minutes_max})")

    launch_chained_crawl.apply_async(eta=to_utc(next_crawl_time))

@shared_task(name="tasks.post_processors", base=DBTask, bind=True)
@inject
def run_post_processors(self, pp_dispatcher: PostProcessorDispatcher = Provide["post_processor_dispatcher"]) -> None:
    logger.info("Running post processors")

    for pp in pp_dispatcher.post_processors:
        logger.info(f"Running post processor {pp}")
        pp.process(self.session, []) # TODO: Provide new or updated reports (not necessary with current post processors)
