import sys, logging, sched, signal

from time import time, sleep
from datetime import datetime
from py_reportit.shared.model import *
from py_reportit.shared.repository.crawl_result import CrawlResultRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.crawler.service.crawler import CrawlerService
from py_reportit.crawler.service.geocoder import GeocoderService

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

Session = SessionLocal

class ShutdownException(Exception):
    pass

class App:

    def __init__(self, config, post_processors):
        self.config = config
        self.post_processors = post_processors
        self.scheduler = None
        self.do_shutdown = False

    def execute_crawler(self):
        logger.info(f"Starting crawl at {datetime.now()}")
        with Session() as session:
            crawler = CrawlerService(
                self.config,
                self.post_processors,
                ReportRepository(session),
                MetaRepository(session),
                ReportAnswerRepository(session),
                CrawlResultRepository(session),
                ReportItService(self.config),
                GeocoderService(self.config)
            )

            try:
                crawler.crawl()
            except KeyboardInterrupt:
                raise
            except:
                logger.error("Error during crawl: ", sys.exc_info()[0])

        logger.info("Crawl finished")

    def run(self):
        if self.config.get("ONE_OFF"):
            logger.info("Running one-off crawl")
            self.execute_crawler()
        else:
            signal.signal(signal.SIGINT, self.initiate_shutdown)
            signal.signal(signal.SIGTERM, self.initiate_shutdown)
            crawl_interval_seconds = float(self.config.get("CRAWL_INTERVAL_MINUTES")) * 60
            logger.info("Running crawl every %f seconds", crawl_interval_seconds)
            self.scheduler = sched.scheduler(time, sleep)
            self.execute_crawler()
            while not self.do_shutdown:
                self.scheduler.enter(crawl_interval_seconds, 1, self.execute_crawler)
                deadline = self.scheduler.run(blocking=False)
                try:
                    logger.info(f"Sleeping for {deadline} seconds")
                    sleep(deadline)
                except ShutdownException:
                    pass

    def initiate_shutdown(self, signum, frame):
        logger.info(f'Received: {signum}, initiating shutdown')
        self.do_shutdown = True
        raise ShutdownException

def run_app():
    App(config, post_processors).run()

if __name__ == "__main__":
    run_app()
else:
    logger.warn("Main module was imported, but is meant to run as standalone")

logger.info("Exiting")