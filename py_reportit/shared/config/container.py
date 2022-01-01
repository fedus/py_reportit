from typing import Callable

from dependency_injector import containers, providers

from py_reportit.shared.config.db import Database, get_session
from py_reportit.shared.repository.report import ReportRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.shared.repository.crawl_result import CrawlResultRepository
from py_reportit.crawler.service.crawler import CrawlerService
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.crawler.service.geocoder import GeocoderService
from py_reportit.crawler.post_processors.abstract_pp import PostProcessorDispatcher
from py_reportit.crawler.post_processors import post_processors
from py_reportit.crawler.post_processors.geocode_pp import Geocode


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
        log_level=config.LOG_LEVEL
    )

    session = providers.Resource(get_session, database=db)

    # Repositories
    report_repository = providers.Factory(ReportRepository, session=session)
    meta_repository = providers.Factory(MetaRepository, session=session)
    report_answer_repository = providers.Factory(ReportAnswerRepository, session=session)
    crawl_result_repository = providers.Factory(CrawlResultRepository, session=session)

    # Services
    reportit_service = providers.Factory(ReportItService, config=config)
    geocoder_service = providers.Factory(GeocoderService, config=config)

    # Helper function to work around scope limitations with class variables and list comprehension
    # see https://stackoverflow.com/questions/13905741/accessing-class-variables-from-a-list-comprehension-in-the-class-definition
    def inflate_post_processors(
        config,
        reportit_service,
        geocoder_service,
        report_repository,
        meta_repository,
        report_answer_repository,
        crawl_result_repository
    ):
        return [providers.Factory(
            pp,
            config=config,
            api_service=reportit_service,
            geocoder_service=geocoder_service,
            report_repository=report_repository,
            meta_repository=meta_repository,
            report_answer_repository=report_answer_repository,
            crawl_result_repository=crawl_result_repository
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
                crawl_result_repository=crawl_result_repository
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
        crawl_result_repository=crawl_result_repository
    )

    crawler_service = providers.Factory(
        CrawlerService,
        config=config,
        post_processor_dispatcher=post_processor_dispatcher,
        api_service=reportit_service,
        report_repository=report_repository,
        meta_repository=meta_repository,
        report_answer_repository=report_answer_repository,
        crawl_result_repository=crawl_result_repository
    )

def run_with_container(config: dict, callable: Callable, modules: list[str] = ["__main__"]) -> None:
    container = Container()

    container.config.from_dict(config)

    container.wire(modules=modules)

    callable()

    container.shutdown_resources()