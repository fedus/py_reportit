import requests
import logging

from typing import Iterable
from requests.sessions import Session
from string import Template
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse, parse_qs, ParseResult
from random import choice

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

        def crawler_get(self: requests.Session, url: str, params={}, **kwargs):
            parsed_scraper_url = urlparse(get_random_scraper_api_from_config(config))
            scraper_args = get_scraper_base_url_and_params(url, params, parsed_scraper_url)
            return self.get(url=scraper_args.get("base_url"), params=scraper_args.get("params"), **kwargs)

        def crawler_post(self: requests.Session, url: str, data=None, json=None, params={}, **kwargs):
            parsed_scraper_url = urlparse(get_random_scraper_api_from_config(config))
            scraper_args = get_scraper_base_url_and_params(url, params, parsed_scraper_url)
            return self.post(url=scraper_args.get("base_url"), data=data, json=json, params=scraper_args.get("params"), **kwargs)

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

def get_random_scraper_api_from_config(config: dict) -> str:
    return choice(config.get('SCRAPER_API_BASE_URLS').split(","))

def get_scraper_base_url_and_params(url: str, params: dict, parsed_scraper_url: ParseResult) -> dict:
    processed_params = {**params, **parse_qs(parsed_scraper_url.query)}
    processed_params["url"] = url
    scraper_base_url = f"{parsed_scraper_url.scheme}://{parsed_scraper_url.netloc}{parsed_scraper_url.path}"
    return { "params": processed_params, "base_url": scraper_base_url }
