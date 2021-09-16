from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import List
from sqlalchemy.orm import Session
from os import path

from py_reportit.shared.config import config
from py_reportit.shared.config.db import SessionLocal
from py_reportit.web.schema.report import Report
from py_reportit.shared.model import *
from py_reportit.shared.repository.report import ReportRepository

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/reports", response_model=List[Report])
def get_reports(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    boxed_limit = max(1, min(100, limit))
    boxed_offset = offset if offset >= 0 else 0
    return ReportRepository(db).get_all(offset=boxed_offset, limit=boxed_limit)

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
