"""py_reportit - A Twitter bot tweeting Report-It messages."""

import logging

from datetime import datetime

from py_reportit.crawler import run_app

logger = logging.getLogger(f"py_reportit.{__name__}")

logger.info(f"py_reportit started at {datetime.now()}")

if __name__ == "__main__":
    run_app()
else:
    logger.warn("Main module was imported, but is meant to run as standalone")

logger.info("Exiting")
