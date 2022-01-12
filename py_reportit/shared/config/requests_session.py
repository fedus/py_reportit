import requests
import logging

from typing import Iterable
from requests.sessions import Session

logger = logging.getLogger(f"py_reportit.{__name__}")

def get_requests_session(config: dict) -> Iterable[Session]:
    with requests.Session() as session:
        logger.debug("Opening requests-session")
        logger.info(f"Current User-Agent: {session.headers['User-Agent']}")
        yield session
    logger.debug("Closing requests session")
