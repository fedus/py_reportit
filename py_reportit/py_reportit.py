import logging

from py_reportit.service.reportit_api import ReportItService
from py_reportit.config import config
from py_reportit.config.post_processors import post_processors_config
from py_reportit.config.db import engine
from py_reportit.repository.report import ReportRepository
from py_reportit.post_processors import post_processors
from sqlalchemy.orm import Session

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

session = Session(engine)
report_repository = ReportRepository(session)
api_service = ReportItService(config)


reports = api_service.get_reports()
report_repository.update_or_create_all(reports)

for pp in post_processors:
    pp(post_processors_config, report_repository).process()

session.commit()
session.close()
