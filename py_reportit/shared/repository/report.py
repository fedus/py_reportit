from py_reportit.shared.repository.abstract_repository import AbstractRepository
from py_reportit.shared.model.report import Report

class ReportRepository(AbstractRepository[Report]):

    model = Report
