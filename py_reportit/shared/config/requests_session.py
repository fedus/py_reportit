import requests
import logging

from typing import Iterable
from requests.sessions import Session
from string import Template

logger = logging.getLogger(f"py_reportit.{__name__}")

def get_requests_session(config: dict) -> Iterable[Session]:
    with requests.Session() as session:
        logger.debug("Opening requests-session")

        if config.get("USE_PROXY", False):
            logger.debug("Setting proxy ...")
            proxy_url = Template(config.get("PROXY_URL")).substitute({
                "PROXY_SCHEME": config.get("PROXY_SCHEME"),
                "PROXY_USER": config.get("PROXY_USER"),
                "PROXY_PASS": config.get("PROXY_PASS"),
                "PROXY_HOST": config.get("PROXY_HOST"),
                "PROXY_PORT": config.get("PROXY_PORT"),
            })
            proxies = { "http": proxy_url, "https": proxy_url }
            session.proxies.update(proxies)
        else:
            logger.info(f"Current User-Agent: {session.headers['User-Agent']}")
        yield session
    logger.debug("Closing requests session")
