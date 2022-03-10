import re, logging, json

from typing import Callable, Optional
from base64 import b64decode
from bs4.element import ResultSet
from bs4 import BeautifulSoup
from datetime import datetime
from requests.models import Response
from requests.sessions import Session
from toolz.dicttoolz import dissoc

from py_reportit.shared.model import *
from py_reportit.shared.model.meta import Meta
from py_reportit.shared.model.report import Report
from py_reportit.shared.model.report_answer import ReportAnswer
from py_reportit.shared.model.answer_meta import ReportAnswerMeta

logger = logging.getLogger(f"py_reportit.{__name__}")

class ReportItService:

    DATE_FORMAT_API = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT_WEB = '%d.%m.%Y %H:%M'

    def __init__(self, config: dict, requests_session: Session):
        self.config = config
        self.requests_session = requests_session

    def get_latest_truncated_report(self) -> Report:
        r = self.requests_session.crawler_get(self.config.get('REPORTIT_API_URL'))

        r.raise_for_status()

        reports_string_raw = b64decode(re.search(self.config.get('REPORTIT_API_REPORTS_REGEX'), r.text).group(1))
        reports_string_escaped = reports_string_raw.decode('raw_unicode_escape')
        raw_reports = json.loads(reports_string_escaped)["reports"]

        most_recent_report = raw_reports[-1]
        return Report(**dissoc(most_recent_report, "thumbnail_url"))

    def get_report_with_answers(self, reportId: int, photo_callback: Optional[Callable[[Report, str], None]] = None) -> Report:
        r = self.fetch_report_page(reportId)

        if r.text.find("Sent on :") < 0:
            raise ReportNotFoundException(f"No report found with id {reportId}")

        soup = BeautifulSoup(r.text, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        report_properties = { "id": reportId }

        # Get title
        header_selection = soup.select(".card-header b")
        raw_header = header_selection[0].text.strip() if len(header_selection) else ""
        title_regex = re.search(r"(?<=\d\s:).*", raw_header)
        report_properties["title"] = title_regex.group().strip() if title_regex else None

        # Get description
        description_selection = soup.select(".card-body .row .card .card-body")
        raw_description = description_selection[0].text.strip() if len(description_selection) else ""
        description_regex = re.search(r"Description\s:\n(.*)", raw_description, re.DOTALL)
        report_properties["description"] = description_regex.group(1).strip() if description_regex else None

        # Get status
        status_regex = re.search(r".*badge\sbg-success.*", r.text)
        report_properties["status"] = "finished" if status_regex else "accepted"

        # Get created datetime
        created_selection = soup.select("table tbody tr:last-child td")
        raw_created = created_selection[0].text.strip() if len(created_selection) else None
        report_properties["created_at"] = datetime.strptime(raw_created, self.DATE_FORMAT_WEB) if raw_created else None

        # Get GPS, image url
        gps_and_image_urls_selection = soup.select(".img-thumbnail")
        report_properties["latitude"], report_properties["longitude"], report_properties["has_photo"] = None, None, False
        if len(gps_and_image_urls_selection) >= 1:
            # Only GPS position
            gps_url = gps_and_image_urls_selection[0]['src']
            gps_regex = re.search(r"center=(\d*\.\d*,\d*\.\d*)", gps_url)
            gps = gps_regex.group(1).strip() if gps_regex else None
            report_properties["latitude"], report_properties["longitude"] = gps.split(',') if gps else (None, None)
        if len(gps_and_image_urls_selection) == 2:
            # Both GPS position and image
            report_properties["has_photo"] = True

        report = Report(**report_properties, meta=Meta())
        answers = self.get_answers(reportId, pre_fetched_page=r)
        report.answers = answers

        if len(answers):
            report.updated_at = answers[-1].created_at
        else:
            report.updated_at = report.created_at
            if report.status == 'finished':
                report.meta.closed_without_answer = True

        if report_properties["has_photo"] and photo_callback:
            base64photo = gps_and_image_urls_selection[1]["src"].split("base64,")[1]
            photo_callback(report, base64photo)

        return report


    def get_answers(self, reportId: int, pre_fetched_page: Response = None) -> list[ReportAnswer]:
        r = pre_fetched_page or self.fetch_report_page(reportId)

        soup = BeautifulSoup(r.text, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        message_blocks = soup.select(".card-body .row:nth-child(2) .card")
        message_dicts = map(self.extract_from_message_block, message_blocks)

        return [ReportAnswer(**message_dict, order=order, report_id=reportId, meta=ReportAnswerMeta()) for order, message_dict in enumerate(message_dicts)]

    def fetch_report_page(self, reportId: int) -> Response:
        r = self.requests_session.crawler_get(
            self.config.get("REPORTIT_API_ANSWER_URL"),
            params={ "session_number": reportId }
        )

        nonces = self.extract_nonces(r.text)
        report_id_input_field_name = self.extract_report_id_input_field(r.text)

        logger.info(f"Using nonce(s) {nonces} and report id input field name {report_id_input_field_name}")

        return self.requests_session.crawler_post(
            self.config.get("REPORTIT_API_ANSWER_URL"),
            { report_id_input_field_name: reportId, **nonces, "session_number": reportId },
            timeout=int(self.config.get("FETCH_REPORTS_TIMEOUT_SECONDS"))
        )
    
    def extract_report_id_input_field(self, html) -> str:
        soup = BeautifulSoup(html, 'html.parser')

        report_id_input_candidates = soup.select("input[required]")

        if not report_id_input_candidates or not len(report_id_input_candidates) \
            or len(report_id_input_candidates) > 1:
            candidates = report_id_input_candidates if report_id_input_candidates else "None"

            raise ReportInputFieldExtractionException(
                f"Could not detect report id input field, candidates: {candidates}"
            )
        
        return report_id_input_candidates[0]["name"]
    
    def extract_nonces(self, html) -> dict:
        soup = BeautifulSoup(html, 'html.parser')

        hidden_fields = soup.select("input[type=hidden]")

        if not hidden_fields or not len(hidden_fields):
            logger.warn("Could not find any nonces")

        return { field["name"]: field["value"] for field in hidden_fields }

    @staticmethod
    def extract_from_message_block(block: ResultSet) -> dict:
        author = block.select(".card-header i")[0].text.strip()
        raw_header = block.select(".card-header")[0].text.strip()
        raw_timestamp = re.search(r"(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})", raw_header).group()
        created_at = datetime.strptime(raw_timestamp, '%d.%m.%Y %H:%M')
        closing = raw_header.split()[0].lower() == "closed"
        raw_text = block.select(".card-body")
        text = raw_text[0].text.strip() if len(raw_text) else ""

        return {
            "author": author,
            "created_at": created_at,
            "closing": closing,
            "text": text
        }

class ReportNotFoundException(Exception):
    pass

class ReportInputFieldExtractionException(Exception):
    pass

class NonceException(Exception):
    pass