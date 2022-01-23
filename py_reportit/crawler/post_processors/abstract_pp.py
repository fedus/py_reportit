import dataclasses

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from py_reportit.crawler.service.geocoder import GeocoderService
from py_reportit.crawler.service.reportit_api import ReportItService
from py_reportit.shared.model.report import Report
from py_reportit.shared.repository.report_answer import ReportAnswerRepository
from py_reportit.shared.repository.meta import MetaRepository
from py_reportit.shared.repository.report import ReportRepository

class PostProcessor(ABC):

    def __init__(self,
                 config: dict,
                 api_service: ReportItService,
                 geocoder_service: GeocoderService,
                 report_repository: ReportRepository,
                 meta_repository: MetaRepository,
                 report_answer_repository: ReportAnswerRepository):
        self.config = config
        self.api_service = api_service
        self.geocoder_service = geocoder_service
        self.report_repository = report_repository
        self.meta_repository = meta_repository
        self.report_answer_repository = report_answer_repository
        super().__init__()

    @abstractmethod
    def process(self, session: Session, new_or_updated_reports: list[Report]):
        pass

@dataclasses.dataclass
class PostProcessorDispatcher:
    post_processors: list[PostProcessor]