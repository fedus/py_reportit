import logging

from py_reportit.service.reportit_api import ReportItService
from py_reportit.config import config
from py_reportit.config.db import engine
from py_reportit.repository.report import ReportRepository
from py_reportit.post_processors import post_processors
from sqlalchemy.orm import Session

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(logging.DEBUG)

session = Session(engine)
report_repository = ReportRepository(session)
api_service = ReportItService(config)


reports = api_service.get_reports()
report_repository.update_or_create_all(reports)

for pp in post_processors:
    pp(config, report_repository).process()

session.commit()
session.close()
