from py_reportit.config.db import engine
from py_reportit.repository.report import ReportRepository
from py_reportit.model.meta import Meta
from py_reportit.model.report import Report
from sqlalchemy.orm import Session

import requests

session = Session(engine)
report_repository = ReportRepository(session)


r = requests.get('https://reportit.vdl.lu/api/get.php')
reports = list(map(lambda rawReport: Report(**rawReport, meta=Meta()), r.json().get('reports')))

#reports = report_repository.get_by_id(20700)

report_repository.update_or_create_all(reports)


session.close()
