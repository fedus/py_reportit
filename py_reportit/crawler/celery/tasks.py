from __future__ import annotations

from dependency_injector.wiring import inject, Provide
from celery import shared_task
from celery.utils.log import get_task_logger

from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.shared.model.report import Report
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.util.reportit_utils import positions_are_rougly_equal

logger = get_task_logger(__name__)

@shared_task
@inject
def crawl_single(
    reportId: int,
    last_lat: float,
    last_lon: float,
    api_service: ReportItService = Provide['reportit_service'],
    photo_service: PhotoService = Provide['photo_service'],
    report_repository: ReportRepository = Provide['report_repository'],
    report_answer_repository: ReportAnswerRepository = Provide['report_answer_repository']
) -> Report:
    fetched_report = api_service.get_report_with_answers(reportId, photo_service.process_base64_photo_if_not_downloaded_yet)

    report_repository.update_or_create(fetched_report)
    report_answer_repository.update_or_create_all(fetched_report.answers)

    if positions_are_rougly_equal(fetched_report.latitude, fetched_report.longitude, last_lat, last_lon, 5):
        logger.info(f"Stop condition hit at report with id {reportId}, not queueing next crawl")
    else:
        pass

    return fetched_report

@shared_task
def test(dt):
    print(dt)