import requests
import logging

from typing import Iterable
from requests.sessions import Session
from string import Template
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(f"py_reportit.{__name__}")

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

def get_requests_session(config: dict) -> Iterable[Session]:
    with requests.Session() as session:
        logger.debug("Opening requests-session")

        def crawler_get(self: requests.Session, url, params={}, **kwargs):
            params["api_key"] = config.get('SCRAPER_API_KEY')
            params["url"] = url
            return self.get(url=config.get('SCRAPER_API_BASE_URL'), params=params, **kwargs)
        
        def crawler_post(self: requests.Session, url, data=None, json=None, params={}, **kwargs):
            params["api_key"] = config.get('SCRAPER_API_KEY')
            params["url"] = url
            return self.post(url=config.get('SCRAPER_API_BASE_URL'), data=data, json=json, params=params, **kwargs)

        if int(config.get("USE_SCRAPER_API", 0)):
            logger.debug("Using Scraper API ...")
            session.crawler_get = crawler_get.__get__(session, requests.Session)
            session.crawler_post = crawler_post.__get__(session, requests.Session)
        else:
            logger.debug("Not using Scraper API")
            session.crawler_get = session.get
            session.crawler_post = session.post

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if int(config.get("USE_PROXY", 0)):
            logger.debug("Setting proxy and disabling SSL cert verification ...")
            proxy_url = Template(config.get("PROXY_URL")).substitute({
                "PROXY_SCHEME": config.get("PROXY_SCHEME"),
                "PROXY_USER": config.get("PROXY_USER"),
                "PROXY_PASS": config.get("PROXY_PASS"),
                "PROXY_HOST": config.get("PROXY_HOST"),
                "PROXY_PORT": config.get("PROXY_PORT"),
            })
            proxies = { "http": proxy_url, "https": proxy_url }
            session.proxies.update(proxies)
            session.verify = False

        yield session
    logger.debug("Closing requests session")
