from dependency_injector.wiring import Provide, Provider, inject
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import Query, Path
from fastapi.responses import FileResponse
from typing import List, Optional
from os import path
from enum import Enum
from datetime import date
from sqlalchemy.orm.session import Session

from py_reportit.shared.config.container import Container
from py_reportit.shared.config import config
from py_reportit.web.schema.report import PagedReportList, Report
from py_reportit.shared.model import *
from py_reportit.shared.repository.report import ReportRepository

description = """
The Report-It Unchained API lets you do awesome stuff based on a repository of all Report-Its submitted to the City of Luxembourg's Report-It system. 🚀

### Reports

You can retrieve reports in three different ways:
- paginated and using filters (recommended)
- all at once (strongly discouraged)
- by ID

Reports are enriched with meta data, such as the **language** (guessed using CLD2, `un` stands for unknown), reverse-geolocated **address data** of the report's location, and **all answers** given by the city.

You should **always** prefer the paginated endpoint over the endpoint that delivers all reports (ie a database dump), unless you **really** want to grab a complete copy of all the data at once.
If you do download the whole database, be warned that it may take some time to process your request.

### Photos

The photo endpoint allows you to download the photo relating to a given report ID. Nonetheless, we strongly encourage you to download photos from the city's website instead (basically, use the url provided in the `photo_url` property).
"""

tags_metadata = [
    {
        "name": "reports",
        "description": "Search, filter and retrieve reports.",
    },
    {
        "name": "photos",
        "description": "Retrieve photos based on report IDs.",
    },
]

def get_session(request: Request):
    sessionmaker = request.app.container.sessionmaker()
    session = sessionmaker()
    try:
        yield session
    finally:
        session.close()

app = FastAPI(
    title="Report-It Unchained API",
    description=description,
    version="0.1.0",
    #terms_of_service="https://zug.lu/rprtt/terms/",
    contact={
        "name": "ZUG - Zentrum fir Urban Gerechtegkeet",
        "url": "https://zug.lu",
        "email": "info@zug.lu",
    },
    #license_info={
    #    "name": "Apache 2.0",
    #    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    #},
    openapi_tags=tags_metadata,
)

class ReportState(str, Enum):
    ALL = "all"
    ACCEPTED = "accepted"
    FINISHED = "finished"

class PhotoState(str, Enum):
    ALL = "all"
    WITH_PHOTO = "with"
    WITHOUT_PHOTO = "without"

@app.get("/reports", response_model=PagedReportList, tags=["reports"])
@inject
def get_reports(
    page: str = Query(None, description="The page to retrieve for the paginated query."),
    page_size: int = Query(50, description="The amount of reports per page."),
    sort_by: str = Query('id', description="The field to sort by."),
    asc: bool = Query(False, description="Whether or not to sort reports in ascending order."),
    status: Optional[ReportState] = Query(ReportState.ALL, description="Filter reports based on their status."),
    photo: Optional[PhotoState] = Query(PhotoState.ALL, description="Filter reports based on whether or not they have photos."),
    after: Optional[date] = Query(None, description="Only return reports created after this date"),
    before: Optional[date] = Query(None, description="Only return reports created before this date"),
    street: Optional[str] = Query(None, description="The street to search for."),
    neighbourhood: Optional[str] = Query(None, description="The neighbourhood to search for."),
    postcode: Optional[int] = Query(None, description="The postcode to search for."),
    search_text: Optional[str] = Query(None, description="Only reports matching the given search text in their title or description will be returned."),
    report_repository_provider: Provider = Depends(Provide[Container.report_repository.provider]),
    session: Session = Depends(get_session)
):
    """
    Make queries for paginated and filtered reports.
    \f
    :param page: The page to retrieve for the paginated query..
    """
    report_repository: ReportRepository = report_repository_provider(session=session)

    boxed_page_size = max(1, min(100, page_size))

    and_q = []
    or_q = []

    if status == ReportState.ACCEPTED:
        and_q.append(report.Report.status=="accepted")
    elif status == ReportState.FINISHED:
        and_q.append(report.Report.status=="finished")

    if photo == PhotoState.WITH_PHOTO:
        and_q.append(report.Report.photo_url!=None)
    elif photo == PhotoState.WITHOUT_PHOTO:
        and_q.append(report.Report.photo_url==None)

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

    paged_reports_with_count = report_repository.get_paged(
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

@app.get("/reports/all", response_model=List[Report], tags=["reports"])
@inject
def get_reports(
    report_repository_provider: Provider = Depends(Provide[Container.report_repository.provider]),
    session: Session = Depends(get_session)
):
    """
    Retrieve all reports in the system, basically a database dump.
    **Using this endpoint is strongly discouraged.** Please consider using the paginated and filtered endpoint instead!
    """
    report_repository: ReportRepository = report_repository_provider(session=session)
    return report_repository.get_all()

@app.get("/reports/{reportId}", response_model=Report, tags=["reports"])
@inject
def get_report(
    reportId: int = Path(None, description="The ID of the report to retrieve"),
    report_repository_provider: Provider = Depends(Provide[Container.report_repository.provider]),
    session: Session = Depends(get_session)
):
    """
    Retrieve the report related to a given ID.
    \f
    :param reportId: The report ID
    """
    report_repository: ReportRepository = report_repository_provider(session=session)
    report = report_repository.get_by_id(reportId)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report with id {reportId} does not exist")
    return report


@app.get("/photos/{reportId}", tags=["photos"])
async def get_photo(reportId: int = Path(None, description="The report ID for which the photo should be retrieved")):
    """
    Retrieve the photo related to a given report ID.
    \f
    :param reportId: The related report ID
    """
    photo_filename = f"{config.get('PHOTO_DOWNLOAD_FOLDER')}/{reportId}.jpg"
    if not path.isfile(photo_filename):
        raise HTTPException(status_code=404, detail=f"No photo found for report with id {reportId}")
    return FileResponse(photo_filename)

container = Container()

container.config.from_dict(config)

container.wire(modules=[__name__])

app.container = container
