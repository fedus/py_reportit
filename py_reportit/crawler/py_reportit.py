import logging

from datetime import datetime
from celery import Celery

from dependency_injector.wiring import Provide, inject
from celery.schedules import crontab
from py_reportit.crawler.util.reportit_utils import string_to_crontab_kwargs

from py_reportit.shared.config.container import build_container_for_crawler
from py_reportit.crawler.celery.celery import create_celery_app
from py_reportit.shared.config.container import Container
from py_reportit.shared.model import *


class App:

    @inject
    def __init__(self, celery_app: Celery, config: dict = Provide[Container.config]):
        self.celery_app = celery_app
        self.config = config

    @inject
    def execute_crawler(self):
        logger.info(f"Scheduling one-off crawl at {datetime.now()}")

        self.celery_app.send_task(
            "tasks.schedule_crawl",
            [int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MIN")), int(self.config.get("CRAWL_FIRST_OFFSET_MINUTES_MAX"))]
        )

        logger.info("One-off crawl scheduling finished.")

    def run(self):
        if self.config.get("SPECIAL_RUN_MODE") == "ONE_OFF_CRAWL":
            logger.info("Running one-off crawl task")
            self.execute_crawler()
        elif self.config.get("SPECIAL_RUN_MODE") == "ONE_OFF_PP":
            logger.info("Running one-off pp task")
            self.celery_app.send_task("tasks.post_processors")

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
    app = App(celery_app)
    app.container = container
    app.run()
