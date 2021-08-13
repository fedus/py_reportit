import logging

from datetime import datetime

from py_reportit.service.reportit_api import ReportItService
from py_reportit.config import config
from py_reportit.config.db import engine
from py_reportit.repository.report import ReportRepository
from py_reportit.post_processors import post_processors
from sqlalchemy.orm import Session

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(config.get("LOG_LEVEL"))

logger.info(f"py_reportit started at {datetime.now()}")

session = Session(engine)
report_repository = ReportRepository(session)
api_service = ReportItService(config)

logger.info("Fetching reports")
reports = api_service.get_reports()

logger.info(f"{len(reports)} reports fetched")
report_repository.update_or_create_all(reports)

logger.info("Running post processors")
for pp in post_processors:
    logger.info(f"Running post processor {pp}")
    pp(config, report_repository).process()

session.close()
logger.info("Exiting")