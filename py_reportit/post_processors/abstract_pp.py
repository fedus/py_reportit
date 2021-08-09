from abc import ABC, abstractmethod

from py_reportit.repository.report import ReportRepository

class AbstractPostProcessor(ABC):

    def __init__(self, config, report_repository: ReportRepository):
        self.config = config
        self.report_repository = report_repository
        super().__init__()

    @abstractmethod
    def process(self):
        pass
