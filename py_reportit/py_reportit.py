import sys, logging, sched

from time import time, sleep
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

def run():
    logger.info("Starting crawl")
    session = Session(engine)

    crawler = CrawlerService(
        config,
        post_processors,
        ReportRepository(session),
        MetaRepository(session),
        CrawlResultRepository(session),
        ReportItService(config)
    )

    try:
        crawler.crawl()
    except KeyboardInterrupt:
        raise
    except:
        logger.error("Error during crawl: ", sys.exc_info()[0])

    session.close()
    logger.info("Crawl finished")

if config.get("ONE_OFF"):
    logger.info("Running one-off crawl")
    run()
else:
    crawl_interval_seconds = float(config.get("CRAWL_INTERVAL_MINUTES")) * 60
    logger.info("Running crawl every %f seconds", crawl_interval_seconds)
    s = sched.scheduler(time, sleep)
    run()
    while True:
        s.enter(crawl_interval_seconds, 1, run)
        s.run()

logger.info("Exiting")