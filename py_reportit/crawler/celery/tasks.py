from __future__ import annotations

from datetime import datetime
from dependency_injector.wiring import inject, Provide
from celery import shared_task
from celery.utils.log import get_task_logger
from requests.exceptions import RequestException, Timeout

from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService, ReportNotFoundException
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.util.reportit_utils import positions_are_rougly_equal, format_time, to_utc

logger = get_task_logger(__name__)

@shared_task
@inject
def chained_crawl(
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

        report_repository.update_or_create(fetched_report)
        report_answer_repository.update_or_create_all(fetched_report.answers)

        logger.info(f"Successfully processed report with id {current_report_id}, title: {fetched_report.title}")

        if positions_are_rougly_equal(fetched_report.latitude, fetched_report.longitude, stop_at_lat, stop_at_lon, 5):
            logger.info(f"Stop condition hit at report with id {current_report_id}, not queueing next crawl")
        elif len(ids_and_crawl_times) == 1:
            logger.info(f"No more reports in queue, crawl finished without hitting stop condition.")
        else:
            popped_ids_and_crawl_times = ids_and_crawl_times[1:]
            next_task_execution_report_id = popped_ids_and_crawl_times[0][0]
            next_task_execution_time = popped_ids_and_crawl_times[0][1]
            logger.info(f"{len(popped_ids_and_crawl_times)} crawls remaining, scheduling crawl for report id {next_task_execution_report_id} at {format_time(next_task_execution_time)}")
            chained_crawl.apply_async([popped_ids_and_crawl_times, stop_at_lat, stop_at_lon], eta=to_utc(next_task_execution_time))

    except ReportNotFoundException:
        logger.info(f"No report found with id {current_report_id}, skipping.")
    except Timeout:
        logger.warn(f"Retrieval of report with id {current_report_id} timed out after {config('FETCH_REPORTS_TIMEOUT_SECONDS')} seconds, skipping")
    except RequestException:
        logger.warn(f"Retrieval of report with id {current_report_id} failed, skipping", exc_info=True)
    except:
        logger.error(f"Error while trying to fetch report with id {current_report_id}, skipping", exc_info=True)

    return
