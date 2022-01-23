import sys, logging, sched, signal

from time import time, sleep
from datetime import datetime

from dependency_injector.wiring import Provide, inject
from dependency_injector.providers import Resource
from celery.schedules import crontab
from py_reportit.crawler.util.reportit_utils import string_to_crontab_kwargs
from sqlalchemy.orm import sessionmaker

from py_reportit.shared.config.container import build_container_for_crawler
from py_reportit.crawler.celery.celery import create_celery_app
from py_reportit.shared.config.container import Container
from py_reportit.shared.model import *
from py_reportit.crawler.service.crawler import CrawlerService

class ShutdownException(Exception):
    pass

class App:

    @inject
    def __init__(self, config: dict = Provide[Container.config]):
        self.config = config
        self.scheduler = None
        self.do_shutdown = False

    @inject
    def execute_crawler(
        self,
        crawler: CrawlerService = Provide[Container.crawler_service],
        session_maker: sessionmaker = Provide[Container.sessionmaker],
        requests_session_provider: Resource = Provide[Container.requests_session.provider],
    ):
        logger.info(f"Starting crawl at {datetime.now()}")

        try:
            with sessionmaker() as session:
                crawler.crawl(session)
            requests_session_provider.shutdown()
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

container = build_container_for_crawler()

config = container.config()

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(config.get("LOG_LEVEL"))


celery_app = create_celery_app(config)

crontab_args_schedule_crawl = string_to_crontab_kwargs(config.get("START_CRAWL_SCHEDULING_AT"))
logger.info(f"Daily scheduled crawl crontab args: {crontab_args_schedule_crawl}")

crontab_args_post_processors = string_to_crontab_kwargs(config.get("START_POST_PROCESSORS_AT"))
logger.info(f"Daily post processor run crontab args: {crontab_args_post_processors}")

celery_app.conf.beat_schedule = {
    'daily_randomize_schedule': {
        'task': 'tasks.schedule_crawl',
        'schedule': crontab(**crontab_args_schedule_crawl),
        'args': [int(config.get("CRAWL_FIRST_OFFSET_MINUTES_MIN")), int(config.get("CRAWL_FIRST_OFFSET_MINUTES_MAX"))]
    },
    'daily_post_processor_run': {
        'task': 'tasks.post_processors',
        'schedule': crontab(**crontab_args_post_processors),
    },
}

def run_app():
    app = App()
    app.container = container
    app.run()
