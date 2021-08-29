from bs4.element import ResultSet
import requests, re
from bs4 import BeautifulSoup
from datetime import datetime

from py_reportit.model.meta import Meta
from py_reportit.model.report import Report
from py_reportit.model.report_answer import ReportAnswer
from py_reportit.model.answer_meta import ReportAnswerMeta

class ReportItService:

    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, config):
        self.config = config

    def get_reports(self) -> list[Report]:
        r = requests.get(self.config.get('REPORTIT_API_URL'))
        unsorted_reports = list(
            map(
                lambda rawReport: Report(**{**rawReport,
                                         "created_at": datetime.strptime(rawReport['created_at'], self.DATE_FORMAT),
                                         "updated_at": datetime.strptime(rawReport['updated_at'], self.DATE_FORMAT)},
                                        meta=Meta(is_online=True)),
                r.json().get('reports')
            )
        )
        return sorted(unsorted_reports, key=lambda report: report.id)

    def get_answers(self, reportId) -> list[ReportAnswer]:
        r = requests.post(self.config.get("REPORTIT_API_ANSWER_URL"), {"searchId": reportId})

        soup = BeautifulSoup(r.text, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        message_blocks = soup.select(".panel-body .row:nth-child(2) .panel.panel-default")
        message_dicts = map(self.extract_from_message_block, message_blocks)

        return [ReportAnswer(**message_dict, order=order, report_id=reportId, meta=ReportAnswerMeta()) for order, message_dict in enumerate(message_dicts)]

    @staticmethod
    def extract_from_message_block(block: ResultSet) -> dict:
        author = block.select(".panel-heading i")[0].text.strip()
        raw_header = block.select(".panel-heading")[0].text.strip()
        raw_timestamp = re.search("(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})", raw_header).group()
        created_at = datetime.strptime(raw_timestamp, '%d.%m.%Y %H:%M')
        closing = raw_header.split()[0].lower() == "closed"
        raw_text = block.select(".panel-body")
        text = raw_text[0].text.strip() if len(raw_text) else ""

        return {
            "author": author,
            "created_at": created_at,
            "closing": closing,
            "text": text
        }
