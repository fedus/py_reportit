from functools import reduce
from fastapi import FastAPI, Depends, HTTPException
from fastapi.params import Query
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from os import path
from enum import Enum

from py_reportit.shared.config import config
from py_reportit.shared.config.db import SessionLocal
from py_reportit.web.schema.report import PagedReportList, Report
from py_reportit.shared.model import *
from py_reportit.shared.repository.report import ReportRepository

app = FastAPI()

class SearchTextColumn(str, Enum):
    title = "title"
    description = "description"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/reports", response_model=PagedReportList)
def get_reports(
    page: str = None,
    page_size: int = 50,
    sort_by: str = 'id',
    asc: bool = False,
    street: Optional[str] = None,
    neighbourhood: Optional[str] = None,
    postcode: Optional[int] = None,
    search_text: Optional[str] = None,
    db: Session = Depends(get_db)
):
    boxed_page_size = max(1, min(100, page_size))

    and_q = []
    or_q = []

    if street:
        and_q.append(report.Report.meta.has(meta.Meta.address_street.like(f'%{street}%')))

    if neighbourhood:
        and_q.append(report.Report.meta.has(meta.Meta.address_neighbourhood.like(f'%{neighbourhood}%')))

    if postcode:
        and_q.append(report.Report.meta.has(meta.Meta.address_postcode == postcode))

    if search_text:
        search_attrs = list(map(lambda search_attr: report.Report.__dict__[search_attr], ["title", "description"]))
        or_q = list(map(lambda col: col.like(f'%{search_text}%'), search_attrs))

    paged_reports_with_count = ReportRepository(db).get_paged(
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

@app.get("/reports/all", response_model=List[Report])
def get_reports(db: Session = Depends(get_db)):
    return ReportRepository(db).get_all()

@app.get("/reports/{reportId}", response_model=Report)
def get_report(reportId: int, db: Session = Depends(get_db)):
    report = ReportRepository(db).get_by_id(reportId)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report with id {reportId} does not exist")
    return report


@app.get("/photos/{reportId}")
async def get_photo(reportId: int):
    photo_filename = f"{config.get('PHOTO_DOWNLOAD_FOLDER')}/{reportId}.jpg"
    if not path.isfile(photo_filename):
        raise HTTPException(status_code=404, detail=f"No photo found for report with id {reportId}")
    return FileResponse(photo_filename)
