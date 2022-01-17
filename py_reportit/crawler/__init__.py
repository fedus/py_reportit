from __future__ import annotations

import logging

from py_reportit.shared.config.container import build_container_for_crawler
from py_reportit.crawler.py_reportit import App
from py_reportit.crawler.celery.celery import create_celery_app

print(__name__)
container = build_container_for_crawler()

config = container.config()

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(config.get("LOG_LEVEL"))

celery_app = create_celery_app(config.get('CELERY_BROKER'))

def run_app():
    app = App()
    app.container = container
    app.run()
