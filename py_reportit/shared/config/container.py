from dependency_injector import containers, providers

from pytz import timezone as pytz_timezone

from py_reportit.shared.config import config
from py_reportit.shared.config.db import Database
from py_reportit.shared.config.requests_session import get_requests_session
from py_reportit.shared.repository.category import CategoryRepository
from py_reportit.shared.repository.category_vote import CategoryVoteRepository
from py_reportit.shared.repository.crawl import CrawlRepository
from py_reportit.shared.repository.crawl_item import CrawlItemRepository
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.shared.repository.user import UserRepository
from py_reportit.crawler.service.crawler import CrawlerService
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.service.geocoder import GeocoderService
from py_reportit.crawler.service.photo import PhotoService
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.crawler.post_processors.twitter_pp import Twitter
from py_reportit.crawler.post_processors.geocode_pp import Geocode
from py_reportit.shared.service.vote_service import VoteService
from py_reportit.shared.service.cache_service import CacheService


post_processors = [Geocode, Twitter]

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Database & session
    db = providers.Singleton(
        Database,
        db_user=config.DB_USER,
        db_password=config.DB_PASSWORD,
        db_host=config.DB_HOST,
        db_port=config.DB_PORT,
        db_database=config.DB_DATABASE,
        log_db=config.LOG_DB
    )

    sessionmaker = providers.Singleton(db.provided.sqlalchemy_sessionmaker)

    requests_session = providers.Resource(get_requests_session, config=config)

    timezone = providers.Factory(pytz_timezone, zone=config.TIMEZONE)

    # Repositories
    report_repository = providers.Factory(ReportRepository)
    meta_repository = providers.Factory(MetaRepository)
    report_answer_repository = providers.Factory(ReportAnswerRepository)
    crawl_repository = providers.Factory(CrawlRepository)
    crawl_item_repository = providers.Factory(CrawlItemRepository)
    category_repository = providers.Factory(CategoryRepository)
    category_vote_repository = providers.Factory(CategoryVoteRepository)
    user_repository = providers.Factory(UserRepository)

    # Services
    cache_service = providers.Singleton(CacheService)
    reportit_service = providers.Factory(
        ReportItService,
        config=config,
        requests_session=requests_session,
        cache_service=cache_service
    )
    geocoder_service = providers.Factory(GeocoderService, config=config, requests_session=requests_session)
    photo_service = providers.Factory(PhotoService, config=config)
    vote_service = providers.Factory(
        VoteService,
        config=config,
        meta_repository=meta_repository,
        category_vote_repository=category_vote_repository,
        category_repository=category_repository
    )

    # Helper function to work around scope limitations with class variables and list comprehension
    # see https://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
    def inflate_post_processors(
        config,
        reportit_service,
        geocoder_service,
        report_repository,
        meta_repository,
        report_answer_repository,
    ):
        return [providers.Factory(
            pp,
            config=config,
            api_service=reportit_service,
            geocoder_service=geocoder_service,
            report_repository=report_repository,
            meta_repository=meta_repository,
            report_answer_repository=report_answer_repository,
        ) for pp in post_processors]

    # PostProcessors
    post_processor_dispatcher = providers.Factory(
        PostProcessorDispatcher,
        post_processors=providers.List(
            *inflate_post_processors(
                config=config,
                reportit_service=reportit_service,
                geocoder_service=geocoder_service,
                report_repository=report_repository,
                meta_repository=meta_repository,
                report_answer_repository=report_answer_repository,
            )
        ),
    )

    # Needed separately because specifically required in bulk geocoding util
    geocode_pp = providers.Factory(
        Geocode,
        config=config,
        api_service=reportit_service,
        geocoder_service=geocoder_service,
        report_repository=report_repository,
        meta_repository=meta_repository,
        report_answer_repository=report_answer_repository,
    )

    crawler_service = providers.Factory(
        CrawlerService,
        config=config,
        api_service=reportit_service,
        photo_service=photo_service,
        report_repository=report_repository,
        meta_repository=meta_repository,
        report_answer_repository=report_answer_repository,
        crawl_repository=crawl_repository,
        crawl_item_repository=crawl_item_repository,
        timezone=timezone
    )

def build_container_for_crawler() -> Container:
    container = Container()

    container.config.from_dict(config)

    container.wire(modules=["__main__", ".py_reportit", ".celery.tasks"], from_package="py_reportit.crawler")

    return container
