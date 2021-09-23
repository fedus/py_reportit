import sys, logging, sched, signal

from time import time, sleep
from datetime import datetime
from py_reportit.shared.model import *
from py_reportit.shared.repository.crawl_result import CrawlResultRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.crawler.service.crawler import CrawlerService

from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.shared.config import config
from py_reportit.shared.config.db import SessionLocal
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.crawler.post_processors import post_processors

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(config.get("LOG_LEVEL"))

logger.info(f"py_reportit started at {datetime.now()}")

do_shutdown = False

Session = SessionLocal

def run():
    logger.info(f"Starting crawl at {datetime.now()}")
    with Session() as session:
        crawler = CrawlerService(
            config,
            post_processors,
            ReportRepository(session),
            MetaRepository(session),
            ReportAnswerRepository(session),
            CrawlResultRepository(session),
            ReportItService(config)
        )

        try:
            crawler.crawl()
        except KeyboardInterrupt:
            raise
        except:
            logger.error("Error during crawl: ", sys.exc_info()[0])

    logger.info("Crawl finished")

if config.get("ONE_OFF"):
    logger.info("Running one-off crawl")
    run()
else:
    def exit_gracefully(signum, frame):
        global do_shutdown
        print('Received:', signum)
        do_shutdown = True
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    crawl_interval_seconds = float(config.get("CRAWL_INTERVAL_MINUTES")) * 60
    logger.info("Running crawl every %f seconds", crawl_interval_seconds)
    s = sched.scheduler(time, sleep)
    run()
    while not do_shutdown:
        s.enter(crawl_interval_seconds, 1, run)
        s.run()

logger.info("Exiting")