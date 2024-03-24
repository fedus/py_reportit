from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Query, Path, APIRouter
from typing import List, Optional
from datetime import date
from sqlalchemy.orm.session import Session
from enum import Enum

from py_reportit.web.dependencies import get_session
from py_reportit.shared.config.container import Container
from py_reportit.web.schema.report import PagedReportList, Report
from py_reportit.shared.model import *
from py_reportit.shared.repository.report import ReportRepository


class ReportState(str, Enum):
    ALL = "all"
    ACCEPTED = "accepted"
    FINISHED = "finished"

class PhotoState(str, Enum):
    ALL = "all"
    WITH_PHOTO = "with"
    WITHOUT_PHOTO = "without"

router = APIRouter(tags=["reports"], prefix="/reports")

@router.get("/", response_model=PagedReportList)
@inject
def get_reports(
    page: str = Query(None, description="The page to retrieve for the paginated query."),
    page_size: int = Query(50, description="The amount of reports per page."),
    sort_by: str = Query('id', description="The field to sort by."),
    asc: bool = Query(False, description="Whether or not to sort reports in ascending order."),
    status: Optional[ReportState] = Query(ReportState.ALL, description="Filter reports based on their status."),
    photo: Optional[PhotoState] = Query(PhotoState.ALL, description="Filter reports based on whether or not they have photos."),
    service: Optional[str] = Query(None, description="The service in charge of the report"),
    category: Optional[int] = Query(None, description="The category to filter by"),
    after: Optional[date] = Query(None, description="Only return reports created after this date"),
    before: Optional[date] = Query(None, description="Only return reports created before this date"),
    street: Optional[str] = Query(None, description="The street to search for."),
    neighbourhood: Optional[str] = Query(None, description="The neighbourhood to search for."),
    postcode: Optional[int] = Query(None, description="The postcode to search for."),
    search_text: Optional[str] = Query(None, description="Only reports matching the given search text in their title or description (or in any of the answers) will be returned."),
    report_repository: ReportRepository = Depends(Provide[Container.report_repository]),
    session: Session = Depends(get_session)
):
    """
    Make queries for paginated and filtered reports.
    \f
    :param page: The page to retrieve for the paginated query..
    """
    boxed_page_size = max(1, min(100, page_size))

    and_q = []
    or_q = []

    if status == ReportState.ACCEPTED:
        and_q.append(report.Report.status=="accepted")
    elif status == ReportState.FINISHED:
        and_q.append(report.Report.status=="finished")

    if photo == PhotoState.WITH_PHOTO:
        and_q.append(report.Report.has_photo==True)
    elif photo == PhotoState.WITHOUT_PHOTO:
        and_q.append(report.Report.has_photo==False)

    if service:
        and_q.append(report.Report.service==service)

    # 0 might be a legit value
    if category != None:
        and_q.append(report.Report.meta.has(meta.Meta.category==category))

    if after:
        and_q.append(report.Report.created_at>=after)
    if before:
        and_q.append(report.Report.created_at<=before)

    if street:
        and_q.append(report.Report.meta.has(meta.Meta.address_street.like(f'%{street}%')))

    if neighbourhood:
        and_q.append(report.Report.meta.has(meta.Meta.address_neighbourhood.like(f'%{neighbourhood}%')))

    if postcode:
        and_q.append(report.Report.meta.has(meta.Meta.address_postcode == postcode))

    if search_text:
        search_attrs = list(map(lambda search_attr: report.Report.__dict__[search_attr], ["title", "description"]))
        or_q = list(map(lambda col: col.like(f'%{search_text}%'), search_attrs))
        or_q.append(report.Report.answers.any(report_answer.ReportAnswer.text.like(f'%{search_text}%')))

    paged_reports_with_count = report_repository.get_paged(
        session,
        page_size=boxed_page_size,
        page=page,
        by=report.Report.__dict__[sort_by],
        asc=asc,
        and_cond=and_q if len(and_q) else None,
        or_cond=or_q if len(or_q) else None
    )

    paged_reports = paged_reports_with_count["page"];

    return PagedReportList(
        previous=paged_reports.paging.bookmark_previous if paged_reports.paging.has_previous else None,
        next=paged_reports.paging.bookmark_next if paged_reports.paging.has_next else None,
        total_count=paged_reports_with_count["total_count"],
        reports=paged_reports,
    )

@router.get("/all", response_model=List[Report])
@inject
def get_reports(
    report_repository: ReportRepository = Depends(Provide[Container.report_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve all reports in the system, basically a database dump.
    **Using this endpoint is strongly discouraged.** Please consider using the paginated and filtered endpoint instead!
    """
    return report_repository.get_all(session)

@router.get("/{reportId}", response_model=Report)
@inject
def get_report(
    reportId: int = Path(description="The ID of the report to retrieve"),
    report_repository: ReportRepository = Depends(Provide[Container.report_repository]),
    session: Session = Depends(get_session)
):
    """
    Retrieve the report related to a given ID.
    \f
    :param reportId: The report ID
    """
    report = report_repository.get_by_id(session, reportId)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report with id {reportId} does not exist")
    return report
