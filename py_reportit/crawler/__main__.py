"""py_reportit - A Twitter bot tweeting Report-It messages."""

import logging

from datetime import datetime

from py_reportit.crawler.py_reportit import App
from py_reportit.crawler import container, config

logging.basicConfig(encoding='utf-8')
logger = logging.getLogger(f"py_reportit")
logger.setLevel(config.get("LOG_LEVEL"))

logger.info(f"py_reportit started at {datetime.now()}")



if __name__ == "__main__":
    app = App()
    app.container = container
    app.run()
else:
    logger.warn("Main module was imported, but is meant to run as standalone")

logger.info("Exiting")
