import logging

from datetime import datetime
from py_reportit.repository.crawl_result import CrawlResultRepository
from py_reportit.repository.meta import MetaRepository
from py_reportit.service.crawler import CrawlerService

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

crawler = CrawlerService(
    config,
    post_processors,
    ReportRepository(session),
    MetaRepository(session),
    CrawlResultRepository(session),
    ReportItService(config)
)

crawler.crawl()

session.close()
logger.info("Exiting")