import requests

from py_reportit.model.meta import Meta
from py_reportit.model.report import Report

class ReportItService:

    def __init__(self, config):
        self.config = config

    def get_reports(self) -> list[Report]:
        r = requests.get(self.config.get('REPORTIT_API_URL'))
        unsorted_reports = list(map(lambda rawReport: Report(**rawReport, meta=Meta(is_online=True)), r.json().get('reports')))
        return sorted(unsorted_reports, key=lambda report: report.id)
